import requests
from .config import DEEPSEEK_API_KEY, REQUEST_TIMEOUT


def analyze_with_deepseek(symbol, technical, fundamentals, news, dry_run=False):
    if dry_run:
        return "Dry-run分析：技术形态满足筛选条件；基本面和新闻为模拟数据；请在真实环境中复核。"
    if not DEEPSEEK_API_KEY:
        return "DeepSeek API Key未配置，已跳过AI分析。"
    news_text = "\n".join([f"- {n.get('title')}" for n in news]) or "无相关新闻"
    prompt = f"""
你是一名股票研究助理。请基于以下信息，对股票 {symbol} 做简洁分析。
要求：不要给出直接买入/卖出建议；输出技术面、基本面、新闻政策、风险、综合关注等级。
技术面：{technical}
基本面：{fundamentals}
新闻：{news_text}
"""
    payload = {"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}], "temperature": 0.3}
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    try:
        r = requests.post("https://api.deepseek.com/v1/chat/completions", json=payload, headers=headers, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"DeepSeek分析失败：{e}"
