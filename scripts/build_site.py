#!/usr/bin/env python3
"""
静态网站构建器 - 将博文 Markdown + 数据生成纯静态 HTML 站点
"""

import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

SITE_DIR = Path("site")
DATA_DIR = Path("data")
POSTS_DIR = SITE_DIR / "posts"
BASE_PATH = os.getenv("PAGES_BASE_PATH", "/github-trends-daily").rstrip("/")
DEFAULT_SITE_URL = "https://cowbook.github.io/github-trends-daily/"
SITE_URL = os.getenv("SITE_URL", DEFAULT_SITE_URL).rstrip("/") + "/"


def _with_base(path: str) -> str:
    """将站内路径拼接到 GitHub Pages project site base path 下"""
    path = path.lstrip("/")
    if BASE_PATH:
        return f"{BASE_PATH}/{path}" if path else f"{BASE_PATH}/"
    return f"/{path}" if path else "/"


def build_html_page(title: str, body_html: str, extra_head: str = "") -> str:
    """用一致的模板包裹 HTML 内容"""
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} | GitHub Trends Daily</title>
    <meta name="description" content="GitHub 每日趋势幽默点评 - 用段子的方式看懂开源世界">
    <link rel="stylesheet" href="{_with_base('css/style.css')}">
    <link rel="alternate" type="application/rss+xml" href="{_with_base('rss.xml')}" title="GitHub Trends Daily">
    {extra_head}
</head>
<body>
    <header class="site-header">
        <div class="container">
            <a href="{_with_base('')}" class="logo">🔥 GitHub Trends Daily</a>
            <nav>
                <a href="{_with_base('')}">首页</a>
                <a href="{_with_base('archive.html')}">归档</a>
                <a href="{_with_base('about.html')}">关于</a>
                <a href="https://github.com/cowbook/github-trends-daily" target="_blank">GitHub</a>
            </nav>
        </div>
    </header>
    <main class="container">
        {body_html}
    </main>
    <footer class="site-footer">
        <div class="container">
            <p>GitHub Trends Daily © {datetime.now().year} · 用幽默的方式看懂开源世界</p>
            <p>数据来源 <a href="https://github.com/trending">GitHub Trending</a> · 每日自动更新</p>
        </div>
    </footer>
</body>
</html>"""


def md_to_html(md_text: str) -> str:
    """简易 Markdown -> HTML（不需要第三方库）"""
    lines = md_text.split("\n")
    html_lines = []
    in_code_block = False
    in_blockquote = False

    for line in lines:
        # Code blocks
        if line.startswith("```"):
            if in_code_block:
                html_lines.append("</pre></code>")
                in_code_block = False
            else:
                html_lines.append('<code><pre style="background:#1e1e2e;color:#cdd6f4;padding:1rem;border-radius:8px;overflow-x:auto;">')
                in_code_block = True
            continue

        if in_code_block:
            html_lines.append(line.replace("<", "&lt;").replace(">", "&gt;"))
            continue

        # Horizontal rule
        if line.strip() == "---":
            html_lines.append('<hr class="divider">')
            continue

        # Headings
        if line.startswith("### "):
            html_lines.append(f"<h3>{line[4:]}</h3>")
            continue
        if line.startswith("## "):
            html_lines.append(f"<h2>{line[3:]}</h2>")
            continue
        if line.startswith("# "):
            html_lines.append(f"<h1>{line[2:]}</h1>")
            continue

        # Blockquotes
        if line.startswith("> "):
            quote_content = line[2:]
            # Process inline markdown in quote
            quote_content = _process_inline(quote_content)
            if not in_blockquote:
                html_lines.append(f'<blockquote><p>{quote_content}')
                in_blockquote = True
            else:
                html_lines.append(f'<br>{quote_content}')
            continue
        else:
            if in_blockquote:
                html_lines.append('</p></blockquote>')
                in_blockquote = False

        # Images
        if line.startswith("!["):
            # ![alt](url)
            import re
            m = re.match(r"!\[([^\]]*)\]\(([^)]+)\)", line)
            if m:
                html_lines.append(f'<img src="{m.group(2)}" alt="{m.group(1)}" class="content-img">')
                continue

        # Lists
        if line.startswith("- "):
            html_lines.append(f"<li>{_process_inline(line[2:])}</li>")
            continue

        # Empty line
        if not line.strip():
            html_lines.append("")
            continue

        # Regular paragraph
        html_lines.append(f"<p>{_process_inline(line)}</p>")

    if in_blockquote:
        html_lines.append("</p></blockquote>")

    return "\n".join(html_lines)


def _process_inline(text: str) -> str:
    """处理行内格式：**bold**, *italic*, `code`, [links]"""
    import re

    # Bold
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    # Italic
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    # Inline code
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    # Links
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2" target="_blank" rel="noopener">\1</a>', text)
    # Emoji: keep as-is for now

    return text


def build_index() -> None:
    """构建首页：显示最近的博文列表"""
    posts_meta = _get_posts_meta()

    post_cards = ""
    for meta in posts_meta[:15]:  # 首页显示最近 15 篇
        post_url = _with_base(f"posts/{meta['slug']}.html")
        post_cards += f"""
        <article class="post-card">
            <time datetime="{meta['date']}">{meta['date']}</time>
            <h2><a href="{post_url}">{meta['title']}</a></h2>
            <p class="post-meta">📦 {meta['repo_count']} 个上榜项目 · ⭐ {meta['total_stars_today']:,} 今日新增</p>
        </article>"""

    body = f"""
    <section class="hero">
        <h1>🔥 GitHub Trends Daily</h1>
        <p>每天用幽默的方式，点评 GitHub 上最火的开源项目</p>
        <p class="hero-sub">人类高质量代码鉴赏 · 每日自动更新 · 纯属娱乐请勿当真</p>
    </section>
    <section class="post-list">
        <h2>📰 最新博文</h2>
        {post_cards or '<p class="empty">暂无博文，请稍候…</p>'}
    </section>
    <section class="cta">
        <p>⭐ 喜欢这个项目？去 <a href="https://github.com/cowbook/github-trends-daily">GitHub</a> 给个 Star 吧！</p>
    </section>
    """

    html = build_html_page("GitHub Trends Daily", body)
    (SITE_DIR / "index.html").write_text(html, encoding="utf-8")
    print("Built: index.html")


def build_archive() -> None:
    """构建归档页"""
    posts_meta = _get_posts_meta()

    post_items = ""
    for meta in posts_meta:
        post_url = _with_base(f"posts/{meta['slug']}.html")
        post_items += f"""
        <li>
            <time>{meta['date']}</time>
            <a href="{post_url}">{meta['title']}</a>
            <span class="archive-stats">({meta['repo_count']} repos, +{meta['total_stars_today']:,} ⭐)</span>
        </li>"""

    body = f"""
    <h1>📚 归档</h1>
    <p>全部博文，按日期排列</p>
    <ul class="archive-list">
        {post_items or '<li>暂无归档</li>'}
    </ul>
    """

    html = build_html_page("归档 | GitHub Trends Daily", body)
    (SITE_DIR / "archive.html").write_text(html, encoding="utf-8")
    print("Built: archive.html")


def build_about() -> None:
    """构建关于页"""
    body = """
    <h1>💡 关于</h1>
    <section class="about-content">
        <h2>这是什么？</h2>
        <p>GitHub Trends Daily 是一个自动化的开源项目，每天抓取 GitHub Trending 页面数据，然后用幽默的风格撰写博文点评。</p>

        <h2>为什么做这个？</h2>
        <p>因为 GitHub Trending 太枯燥了！一堆数字和仓库名，看得眼花。我们用段子的方式让你秒懂今天的开源热点。</p>

        <h2>技术栈</h2>
        <ul>
            <li>🐍 Python 爬虫抓取数据</li>
            <li>📝 模板引擎生成幽默博文</li>
            <li>🌐 纯静态 HTML/CSS 网站</li>
            <li>⚡ GitHub Actions 每日自动更新</li>
            <li>🚀 GitHub Pages 免费部署</li>
        </ul>

        <h2>免责声明</h2>
        <p>本项目纯属娱乐，点评内容为 AI 生成，不代表任何立场。数据来源 GitHub Trending，每日 UTC 时间自动更新。</p>
    </section>
    """

    html = build_html_page("关于 | GitHub Trends Daily", body)
    (SITE_DIR / "about.html").write_text(html, encoding="utf-8")
    print("Built: about.html")


def _get_posts_meta() -> list[dict]:
    """获取所有博文的元数据"""
    posts = []
    if not POSTS_DIR.exists():
        return posts

    for json_file in sorted(POSTS_DIR.glob("*.json"), reverse=True):
        try:
            data = json.loads(json_file.read_text(encoding="utf-8"))
            posts.append(data)
        except (json.JSONDecodeError, KeyError):
            continue

    return posts


def build_single_post(data_file: Path) -> None:
    """为单个博文构建 HTML 页面"""
    with open(data_file, encoding="utf-8") as f:
        data = json.load(f)

    # 查找对应的 Markdown 文件
    md_file = data_file.with_suffix(".md")
    if md_file.exists():
        md_content = md_file.read_text(encoding="utf-8")
    else:
        md_content = f"# 数据加载中..."

    # 提取标题（第一行的 # 标题）
    title_line = md_content.split("\n")[0].replace("# ", "")
    body_html = md_to_html("\n".join(md_content.split("\n")[1:]))

    # Open Graph meta
    extra_head = f"""
    <meta property="og:title" content="{data.get('title', title_line)}">
    <meta property="og:type" content="article">
    <meta property="og:description" content="{data.get('title', 'GitHub Trends Daily')}">
    """

    html = build_html_page(title_line, body_html, extra_head)
    slug = data["date"]
    output_path = POSTS_DIR / f"{slug}.html"
    output_path.write_text(html, encoding="utf-8")
    print(f"Built: posts/{slug}.html")


def build_rss() -> None:
    """生成 RSS Feed"""
    posts_meta = _get_posts_meta()

    items = ""
    for meta in posts_meta[:20]:
        post_link = f"{SITE_URL}posts/{meta['slug']}.html"
        items += f"""
    <item>
        <title>{meta.get('title', meta['date'])}</title>
        <link>{post_link}</link>
        <description>GitHub Trending {meta['date']} - {meta.get('repo_count', 0)} repos, +{meta.get('total_stars_today', 0)} stars</description>
        <pubDate>{meta['date']}T00:00:00Z</pubDate>
        <guid>{post_link}</guid>
    </item>"""

    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
    <title>GitHub Trends Daily</title>
    <link>{SITE_URL}</link>
    <description>GitHub 每日趋势幽默点评</description>
    <language>zh-CN</language>
    {items}
</channel>
</rss>"""

    (SITE_DIR / "rss.xml").write_text(rss, encoding="utf-8")
    print("Built: rss.xml")


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-file", help="单个博文数据文件路径")
    parser.add_argument("--all", action="store_true", default=True)
    args = parser.parse_args()

    SITE_DIR.mkdir(parents=True, exist_ok=True)
    POSTS_DIR.mkdir(parents=True, exist_ok=True)

    if args.data_file:
        build_single_post(Path(args.data_file))
    else:
        # 构建所有页面
        build_index()
        build_archive()
        build_about()
        build_rss()

        # 构建所有博文页面
        for data_file in sorted(POSTS_DIR.glob("*.json")):
            build_single_post(data_file)

    print("\n✅ Site built successfully!")


if __name__ == "__main__":
    main()
