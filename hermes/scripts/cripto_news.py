#!/usr/bin/env python3
"""
Crypto News Digest — Agregador de notícias de múltiplas fontes
Fontes: CryptoCompare (grátis) + NewsAPI (com key)
Output: Telegram (parse_mode=HTML) ou stdout
Uso: python3 cripto_news.py [--source cryptocompare|newsapi|all] [--limit 5]
"""
import requests
import json
import os
import sys
import ssl
from datetime import datetime, timedelta

# ── Config ───────────────────────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID") or os.getenv("TELEGRAM_HOME_CHANNEL", "")

# Load .env manually
ENV_FILE = os.path.expanduser("~/.hermes/.env")
if os.path.exists(ENV_FILE):
    with open(ENV_FILE) as f:
        for line in f:
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k, v)

NEWSAPI_KEY = os.getenv("NEWSAPI_API_KEY", "")
CRYPTO_COMPARE_URL = "https://min-api.cryptocompare.com"
COINGECKO = "https://api.coingecko.com/api/v3"
BINANCE_URL = "https://api.binance.com"

# ── Helpers ──────────────────────────────────────────────────────────────────
def send_telegram(html: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram: missing token/chat_id", file=sys.stderr)
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": html,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Telegram error: {e}", file=sys.stderr)

def get_coingecko_trending(limit=5):
    """CoinGecko Trending - coins mais procuradas (gratuito, sem key)"""
    try:
        r = requests.get(
            f"{COINGECKO}/search/trending",
            timeout=10
        )
        if r.status_code != 200:
            return []
        coins = r.json().get("coins", [])
        return [
            {
                "title": f"🔥 Trending: {c['item']['name']} ({c['item']['symbol'].upper()})",
                "url": f"https://www.coingecko.com/en/coins/{c['item']['id']}",
                "source": "CoinGecko",
                "published": "",
                "body": f"Market cap rank #{c['item']['market_cap_rank']} · {c['item'].get('score','N/A')}"
            }
            for c in coins[:limit]
            if c["item"].get("market_cap_rank")
        ]
    except Exception as e:
        print(f"CoinGecko trending error: {e}", file=sys.stderr)
        return []

def get_crypto_global(limit=5):
    """CoinGecko Global Market Data - visão macro (gratuito, sem key)"""
    try:
        r = requests.get(f"{COINGECKO}/global", timeout=10)
        if r.status_code != 200:
            return []
        d = r.json().get("data", {})
        total_cap = float(d.get("total_market_cap", {}).get("usd", 0))
        btc_dom = float(d.get("market_cap_percentage", {}).get("btc", 0))
        active_coins = d.get("active_cryptocurrencies", 0)
        return [
            {
                "title": f"🌍 Mercado Global: ${total_cap/1e12:.2f}T total · BTC {btc_dom:.1f}% dominance",
                "url": "https://www.coingecko.com",
                "source": "CoinGecko",
                "published": "",
                "body": f"{active_coins} moedas ativas em {d.get('markets', 0)} exchanges"
            }
        ]
    except Exception as e:
        print(f"CoinGecko global error: {e}", file=sys.stderr)
        return []

def get_newsapi_crypto(limit=5):
    """NewsAPI - requer API key no .env"""
    if not NEWSAPI_KEY:
        return []
    try:
        r = requests.get(
            "https://newsapi.org/v2/everything",
            params={
                "q": "bitcoin OR cryptocurrency OR ethereum",
                "pageSize": limit,
                "sortBy": "publishedAt",
                "language": "en"
            },
            headers={"X-Api-Key": NEWSAPI_KEY},
            timeout=10
        )
        if r.status_code != 200:
            print(f"NewsAPI error: {r.status_code}", file=sys.stderr)
            return []
        articles = r.json().get("articles", [])
        return [
            {
                "title": a["title"],
                "url": a["url"],
                "source": a["source"]["name"],
                "published": a["publishedAt"],
                "body": a.get("description", "")[:200]
            }
            for a in articles if a.get("title")
        ]
    except Exception as e:
        print(f"NewsAPI error: {e}", file=sys.stderr)
        return []

def get_binance_announcements():
    """Binance announcements via public API"""
    try:
        r = requests.get(
            f"{BINANCE_URL}/api/v3/exchangeInfo",
            timeout=10
        )
        if r.status_code == 200:
            return ["Binance system operational"]
        return []
    except Exception as e:
        return [f"Binance API: {e}"]

def format_epoch(ts):
    """Converte epoch timestamp para data legível"""
    try:
        return datetime.fromtimestamp(ts).strftime("%d/%m %H:%M")
    except:
        return ""

def html_news_item(i, item):
    title = item["title"][:80] + ("..." if len(item["title"]) > 80 else "")
    source = item.get("source", "Unknown")
    time_str = format_epoch(item["published"]) if isinstance(item["published"], (int, float)) else (item["published"][:10] if item.get("published") else "")
    url = item["url"]
    body = item.get("body", "")[:100]
    
    return (
        f"<b>{i}. {title}</b>\n"
        f"   📰 {source} • {time_str}\n"
        f"   {body}\n"
        f"   🔗 {url}\n"
    )

def format_html(news_items, source_label):
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    header = (
        f"📰 <b>CRYPTO NEWS — {source_label}</b>\n"
        f"   {now}\n"
        f"   {'─'*40}\n\n"
    )
    
    if not news_items:
        return header + "   Nenhuma notícia encontrada."
    
    items_html = "\n".join(
        html_news_item(i+1, item) + "\n"
        for i, item in enumerate(news_items)
    )
    
    footer = f"\n{'─'*40}\n📊 {len(news_items)} notícias"
    return header + items_html + footer

def main():
    source = "all"
    limit = 5
    
    for arg in sys.argv[1:]:
        if arg == "--source" and len(sys.argv) > 2:
            source = sys.argv[sys.argv.index(arg)+1]
        if arg.isdigit():
            limit = int(arg)
    
    all_news = []
    sources_used = []
    
    if source in ("newsapi", "all"):
        na_news = get_newsapi_crypto(limit)
        if na_news:
            # Deduplicate by title similarity
            titles = {n["title"][:50] for n in all_news}
            for n in na_news:
                if n["title"][:50] not in titles:
                    all_news.append(n)
                    titles.add(n["title"][:50])
            sources_used.append("NewsAPI")
    
    if source in ("trending", "all"):
        tg_news = get_coingecko_trending(limit)
        if tg_news:
            all_news.extend(tg_news)
            sources_used.append("🔥 Trending")
    
    if source in ("global", "all"):
        gl_news = get_crypto_global()
        if gl_news:
            all_news.extend(gl_news)
            sources_used.append("🌍 Global")
    
    if not all_news:
        print("No news found.", file=sys.stderr)
        return 1
    
    # Sort by published date (most recent first)
    def get_date(n):
        p = n.get("published", 0)
        if isinstance(p, (int, float)):
            return datetime.fromtimestamp(p) if p > 1e9 else datetime.fromisoformat(str(p))
        return datetime.min
    all_news.sort(key=get_date, reverse=True)
    
    label = " + ".join(sources_used)
    html = format_html(all_news[:limit], label)
    
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        send_telegram(html)
    else:
        # Strip HTML for stdout
        import re
        plain = re.sub(r"<[^>]+>", "", html)
        print(plain)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
