Recon Spider 🕷️
================

Recon Spider is a command-line Python web crawler designed for web reconnaissance. It supports both breadth-first and depth-first search modes, detects sensitive files and directories, extracts HTML comments, and reports findings in real time with color-coded output. Threading support is included for faster crawling in BFS mode.

Features
--------
- 🔎 Recursive crawling of internal links only
- 🗃️ Extraction of HTML comments
- 📁 Detection of potentially sensitive files (e.g., `.env`, `settings.py`, `.bak`, `/admin/`)
- 🌐 BFS and DFS crawling modes
- ⚙️ Optional `robots.txt` handling
- 🎨 Colored output using `colorama`
- 🧵 Multithreaded crawling in BFS mode
- 📄 Optional results export to a file
- 🧠 Basic correlation between comments and exposed paths

Installation
------------
```bash
git clone https://github.com/mahmoudelfawair/ReconSpider.git
cd ReconSpider
pip install -r requirements.txt
```

Usage
-----
```bash
python recon_spider.py --url http://example.com [options]
```

Options
-------
| Argument             | Description                                              |
|----------------------|----------------------------------------------------------|
| `--url`              | Seed URL to start crawling (required)                   |
| `--mode`             | Crawling mode: `bfs` or `dfs` (default: bfs)            |
| `--depth`            | Depth for DFS mode (default: 3)                         |
| `--output`           | Save results to a specified file                        |
| `--respect-robots`   | Optionally respect `robots.txt`                         |
| `--threads`          | Number of threads to use in BFS (default: 5)            |

Example
-------
```bash
python recon_spider.py --url http://testphp.vulnweb.com --mode bfs --threads 10 --output report.txt
```

Sample Output
-------------
- ✅ Green: Pages visited
- ⚠️ Yellow: HTML comments
- ❗ Red: Sensitive files or paths
- 🔍 Magenta: Detected correlation (comment mentions "file" and `/files/` exists)
