#!/usr/bin/env python3
"""
SNIPER SCANNER — Binance USDT + USDC
Escaneia TODOS os pares, filtra sniper shots e envia ao Telegram.
Uso: python3 binance_sniper_alert.py
      python3 binance_sniper_alert.py --dry  (teste sem enviar)
"""
import requests
import json
import time
import sys
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE = "https://api.binance.com"

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID") or os.getenv("TELEGRAM_HOME_CHANNEL", "")

def send_telegram(text):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
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
        return True
    except Exception:
        return False

STABLECOINS = {
    "USDT", "USDC", "BUSD", "USD", "TUSD", "USDP", "FDUSD",
    "DAI", "LUSD", "EUR", "GBP", "JPY", "BRL", "MXN",
}

# ─── Helpers ───────────────────────────────────────────────────
def get_pairs(suffix):
    r = requests.get(f"{BASE}/api/v3/exchangeInfo", timeout=15)
    data = r.json()
    return [s["symbol"] for s in data["symbols"]
            if s["symbol"].endswith(suffix) and s["status"] == "TRADING"]

def get_klines(symbol, limit=80):
    try:
        r = requests.get(f"{BASE}/api/v3/klines",
            params={"symbol": symbol, "interval": "15m", "limit": limit}, timeout=8)
        r.raise_for_status()
        return r.json()
    except:
        return None

def calc_rsi(closes):
    n = min(14, len(closes)-1)
    deltas = [closes[i] - closes[i-1] for i in range(-n, 0)]
    gains  = [d if d > 0 else 0 for d in deltas]
    losses = [-d if d < 0 else 0 for d in deltas]
    ag = sum(gains)/n; al = sum(losses)/n
    if al == 0: return 100
    return 100 - (100 / (1 + ag/al))

def score_coin(klines_data, asset):
    """Retorna dict com score e métricas ou None se não qualifies"""
    closes = [float(c[4]) for c in klines_data]
    vols   = [float(c[5]) for c in klines_data]
    price  = closes[-1]

    if len(closes) < 40 or price <= 0:
        return None

    last4  = closes[-4:]
    last16 = closes[-16:]
    last96 = closes[-96:] if len(closes) >= 96 else closes

    ret1h  = ((last4[-1]-last4[0])/last4[0])*100   if len(last4) >= 2 else 0
    ret4h  = ((last16[-1]-last16[0])/last16[0])*100 if len(last16) >= 2 else 0
    ret24h = ((last96[-1]-last96[0])/last96[0])*100 if len(last96) >= 2 else 0

    v4h   = sum(vols[-16:])
    vprev = sum(vols[-96:-16]) if len(vols) >= 96 else sum(vols[-50:-16]) if len(vols) > 16 else sum(vols)
    vol_ratio = v4h / (vprev/20) if vprev > 0 else 0

    avg_vol = sum(vols[-60:]) / 60
    vol_spike = vols[-1] / avg_vol if avg_vol > 0 else 0

    max24 = max(last96) if len(last96) >= 50 else max(closes)
    min24 = min(last96) if len(last96) >= 50 else min(closes)
    dd    = ((max24 - price) / max24) * 100
    dist_low = ((price - min24) / min24) * 100

    rsi = calc_rsi(closes)
    vol_24h = sum(float(c[7]) for c in klines_data[-96:])

    # ── SCORE ──
    score = 0
    reasons = []

    if vol_ratio >= 3:   score += 25; reasons.append(f"VOL {vol_ratio:.0f}x")
    elif vol_ratio >= 2: score += 18; reasons.append(f"VOL {vol_ratio:.0f}x")
    elif vol_ratio >= 1.5: score += 10; reasons.append(f"VOL {vol_ratio:.0f}x")

    if 62 <= rsi <= 72:   score += 25; reasons.append(f"RSI {rsi:.0f}")
    elif rsi >= 55:        score += 12

    if -2.0 <= ret1h <= 0.3:  score += 15; reasons.append(f"RECUO {ret1h:+.1f}%")
    elif 0.3 < ret1h <= 1.5:  score += 8

    if 1 <= dd <= 5:   score += 15; reasons.append(f"DD {dd:.1f}%")
    elif dd <= 2:      score += 20; reasons.append(f"DD {dd:.1f}%")
    elif dd <= 10:     score += 6

    if 2 <= ret4h <= 10:  score += 15; reasons.append(f"MOM +{ret4h:.0f}%")
    elif 10 < ret4h <= 20: score += 8
    elif 0 <= ret4h < 2:   score += 6

    if vol_spike >= 2.0: score += 8
    elif vol_spike >= 1.5: score += 5

    if dist_low >= 20: score += 5

    # ── FILTROS ──
    if score < 65:    return None
    if vol_ratio < 1.5: return None
    if price < 0.00001: return None
    if ret1h < -4:   return None
    if vol_24h < 50_000: return None  # < $50k vol 24h = shitcoin

    return {
        "symbol": "", "price": price, "score": score,
        "reasons": reasons,
        "ret1h": ret1h, "ret4h": ret4h, "ret24h": ret24h,
        "vol_ratio": vol_ratio, "vol_spike": vol_spike,
        "rsi": rsi, "drawdown": dd, "dist_low": dist_low,
        "max24": max24, "vol_24h": vol_24h, "asset": asset
    }

def scan_one(args):
    pair, asset = args
    base = pair.replace(asset, "")
    if base in STABLECOINS:
        return None
    k = get_klines(pair)
    if not k or len(k) < 40:
        return None
    result = score_coin(k, asset)
    if result:
        result["symbol"] = base
    return result

def scan_all(mtype):
    """Escaneia todos os pares com concorrência"""
    asset = "USDT" if mtype == "USDT" else "USDC"
    pairs = get_pairs(asset)
    results = []
    seen = set()

    with ThreadPoolExecutor(max_workers=25) as ex:
        futures = {ex.submit(scan_one, (p, asset)): p for p in pairs}
        done = 0
        for f in as_completed(futures):
            done += 1
            if done % 100 == 0:
                print(f"  {mtype}: {done}/{len(pairs)}", flush=True)
            try:
                r = f.result()
                if r and r["symbol"] not in seen:
                    seen.add(r["symbol"])
                    results.append(r)
            except Exception:
                pass
            time.sleep(0.005)

    results.sort(key=lambda x: x["score"], reverse=True)
    return results, len(pairs)

# ─── Formatação Telegram ───────────────────────────────────────
def fmt_tg(usdc_res, usdt_res, runtime):
    now = datetime.now().strftime("%d/%m %H:%M BRT")
    total = len(usdc_res) + len(usdt_res)
    lines = [f"<b>SNIPER SCAN — {now}</b>",
             f"Escaneou ~{total} pares em {runtime:.0f}s",
             ""]

    def coin_block(r, qty=15):
        p = r["price"]
        lines2 = [
            f"◆ <b>{r['symbol']}</b> ({r['asset']})",
            f"  ${p:.6f}  |  Score {r['score']}",
            f"  1h {r['ret1h']:+.1f}% | 4h {r['ret4h']:+.1f}% | 24h {r['ret24h']:+.1f}%",
            f"  VOL {r['vol_ratio']:.0f}x | RSI {r['rsi']:.0f} | DD {r['drawdown']:.1f}%",
        ]
        for tp in [5, 7, 10]:
            tp_p = p * (1 + tp/100)
            lines2.append(f"  +{tp}% → ${tp_p:.6f}  |  ${qty*(tp_p):.2f}")
        lines2.append("")
        return lines2

    if usdc_res:
        top = usdc_res[:6]
        lines.append(f"USDC ({len(usdc_res)} alertas)")
        for r in top:
            lines.extend(coin_block(r))
    else:
        lines.append("USDC — sem alertas agora")

    lines.append("")

    if usdt_res:
        top = usdt_res[:4]
        lines.append(f"USDT ({len(usdt_res)} alertas)")
        for r in top:
            lines.extend(coin_block(r))

    return "\n".join(lines)

def fmt_dry(usdc_res, usdt_res, runtime):
    now = datetime.now().strftime("%H:%M")
    all_res = sorted(usdc_res + usdt_res, key=lambda x: x["score"], reverse=True)
    print(f"\nSNIPER — {now} BRT — {len(all_res)} oportunidades em {runtime:.0f}s")
    print(f"{'SYM':<10} {'ASSET':<5} {'SCORE':>6} {'1h':>7} {'4h':>7} {'VOLx':>7} {'RSI':>6} {'DD':>6}")
    print('-'*60)
    for r in all_res[:20]:
        print(f"{r['symbol']:<10} {r['asset']:<5} {r['score']:>5} {r['ret1h']:>+6.1f}% {r['ret4h']:>+6.1f}% {r['vol_ratio']:>6.0f}x {r['rsi']:>5.0f} {r['drawdown']:>5.1f}%")

# ─── Main ──────────────────────────────────────────────────────
if __name__ == "__main__":
    dry = "--dry" in sys.argv

    start = time.time()
    print("Escaneando USDC...", flush=True, file=sys.stderr)
    usdc, usdc_total = scan_all("USDC")
    print(f"  USDC: {len(usdc)} alertas", file=sys.stderr)

    print("Escaneando USDT...", flush=True, file=sys.stderr)
    usdt, usdt_total = scan_all("USDT")
    print(f"  USDT: {len(usdt)} alertas", file=sys.stderr)

    runtime = time.time() - start

    if dry:
        fmt_dry(usdc, usdt, runtime)
        sys.exit(0)

    # Salvar último resultado
    all_res = sorted(usdc + usdt, key=lambda x: x["score"], reverse=True)
    with open("/tmp/sniper_latest.json", "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "runtime": round(runtime, 1),
            "usdc": usdc[:10], "usdt": usdt[:10],
            "total_all": len(all_res)
        }, f, default=str)

    if not all_res:
        sys.exit(0)

    msg = fmt_tg(usdc, usdt, runtime)
    send_telegram(msg)

    with open("/tmp/sniper_msg.txt", "w") as f:
        f.write(msg)
