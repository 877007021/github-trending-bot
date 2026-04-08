#!/usr/bin/env python3
"""
HTML 报告生成脚本
根据 JSON 数据生成美观的 HTML 报告页面
"""

import json
import os
from datetime import datetime, timezone, timedelta

CST = timezone(timedelta(hours=8))
TODAY = datetime.now(CST).strftime("%Y-%m-%d")
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DOCS_DIR = os.path.join(BASE_DIR, "docs")
os.makedirs(DOCS_DIR, exist_ok=True)
os.makedirs(os.path.join(DOCS_DIR, "archive"), exist_ok=True)


def load_json(filename):
    filepath = os.path.join(DATA_DIR, filename)
    if not os.path.exists(filepath):
        return []
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def format_stars(n):
    if n >= 10000:
        return f"{n / 10000:.1f}w"
    elif n >= 1000:
        return f"{n / 1000:.1f}k"
    return str(n)


def lang_color(lang):
    colors = {
        "Python": "#3572A5", "JavaScript": "#f1e05a", "TypeScript": "#3178c6",
        "Rust": "#dea584", "Java": "#b07219", "Go": "#00ADD8", "C++": "#f34b7d",
        "C": "#555555", "C#": "#178600", "Shell": "#89e051", "Kotlin": "#A97BFF",
        "Swift": "#F05138", "Jupyter Notebook": "#DA5B0B", "Jupyter": "#DA5B0B",
        "Zig": "#ec915c", "HTML": "#e34c26", "CSS": "#563d7c", "Ruby": "#701516",
        "PHP": "#4F5D95", "Dart": "#00B4AB", "Lua": "#000080", "R": "#198CE7",
        "Scala": "#c22d40", "Vue": "#41b883", "Svelte": "#ff3e00",
    }
    return colors.get(lang, "#8b8b8b")


def generate_repo_table(repos, title, icon="🔥"):
    if not repos:
        return f'<div class="section"><h2>{icon} {title}</h2><p class="empty">暂无数据</p></div>'

    rows = ""
    for i, repo in enumerate(repos):
        lang_dot = f'<span class="lang-dot" style="background:{lang_color(repo["language"])}"></span>' if repo["language"] else ""
        lang_text = f'<span class="lang">{repo["language"]}</span>' if repo["language"] else '<span class="lang">-</span>'
        delta = repo.get("delta_stars", 0)
        delta_str = f'+{format_stars(delta)}' if delta > 0 else "-"

        rows += f"""
        <tr class="{'even' if i % 2 == 0 else 'odd'}">
            <td class="rank">{i + 1}</td>
            <td class="repo">
                <a href="{repo['url']}" target="_blank" rel="noopener">{repo['name']}</a>
            </td>
            <td class="desc">{repo['description'][:80]}{'...' if len(repo['description']) > 80 else ''}</td>
            <td class="lang-cell">{lang_dot}{lang_text}</td>
            <td class="stars">⭐ {format_stars(repo['total_stars'])}</td>
            <td class="delta">{delta_str}</td>
        </tr>"""

    return f"""
    <div class="section">
        <h2>{icon} {title}</h2>
        <div class="table-wrapper">
            <table>
                <thead>
                    <tr>
                        <th>#</th>
                        <th>项目</th>
                        <th>描述</th>
                        <th>语言</th>
                        <th>⭐ 总数</th>
                        <th>📈 增长</th>
                    </tr>
                </thead>
                <tbody>{rows}</tbody>
            </table>
        </div>
    </div>"""


def generate_dev_table(devs):
    if not devs:
        return '<div class="section"><h2>👨‍💻 热门开发者</h2><p class="empty">暂无数据</p></div>'

    rows = ""
    for i, dev in enumerate(devs):
        repo_link = f'<a href="{dev["repo_url"]}" target="_blank" rel="noopener">{dev["popular_repo"]}</a>' if dev.get("repo_url") else "-"
        rows += f"""
        <tr class="{'even' if i % 2 == 0 else 'odd'}">
            <td class="rank">{i + 1}</td>
            <td class="dev">
                <img src="https://github.com/{dev['username']}.png?size=32" alt="{dev['username']}" class="avatar" loading="lazy" onerror="this.style.display='none'">
                <a href="{dev['url']}" target="_blank" rel="noopener">{dev['display_name']}</a>
                <span class="username">@{dev['username']}</span>
            </td>
            <td class="dev-repo">{repo_link}</td>
        </tr>"""

    return f"""
    <div class="section">
        <h2>👨‍💻 热门开发者 (Trending Developers)</h2>
        <div class="table-wrapper">
            <table class="dev-table">
                <thead>
                    <tr>
                        <th>#</th>
                        <th>开发者</th>
                        <th>热门仓库</th>
                    </tr>
                </thead>
                <tbody>{rows}</tbody>
            </table>
        </div>
    </div>"""


def generate_html(daily, weekly, monthly, devs):
    date_display = datetime.now(CST).strftime("%Y 年 %m 月 %d 日")

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GitHub 热点速报 - {TODAY}</title>
    <meta name="description" content="GitHub Trending 每日热门榜单 - {date_display}">
    <style>
        :root {{
            --bg: #0d1117;
            --card: #161b22;
            --border: #30363d;
            --text: #e6edf3;
            --text-secondary: #8b949e;
            --accent: #58a6ff;
            --accent2: #f78166;
            --green: #3fb950;
            --red: #f85149;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans SC', Helvetica, Arial, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.6;
            min-height: 100vh;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}

        /* Header */
        .header {{
            text-align: center;
            padding: 40px 20px;
            border-bottom: 1px solid var(--border);
            margin-bottom: 30px;
        }}
        .header h1 {{
            font-size: 2.5em;
            background: linear-gradient(135deg, var(--accent), var(--accent2));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 8px;
        }}
        .header .subtitle {{ color: var(--text-secondary); font-size: 1.1em; }}
        .header .date {{ color: var(--text-secondary); margin-top: 12px; font-size: 0.95em; }}
        .header .nav-links {{ margin-top: 16px; }}
        .header .nav-links a {{
            color: var(--accent);
            text-decoration: none;
            margin: 0 12px;
            font-size: 0.9em;
        }}
        .header .nav-links a:hover {{ text-decoration: underline; }}

        /* Sections */
        .section {{
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 24px;
        }}
        .section h2 {{
            font-size: 1.4em;
            margin-bottom: 16px;
            padding-bottom: 12px;
            border-bottom: 1px solid var(--border);
        }}
        .empty {{ color: var(--text-secondary); text-align: center; padding: 20px; }}

        /* Tables */
        .table-wrapper {{ overflow-x: auto; }}
        table {{ width: 100%; border-collapse: collapse; font-size: 0.9em; }}
        th {{
            text-align: left;
            padding: 10px 12px;
            color: var(--text-secondary);
            font-weight: 600;
            font-size: 0.85em;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            border-bottom: 2px solid var(--border);
            white-space: nowrap;
        }}
        td {{ padding: 10px 12px; border-bottom: 1px solid var(--border); vertical-align: middle; }}
        tr.even {{ background: rgba(255,255,255,0.02); }}
        tr:hover {{ background: rgba(88,166,255,0.06); }}
        .rank {{ width: 40px; text-align: center; color: var(--text-secondary); font-weight: 600; }}
        .repo a {{ color: var(--accent); text-decoration: none; font-weight: 500; }}
        .repo a:hover {{ text-decoration: underline; }}
        .desc {{ color: var(--text-secondary); max-width: 350px; }}
        .lang-cell {{ white-space: nowrap; }}
        .lang-dot {{
            display: inline-block;
            width: 10px; height: 10px;
            border-radius: 50%;
            margin-right: 6px;
            vertical-align: middle;
        }}
        .lang {{ color: var(--text-secondary); font-size: 0.85em; }}
        .stars {{ text-align: right; white-space: nowrap; }}
        .delta {{ text-align: right; color: var(--green); font-weight: 600; white-space: nowrap; }}

        /* Dev table */
        .dev {{ white-space: nowrap; }}
        .dev .avatar {{
            width: 28px; height: 28px;
            border-radius: 50%;
            margin-right: 8px;
            vertical-align: middle;
        }}
        .dev a {{ color: var(--accent); text-decoration: none; font-weight: 500; }}
        .dev a:hover {{ text-decoration: underline; }}
        .dev .username {{ color: var(--text-secondary); font-size: 0.85em; margin-left: 6px; }}
        .dev-repo a {{ color: var(--text); text-decoration: none; }}
        .dev-repo a:hover {{ color: var(--accent); }}

        /* Footer */
        .footer {{
            text-align: center;
            padding: 30px 20px;
            color: var(--text-secondary);
            font-size: 0.85em;
            border-top: 1px solid var(--border);
            margin-top: 30px;
        }}
        .footer a {{ color: var(--accent); text-decoration: none; }}

        /* Responsive */
        @media (max-width: 768px) {{
            .header h1 {{ font-size: 1.8em; }}
            .section {{ padding: 16px; }}
            table {{ font-size: 0.8em; }}
            .desc {{ max-width: 200px; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔥 GitHub 热点速报</h1>
            <div class="subtitle">Trending Repositories & Developers</div>
            <div class="date">{date_display}</div>
            <div class="nav-links">
                <a href="../index.html">📋 首页</a>
                <a href="https://github.com/trending" target="_blank" rel="noopener">🔗 GitHub Trending</a>
            </div>
        </div>

        {generate_repo_table(daily, "今日热门榜 (Daily Trending)", "📊")}
        {generate_repo_table(weekly, "本周升星榜 (Weekly Rising Stars)", "🚀")}
        {generate_repo_table(monthly, "本月升星榜 (Monthly Rising Stars)", "👑")}
        {generate_dev_table(devs)}

        <div class="footer">
            <p>数据来源：<a href="https://github.com/trending" target="_blank" rel="noopener">GitHub Trending</a> | 自动生成于 {datetime.now(CST).strftime("%Y-%m-%d %H:%M")}</p>
            <p style="margin-top: 8px;">由 GitHub Actions 每日自动更新 ⚡</p>
        </div>
    </div>
</body>
</html>"""


def main():
    print(f"📝 正在生成 {TODAY} 的 HTML 报告...")

    daily = load_json(f"{TODAY}_daily.json")
    weekly = load_json(f"{TODAY}_weekly.json")
    monthly = load_json(f"{TODAY}_monthly.json")
    devs = load_json(f"{TODAY}_developers.json")

    if not daily and not weekly and not monthly:
        print("  ⚠️ 未找到数据文件，请先运行 fetch_trending.py")
        return

    html = generate_html(daily, weekly, monthly, devs)

    # 保存到归档目录
    archive_dir = os.path.join(DOCS_DIR, "archive")
    os.makedirs(archive_dir, exist_ok=True)
    archive_path = os.path.join(archive_dir, f"{TODAY}.html")
    with open(archive_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  ✅ 归档报告已保存: {archive_path}")

    # 同时保存为当天的 index（覆盖最新）
    index_path = os.path.join(DOCS_DIR, "index.html")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  ✅ 最新报告已保存: {index_path}")

    # 生成 Markdown 版本
    md = generate_markdown(daily, weekly, monthly, devs)
    md_path = os.path.join(archive_dir, f"{TODAY}.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"  ✅ Markdown 报告已保存: {md_path}")

    print(f"\n🎉 报告生成完成！")


def generate_markdown(daily, weekly, monthly, devs):
    date_display = datetime.now(CST).strftime("%Y 年 %m 月 %d 日")
    lines = [
        f"# 🔥 GitHub 热点速报 - {date_display}",
        "",
        f"> 数据来源：[GitHub Trending](https://github.com/trending) | 自动生成",
        "",
        "---",
        "",
    ]

    for repos, title in [(daily, "📊 今日热门榜"), (weekly, "🚀 本周升星榜"), (monthly, "👑 本月升星榜")]:
        lines.append(f"## {title}")
        lines.append("")
        lines.append("| # | 项目 | 描述 | 语言 | ⭐ 总数 | 📈 增长 |")
        lines.append("|---|------|------|------|---------|--------|")
        for i, r in enumerate(repos):
            desc = r["description"][:60] + ("..." if len(r["description"]) > 60 else "")
            delta = f'+{format_stars(r.get("delta_stars", 0))}' if r.get("delta_stars", 0) > 0 else "-"
            lines.append(f"| {i+1} | [{r['name']}]({r['url']}) | {desc} | {r['language'] or '-'} | {format_stars(r['total_stars'])} | {delta} |")
        lines.append("")

    lines.append("## 👨‍💻 热门开发者")
    lines.append("")
    lines.append("| # | 开发者 | 热门仓库 |")
    lines.append("|---|--------|----------|")
    for i, d in enumerate(devs):
        repo = f"[{d['popular_repo']}]({d['repo_url']})" if d.get("repo_url") else "-"
        lines.append(f"| {i+1} | [{d['display_name']}]({d['url']}) | {repo} |")
    lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    main()
