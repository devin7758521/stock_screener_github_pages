import urllib.parse


def get_google_news(symbol, max_items=5, dry_run=False):
    if dry_run:
        return [{"title": f"{symbol} demo news: business momentum remains positive", "link": "", "published": ""}]
    try:
        import feedparser
        query = urllib.parse.quote(f"{symbol} stock")
        url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
        feed = feedparser.parse(url)
        seen, news = set(), []
        for entry in feed.entries:
            title = entry.get("title", "")
            link = entry.get("link", "")
            key = (title.lower(), link)
            if not title or key in seen:
                continue
            seen.add(key)
            news.append({"title": title, "link": link, "published": entry.get("published", "")})
            if len(news) >= max_items:
                break
        return news
    except Exception as e:
        print(f"[WARN] 新闻获取失败 {symbol}: {e}")
        return []
