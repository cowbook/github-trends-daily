#!/usr/bin/env python3
"""GitHub Trending Scraper - v4: 精确保号提取"""

import json
import re
import sys
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import URLError


TRENDING_URL = "https://github.com/trending"


def scrape_trending() -> list[dict]:
    """抓取 GitHub Trending 页面"""
    req = Request(TRENDING_URL, headers={
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-US,en;q=0.9",
    })

    try:
        with urlopen(req, timeout=30) as resp:
            html = resp.read().decode("utf-8")
    except URLError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    articles = re.split(r'<article\s+class="Box-row[^"]*">', html)[1:]
    repos = []

    for article in articles:
        repo = {}

        # --- Repo name from h2 ---
        # Extract h2 content first, then find the repo link inside it
        h2_content_match = re.search(r'<h2[^>]*>(.*?)</h2>', article, re.DOTALL)
        if not h2_content_match:
            continue
        h2_content = h2_content_match.group(1)
        link_match = re.search(r'<a[^>]*href="(/[^"]+)"', h2_content)
        if not link_match:
            continue
        repo_path = link_match.group(1)
        repo["url"] = "https://github.com" + repo_path
        parts = repo_path.strip("/").split("/")
        if len(parts) >= 2:
            repo["repo"] = f"{parts[0]} / {parts[1]}"
        else:
            repo["repo"] = repo_path

        # --- Description ---
        desc_match = re.search(r'<p\b[^>]*>\s*(.+?)\s*</p>', article, re.DOTALL)
        if desc_match:
            desc = re.sub(r'<[^>]+>', '', desc_match.group(1))
            desc = re.sub(r'\s+', ' ', desc).strip()
            repo["description"] = desc
        else:
            repo["description"] = ""

        # --- Language ---
        lang_match = re.search(r'itemprop="programmingLanguage"[^>]*>\s*(\S[^<]*)', article)
        repo["language"] = lang_match.group(1).strip() if lang_match else "Unknown"

        # --- Numbers ---
        # Strategy: plain text is "... <language> <total_stars> <total_forks> Built by ... <stars_today> stars today"
        plain = re.sub(r'<[^>]+>', ' ', article)
        plain = re.sub(r'\s+', ' ', plain).strip()

        # Find "X stars today"
        stars_today_match = re.search(r'(\d[\d,]*)\s*stars?\s*today', plain)
        repo["stars_today"] = int(stars_today_match.group(1).replace(",", "")) if stars_today_match else 0

        # Find language position, then grab next two numbers
        lang_pos = plain.find(repo["language"])
        if lang_pos >= 0:
            after_lang = plain[lang_pos + len(repo["language"]):]
            nums = re.findall(r'(\d[\d,]*)', after_lang)
            if len(nums) >= 2:
                repo["total_stars"] = int(nums[0].replace(",", ""))
                repo["total_forks"] = int(nums[1].replace(",", ""))

                # Sanity check: sometimes the order gets confused
                # If stars_today > total_stars, something's wrong
                if repo["stars_today"] > repo["total_stars"] and len(nums) >= 3:
                    # Try taking the next number
                    for n in nums:
                        val = int(n.replace(",", ""))
                        if val > repo["stars_today"]:
                            repo["total_stars"] = val
                            break
            else:
                repo["total_stars"] = 0
                repo["total_forks"] = 0
        else:
            repo["total_stars"] = 0
            repo["total_forks"] = 0

        # --- Contributors ---
        contributors = re.findall(r'<img[^>]+alt="@(\w+)"', article)
        repo["contributors"] = contributors

        repos.append(repo)

    return repos


def main():
    repos = scrape_trending()

    data = {
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "count": len(repos),
        "repos": repos,
    }

    output_path = sys.argv[1] if len(sys.argv) > 1 else "data/latest.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Scraped {len(repos)} repos -> {output_path}")


if __name__ == "__main__":
    main()
