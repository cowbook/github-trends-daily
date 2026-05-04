# GitHub Trends Daily 🔥

每天自动抓取 GitHub Trending，用幽默风趣的中文段子点评最热开源项目。

## ✨ 特性

- 🤖 **全自动**：GitHub Actions 每日定时抓取，无需手动操作
- 😂 **幽默点评**：每个上榜项目都有风趣的中文段子
- 🎨 **简洁大气**：响应式设计，移动端友好
- 📡 **RSS 订阅**：支持 RSS 阅读器
- 🆓 **完全免费**：基于 GitHub Pages，零成本部署

## 🚀 快速开始

### 1. Fork 本项目

点击右上角 Fork 按钮，复制到你自己的账号下。

### 2. 启用 GitHub Pages

1. 进入仓库 Settings → Pages
2. Source 选择 "GitHub Actions"
3. 保存

### 3. 启用 Workflow 权限

1. 进入仓库 Settings → Actions → General
2. Workflow permissions 选择 "Read and write permissions"
3. 保存

### 4. 手动触发首次运行

1. 进入 Actions 标签页
2. 选择 "Daily GitHub Trends" workflow
3. 点击 "Run workflow"

等待几分钟，你的网站就上线了！访问 `https://你的用户名.github.io/github-trends-daily/`

## 📁 项目结构

```
github-trends-daily/
├── .github/workflows/daily.yml   # GitHub Actions 自动运行配置
├── scripts/
│   ├── scraper.py                # 爬虫：抓取 GitHub Trending
│   ├── generate_post.py          # 生成器：幽默博文生成
│   ├── build_site.py             # 构建器：Markdown → HTML
│   └── run.py                    # 主控：一键执行全流程
├── data/                         # 原始数据（JSON）
├── site/                         # 生成的静态网站
│   ├── index.html
│   ├── archive.html
│   ├── about.html
│   ├── css/style.css
│   ├── rss.xml
│   └── posts/                    # 每日博文
├── templates/                    # HTML 模板
├── requirements.txt
└── README.md
```

## 🛠 本地运行

```bash
# 安装依赖
pip install -r requirements.txt

# 一键运行
python scripts/run.py

# 查看生成的网站
# 打开 site/index.html
```

## 📝 自定义

- **添加 AI 点评**：在 `generate_post.py` 中接入 OpenAI/Claude API，让段子更智能
- **修改风格**：编辑 `site/css/style.css` 自定义配色
- **调整频率**：修改 `.github/workflows/daily.yml` 中的 cron 表达式

## 📄 许可

MIT License
