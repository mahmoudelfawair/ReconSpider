import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import argparse
import re
import sys
from collections import deque
from colorama import Fore, Style, init
import os
import threading
from queue import Queue

init(autoreset=True)

visited = set()
comments_found = []
sensitive_files_found = []
lock = threading.Lock()

sensitive_patterns = [
    re.compile(r"\.env$"),
    re.compile(r"web\.config$"),
    re.compile(r"settings\.py$"),
    re.compile(r"settings\.php$"),
    re.compile(r"\.bak$"),
    re.compile(r"\.old$"),
    re.compile(r"\.zip$"),
    re.compile(r"\.tar\.gz$"),
    re.compile(r"error\.log$"),
    re.compile(r"access\.log$"),
    re.compile(r"/files/?$"),
    re.compile(r"/backup/?$"),
    re.compile(r"/admin/?$"),
]

def normalize_link(base, link):
    return urljoin(base, link.split('#')[0].strip())

def is_internal(url, domain):
    return domain in urlparse(url).netloc

def should_visit(url, domain):
    return is_internal(url, domain) and url not in visited and not re.search(r"\.(jpg|jpeg|png|gif|svg|css|js|ico|woff|woff2|ttf)$", url)

def extract_comments(html):
    return re.findall(r"<!--(.*?)-->", html, re.DOTALL)

def print_color(text, color):
    print(color + text + Style.RESET_ALL)

def fetch(url):
    try:
        response = requests.get(url, timeout=5, verify=False)
        if response.status_code == 200:
            return response.text
    except requests.RequestException:
        pass
    return None

def process_url(url, domain, queue):
    with lock:
        if url in visited:
            return
        visited.add(url)
    html = fetch(url)
    if html:
        print_color(f"[+] Visited: {url}", Fore.GREEN)
        comments = extract_comments(html)
        for comment in comments:
            print_color(f"    [COMMENT] {comment.strip()[:100]}", Fore.YELLOW)
            with lock:
                comments_found.append((url, comment.strip()))

        for pattern in sensitive_patterns:
            if pattern.search(url):
                print_color(f"    [SENSITIVE] {url}", Fore.RED)
                with lock:
                    sensitive_files_found.append(url)

        soup = BeautifulSoup(html, 'html.parser')
        for link in soup.find_all('a', href=True):
            new_url = normalize_link(url, link['href'])
            if should_visit(new_url, domain):
                queue.put(new_url)

def crawl_bfs_threaded(seed, domain, thread_count=5):
    queue = Queue()
    queue.put(seed)

    def worker():
        while True:
            url = queue.get()
            if url is None:
                break
            process_url(url, domain, queue)
            queue.task_done()

    threads = []
    for _ in range(thread_count):
        t = threading.Thread(target=worker)
        t.start()
        threads.append(t)

    queue.join()

    for _ in threads:
        queue.put(None)
    for t in threads:
        t.join()

def crawl_dfs(url, domain, max_depth, current_depth=0):
    with lock:
        if url in visited or current_depth > max_depth:
            return
        visited.add(url)
    html = fetch(url)
    if html:
        print_color(f"[+] Visited: {url}", Fore.GREEN)
        comments = extract_comments(html)
        for comment in comments:
            print_color(f"    [COMMENT] {comment.strip()[:100]}", Fore.YELLOW)
            with lock:
                comments_found.append((url, comment.strip()))

        for pattern in sensitive_patterns:
            if pattern.search(url):
                print_color(f"    [SENSITIVE] {url}", Fore.RED)
                with lock:
                    sensitive_files_found.append(url)

        soup = BeautifulSoup(html, 'html.parser')
        for link in soup.find_all('a', href=True):
            new_url = normalize_link(url, link['href'])
            if should_visit(new_url, domain):
                crawl_dfs(new_url, domain, max_depth, current_depth + 1)

def main():
    parser = argparse.ArgumentParser(description="Recon Spider - A simple web crawler for recon tasks")
    parser.add_argument('--url', required=True, help='Seed URL to start crawling from')
    parser.add_argument('--mode', choices=['bfs', 'dfs'], default='bfs', help='Crawling mode (bfs or dfs)')
    parser.add_argument('--depth', type=int, default=3, help='Depth limit for DFS mode')
    parser.add_argument('--output', help='Save results to file')
    parser.add_argument('--respect-robots', action='store_true', help='Respect robots.txt (optional)')
    parser.add_argument('--threads', type=int, default=5, help='Number of threads for BFS crawling')
    args = parser.parse_args()

    domain = urlparse(args.url).netloc

    if args.respect_robots:
        robots_url = urljoin(args.url, '/robots.txt')
        try:
            robots = requests.get(robots_url, timeout=5)
            print_color(f"[*] Fetched robots.txt from {robots_url}", Fore.CYAN)
            print(robots.text)
        except:
            print_color(f"[!] Failed to fetch robots.txt", Fore.RED)

    if args.mode == 'bfs':
        crawl_bfs_threaded(args.url, domain, args.threads)
    else:
        crawl_dfs(args.url, domain, args.depth)

    if args.output:
        with open(args.output, 'w') as f:
            f.write(f"Total pages visited: {len(visited)}\n")
            f.write(f"Comments extracted: {len(comments_found)}\n")
            f.write("Sensitive files found:\n")
            for item in sensitive_files_found:
                f.write(f"- {item}\n")

    print("\n--- Summary ---")
    print(f"Total pages visited: {len(visited)}")
    print(f"Comments extracted: {len(comments_found)}")
    print(f"Sensitive files found: {len(sensitive_files_found)}")
    for file in sensitive_files_found:
        print_color(f"[!] {file}", Fore.RED)

    for comment_url, comment_text in comments_found:
        if "file" in comment_text.lower() and any("/files" in url for url in sensitive_files_found):
            print_color(f"[*] Possible correlation found: '{comment_text.strip()[:60]}' hints at /files/ on {comment_url}", Fore.MAGENTA)

if __name__ == '__main__':
    requests.packages.urllib3.disable_warnings()
    main()
