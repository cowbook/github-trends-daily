#!/usr/bin/env python3
"""
GitHub Trending 幽默博文生成器
将枯燥的趋势数据变成风趣幽默的每日点评
"""

import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path


# ============================================================
# 幽默段子模板库
# ============================================================

# 开场金句
OPENING_LINES = [
    "又到了每天「看看别人在写什么，然后默默关掉继续写 CRUD」的时刻 🤡",
    "GitHub Trending 今日播报：人类又在重复造轮子了，但这次的轮子能自动驾驶 🚗",
    "欢迎收看本期《GitHub 动物园》：每天都有新品种的代码生物被发现 🦄",
    "今日 Trending 速递 —— 看看哪些项目在让程序员们疯狂 Star，然后忘记自己也要写代码 😅",
    "又一天过去了。又有 25 个新框架诞生了。前端开发者表示情绪稳定 🔥",
    "早上好！今天的 GitHub Trending 菜单已更新，主厨推荐：新鲜的造轮子和陈年老 Bug 🍽️",
    "震惊！这些 GitHub 项目今天竟然获得了这么多 Star！第 3 个我直接好家伙 🤯",
]

# Repo 点评模板：根据语言/repo特征生成
LANGUAGE_JOKES = {
    "Python": [
        "Python 玩家又发力了，这次不写爬虫改写{thing}了 🐍",
        "又一个 Python 项目登顶 —— 毕竟人生苦短，我用 Python（然后花三天配环境）",
        "Python 党的胜利！虽然跑得慢，但我们写得快啊 ✍️",
    ],
    "JavaScript": [
        "JavaScript 项目再次屠榜。前端：今天的我也在创造历史（和 node_modules 黑洞）🕳️",
        "npm install 一下，你的硬盘少了 5GB —— 但世界多了个新框架 🌐",
        "JavaScript 圈今日新瓜：{repo} 又双叒叕火了。下周可能就过时了，珍惜当下 🙏",
    ],
    "TypeScript": [
        "TypeScript 玩家优雅路过。没有类型的人生是不完整的人生 ✨",
        "TS 项目冲上 Trending：把 JS 的坑填上，然后优雅地掉进新坑 🎩",
        "TypeScript 趋势：我们不写 Bug，我们只写「类型不匹配」📐",
    ],
    "Rust": [
        "Rust 项目上榜！Rustacean 们举起你们的 Ferris！虽然编译了半小时 🦀",
        "Rust：让编译器替你写代码（如果它能编译通过的话）⚙️",
        "Rust 又火了。owner 说这不是重写，是「内存安全的升级」💪",
    ],
    "Go": [
        "Go 语言项目：简单、高效、没有泛型……哦等等，现在有了 🤷",
        "Gopher 又出手了。Go 的哲学：能用一个 goroutine 解决的就绝不用两个 🏃",
    ],
    "C": [
        "C 语言项目上榜！向所有还在手动管理内存的勇士致敬 🫡",
        "C 语言：segfault 是程序员最好的老师 💀",
    ],
    "C++": [
        "C++ 项目来了。template< typename T > 能解决一切问题，包括制造问题 🧩",
        "C++：我写了 20 年代码，依然不知道 undefinced behavior 是什么行为 🤔",
    ],
}

# 通用搞笑点评
GENERAL_JOKES = [
    "今天刚上线就收割 {stars} 个 Star，比我在公司一个季度写的代码还多 ⭐",
    "这个仓库证明了一件事：README 写得好，Star 少不了 📝",
    "建议改名为「{repo}：一个让面试官闭嘴的项目」💼",
    "当你看到 {stars_today} stars/day 的时候，就知道又一个「Hello World」项目火了 🔥",
    "项目简介翻译成人话：{desc_short}……剩下的自己体会 😏",
    "这个项目告诉我们：只要 Star 够多，Bug 就是 Feature 🐛✨",
    "建议直接 Fork，然后在简历上写「参与了顶尖开源项目开发」📋",
    "又一个「我用 XXX 重写了 YYY」的项目，但这次真的不一样！大概吧。🔄",
    "看完这个项目，我默默打开了 VSCode……然后继续摸鱼 🐟",
]

# 收尾幽默
CLOSING_LINES = [
    "\n> 以上就是今天的 GitHub Trending 速报。明天同一时间，我们继续围观人类如何用代码改变世界（或者只是改变 node_modules 的大小）。\n",
    "\n> 今日播报完毕。记住：Star 再多，不如你的代码能跑。晚安，搬砖人 💤\n",
    "\n> 今天的 Trending 告诉我们：好的 README 是成功的一半，剩下一半是运气。明天见 👋\n",
    "\n> 以上就是今天的「别人家的代码」时间。现在，请回到你的 IDE，面对你的 Bug 🪲\n",
    "\n> 今日盘点结束。友情提示：欣赏开源项目很美好，但请不要在生产环境直接 git clone 然后 import * 🚨\n",
    "\n> 播报完毕。如果你觉得今天的内容还不错，请 Star 本项目（不是上面那些，是本项目！）🌟\n",
]


def pick_joke(repo: dict, joke_list: list) -> str:
    """从列表随机选一个，用 repo 数据填充"""
    template = random.choice(joke_list)
    desc = repo.get("description", "nothing")
    desc_short = desc[:80] + ("..." if len(desc) > 80 else "")
    repo_name = repo.get("repo", "unknown").split("/")[-1]
    return template.format(
        repo=repo_name,
        stars=repo.get("total_stars", 0),
        stars_today=repo.get("stars_today", 0),
        desc_short=desc_short,
        thing=desc_short[:20] or "AI",
        lang=repo.get("language", "Unknown"),
    )


def generate_hot_take(repo: dict) -> str:
    """为单个 repo 生成一句幽默点评"""
    lang = repo.get("language", "Unknown")

    # 70% 概率用语言相关梗，30% 通用梗
    if lang in LANGUAGE_JOKES and random.random() < 0.7:
        return pick_joke(repo, LANGUAGE_JOKES[lang])
    else:
        return pick_joke(repo, GENERAL_JOKES)


def generate_title(repos: list[dict], date_str: str) -> str:
    """生成博文标题"""
    if not repos:
        return f"GitHub Trending {date_str}：今天没人写代码？"

    top = repos[0]
    top_name = top["repo"].split("/")[-1]

    titles = [
        f"GitHub Trending {date_str}：{top_name} 领跑，{len(repos)} 个项目杀入榜单",
        f"今日 GitHub 热搜：{top_name} 成最大赢家，还有 {len(repos)-1} 个陪跑选手",
        f"GitHub {date_str} 趋势榜：{top_name} 一骑绝尘，后面 {len(repos)-1} 个项目表示不服",
        f"【GitHub 日报】{date_str}：今天 {top_name} 最火，程序员的品味终于正常了？",
    ]
    return random.choice(titles)


def generate_post(data: dict) -> str:
    """生成完整的 Markdown 博文"""
    date_str = data["date"]
    repos = data["repos"]

    opening = random.choice(OPENING_LINES)
    closing = random.choice(CLOSING_LINES)
    title = generate_title(repos, date_str)

    lines = [
        f"# {title}",
        "",
        f"📅 {date_str} | 🔗 {len(repos)} 个项目 | ⏰ 每日更新",
        "",
        opening,
        "",
        "---",
        "",
    ]

    # 排行榜
    for i, repo in enumerate(repos, 1):
        name = repo["repo"]
        url = repo["url"]
        desc = repo["description"] or "（作者懒得写描述，但这不重要，Star 够多就行）"
        lang = repo["language"]
        stars = repo["total_stars"]
        stars_today = repo["stars_today"]
        forks = repo["total_forks"]

        # 奖牌 emoji
        if i == 1:
            medal = "🥇"
        elif i == 2:
            medal = "🥈"
        elif i == 3:
            medal = "🥉"
        else:
            medal = f"{i}."

        lines.extend(
            [
                f"## {medal} [{name}]({url})",
                "",
                f"📝 {desc}",
                "",
                f"⭐ {stars:,} total | 🍴 {forks:,} forks | 🔥 +{stars_today:,} today | 🏷️ {lang}",
                "",
                f"> {generate_hot_take(repo)}",
                "",
            ]
        )

    # 数据总结
    total_stars_today = sum(r["stars_today"] for r in repos)
    languages = set(r["language"] for r in repos if r["language"] != "Unknown")

    lines.extend(
        [
            "---",
            "",
            "## 📊 今日数据小结",
            "",
            f"- 上榜项目：{len(repos)} 个",
            f"- 今日总新增 Star：{total_stars_today:,} ⭐",
            f"- 涉及语言：{', '.join(sorted(languages))}",
            f"- 一句话总结：今天又是 {'AI 和 LLM' if any('AI' in r.get('description','') or 'LLM' in r.get('description','') or 'GPT' in r.get('description','') for r in repos) else '程序员们'} 统治 GitHub 的一天",
            "",
            closing,
        ]
    )

    return "\n".join(lines)


def main():
    import sys

    input_file = sys.argv[1] if len(sys.argv) > 1 else "data/latest.json"
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    with open(input_file, encoding="utf-8") as f:
        data = json.load(f)

    markdown = generate_post(data)

    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(markdown)
        print(f"Post generated -> {output_file}")
    else:
        print(markdown)


if __name__ == "__main__":
    main()
