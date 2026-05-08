#!/usr/bin/env python3
"""
SISTEMA DE SCORING PRE-PUMP — VERSÃO FINAL
Baseado nos dados reais de 123 pumps na Binance (21 dias de dados)

PADRÃO IDENTIFICADO (dados reais):
1. Volume 7d antes >= 2x média → presente em 71% dos grandes pumps
2. RSI >= 65 (sobrecompra) → presente em 67% dos grandes pumps
3. Preço dentro de 15% do máximo 7d → presente em 79% dos grandes pumps
4. Retorno 7d > 0 (já subindo) → presente em 57% dos grandes pumps
5. Distância da mínima < 30% → presente em 86% dos grandes pumps
6. Alta volatilidade (std > 0.5%/h) → indica momentum
"""

import requests
import json
import time
from datetime import datetime
from collections import Counter

def get_klines(symbol, interval='1h', limit=200):
    try:
        r = requests.get('https://api.binance.com/api/v3/klines',
                        params={'symbol': symbol, 'interval': interval, 'limit': limit},
                        timeout=10)
        r.raise_for_status()
        return r.json()
    except:
        return None

def calc_rsi(prices, period=14):
    if len(prices) < period + 1:
        return None
    deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
    gains = [d if d > 0 else 0 for d in deltas[-period:]]
    losses = [-d if d < 0 else 0 for d in deltas[-period:]]
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def analyze_coin(symbol):
    """Retorna score de probabilidade de pump para um par"""
    candles = get_klines(symbol, '1h', 200)
    if not candles or len(candles) < 100:
        return None

    closes = [float(c[4]) for c in candles]
    volumes = [float(c[5]) for c in candles]

    #分割: últimas 24h, 48h, 168h (7d)
    c24 = closes[-24:]
    c48 = closes[-48:]
    c168 = closes[-168:] if len(closes) >= 168 else closes
    c_all = closes

    v24 = volumes[-24:]
    v48 = volumes[-48:]
    v168 = volumes[-168:] if len(volumes) >= 168 else volumes
    older_168 = volumes[-336:-168] if len(volumes) >= 336 else v168[:len(v168)//2]

    # 1. VOLUME RATIO 7d (volume recente vs anterior)
    avg_v_7d = sum(v168) / len(v168) if v168 else 1
    older_avg = sum(older_168) / len(older_168) if older_168 else avg_v_7d
    vol_ratio_7d = avg_v_7d / older_avg if older_avg > 0 else 1

    # 2. VOLUME RATIO 24h
    avg_v_24 = sum(v24) / 24
    older_24 = sum(v48[:24]) / 24 if len(v48) >= 24 else avg_v_24
    vol_ratio_24 = avg_v_24 / older_24 if older_24 > 0 else 1

    # 3. RSI
    rsi = calc_rsi(c168[-15:]) if len(c168) >= 15 else calc_rsi(c48[-15:]) if len(c48) >= 15 else None

    # 4. Drawdown do máximo em 7d
    max_7d = max(c168)
    current_price = c168[-1]
    drawdown_7d = ((max_7d - current_price) / max_7d) * 100 if max_7d > 0 else 0

    # 5. Distância da mínima em 7d
    min_7d = min(c168)
    dist_from_low_7d = ((current_price - min_7d) / min_7d) * 100 if min_7d > 0 else 0

    # 6. Retorno 7d
    ret_7d = ((c168[-1] - c168[0]) / c168[0]) * 100 if c168[0] > 0 else 0

    # 7. Retorno 24h
    ret_24h = ((c24[-1] - c24[0]) / c24[0]) * 100 if c24[0] > 0 else 0

    # 8. Volatilidade 7d (std dev dos retornos)
    rets_7d = [(c168[i]-c168[i-1])/c168[i-1]*100 for i in range(1,len(c168))]
    mean_ret = sum(rets_7d) / len(rets_7d) if rets_7d else 0
    volatility_7d = (sum((r - mean_ret)**2 for r in rets_7d) / len(rets_7d)) ** 0.5 if rets_7d else 0

    # 9. Consolidacao: range 7d vs preço atual
    range_7d = ((max_7d - min_7d) / min_7d) * 100 if min_7d > 0 else 0

    # SCORING
    score = 0
    reasons = []

    # FATOR 1: Volume spiking (PESO ALTO)
    if vol_ratio_7d >= 3.0:
        score += 35
        reasons.append(f"VOLUME 7d: {vol_ratio_7d:.1f}x (+35)")
    elif vol_ratio_7d >= 2.0:
        score += 25
        reasons.append(f"VOLUME 7d: {vol_ratio_7d:.1f}x (+25)")
    elif vol_ratio_7d >= 1.5:
        score += 15
        reasons.append(f"VOLUME 7d: {vol_ratio_7d:.1f}x (+15)")
    elif vol_ratio_7d >= 1.2:
        score += 7
        reasons.append(f"VOLUME 7d: {vol_ratio_7d:.1f}x (+7)")

    # FATOR 2: RSI sobrecompra (PESO ALTO)
    if rsi and rsi >= 75:
        score += 25
        reasons.append(f"RSI: {rsi:.0f} sobrecompra (+25)")
    elif rsi and rsi >= 65:
        score += 18
        reasons.append(f"RSI: {rsi:.0f} sobrecompra (+18)")
    elif rsi and rsi >= 55:
        score += 10
        reasons.append(f"RSI: {rsi:.0f} neutro-alto (+10)")

    # FATOR 3: Perto do máximo (PESO MÉDIO)
    if drawdown_7d <= 5:
        score += 20
        reasons.append(f"Perto máximo 7d: -{drawdown_7d:.1f}% (+20)")
    elif drawdown_7d <= 10:
        score += 15
        reasons.append(f"Perto máximo 7d: -{drawdown_7d:.1f}% (+15)")
    elif drawdown_7d <= 15:
        score += 10
        reasons.append(f"Perto máximo 7d: -{drawdown_7d:.1f}% (+10)")
    elif drawdown_7d <= 25:
        score += 5
        reasons.append(f"Perto máximo 7d: -{drawdown_7d:.1f}% (+5)")

    # FATOR 4: Retorno 7d positivo (PESO MÉDIO)
    if ret_7d >= 10:
        score += 15
        reasons.append(f"Retorno 7d: +{ret_7d:.1f}% (+15)")
    elif ret_7d >= 5:
        score += 12
        reasons.append(f"Retorno 7d: +{ret_7d:.1f}% (+12)")
    elif ret_7d >= 0:
        score += 8
        reasons.append(f"Retorno 7d: +{ret_7d:.1f}% (+8)")
    elif ret_7d >= -5:
        score += 2
        reasons.append(f"Retorno 7d: {ret_7d:.1f}% (+2)")

    # FATOR 5: Volatilidade (momentum acceleration)
    if volatility_7d >= 1.5:
        score += 10
        reasons.append(f"Volatilidade 7d: {volatility_7d:.2f}%/h (+10)")
    elif volatility_7d >= 1.0:
        score += 7
        reasons.append(f"Volatilidade 7d: {volatility_7d:.2f}%/h (+7)")
    elif volatility_7d >= 0.5:
        score += 4
        reasons.append(f"Volatilidade 7d: {volatility_7d:.2f}%/h (+4)")

    # FATOR 6: Distância da mínima (não está "dead")
    if dist_from_low_7d >= 50:
        score += 8
        reasons.append(f"Acima mínima 7d: +{dist_from_low_7d:.0f}% (+8)")
    elif dist_from_low_7d >= 20:
        score += 5
        reasons.append(f"Acima mínima 7d: +{dist_from_low_7d:.0f}% (+5)")

    # FATOR 7: Consolidacao (range apertado antes de explodir)
    if range_7d <= 20:
        score += 7
        reasons.append(f"Consolidação 7d: {range_7d:.0f}% (+7)")
    elif range_7d <= 40:
        score += 4
        reasons.append(f"Consolidação 7d: {range_7d:.0f}% (+4)")

    # CLASSIFICAÇÃO
    if score >= 85:
        classification = "🔴 EXTREMO"
    elif score >= 70:
        classification = "🟠 MUITO ALTO"
    elif score >= 55:
        classification = "🟡 ALTO"
    elif score >= 40:
        classification = "🟢 MÉDIO"
    else:
        classification = "⚪ BAIXO"

    return {
        'symbol': symbol.replace('USDT', ''),
        'price': current_price,
        'score': score,
        'classification': classification,
        'reasons': reasons,
        'metrics': {
            'vol_ratio_7d': round(vol_ratio_7d, 2),
            'vol_ratio_24h': round(vol_ratio_24, 2),
            'rsi': round(rsi, 1) if rsi else None,
            'drawdown_7d': round(drawdown_7d, 1),
            'ret_7d': round(ret_7d, 2),
            'ret_24h': round(ret_24h, 2),
            'volatility_7d': round(volatility_7d, 2),
            'dist_from_low_7d': round(dist_from_low_7d, 1),
            'range_7d': round(range_7d, 1),
        }
    }

# Carregar pares
with open('/tmp/binance_usdt_pairs.txt') as f:
    pairs = [l.strip() for l in f if l.strip()]

print(f"Scaneando {len(pairs)} pares USDT para score PRE-PUMP...")
print(f"Modelo baseado em 123 pumps reais (21 dias de dados Binance)")
print()

results = []
for idx, pair in enumerate(pairs):
    if idx % 50 == 0:
        print(f"Progresso: {idx}/{len(pairs)}")

    result = analyze_coin(pair)
    if result and result['score'] >= 40:
        results.append(result)

    if idx % 10 == 0:
        time.sleep(0.05)

print(f"\nEscaneamento completo: {len(pairs)}/{len(pairs)}")
print()

# Ordenar por score
results.sort(key=lambda x: x['score'], reverse=True)

print("="*70)
print("🔍 COINS COM MAIOR PROBABILIDADE DE PUMP (score >= 40)")
print("="*70)
print(f"\n{'SYM':<8} {'SCORE':>7} {'CLAS':<12} {'VOL 7d':>8} {'RSI':>6} {'DD 7d':>7} {'RET 7d':>8} {'VOLAT':>7}")
print("-"*70)

for r in results[:30]:
    m = r['metrics']
    print(f"{r['symbol']:<8} {r['score']:>6} {r['classification']:<12} {m['vol_ratio_7d']:>7.1f}x {m['rsi'] if m['rsi'] else 'N/A':>6} {m['drawdown_7d']:>6.1f}% {m['ret_7d']:>+7.1f}% {m['volatility_7d']:>6.2f}%")

# Distribuição
print(f"\n\nDistribuição de scores:")
scores_all = [r['score'] for r in results]
for threshold in [85, 70, 55, 40]:
    count = sum(1 for s in scores_all if s >= threshold)
    print(f"  >= {threshold}: {count} coins")

# Guardar top para análise
top_10 = results[:10]
print(f"\n\n{'='*70}")
print("TOP 10 — ANÁLISE DETALHADA")
print("="*70)
for r in top_10:
    print(f"\n{r['symbol']} — Score {r['score']} ({r['classification']})")
    print(f"  Preço: ${r['price']:.6f}")
    for reason in r['reasons']:
        print(f"  • {reason}")
    m = r['metrics']
    print(f"  RAW: vol_7d={m['vol_ratio_7d']}x | rsi={m['rsi']} | dd={m['drawdown_7d']}% | ret_7d={m['ret_7d']}% | range={m['range_7d']}%")

# Salvar resultado
with open('/tmp/pump_scores_current.json', 'w') as f:
    json.dump(results, f)
print(f"\n\nSalvo em /tmp/pump_scores_current.json")

# Backtesting simples: dos pumps que tivemos na etapa anterior,
# qual era o score deles 7 dias antes?
print(f"\n\n{'='*70}")
print("BACKTEST: Qual score os pumps reais teriam gotten?")
print("="*70)

# pump_data contém os pumps
with open('/tmp/all_pumps_15pct.json') as f:
    pump_details = json.load(f)

# Para os 20 maiores pumps, verificar se score seria alto
# (Nem todos têm dados suficientes no JSON salvo, mas podemos recalcular)
print("Recalculando scores para pumps recentes...")

backtest_pumps = [
    ('IO', '2026-05-06 03:00', 46.2),
    ('STX', '2026-05-05 16:00', 35.4),
    ('TST', '2026-05-03 05:00', 32.7),
    ('HIVE', '2026-05-05 02:00', 30.0),
]

for sym, ptime, ppct in backtest_pumps:
    # Score atual (hoje)
    r = analyze_coin(f"{sym}USDT")
    if r:
        print(f"\n  {sym} (pump passado de {ppct}% em {ptime}):")
        print(f"    Score atual: {r['score']} ({r['classification']})")
        print(f"    Retorno 7d: {r['metrics']['ret_7d']}%")
        print(f"    Vol ratio 7d: {r['metrics']['vol_ratio_7d']}x")
        print(f"    RSI: {r['metrics']['rsi']}")
        print(f"    Drawdown 7d: -{r['metrics']['drawdown_7d']}%")
