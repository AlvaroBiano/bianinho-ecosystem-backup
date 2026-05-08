#!/usr/bin/env python3
"""
Monitor de Preços Binance - Cripto
Uso: python3 cripto_price_monitor.py [symbol] [interval]
Exemplo: python3 cripto_price_monitor.py BTCUSDT 15
Default: BTCUSDT, 15 minutos
"""

import sys
import requests
from datetime import datetime

try:
    symbol = sys.argv[1].upper() if len(sys.argv) > 1 else "BTCUSDT"
    interval_map = {"1": "1m", "5": "5m", "15": "15m", "30": "30m",
                    "1h": "1h", "4h": "4h", "1d": "1d"}
    interval = sys.argv[2] if len(sys.argv) > 2 else "15m"
    interval = interval_map.get(interval, interval)
except:
    symbol = "BTCUSDT"
    interval = "15m"

BASE_URL = "https://api.binance.com"

def get_price(symbol):
    r = requests.get(f"{BASE_URL}/api/v3/ticker/24hr", params={"symbol": symbol}, timeout=10)
    r.raise_for_status()
    return r.json()

def get_klines(symbol, interval, limit=100):
    r = requests.get(f"{BASE_URL}/api/v3/klines",
                      params={"symbol": symbol, "interval": interval, "limit": limit},
                      timeout=10)
    r.raise_for_status()
    return r.json()

def format_num(n, decimals=2):
    return f"{float(n):,.{decimals}f}"

def main():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n{'='*50}")
    print(f"  BINANCE PRICE MONITOR")
    print(f"  {now}")
    print(f"{'='*50}")

    # Preço atual
    ticker = get_price(symbol)
    price = float(ticker["lastPrice"])
    high = float(ticker["highPrice"])
    low = float(ticker["lowPrice"])
    change = float(ticker["priceChangePercent"])
    vol = float(ticker["volume"])
    quote_vol = float(ticker["quoteVolume"])

    symbol_base = symbol.replace("USDT", "").replace("BRL", "")
    quote = "USDT" if "USDT" in symbol else ("BRL" if "BRL" in symbol else "USD")

    print(f"\n  📊 {symbol} (Binance)")
    print(f"  Preço:     ${price:,.2f} {quote}")
    print(f"  24h High:  ${high:,.2f}")
    print(f"  24h Low:   ${low:,.2f}")
    print(f"  24h Chg:   {change:+.2f}%")
    print(f"  Volume:    {vol:,.2f} {symbol_base}")
    print(f"  Quote Vol: ${quote_vol:,.0f} {quote}")

    # RSI simples (últimos 100 candles)
    try:
        klines = get_klines(symbol, interval, 100)
        closes = [float(k[4]) for k in klines]
        deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
        gains = [d for d in deltas if d > 0]
        losses = [-d for d in deltas if d < 0]
        avg_gain = sum(gains) / len(gains) if gains else 0
        avg_loss = sum(losses) / len(losses) if losses else 0
        rs = avg_gain / avg_loss if avg_loss else 0
        rsi = 100 - (100 / (1 + rs)) if rs else 50
        print(f"\n  📈 RSI({interval}): {rsi:.1f}")

        # Tendência (MM20)
        sma20 = sum(closes[-20:]) / 20
        trend = "↑ ALTA" if price > sma20 else "↓ BAIXA"
        print(f"  📐 SMA20:  ${sma20:,.2f} ({trend})")
    except Exception as e:
        print(f"\n  RSI: erro ({e})")

    print(f"\n{'='*50}")
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n  Cancelado.")
        sys.exit(0)
    except Exception as e:
        print(f"\n  Erro: {e}")
        sys.exit(1)
