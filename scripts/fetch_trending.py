#!/usr/bin/env python3
"""
GitHub Trending 数据获取脚本
通过 OpenRouter AI（openai/gpt-oss-120b:free）解析页面，替代硬编码 HTML 选择器
确保 GitHub 页面结构变化时项目仍能稳定运行

模型选择策略：
  - 使用固定模型 openai/gpt-oss-120b:free（131K 上下文，131K 最大输出）
  - 最多重试 3 次，采用指数退避策略（5s → 15s → 45s）
  - 所有重试失败时，回退到正则解析
"""

import json
import os
import re
import sys
import time
from datetime import datetime, timezone, timedelta

import requests

# 北京时区 (UTC+8)
CST = timezone(timedelta(hours=8))
TODAY = datetime.now(CST).strftime("%Y-%m-%d")
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)

# OpenRouter 配置
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
AI_MODEL = "openai/gpt-oss-120b:free"

# 重试配置
MAX_RETRIES = 3
RETRY_DELAYS = [5, 15, 45]  # 指数退避（秒）

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
}


# ============================================================
# OpenRouter AI 调用（固定模型 + 重试）
# ============================================================

def fetch_page_html(url):
    """获取页面 HTML"""
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.text


def call_openrouter(html_content, prompt):
    """
    调用 OpenRouter AI 解析 HTML 内容。
    使用固定模型 openai/gpt-oss-120b:free。
    最多重试 3 次，采用指数退避策略。
    """
    if not OPENROUTER_API_KEY:
        print("    ⚠️ 未设置 OPENROUTER_API_KEY，使用正则回退解析")
        return None

    # 截取 HTML 关键内容（<article> 标签）
    articles_match = re.findall(r'<article[^>]*>.*?</article>', html_content, re.DOTALL)
    if articles_match:
        trimmed_html = "\n".join(articles_match)
    else:
        body_match = re.search(r'<body[^>]*>(.*?)</body>', html_content, re.DOTALL)
        trimmed_html = body_match.group(1) if body_match else html_content

    # 限制 HTML 长度，避免超出模型上下文
    max_html_len = 50000
    if len(trimmed_html) > max_html_len:
        trimmed_html = trimmed_html[:max_html_len] + "\n... (truncated)"

    # 构建请求体（使用固定模型）
    payload = {
        "model": AI_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "你是一个 HTML 数据提取专家。"
                    "从给定的 GitHub Trending 页面 HTML 中提取结构化数据。"
                    "严格按照要求的 JSON 格式输出，不要输出任何其他内容。"
                    "只输出纯 JSON，不要包含 markdown 代码块标记。"
                ),
            },
            {"role": "user", "content": f"{prompt}\n\n以下是页面 HTML：\n{trimmed_html}"},
        ],
        "temperature": 0.0,
        "max_tokens": 16384,
    }

    api_headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/trending-bot",
        "X-Title": "GitHub Trending Bot",
    }

    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            if attempt > 0:
                delay = RETRY_DELAYS[min(attempt - 1, len(RETRY_DELAYS) - 1)]
                print(f"    ⏳ 第 {attempt + 1}/{MAX_RETRIES} 次重试，等待 {delay}s...")
                time.sleep(delay)

            resp = requests.post(
                OPENROUTER_API_URL,
                headers=api_headers,
                json=payload,
                timeout=120,
            )
            resp.raise_for_status()

            resp_data = resp.json()
            content = resp_data["choices"][0]["message"]["content"].strip()
            finish_reason = resp_data["choices"][0].get("finish_reason", "")
            actual_model = resp_data.get("model", AI_MODEL)

            # 清理 markdown 代码块包裹
            content = re.sub(r"^```(?:json)?\s*", "", content)
            content = re.sub(r"\s*```$", "", content)

            result = json.loads(content)

            # 检查截断
            if finish_reason == "length":
                print(f"    ⚠️ 模型 {actual_model} 输出被截断")
                last_error = "输出被截断"
                continue

            print(f"    🤖 模型 {actual_model} 解析成功")
            return result

        except requests.exceptions.Timeout:
            last_error = "请求超时"
            print(f"    ⏱️ 请求超时（{120}s）")
        except requests.exceptions.HTTPError as e:
            status = e.response.status_code
            if status == 401:
                print("    ❌ API Key 无效，回退到正则解析")
                return None
            elif status == 402:
                print("    💰 账户余额不足，回退到正则解析")
                return None
            elif status == 400:
                print(f"    🚫 模型不可用（400），回退到正则解析")
                return None
            elif status == 429:
                last_error = f"速率限制 (429)"
                print(f"    ⚠️ 速率限制，稍后重试...")
            else:
                last_error = f"HTTP {status}"
                print(f"    ⚠️ HTTP 错误: {status}")
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            last_error = f"{type(e).__name__}: {e}"
            print(f"    ⚠️ 响应解析异常: {type(e).__name__}")
        except Exception as e:
            last_error = str(e)
            print(f"    ⚠️ 未知错误: {e}")

    print(f"    ⚠️ AI 解析失败（{MAX_RETRIES} 次重试后），回退到正则解析")
    return None


# ============================================================
# 正则回退解析（当 AI 不可用时使用）
# ============================================================

def regex_parse_repos(html):
    """正则表达式回退解析仓库列表"""
    repos = []
    articles = re.findall(r'<article[^>]*>(.*?)</article>', html, re.DOTALL)

    for article in articles:
        # 仓库名
        href_match = re.search(r'<h2[^>]*>\s*<a[^>]*href="(/[^"]+)"', article)
        if not href_match:
            continue
        repo_name = href_match.group(1).strip("/")

        # 描述
        desc_match = re.search(r'<p[^>]*class="[^"]*color-fg-muted[^"]*"[^>]*>(.*?)</p>', article, re.DOTALL)
        description = re.sub(r"<[^>]+>", "", desc_match.group(1)).strip() if desc_match else ""

        # 语言
        lang_match = re.search(r'<span[^>]*itemprop="programmingLanguage"[^>]*>(.*?)</span>', article)
        language = lang_match.group(1).strip() if lang_match else ""

        # 总星数和 Forks
        total_stars = 0
        forks = 0
        star_links = re.findall(r'<a[^>]*href="([^"]*?/stargazers)"[^>]*>.*?([\d,]+)\s*</a>', article, re.DOTALL)
        for href, text in star_links:
            total_stars = int(text.replace(",", ""))
        fork_links = re.findall(r'<a[^>]*href="([^"]*?/forks)"[^>]*>.*?([\d,]+)\s*</a>', article, re.DOTALL)
        for href, text in fork_links:
            forks = int(text.replace(",", ""))

        # 新增星数
        delta_stars = 0
        delta_text = ""
        delta_match = re.search(r'([\d,]+)\s*stars\s*(?:today|this week|this month)', article)
        if delta_match:
            delta_stars = int(delta_match.group(1).replace(",", ""))
            delta_text = delta_match.group(0)

        repos.append({
            "name": repo_name,
            "description": description,
            "language": language,
            "total_stars": total_stars,
            "delta_stars": delta_stars,
            "delta_text": delta_text,
            "forks": forks,
            "url": f"https://github.com/{repo_name}",
        })

    return repos


def regex_parse_developers(html):
    """正则表达式回退解析开发者列表"""
    devs = []
    articles = re.findall(r'<article[^>]*>(.*?)</article>', html, re.DOTALL)

    for article in articles:
        # 用户名和显示名
        h1_match = re.search(r'<h1[^>]*class="[^"]*h3[^"]*"[^>]*>\s*<a[^>]*href="(/[^"]+)"[^>]*>(.*?)</a>', article, re.DOTALL)
        if not h1_match:
            continue
        username = h1_match.group(1).strip("/")
        display_name = re.sub(r"<[^>]+>", "", h1_match.group(2)).strip()

        # 热门仓库
        inner_match = re.search(r'<article[^>]*>.*?<h1[^>]*>\s*<a[^>]*href="(/[^"]+/(?:[^/"]+))"', article, re.DOTALL)
        popular_repo = ""
        if inner_match:
            parts = inner_match.group(1).strip("/").split("/")
            if len(parts) >= 2:
                popular_repo = parts[1]

        devs.append({
            "username": username,
            "display_name": display_name,
            "popular_repo": popular_repo,
            "url": f"https://github.com/{username}",
            "repo_url": f"https://github.com/{username}/{popular_repo}" if popular_repo else "",
        })

    return devs


# ============================================================
# 主解析函数（AI 优先，正则回退）
# ============================================================

REPO_PROMPT = """从以下 GitHub Trending 仓库页面 HTML 中提取所有仓库信息。
返回一个 JSON 数组，每个元素包含：
- "name": 仓库全名（如 "owner/repo"）
- "description": 仓库描述（纯文本，最多50字）
- "language": 编程语言
- "total_stars": 总星数（整数）
- "delta_stars": 新增星数（整数）
- "forks": fork 数（整数）
- "url": "https://github.com/owner/repo"

注意：
- total_stars 是星数链接中的数字
- delta_stars 是 "XXX stars today/this week/this month" 中的数字
- 所有数字字段必须是整数
- description 保持在50字以内以节省空间
- 必须提取页面中所有仓库，不要遗漏"""

DEV_PROMPT = """从以下 GitHub Trending Developers 页面 HTML 中提取所有开发者信息。
返回一个 JSON 数组，每个元素包含：
- "username": GitHub 用户名
- "display_name": 显示名称（纯文本）
- "popular_repo": 该开发者的热门仓库名
- "url": "https://github.com/username"
- "repo_url": "https://github.com/username/repo"（如果有热门仓库的话）

注意：每个 <article> 标签代表一个开发者。必须提取所有开发者，不要遗漏。"""


def fetch_trending_repos(since="daily"):
    """获取热门仓库列表（AI 优先，正则回退）"""
    url = f"https://github.com/trending?since={since}"
    print(f"    🌐 请求 {url}...")
    html = fetch_page_html(url)

    # 尝试 AI 解析
    MIN_EXPECTED = 10
    ai_result = call_openrouter(html, REPO_PROMPT)
    if ai_result and isinstance(ai_result, list) and len(ai_result) >= MIN_EXPECTED:
        valid = True
        for item in ai_result:
            if not isinstance(item.get("name"), str) or "/" not in item.get("name", ""):
                valid = False
                break
        if valid:
            print(f"    🤖 AI 解析成功，获取到 {len(ai_result)} 个仓库")
            return ai_result
    elif ai_result and isinstance(ai_result, list) and len(ai_result) > 0:
        print(f"    ⚠️ AI 仅返回 {len(ai_result)} 个仓库（预期 ≥{MIN_EXPECTED}），回退到正则解析")

    # 回退到正则解析
    print(f"    📋 使用正则回退解析...")
    return regex_parse_repos(html)


def fetch_trending_developers():
    """获取热门开发者列表（AI 优先，正则回退）"""
    url = "https://github.com/trending/developers"
    print(f"    🌐 请求 {url}...")
    html = fetch_page_html(url)

    # 尝试 AI 解析
    MIN_EXPECTED = 15
    ai_result = call_openrouter(html, DEV_PROMPT)
    if ai_result and isinstance(ai_result, list) and len(ai_result) >= MIN_EXPECTED:
        valid = True
        for item in ai_result:
            if not isinstance(item.get("username"), str):
                valid = False
                break
        if valid:
            print(f"    🤖 AI 解析成功，获取到 {len(ai_result)} 位开发者")
            return ai_result
    elif ai_result and isinstance(ai_result, list) and len(ai_result) > 0:
        print(f"    ⚠️ AI 仅返回 {len(ai_result)} 位开发者（预期 ≥{MIN_EXPECTED}），回退到正则解析")

    # 回退到正则解析
    print(f"    📋 使用正则回退解析...")
    return regex_parse_developers(html)


def main():
    if OPENROUTER_API_KEY:
        print(f"📅 正在获取 {TODAY} 的 GitHub Trending 数据... [🤖 AI 模式]")
        print(f"    🤖 使用模型: {AI_MODEL}")
        print(f"    🔄 重试策略: 最多 {MAX_RETRIES} 次，指数退避 {RETRY_DELAYS}s")
    else:
        print(f"📅 正在获取 {TODAY} 的 GitHub Trending 数据... [📋 正则回退模式]")

    # 获取不同时间范围的热门仓库
    for since, label in [("daily", "今日"), ("weekly", "本周"), ("monthly", "本月")]:
        print(f"  📊 获取{label}热门仓库...")
        repos = fetch_trending_repos(since)
        filepath = os.path.join(DATA_DIR, f"{TODAY}_{since}.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(repos, f, ensure_ascii=False, indent=2)
        print(f"    ✅ 获取到 {len(repos)} 个仓库，已保存到 {filepath}")

    # 获取热门开发者
    print("  👨‍💻 获取热门开发者...")
    devs = fetch_trending_developers()
    filepath = os.path.join(DATA_DIR, f"{TODAY}_developers.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(devs, f, ensure_ascii=False, indent=2)
    print(f"    ✅ 获取到 {len(devs)} 位开发者，已保存到 {filepath}")

    print(f"\n🎉 数据获取完成！")


if __name__ == "__main__":
    main()
