#!/usr/bin/env python3
"""
首页索引生成脚本
汇总所有历史报告，生成带日期筛选功能的导航首页
"""

import json
import os
from datetime import datetime, timezone, timedelta

CST = timezone(timedelta(hours=8))
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DOCS_DIR = os.path.join(BASE_DIR, "docs")
ARCHIVE_DIR = os.path.join(DOCS_DIR, "archive")


def get_all_dates():
    """获取所有有数据的历史日期"""
    dates = set()
    if not os.path.exists(DATA_DIR):
        return sorted(dates, reverse=True)

    for filename in os.listdir(DATA_DIR):
        if filename.endswith("_daily.json"):
            date_str = filename.replace("_daily.json", "")
            dates.add(date_str)

    return sorted(dates, reverse=True)


def load_json_for_date(date_str):
    """加载指定日期的所有数据"""
    data = {}
    for key in ["daily", "weekly", "monthly", "developers"]:
        filepath = os.path.join(DATA_DIR, f"{date_str}_{key}.json")
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                data[key] = json.load(f)
    return data


def generate_index_html(dates):
    now = datetime.now(CST).strftime("%Y 年 %m 月 %d 日 %H:%M")

    # 生成历史报告卡片数据（内嵌 JSON 供 JS 筛选使用）
    cards_data = []
    for date_str in dates:
        data = load_json_for_date(date_str)
        daily = data.get("daily", [])
        top_repo = daily[0] if daily else None

        if top_repo:
            preview = f"{top_repo['name']} (+{top_repo.get('delta_stars', 0):,}⭐)"
        else:
            preview = "数据可用"

        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            weekday = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][dt.weekday()]
            date_display = dt.strftime("%m月%d日")
            year = dt.strftime("%Y")
            month = dt.strftime("%Y-%m")
        except ValueError:
            weekday = ""
            date_display = date_str
            year = date_str[:4]
            month = date_str[:7]

        cards_data.append({
            "date": date_str,
            "year": year,
            "month": month,
            "display": date_display,
            "weekday": weekday,
            "preview": preview,
        })

    # 生成可用的年份和月份列表
    all_years = sorted(set(c["year"] for c in cards_data), reverse=True)
    all_months = sorted(set(c["month"] for c in cards_data), reverse=True)

    # 生成筛选按钮的 HTML
    year_buttons = "".join(
        f'<button class="filter-btn active" data-type="year" data-value="{y}">{y}</button>'
        for y in all_years
    )
    month_buttons = "".join(
        f'<button class="filter-btn active" data-type="month" data-value="{m}">{m}</button>'
        for m in all_months
    )

    # 生成历史卡片 HTML
    history_cards = ""
    for c in cards_data:
        history_cards += f"""
        <a href="archive/{c['date']}.html" class="history-card" data-year="{c['year']}" data-month="{c['month']}">
            <div class="card-date">
                <span class="card-day">{c['display']}</span>
                <span class="card-weekday">{c['weekday']}</span>
            </div>
            <div class="card-preview">{c['preview']}</div>
            <div class="card-arrow">→</div>
        </a>"""

    # 最新报告预览
    latest_data = load_json_for_date(dates[0]) if dates else {}
    latest_daily = latest_data.get("daily", [])
    latest_preview_rows = ""
    for i, repo in enumerate(latest_daily[:5]):
        delta = repo.get("delta_stars", 0)
        delta_str = f'+{delta:,}' if delta > 0 else "-"
        latest_preview_rows += f"""
        <tr>
            <td class="rank">{i + 1}</td>
            <td><a href="{repo['url']}" target="_blank" rel="noopener">{repo['name']}</a></td>
            <td class="lang-cell">{repo['language'] or '-'}</td>
            <td class="stars">⭐ {repo['total_stars']:,}</td>
            <td class="delta">{delta_str}</td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GitHub 热点速报 - 每日热门榜单归档</title>
    <meta name="description" content="GitHub Trending 每日热门榜单自动归档，包含今日热门榜、本周升星榜、本月升星榜">
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
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans SC', Helvetica, Arial, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.6;
            min-height: 100vh;
        }}
        .container {{ max-width: 1000px; margin: 0 auto; padding: 20px; }}

        .header {{
            text-align: center;
            padding: 50px 20px 30px;
            border-bottom: 1px solid var(--border);
            margin-bottom: 30px;
        }}
        .header h1 {{
            font-size: 3em;
            background: linear-gradient(135deg, var(--accent), var(--accent2));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 8px;
        }}
        .header .subtitle {{ color: var(--text-secondary); font-size: 1.2em; }}
        .header .stats {{
            display: flex;
            justify-content: center;
            gap: 30px;
            margin-top: 24px;
            flex-wrap: wrap;
        }}
        .header .stat {{ text-align: center; }}
        .header .stat .num {{
            font-size: 2em;
            font-weight: 700;
            color: var(--accent);
        }}
        .header .stat .label {{
            font-size: 0.85em;
            color: var(--text-secondary);
        }}

        /* Latest preview */
        .latest-section {{
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 30px;
        }}
        .latest-section h2 {{
            font-size: 1.3em;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .latest-section h2 .badge {{
            background: var(--green);
            color: #000;
            font-size: 0.7em;
            padding: 2px 8px;
            border-radius: 10px;
            font-weight: 600;
        }}
        .view-all {{
            display: inline-block;
            color: var(--accent);
            text-decoration: none;
            font-size: 0.9em;
            margin-top: 12px;
        }}
        .view-all:hover {{ text-decoration: underline; }}

        table {{ width: 100%; border-collapse: collapse; font-size: 0.9em; }}
        th {{
            text-align: left;
            padding: 8px 12px;
            color: var(--text-secondary);
            font-weight: 600;
            font-size: 0.8em;
            text-transform: uppercase;
            border-bottom: 2px solid var(--border);
        }}
        td {{ padding: 8px 12px; border-bottom: 1px solid var(--border); }}
        tr:hover {{ background: rgba(88,166,255,0.06); }}
        .rank {{ width: 30px; text-align: center; color: var(--text-secondary); font-weight: 600; }}
        td a {{ color: var(--accent); text-decoration: none; }}
        td a:hover {{ text-decoration: underline; }}
        .lang-cell {{ color: var(--text-secondary); }}
        .stars {{ text-align: right; }}
        .delta {{ text-align: right; color: var(--green); font-weight: 600; }}

        /* Filter section */
        .filter-section {{
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 20px 24px;
            margin-bottom: 24px;
        }}
        .filter-section h2 {{
            font-size: 1.3em;
            margin-bottom: 16px;
        }}
        .filter-group {{
            margin-bottom: 12px;
        }}
        .filter-group:last-child {{
            margin-bottom: 0;
        }}
        .filter-label {{
            font-size: 0.8em;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
            font-weight: 600;
        }}
        .filter-buttons {{
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
        }}
        .filter-btn {{
            padding: 5px 14px;
            border: 1px solid var(--border);
            border-radius: 20px;
            background: transparent;
            color: var(--text-secondary);
            cursor: pointer;
            font-size: 0.85em;
            transition: all 0.2s;
        }}
        .filter-btn:hover {{
            border-color: var(--accent);
            color: var(--accent);
        }}
        .filter-btn.active {{
            background: var(--accent);
            border-color: var(--accent);
            color: #fff;
        }}
        .filter-count {{
            margin-top: 10px;
            font-size: 0.85em;
            color: var(--text-secondary);
        }}
        .filter-count span {{
            color: var(--accent);
            font-weight: 600;
        }}

        /* History grid */
        .history-section {{
            margin-bottom: 30px;
        }}
        .history-section h2 {{
            font-size: 1.3em;
            margin-bottom: 16px;
        }}
        .history-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 12px;
        }}
        .history-card {{
            display: flex;
            align-items: center;
            gap: 16px;
            padding: 16px;
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 10px;
            text-decoration: none;
            color: var(--text);
            transition: border-color 0.2s, transform 0.1s, opacity 0.2s;
        }}
        .history-card:hover {{
            border-color: var(--accent);
            transform: translateY(-1px);
        }}
        .history-card.hidden {{
            display: none;
        }}
        .card-date {{
            display: flex;
            flex-direction: column;
            min-width: 60px;
        }}
        .card-day {{ font-weight: 600; font-size: 1.05em; }}
        .card-weekday {{ color: var(--text-secondary); font-size: 0.8em; }}
        .card-preview {{
            flex: 1;
            color: var(--text-secondary);
            font-size: 0.9em;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}
        .card-arrow {{
            color: var(--accent);
            font-size: 1.2em;
        }}

        .footer {{
            text-align: center;
            padding: 30px 20px;
            color: var(--text-secondary);
            font-size: 0.85em;
            border-top: 1px solid var(--border);
        }}
        .footer a {{ color: var(--accent); text-decoration: none; }}

        @media (max-width: 768px) {{
            .header h1 {{ font-size: 2em; }}
            .history-grid {{ grid-template-columns: 1fr; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔥 GitHub 热点速报</h1>
            <div class="subtitle">每日热门榜单自动归档</div>
            <div class="stats">
                <div class="stat">
                    <div class="num">{len(dates)}</div>
                    <div class="label">已归档天数</div>
                </div>
                <div class="stat">
                    <div class="num">{sum(len(load_json_for_date(d).get('daily', [])) for d in dates)}</div>
                    <div class="label">收录项目</div>
                </div>
                <div class="stat">
                    <div class="num">⏰</div>
                    <div class="label">每日 7:00 更新</div>
                </div>
            </div>
        </div>

        {"<div class='latest-section'><h2>📊 今日热门榜 <span class='badge'>LATEST</span></h2>" + "<table><thead><tr><th>#</th><th>项目</th><th>语言</th><th>⭐</th><th>📈</th></tr></thead><tbody>" + latest_preview_rows + "</tbody></table>" + f"<a href='archive/{dates[0]}.html' class='view-all'>查看完整报告 →</a></div>" if dates else ""}

        <div class="filter-section">
            <h2>🔍 筛选历史报告</h2>
            <div class="filter-group">
                <div class="filter-label">年份</div>
                <div class="filter-buttons" id="year-filters">
                    {year_buttons}
                </div>
            </div>
            <div class="filter-group">
                <div class="filter-label">月份</div>
                <div class="filter-buttons" id="month-filters">
                    {month_buttons}
                </div>
            </div>
            <div class="filter-count">
                显示 <span id="visible-count">{len(cards_data)}</span> / {len(cards_data)} 条记录
            </div>
        </div>

        <div class="history-section">
            <h2>📚 历史报告</h2>
            <div class="history-grid" id="history-grid">
                {history_cards}
            </div>
        </div>

        <div class="footer">
            <p>由 GitHub Actions 每日自动更新 | 数据来源 <a href="https://github.com/trending" target="_blank" rel="noopener">GitHub Trending</a></p>
            <p style="margin-top: 8px;">最后更新：{now}</p>
        </div>
    </div>

    <script>
    (function() {{
        // 筛选状态：记录每个分组当前激活的值
        const activeFilters = {{ type: 'year', values: new Set({json.dumps(all_years)}), type2: 'month', values2: new Set({json.dumps(all_months)}) }};

        // 初始化：从 URL hash 读取筛选条件
        function initFromHash() {{
            const hash = window.location.hash.slice(1);
            if (!hash) return;
            const params = new URLSearchParams(hash);
            const year = params.get('year');
            const month = params.get('month');
            if (year) {{
                document.querySelectorAll('#year-filters .filter-btn').forEach(btn => {{
                    btn.classList.toggle('active', btn.dataset.value === year);
                }});
                activeFilters.values = new Set([year]);
            }}
            if (month) {{
                document.querySelectorAll('#month-filters .filter-btn').forEach(btn => {{
                    btn.classList.toggle('active', btn.dataset.value === month);
                }});
                activeFilters.values2 = new Set([month]);
            }}
            applyFilters();
        }}

        // 应用筛选
        function applyFilters() {{
            const cards = document.querySelectorAll('.history-card');
            let visibleCount = 0;
            cards.forEach(card => {{
                const year = card.dataset.year;
                const month = card.dataset.month;
                const match = activeFilters.values.has(year) && activeFilters.values2.has(month);
                card.classList.toggle('hidden', !match);
                if (match) visibleCount++;
            }});
            document.getElementById('visible-count').textContent = visibleCount;
        }}

        // 更新 hash
        function updateHash() {{
            const year = activeFilters.values.size === 1 ? [...activeFilters.values][0] : '';
            const month = activeFilters.values2.size === 1 ? [...activeFilters.values2][0] : '';
            let hash = '';
            if (year) hash += 'year=' + year;
            if (month) hash += (hash ? '&' : '') + 'month=' + month;
            history.replaceState(null, '', hash ? '#' + hash : window.location.pathname);
        }}

        // 绑定年份按钮
        document.querySelectorAll('#year-filters .filter-btn').forEach(btn => {{
            btn.addEventListener('click', function() {{
                const val = this.dataset.value;
                if (this.classList.contains('active')) {{
                    // 至少保留一个激活
                    if (activeFilters.values.size <= 1) return;
                    this.classList.remove('active');
                    activeFilters.values.delete(val);
                }} else {{
                    this.classList.add('active');
                    activeFilters.values.add(val);
                }}
                updateHash();
                applyFilters();
            }});
        }});

        // 绑定月份按钮
        document.querySelectorAll('#month-filters .filter-btn').forEach(btn => {{
            btn.addEventListener('click', function() {{
                const val = this.dataset.value;
                if (this.classList.contains('active')) {{
                    if (activeFilters.values2.size <= 1) return;
                    this.classList.remove('active');
                    activeFilters.values2.delete(val);
                }} else {{
                    this.classList.add('active');
                    activeFilters.values2.add(val);
                }}
                updateHash();
                applyFilters();
            }});
        }});

        // 页面加载时初始化
        initFromHash();
    }})();
    </script>
</body>
</html>"""


def main():
    print("📋 正在生成首页索引...")

    dates = get_all_dates()
    print(f"  📅 找到 {len(dates)} 天的历史数据")

    html = generate_index_html(dates)

    index_path = os.path.join(DOCS_DIR, "index.html")
    os.makedirs(DOCS_DIR, exist_ok=True)
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  ✅ 首页已保存: {index_path}")


if __name__ == "__main__":
    main()
