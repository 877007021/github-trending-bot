# 🔥 GitHub Trending Bot

自动获取 GitHub Trending 榜单数据，通过 OpenRouter AI 智能解析，生成美观的 HTML 报告，通过 GitHub Pages 每日更新。

## ✨ 功能特性

- 📊 **每日热门榜** - 过去 24 小时 Star 增长最多的项目
- 🚀 **本周升星榜** - 本周 Star 增长最多的项目
- 👑 **本月升星榜** - 本月 Star 增长最多的项目
- 👨‍💻 **热门开发者** - 今日最受关注的开源开发者
- 📚 **历史归档** - 按日期保存所有历史报告
- 🔍 **时间筛选** - 支持按年份/月份筛选历史报告
- 🤖 **AI 解析** - 通过 OpenRouter 免费 AI 模型解析，GitHub 改版也不怕
- 🛡️ **正则回退** - AI 不可用时自动降级为正则解析，双重保障
- 🌐 **GitHub Pages** - 自动部署在线浏览
- ⏰ **定时执行** - 每天北京时间 7:00 自动更新

## 🚀 快速部署

### 1. 创建仓库并推送代码

将本项目代码推送到你的 GitHub 仓库。

### 2. 配置 OpenRouter API Key（推荐但非必须）

> **AI 解析是可选的**。如果没有配置 API Key，系统会自动使用正则回退解析，同样能正常工作。
> 配置 AI 解析的好处是：即使 GitHub 修改了页面 HTML 结构，项目也能持续稳定运行。

1. 注册 [OpenRouter](https://openrouter.ai/) 账号（免费）
2. 获取 API Key
3. 进入仓库 **Settings** → **Secrets and variables** → **Actions**
4. 点击 **New repository secret**
5. Name: `OPENROUTER_API_KEY`，Value: 你的 API Key

### 3. 启用 GitHub Pages

1. 进入仓库 **Settings** → **Pages**
2. Source 选择 **GitHub Actions**

### 4. 等待自动运行或手动触发

工作流会在每天 **UTC 23:00（北京时间 7:00）** 自动执行。

手动触发：
1. 进入 **Actions** 标签页
2. 选择 **GitHub Trending Daily Report**
3. 点击 **Run workflow**

### 5. 查看报告

几分钟后，访问 `https://<你的用户名>.github.io/<仓库名>/` 即可查看。

## 📁 项目结构

```
├── .github/workflows/
│   └── daily-report.yml    # GitHub Actions 工作流配置
├── scripts/
│   ├── fetch_trending.py   # 数据获取（AI 解析 + 正则回退）
│   ├── generate_report.py  # HTML/Markdown 报告生成
│   └── generate_index.py   # 首页索引（含时间筛选）
├── data/                   # JSON 数据存储（按日期归档）
├── docs/                   # 生成的 HTML 报告
│   ├── index.html          # 首页（最新报告 + 历史筛选）
│   └── archive/            # 历史报告归档
└── README.md
```

## ⚙️ 自定义配置

### 修改更新时间

编辑 `.github/workflows/daily-report.yml` 中的 cron 表达式：

```yaml
schedule:
  - cron: '0 23 * * *'  # UTC 23:00 = 北京时间 7:00
```

### 切换 AI 模型

编辑 `scripts/fetch_trending.py` 中的 `DEFAULT_MODEL`：

```python
# 免费自动路由（推荐）
DEFAULT_MODEL = "openrouter/free"

# 或指定某个免费模型
DEFAULT_MODEL = "google/gemini-2.0-flash-exp:free"
DEFAULT_MODEL = "meta-llama/llama-4-maverick:free"
```

### 修改抓取范围

编辑 `scripts/fetch_trending.py`，在 `main()` 函数中添加或删除时间范围：

```python
for since, label in [("daily", "今日"), ("weekly", "本周"), ("monthly", "本月")]:
    repos = fetch_trending_repos(since)
```

## 🔒 安全说明

- **API Key 安全**：`OPENROUTER_API_KEY` 通过 GitHub Secrets 注入，**不会出现在代码或日志中**
- **无硬编码密钥**：代码中不包含任何 API Key
- **最小权限**：GitHub Actions 仅使用必要的权限（contents、pages、id-token）

## 🛠 技术栈

- **数据获取**: Python + Requests
- **AI 解析**: OpenRouter 免费 API（openrouter/free）
- **回退解析**: Python 正则表达式
- **报告生成**: Python（HTML 模板 + JavaScript 筛选）
- **CI/CD**: GitHub Actions
- **部署**: GitHub Pages

## 📄 License

MIT
