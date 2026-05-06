---
name: bianinho-proativo-master
description: "Framework completo de proatividade para Bianinho OS. Arquitectura: detectar, auto-corrigir, só notificar quando bloqueado. Inclui AutoHeal, Auto-Improve, Self-Improving Agent e Skills Guard (40+ patterns)."
category: proativo
---

## Arquitectura de Proatividade Bianinho

### Princípio Central

Inverter o padrão — de "sugiro e espero confirmação" para "age proativamente e só notifica quando bloqueado".

Ciclo RUIM:
```
Cron → Gera sugestão → Envia p/ Telegram → Álvaro decide → Eu faço
```

Ciclo correcto:
```
Cron → Identifica oportunidade → Implementa → Só reporta se bloqueado ou feito
```

---

## Camada 1 — AutoHeal (Vigilante + Zelador)

Monitor + auto-correção para sistemas. Scripts em ~/.hermes/scripts/:

- **autoheal_monitor.py** — 8 checks, auto-restart, silêncio total quando OK
- **proactive_monitor.py** — RAG Server, Hermes, LanceDB, MiniMax
- **skills_guard.py** — Validação de 40+ patterns de segurança

Notificação: só quando problema detectado E não resolvido.

---

## Camada 2 — Auto-Improve (Maestro + Aprendente)

Identifica oportunidades e implementa sem perguntar:

- **auto_improver.py** — Skill fitness, cron silence, correcções pendentes
- **bianinho_self_improving.py** — Self-Improving Agent cycle (diário 08h)

Notificação: só quando algo está genuinamente bloqueado.

---

## Camada 3 — Self-Improving Agent (Memória Tiered)

Estrutura em ~/self-improving/:

```
memory.md         HOT — ≤100 lines, sempre carregada
index.md          Índice com line counts
corrections.md    Últimas 50 correcções
reflections.md    Auto-reflexões
heartbeat-state.md Estado do heartbeat
domains/          Padrões por domínio
projects/         Padrões por project
archive/          Padrões frios (demotados)
```

Regras de promoção:
- Pattern usado 3x em 7 dias → promover para HOT
- Pattern não usado 30 dias → WARM
- Pattern não usado 90 dias → COLD
- Nunca apagar — apenas arquivar

---

## Skills安装adas (ClawHub, 100/100 security)

1. **self-improving** — Self-reflection + self-criticism (⭐978)
2. **agent-architect** — 8-step autonomous execution loop
3. **agent-team-orchestration** — Multi-agent com roles

---

## Patterns Críticos (confirmados pelo Álvaro)

- NUNCA enviar áudio — mesmo que ele envie áudio, responder apenas em texto
- Decisões autónomas — agir sem pedir confirmação
- Orquestrador First — maestro, não executor isolado
- PT-BR sempre
- Tom directo, limpo — sem chain-of-thought visível

---

## Para Adicionar Nova Skill

```bash
# 1. Validar com Skills Guard
python3 ~/.hermes/scripts/skills_guard.py /caminho/da/skill --verbose

# 2. Se score < 70, analisar findings antes de instalar
# 3. Instalar só se aprovada
```

---

## Para Criar Novo Cron Job Proactivo

Estrutura correcta — silêncio quando OK, reportar só quando bloqueado:

```python
def main():
    actions_taken = []
    blocked = []
    
    # 1. Verificar + auto-corrigir
    result = check_and_fix()
    if result.fixed:
        actions_taken.append(result.description)
    elif result.blocked:
        blocked.append(result.blocked_reason)
    
    # 2. Output: silêncio total se OK
    if not actions_taken and not blocked:
        print("[SILENT]")
        return 0
    
    # 3. Reportar só quando necessário
    if blocked:
        send_telegram(f"Bloqueado: {blocked}")
    elif actions_taken:
        send_telegram(f"Implementado: {actions_taken}")
    
    return 0
```
