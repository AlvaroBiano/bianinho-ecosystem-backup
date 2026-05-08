#!/usr/bin/env python3
"""
Crypto API Status — Testa todas as APIs de criptomoedas
Uso: python3 cripto_status.py
Output: Status de cada API + dados de exemplo
"""
import requests
import os
import sys
import json
from datetime import datetime

# Load .env
ENV_FILE = os.path.expanduser("~/.hermes/.env")
if os.path.exists(ENV_FILE):
    with open(ENV_FILE) as f:
        for line in f:
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k, v)

# ── Config ───────────────────────────────────────────────────────────────────
CMC_KEY   = os.getenv("COINMARKETCAP_API_KEY", "")
NEWS_KEY  = os.getenv("NEWSAPI_API_KEY", "")
BINANCE   = "https://api.binance.com"
COINGECKO = "https://api.coingecko.com/api/v3"
CC        = "https://min-api.cryptocompare.com"
COINCAP   = "https://api.coincap.io/v2"
DEFI_LLAMA = "https://api.llama.fi"
PAPRIKA   = "https://api.coinpaprika.com/v1"

def status_ok(name, latency_ms, detail=""):
    icon = "✅" if latency_ms < 3000 else "⚠️"
    detail_str = f" → {detail}" if detail else ""
    print(f"  {icon} {name}: OK ({latency_ms:.0f}ms){detail_str}")

def status_fail(name, reason):
    print(f"  ❌ {name}: FAIL — {reason}")

def test_binance():
    """Binance public API — sem key"""
    t0 = datetime.now()
    try:
        r = requests.get(f"{BINANCE}/api/v3/ticker/24hr",
                        params={"symbol": "BTCUSDT"}, timeout=10)
        ms = (datetime.now() - t0).total_seconds() * 1000
        if r.status_code == 200:
            d = r.json()
            price = float(d["lastPrice"])
            vol_24h = float(d["quoteVolume"]) / 1e9
            change = float(d["priceChangePercent"])
            status_ok("Binance", ms, f"BTC=${price:,.0f} vol=${vol_24h:.1f}B {change:+.2f}%")
            return True
        status_fail("Binance", f"HTTP {r.status_code}")
    except Exception as e:
        status_fail("Binance", str(e))
    return False

def test_coingecko():
    """CoinGecko — gratuito, sem key"""
    t0 = datetime.now()
    try:
        r = requests.get(f"{COINGECKO}/simple/price",
                         params={"ids": "bitcoin,ethereum,solana",
                                 "vs_currencies": "usd",
                                 "include_24hr_vol": "true"},
                         timeout=10)
        ms = (datetime.now() - t0).total_seconds() * 1000
        if r.status_code == 200:
            d = r.json()
            btc = d.get("bitcoin", {}).get("usd", 0)
            status_ok("CoinGecko", ms, f"BTC=${btc:,.0f}")
            return True
        status_fail("CoinGecko", f"HTTP {r.status_code}")
    except Exception as e:
        status_fail("CoinGecko", str(e))
    return False

def test_cryptocompare():
    """CryptoCompare — gratuito, sem key. News + preço."""
    t0 = datetime.now()
    try:
        r = requests.get(f"{CC}/data/pricemultifull",
                        params={"fsyms": "BTC,ETH", "tsyms": "USD"},
                        timeout=10)
        ms = (datetime.now() - t0).total_seconds() * 1000
        if r.status_code == 200:
            d = r.json()
            btc_price = d["RAW"]["BTC"]["USD"]["PRICE"]
            status_ok("CryptoCompare", ms, f"BTC=${btc_price:,.0f}")
            return True
        status_fail("CryptoCompare", f"HTTP {r.status_code}")
    except Exception as e:
        status_fail("CryptoCompare", str(e))
    return False

def test_coincap():
    """CoinCap — gratuito, sem key. Pode falhar com DNS no MacBook."""
    t0 = datetime.now()
    try:
        r = requests.get(f"{COINCAP}/assets/bitcoin", timeout=10)
        ms = (datetime.now() - t0).total_seconds() * 1000
        if r.status_code == 200:
            d = r.json().get("data", {})
            price = float(d.get("priceUsd", 0))
            status_ok("CoinCap", ms, f"BTC=${price:,.0f}")
            return True
        status_fail("CoinCap", f"HTTP {r.status_code}")
    except Exception as e:
        status_fail("CoinCap", f"{type(e).__name__}: {e}")
    return False

def test_defi_llama():
    """DeFi Llama — gratuito, sem key"""
    t0 = datetime.now()
    try:
        r = requests.get(f"{DEFI_LLAMA}/protocols", timeout=15)
        ms = (datetime.now() - t0).total_seconds() * 1000
        if r.status_code == 200:
            protocols = r.json()
            total_tvl = sum(float(p.get("tvl", 0) or 0) for p in protocols)
            top5_names = [p["name"] for p in sorted(protocols, key=lambda x: float(x.get("tvl",0) or 0), reverse=True)[:5]]
            status_ok("DeFi Llama", ms, f"total TVL=${total_tvl/1e9:.1f}B top5={', '.join(top5_names)}")
            return True
        status_fail("DeFi Llama", f"HTTP {r.status_code}")
    except Exception as e:
        status_fail("DeFi Llama", str(e))
    return False

def test_coinpaprika():
    """CoinPaprika — gratuito, sem key"""
    t0 = datetime.now()
    try:
        r = requests.get(f"{PAPRIKA}/tickers", timeout=10)
        ms = (datetime.now() - t0).total_seconds() * 1000
        if r.status_code == 200:
            data = r.json()
            btc = next((x for x in data if x.get("id") == "btc-bitcoin"), None)
            if btc:
                price = float(btc.get("price_usd", 0))
                status_ok("CoinPaprika", ms, f"BTC=${price:,.0f} ({len(data)} coins)")
            else:
                status_ok("CoinPaprika", ms, f"OK ({len(data)} coins, BTC não encontrado)")
            return True
        status_fail("CoinPaprika", f"HTTP {r.status_code}")
    except Exception as e:
        status_fail("CoinPaprika", str(e))
    return False

def test_coinmarketcap():
    """CoinMarketCap — requer API key"""
    if not CMC_KEY:
        status_fail("CoinMarketCap", "Sem API key no .env")
        return False
    t0 = datetime.now()
    try:
        r = requests.get(
            "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest",
            params={"limit": 3, "sort": "market_cap"},
            headers={"X-CMC_PRO_API_KEY": CMC_KEY},
            timeout=10
        )
        ms = (datetime.now() - t0).total_seconds() * 1000
        if r.status_code == 200:
            d = r.json()
            coins = d.get("data", [])
            top = ", ".join([f"{c['symbol']}=${float(c['quote']['USD']['price']):.2f}" for c in coins[:3]])
            status_ok("CoinMarketCap", ms, top)
            return True
        status_fail("CoinMarketCap", f"HTTP {r.status_code}: {str(r.json())[:100]}")
    except Exception as e:
        status_fail("CoinMarketCap", str(e))
    return False

def test_newsapi():
    """NewsAPI — requer API key"""
    if not NEWS_KEY:
        status_fail("NewsAPI", "Sem API key no .env")
        return False
    t0 = datetime.now()
    try:
        r = requests.get(
            "https://newsapi.org/v2/everything",
            params={"q": "bitcoin", "pageSize": 3, "sortBy": "publishedAt"},
            headers={"X-Api-Key": NEWS_KEY},
            timeout=10
        )
        ms = (datetime.now() - t0).total_seconds() * 1000
        if r.status_code == 200:
            d = r.json()
            count = d.get("totalResults", 0)
            status_ok("NewsAPI", ms, f"{count} artigos disponíveis")
            return True
        status_fail("NewsAPI", f"HTTP {r.status_code}")
    except Exception as e:
        status_fail("NewsAPI", str(e))
    return False

def test_binance_klines():
    """Binance klines endpoint — sem key"""
    t0 = datetime.now()
    try:
        r = requests.get(
            f"{BINANCE}/api/v3/klines",
            params={"symbol": "BTCUSDT", "interval": "1h", "limit": 5},
            timeout=10
        )
        ms = (datetime.now() - t0).total_seconds() * 1000
        if r.status_code == 200:
            data = r.json()
            last_close = float(data[-1][4])
            status_ok("Binance klines", ms, f"BTC=${last_close:,.0f}")
            return True
        status_fail("Binance klines", f"HTTP {r.status_code}")
    except Exception as e:
        status_fail("Binance klines", str(e))
    return False

def test_binance_depth():
    """Binance order book depth — sem key"""
    t0 = datetime.now()
    try:
        r = requests.get(
            f"{BINANCE}/api/v3/depth",
            params={"symbol": "BTCUSDT", "limit": 5},
            timeout=10
        )
        ms = (datetime.now() - t0).total_seconds() * 1000
        if r.status_code == 200:
            d = r.json()
            bids = len(d.get("bids", []))
            asks = len(d.get("asks", []))
            status_ok("Binance depth", ms, f"bids={bids} asks={asks}")
            return True
        status_fail("Binance depth", f"HTTP {r.status_code}")
    except Exception as e:
        status_fail("Binance depth", str(e))
    return False

def main():
    print("\n" + "="*60)
    print("  🔍 CRYPTO API STATUS")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    print()

    print("  [ APIS PÚBLICAS (sem key) ]")
    test_binance()
    test_binance_klines()
    test_binance_depth()
    test_coingecko()
    test_cryptocompare()
    test_coincap()
    test_defi_llama()
    test_coinpaprika()
    print()

    print("  [ APIS COM API KEY ]")
    test_coinmarketcap()
    test_newsapi()
    print()

    print("="*60)
    print("  Rate Limits de Referência:")
    print("  • Binance: 1200 requests/min")
    print("  • CoinGecko: 10-30 calls/min (sem key)")
    print("  • CryptoCompare: 10-50 req/sec")
    print("  • CoinCap: 10,000 requests/hora")
    print("  • CoinMarketCap: 10-40/min (com key)")
    print("  • NewsAPI: 100/day (grátis)")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
