#!/usr/bin/env python3
"""
Multi-Coin Ticker — RSI + Volume de múltiplas moedas da Binance
Busca top moedas por volume, calcula RSI, identifica sobrecompra/sobrevenda
Uso: python3 cripto_multi_ticker.py [--top 20] [--min-vol 1e8]
"""
import requests
import json
import os
import sys
import math
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# ── Config ───────────────────────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID") or os.getenv("TELEGRAM_HOME_CHANNEL", "")
BINANCE = "https://api.binance.com"

# Load .env
ENV_FILE = os.path.expanduser("~/.hermes/.env")
if os.path.exists(ENV_FILE):
    with open(ENV_FILE) as f:
        for line in f:
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k, v)

def send_telegram(html: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": html,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }, timeout=10)
    except Exception as e:
        print(f"Telegram error: {e}", file=sys.stderr)

def get_rsi(prices, period=14):
    """Calcula RSI de uma lista de preços de fecho"""
    if len(prices) < period + 1:
        return None
    deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
    gains = [d for d in deltas[-period:] if d > 0]
    losses = [-d for d in deltas[-period:] if d < 0]
    avg_gain = sum(gains) / period if gains else 0
    avg_loss = sum(losses) / period if losses else 0
    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def get_top_usdt_pairs(limit=50):
    """Busca top USDT pares por volume 24h"""
    r = requests.get(
        f"{BINANCE}/api/v3/ticker/24hr",
        params={"symbol": "USDTUSDT"},  # placeholder, we'll filter
        timeout=10
    )
    # Binance não filtra por quote assim — vamos usar exchangeInfo
    info_r = requests.get(f"{BINANCE}/api/v3/exchangeInfo", timeout=10)
    if info_r.status_code != 200:
        return []
    
    symbols = [
        s["symbol"] for s in info_r.json()["symbols"]
        if s["quoteAsset"] == "USDT" and s["status"] == "TRADING"
    ]
    
    # Pega 24hr tickers para todos
    tickers_r = requests.get(f"{BINANCE}/api/v3/ticker/24hr", timeout=10)
    if tickers_r.status_code != 200:
        return []
    
    all_tickers = {t["symbol"]: t for t in tickers_r.json()}
    
    pairs = []
    for sym in symbols:
        t = all_tickers.get(sym)
        if not t:
            continue
        try:
            quote_vol = float(t.get("quoteVolume", 0))
            price = float(t.get("lastPrice", 0))
            if quote_vol > 0 and price > 0:
                pairs.append({
                    "symbol": sym,
                    "price": price,
                    "quote_vol": quote_vol,
                    "price_change": float(t.get("priceChangePercent", 0)),
                    "high": float(t.get("highPrice", 0)),
                    "low": float(t.get("lowPrice", 0)),
                })
        except (ValueError, TypeError):
            continue
    
    pairs.sort(key=lambda x: x["quote_vol"], reverse=True)
    return pairs[:limit]

def get_rsi_for_symbol(symbol, interval="1h", period=14):
    """Busca klines e calcula RSI para um símbolo"""
    try:
        r = requests.get(
            f"{BINANCE}/api/v3/klines",
            params={"symbol": symbol, "interval": interval, "limit": period + 10},
            timeout=10
        )
        if r.status_code != 200:
            return None
        closes = [float(k[4]) for k in r.json()]
        return get_rsi(closes, period)
    except Exception:
        return None

def format_html_rows(rows):
    """Formata ticker como tabela HTML Telegram"""
    now = datetime.now().strftime("%d/%m %H:%M")
    header = (
        f"📊 <b>MULTI-TICKER BINANCE</b>\n"
        f"   {now} • Top {len(rows)} USDT\n"
        f"   {'─'*42}\n"
        f"<b>  SYMBOL   PRICE        RSI   VOL 24H   CHG%</b>\n"
    )
    
    lines = []
    for row in rows:
        sym = row["symbol"].replace("USDT", "")
        price = row["price"]
        rsi = row["rsi"]
        vol = row["quote_vol"]
        chg = row["price_change"]
        
        # Format price (varies wildly between coins)
        if price >= 1000:
            price_str = f"${price:,.0f}"
        elif price >= 1:
            price_str = f"${price:,.2f}"
        elif price >= 0.01:
            price_str = f"${price:.4f}"
        else:
            price_str = f"${price:.6f}"
        
        # RSI indicator
        if rsi is None:
            rsi_str = "  —"
        elif rsi >= 70:
            rsi_str = f"<b><i>{rsi:5.1f} 🔴</i></b>"
        elif rsi <= 30:
            rsi_str = f"<b><i>{rsi:5.1f} 🟢</i></b>"
        else:
            rsi_str = f"{rsi:5.1f}"
        
        # Volume formatting
        if vol >= 1e9:
            vol_str = f"${vol/1e9:.1f}B"
        elif vol >= 1e6:
            vol_str = f"${vol/1e6:.0f}M"
        else:
            vol_str = f"${vol/1e3:.0f}K"
        
        # Change indicator
        chg_indicator = "▲" if chg >= 0 else "▼"
        chg_str = f"{chg_indicator}{abs(chg):.2f}%"
        if chg >= 5:
            chg_str = f"<b>{chg_str} 🚀</b>"
        elif chg <= -5:
            chg_str = f"<b>{chg_str} 💥</b>"
        
        lines.append(
            f"  {sym:<8} {price_str:<14} {rsi_str}  {vol_str:<10} {chg_str}"
        )
    
    footer = f"\n{'─'*42}\n💡 RSI>70 sobrecompra | RSI<30 sobrevenda"
    return header + "\n".join(lines)

def main():
    # Parse args
    top_n = 20
    for arg in sys.argv[1:]:
        if arg.isdigit():
            top_n = int(arg)
    
    print(f"Fetching top {top_n} USDT pairs...", file=sys.stderr)
    
    # Get top pairs
    pairs = get_top_usdt_pairs(limit=top_n * 2)  # fetch extra to filter
    
    if not pairs:
        print("No pairs found", file=sys.stderr)
        return 1
    
    # Fetch RSI in parallel
    def enrich_with_rsi(pair):
        rsi = get_rsi_for_symbol(pair["symbol"], "1h", 14)
        pair["rsi"] = rsi
        return pair
    
    enriched = []
    with ThreadPoolExecutor(max_workers=20) as ex:
        futures = {ex.submit(enrich_with_rsi, p): p for p in pairs[:top_n]}
        for i, future in enumerate(as_completed(futures)):
            try:
                result = future.result()
                enriched.append(result)
                if i % 5 == 0:
                    print(f"  RSI {i+1}/{len(futures)}...", file=sys.stderr)
            except Exception as e:
                print(f"  Error: {e}", file=sys.stderr)
    
    # Sort by volume (original order = by volume)
    enriched.sort(key=lambda x: x["quote_vol"], reverse=True)
    
    # Output
    html = format_html_rows(enriched)
    
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
