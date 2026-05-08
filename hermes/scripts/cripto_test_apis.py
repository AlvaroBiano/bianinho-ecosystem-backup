#!/usr/bin/env python3
"""
Teste de conectividade com todas as APIs de criptomoedas.
Uso: python3 cripto_test_apis.py
"""

import requests
import sys
from datetime import datetime

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"

def log(ok, msg):
    symbol = f"{GREEN}✓{RESET}" if ok else f"{RED}✗{RESET}"
    print(f"  {symbol} {msg}")

def test_binance():
    print(f"\n{YELLOW}[1] Binance API{RESET}")
    try:
        # Preço atual BTCUSDT
        r = requests.get("https://api.binance.com/api/v3/ticker/24hr",
                         params={"symbol": "BTCUSDT"}, timeout=10)
        r.raise_for_status()
        data = r.json()
        price = float(data["lastPrice"])
        high = float(data["highPrice"])
        low = float(data["lowPrice"])
        vol = float(data["volume"])
        print(f"  BTCUSDT: ${price:,.2f} | High: ${high:,.2f} | Low: ${low:,.2f}")
        print(f"  Volume 24h: {vol:,.2f} BTC")
        log(True, f"Binance OK (HTTP {r.status_code})")

        # Testar também ETHUSDT
        r2 = requests.get("https://api.binance.com/api/v3/ticker/24hr",
                          params={"symbol": "ETHUSDT"}, timeout=10)
        eth = float(r2.json()["lastPrice"])
        log(True, f"ETHUSDT: ${eth:,.2f}")

        return True
    except Exception as e:
        log(False, f"Binance falhou: {e}")
        return False

def test_coingecko():
    print(f"\n{YELLOW}[2] CoinGecko API{RESET}")
    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {"ids": "bitcoin,ethereum,solana", "vs_currencies": "usd"}
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        print(f"  BTC: ${data['bitcoin']['usd']:,.2f}")
        print(f"  ETH: ${data['ethereum']['usd']:,.2f}")
        print(f"  SOL: ${data['solana']['usd']:,.2f}")
        log(True, f"CoinGecko OK (HTTP {r.status_code})")
        return True
    except Exception as e:
        log(False, f"CoinGecko falhou: {e}")
        return False

def test_cryptocompare():
    print(f"\n{YELLOW}[3] CryptoCompare API{RESET}")
    try:
        # News
        r = requests.get("https://min-api.cryptocompare.com/data/v2/news/",
                         params={"lang": "EN"}, timeout=10)
        r.raise_for_status()
        news = r.json()
        log(True, f"CryptoCompare News OK ({len(news['Data'])} articles)")

        # Price
        r2 = requests.get("https://min-api.cryptocompare.com/data/pricemultifull",
                          params={"fsyms": "BTC,ETH", "tsyms": "USD"}, timeout=10)
        prices = r2.json()["RAW"]
        btc = prices["BTC"]["USD"]["PRICE"]
        eth = prices["ETH"]["USD"]["PRICE"]
        print(f"  BTC: ${btc:,.2f} | ETH: ${eth:,.2f}")
        return True
    except Exception as e:
        log(False, f"CryptoCompare falhou: {e}")
        return False

def test_coincap():
    print(f"\n{YELLOW}[4] CoinCap API{RESET}")
    try:
        r = requests.get("https://api.coincap.io/v2/assets/bitcoin", timeout=10)
        r.raise_for_status()
        data = r.json()["data"]
        price = float(data["priceUsd"])
        vol = float(data["volumeUsd24Hr"])
        supply = float(data["supply"])
        print(f"  BTC: ${price:,.2f}")
        print(f"  Volume 24h: ${vol:,.0f}")
        log(True, f"CoinCap OK (HTTP {r.status_code})")
        return True
    except Exception as e:
        log(False, f"CoinCap falhou: {e}")
        return False

def test_defi_llama():
    print(f"\n{YELLOW}[5] DeFi Llama API{RESET}")
    try:
        r = requests.get("https://api.llama.fi/protocols", timeout=10)
        r.raise_for_status()
        data = r.json()
        total_tvl = sum(float(p.get('tvl', 0) or 0) for p in data if p.get('tvl'))
        print(f"  Total protocols: {len(data)}")
        print(f"  Total DeFi TVL: ${total_tvl:,.0f}")
        top = sorted(data, key=lambda x: float(x.get('tvl', 0) or 0), reverse=True)[:3]
        print(f"  Top: {', '.join(p['symbol'] for p in top)}")
        log(True, f"DeFi Llama OK (HTTP {r.status_code})")
        return True
    except Exception as e:
        log(False, f"DeFi Llama falhou: {e}")
        return False

def test_coinpaprika():
    print(f"\n{YELLOW}[6] CoinPaprika API{RESET}")
    try:
        r = requests.get("https://api.coinpaprika.com/v1/coins/btc-bitcoin", timeout=10)
        r.raise_for_status()
        data = r.json()
        print(f"  BTC name: {data['name']}")
        log(True, f"CoinPaprika OK (HTTP {r.status_code})")
        return True
    except Exception as e:
        log(False, f"CoinPaprika falhou: {e}")
        return False

def test_cryptopanic():
    print(f"\n{YELLOW}[7] CryptoPanic News API{RESET}")
    try:
        r = requests.get("https://cryptopanic.com/api/v1/posts/",
                         params={"auth_token": "free", "filter": "hot",
                                 "currencies": "btc,eth", "limit": 3},
                         timeout=10)
        r.raise_for_status()
        data = r.json()
        posts = data.get("results", [])
        print(f"  {len(posts)} posts encontrados")
        for p in posts[:2]:
            print(f"  - {p['title'][:60]}...")
        log(True, f"CryptoPanic OK (HTTP {r.status_code})")
        return True
    except Exception as e:
        log(False, f"CryptoPanic falhou: {e}")
        return False

def main():
    print(f"{'='*55}")
    print(f"  TESTE DE APIs DE CRIPTOMOEDAS")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*55}")

    results = []
    results.append(("Binance", test_binance()))
    results.append(("CoinGecko", test_coingecko()))
    results.append(("CryptoCompare", test_cryptocompare()))
    results.append(("CoinCap", test_coincap()))
    results.append(("DeFi Llama", test_defi_llama()))
    results.append(("CoinPaprika", test_coinpaprika()))
    results.append(("CryptoPanic", test_cryptopanic()))

    print(f"\n{'='*55}")
    print(f"  RESUMO")
    print(f"{'='*55}")
    for name, ok in results:
        log(ok, name)

    passed = sum(1 for _, ok in results if ok)
    print(f"\n  {passed}/{len(results)} APIs operacionais")
    print(f"{'='*55}")

    return 0 if passed == len(results) else 1

if __name__ == "__main__":
    sys.exit(main())
