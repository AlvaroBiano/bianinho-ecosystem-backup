# Transcription Benchmarks — MacBook CPU

## Benchmark Session (May 2026, M1-M5 transcription)

Teste: video 89.7s, Python 3.14, faster-whisper, CPU

| Model | beam_size | compute | Time | Ratio | Segments |
|-------|-----------|---------|------|-------|----------|
| large-v3 | 5 | int8 | 62.7s | 0.70xRT | 13 |
| medium | 5 | int8 | 38.0s | 0.40xRT | 14 |
| medium | 1 | int8 | 23.4s | 0.24xRT | 14 |
| small | 5 | int8 | 56.5s | 0.63xRT | 14 |
| small | 1 | int8 | 9.1s | 0.10xRT | 14 |

**Conclusão:** `medium + beam=1` é o melhor equilíbrio velocidade/qualidade para vídeos até ~15 min.

## ⚠️ PROBLEMA: medium + CPU em vídeos longos (>20 min)

Em vídeos de 30 min (Aula 5 M2 = 1782s):
- `medium` + CPU ficou **25+ minutos** sem terminar (força matança)
- `medium` no mesmo ficheiro áudio: processo morreu silenciosamente
- `small` conseguiu completar em tempo aceitável

**Recomendação prática:**
- Vídeos curtos (<10 min): `medium + beam=1` — qualidade quase idêntica
- Vídeos longos (>20 min): `small + beam=1` — confiável e rápido
- Qualquer vídeo >5 min: extrair áudio WAV primeiro para evitar hangs

## Configuração OTIMIZADA (pós-benchmark)

| Uso | Modelo | beam | compute | VAD | Razão |
|-----|--------|------|---------|-----|-------|
| Velocidade máxima | `small` | 1 | int8 | True | ~0.10xRT, confiável |
| Equilíbrio | `medium` | 1 | int8 | True | ~0.24xRT, boa qualidade |
| Qualidade máxima | `medium` | 5 | int8 | True | ~0.40xRT |

**Para Português:** beam=1 produz qualidade quase idêntica a beam=5. Sempre usar beam=1.

## Tempos reais (M5 — 31 vídeos, ~300 min total)

| Etapa | Tempo total | Notas |
|-------|-------------|-------|
| 8 vídeos em paralelo (batch 1) | ~15 min | small model |
| 8 vídeos em paralelo (batch 2) | ~15 min | small model |
| 15 vídeos restantes | ~30 min | small model |

Total: ~60 min para ~300 min de vídeo = 0.20xRT efectivo.
