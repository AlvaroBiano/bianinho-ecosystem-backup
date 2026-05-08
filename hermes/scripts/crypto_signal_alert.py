#!/usr/bin/env python3
"""
Crypto Signal Alert — FAST version com concurrency
 só USDT (mais líquido), baixa top 200 por vol, klines em paralelo
"""

import requests
import json
import os
import sys
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# ── Config ──────────────────────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID") or os.getenv("TELEGRAM_HOME_CHANNEL", "")
SCORE_THRESHOLD    = 95
TOP_VOL_PAIRS      = 200          # só os top 200 por volume 24h
MAX_WORKERS        = 30           # threads concorrentes
CACHE_FILE         = "/tmp/crypto_alert_cache.json"
# ─────────────────────────────────────────────────────────────────────────────

BASE = "https://api.binance.com"
_log_lock = threading.Lock()

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    with _log_lock:
        print(f"[{ts}] {msg}", file=sys.stderr)

def send_telegram(text):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        log("AVISO: TELEGRAM_BOT_TOKEN ou TELEGRAM_CHAT_ID não definidos")
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": "true"
    }
    try:
        r = requests.post(url, json=payload, timeout=10)
        r.raise_for_status()
        log(f"Telegram OK")
        return True
    except Exception as e:
        log(f"ERRO Telegram: {e}")
        return False

def get_top_usdt_pairs(n=200):
    """Pega top N pares USDT por volume 24h (2 chamadas: exchangeInfo + ticker)."""
    # 1) Lista de símbolos TRADING
    info = requests.get(f"{BASE}/api/v3/exchangeInfo", timeout=10).json()
    trading = {s["symbol"] for s in info["symbols"]
               if s["quoteAsset"] == "USDT" and s["status"] == "TRADING"}

    # 2) Todos os tickers (1 chamada)
    r = requests.get(f"{BASE}/api/v3/ticker/24hr", timeout=15)
    r.raise_for_status()
    pairs = []
    for t in r.json():
        sym = t.get("symbol", "")
        if not sym.endswith("USDT") or sym not in trading:
            continue
        try:
            qv    = float(t.get("quoteVolume", 0))
            price = float(t.get("lastPrice", 0))
            if qv > 10_000 and price > 0.00001:
                pairs.append({"symbol": sym, "quoteVolume": qv, "price": price})
        except (ValueError, TypeError):
            continue
    pairs.sort(key=lambda x: -x["quoteVolume"])
    return [p["symbol"] for p in pairs[:n]]

def fetch_klines(symbol):
    """Busca klines 15m × 96 para um símbolo."""
    try:
        r = requests.get(
            f"{BASE}/api/v3/klines",
            params={"symbol": symbol, "interval": "15m", "limit": 96},
            timeout=6
        )
        r.raise_for_status()
        return r.json()
    except Exception:
        return None

def calc_score(klines_data, symbol):
    """Calcula score. Retorna dict ou None."""
    try:
        k = klines_data
        closes = [float(c[4]) for c in k]
        vols   = [float(c[5]) for c in k]
        price  = closes[-1]

        last4  = closes[-4:];  last16 = closes[-16:]; last96 = closes[-96:]
        ret1h  = ((last4[-1]-last4[0])/last4[0])*100
        ret4h  = ((last16[-1]-last16[0])/last16[0])*100

        v4h    = sum(vols[-16:])
        vprev  = sum(vols[-96:-16])/20
        vol_ratio = v4h/vprev if vprev > 0 else 0
        avg_v  = sum(vols[-60:])/60
        v_spike = vols[-1]/avg_v if avg_v > 0 else 0
        max24  = max(last96); min24 = min(last96)
        dd     = ((max24-price)/max24)*100
        dist_low = ((price-min24)/min24)*100

        # RSI 14
        period = 14
        deltas = [closes[i]-closes[i-1] for i in range(-period, 0)]
        g=[d if d>0 else 0 for d in deltas]
        l=[-d if d<0 else 0 for d in deltas]
        ag=sum(g)/period; al=sum(l)/period
        rsi = 100-(100/(1+ag/al)) if al>0 else 100

        # ── FILTROS Duros (TODOS têm que passar) ─────────────────
        # RSI: 50-75 é válido
        if not (50 <= rsi <= 75):
            return None
        # DD: 0 a 6% do topo 24h
        if not (0.0 <= dd <= 6.0):
            return None
        # 1h: -2% a +2% (consolidação ou ligeiro pullback)
        if not (-2.0 <= ret1h <= 2.0):
            return None
        # Volume: >= 3x é obrigatório
        if vol_ratio < 3.0:
            return None
        # 4h: 0% a 25% (subindo ou lateral)
        if not (0.0 <= ret4h <= 25.0):
            return None
        # Dist do mínimo 24h: >= 2% (já rebotou)
        if dist_low < 2.0:
            return None
        # ── Fim dos filtros ─────────────────────────────────────

        score = 0
        if   vol_ratio >= 4:   score += 30
        elif vol_ratio >= 3:   score += 25
        elif vol_ratio >= 2:   score += 18
        if   62 <= rsi <= 72: score += 25
        elif rsi >= 55:        score += 12
        elif rsi > 75:         score -= 10
        if   -2.0 <= ret1h <= 0.3: score += 15
        elif 0.3 < ret1h <= 1.5:   score += 8
        elif ret1h < -2:            score -= 8
        if   1 <= dd <= 5:  score += 15
        elif dd <= 2:       score += 20
        elif dd <= 10:      score += 6
        elif dd > 15:       score -= 10
        if   2 <= ret4h <= 10: score += 15
        elif 10 < ret4h <= 20:  score += 8
        elif 0 <= ret4h < 2:   score += 6
        elif ret4h > 30:        score -= 15
        if   v_spike >= 2:  score += 8
        elif v_spike >= 1.5: score += 5
        if   dist_low >= 20: score += 5

        return {
            "symbol": symbol,
            "price": price,
            "score": score,
            "rsi": rsi,
            "ret1h": ret1h,
            "ret4h": ret4h,
            "vol_ratio": vol_ratio,
            "v_spike": v_spike,
            "dd": dd,
            "dist_low": dist_low,
            "max24": max24,
            "low24": min24,
        }
    except Exception:
        return None

def verdict(s):
    """Gera veredito directo com filtro extra de confiança."""
    rsi = s["rsi"]
    dd = s["dd"]
    vol = s["vol_ratio"]
    score = s["score"]
    ret4h = s["ret4h"]

    if score >= 100 and vol >= 5 and 62 <= rsi <= 72 and 1 <= dd <= 4:
        return "🚀 TOP — ENTRAR AGORA"
    elif score >= 100:
        return "🚀 ENTRAR"
    elif score >= 95:
        return "📡 CONSIDERAR"


def format_alert(signals):
    now = datetime.now().strftime("%d/%m %H:%M")
    score_100 = [s for s in signals if s["score"] >= 100]
    score_95  = [s for s in signals if s["score"] == 95]

    header = f"<b>ALERTA CRYPTO</b> — {now}\n"

    lines = []

    # Score 100
    for s in sorted(score_100, key=lambda x: -x["score"]):
        v = verdict(s)
        qty = 15 / s["price"]
        tp5  = s["price"] * 1.05
        tp10 = s["price"] * 1.10
        stop = s["price"] * 0.97
        lines.append(
            f"{v}\n"
            f"<b>{s['symbol'].replace('USDT','')}/USDT</b> ${s['price']:.6f}\n"
            f"RSI {s['rsi']:.0f} | Vol {s['vol_ratio']:.0f}x | DD {s['dd']:.1f}%\n"
            f"+5%: ${tp5:.6f} | +10%: ${tp10:.6f}\n"
            f"Stop -3%: ${stop:.6f} | $15 → {qty:.0f} units\n"
        )

    # Score 95
    for s in sorted(score_95, key=lambda x: -x["score"]):
        v = verdict(s)
        lines.append(
            f"{v}\n"
            f"<b>{s['symbol'].replace('USDT','')}/USDT</b> ${s['price']:.6f}\n"
            f"RSI {s['rsi']:.0f} | Vol {s['vol_ratio']:.0f}x | DD {s['dd']:.1f}%\n"
        )

    if not lines:
        return None

    footer = "Filtros: RSI 50-74 | DD 0.5-5% | Vol 4h 3x+ | 1h -1.5% a +1.5%"
    return header + "\n".join(lines) + "\n\n" + footer

def main():
    log("=== Scan iniciado ===")
    symbols = get_top_usdt_pairs(TOP_VOL_PAIRS)
    log(f"{len(symbols)} pares para escanear")

    # Fetch klines em paralelo
    klines_map = {}
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = {ex.submit(fetch_klines, s): s for s in symbols}
        done = 0
        for fut in as_completed(futures):
            done += 1
            if done % 50 == 0:
                log(f"  {done}/{len(symbols)} klines recebidos...")
            sym = futures[fut]
            data = fut.result()
            if data:
                klines_map[sym] = data

    log(f"{len(klines_map)} klines OK — calculando scores...")

    # Calcula scores
    signals = []
    cache = {}
    try:
        with open(CACHE_FILE) as f:
            cache = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        pass

    now_ts = datetime.now().timestamp()

    for sym, klines_data in klines_map.items():
        score_data = calc_score(klines_data, sym)
        if score_data and score_data["score"] >= SCORE_THRESHOLD:
            last = cache.get(sym, 0)
            if now_ts - last > 1800:  # 30 min cooldown
                signals.append(score_data)
                cache[sym] = now_ts

    if signals:
        with open(CACHE_FILE, "w") as f:
            json.dump(cache, f)
        msg = format_alert(signals)
        if msg:
            send_telegram(msg)
        log(f"Alerta enviado: {[s['symbol'] for s in signals]}")
    else:
        log("Nenhum sinal >= 95.")

if __name__ == "__main__":
    main()
