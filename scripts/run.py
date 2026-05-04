#!/usr/bin/env python3
"""
主控脚本：一键执行抓取 → 生成博文 → 构建网站
"""

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).parent.parent
SCRIPTS = ROOT / "scripts"
DATA_DIR = ROOT / "data"
SITE_DIR = ROOT / "site"
POSTS_DIR = SITE_DIR / "posts"


def run(cmd: list[str]) -> None:
    """Run a command and check result"""
    result = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Error: {' '.join(cmd)}")
        print(result.stderr)
        sys.exit(1)
    print(result.stdout)


def main():
    print("=" * 60)
    print("  GitHub Trends Daily - Build Pipeline")
    print("=" * 60)
    print()

    # 1. Ensure directories
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    POSTS_DIR.mkdir(parents=True, exist_ok=True)

    # 2. Scrape trending data
    print("📡 Step 1: Scraping GitHub Trending...")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    data_file = DATA_DIR / f"{today}.json"
    latest_file = DATA_DIR / "latest.json"

    run([sys.executable, str(SCRIPTS / "scraper.py"), str(data_file)])

    # Copy to latest.json for convenience
    import shutil
    shutil.copy(data_file, latest_file)

    # 3. Generate blog post
    print("\n📝 Step 2: Generating humorous blog post...")
    md_file = POSTS_DIR / f"{today}.md"
    run([sys.executable, str(SCRIPTS / "generate_post.py"), str(data_file), str(md_file)])

    # 4. Save post metadata for site building
    with open(data_file, encoding="utf-8") as f:
        data = json.load(f)

    # Read title from generated markdown
    with open(md_file, encoding="utf-8") as f:
        first_line = f.readline().replace("# ", "").strip()

    total_stars_today = sum(r["stars_today"] for r in data["repos"])

    post_meta = {
        "date": data["date"],
        "slug": data["date"],
        "title": first_line,
        "repo_count": len(data["repos"]),
        "total_stars_today": total_stars_today,
    }

    meta_file = POSTS_DIR / f"{today}.json"
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(post_meta, f, ensure_ascii=False, indent=2)

    # 5. Build static site
    print("\n🏗️  Step 3: Building static site...")
    run([sys.executable, str(SCRIPTS / "build_site.py")])

    # 6. Summary
    print()
    print("=" * 60)
    print("  ✅ Build Complete!")
    print(f"     Date: {today}")
    print(f"     Repos scraped: {len(data['repos'])}")
    print(f"     Stars today: {total_stars_today:,}")
    print(f"     Site ready at: {SITE_DIR}/")
    print("=" * 60)


if __name__ == "__main__":
    main()
