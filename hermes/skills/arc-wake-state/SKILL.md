---
name: arc-wake-state
description: Persist agent state across crashes, context deaths, and restarts for Hermes agents. Use when you need to save current context, restore after a crash, maintain a memory file across sessions, or implement crash recovery. Essential for autonomous agents that must survive context window limits.
hermes-adapted: true
hermes-version: "1.0.0"
---

# Wake State — Crash Recovery & Persistence (Hermes)

Sobrevive à morte de contexto. Todo o agente autónomo eventualmente atinge o limite da janela de contexto e "morre". Esta skill garante que acordas sabendo exatamente o que estavas a fazer.

## Estado de Adaptação

✅ Adaptada para Hermes — Fevereiro 2026
- Path: `~/.hermes/wake-state/`
- Restante código: 100% funcional sem alterações

## Porquê Existe

O Hermes tem sessões persistentes, mas as janelas de contexto ainda têm limites. Quando enchem e reiniciam, precisas de um mecanismo de handover fiável. Wake State dá-te:

1. **Ficheiros de estado estruturados** — não só texto cru, mas estado key-value parseable
2. **Auto-snapshots** — guarda estado em cada iteração automaticamente
3. **Detecção de crash** — sabe se a última sessão terminou de forma limpa ou crashed
4. **Fila de tarefas** — lista de TODOs persistente que sobrevive a restarts
5. **Checkpoint/restore** — guarda checkpoints nomeados e restaura a eles

## Comandos

### Guardar estado atual
```bash
python3 ~/.hermes/skills/arc-wake-state/scripts/wakestate.py save \
  --status "A instalar skill arc-wake-state" \
  --task "Adaptar skill para Hermes, testar, documentar" \
  --note "Álvaro aprovou a instalação"
```

### Ler estado atual
```bash
python3 ~/.hermes/skills/arc-wake-state/scripts/wakestate.py read
```

### Adicionar tarefa à fila persistente
```bash
python3 ~/.hermes/skills/arc-wake-state/scripts/wakestate.py task-add \
  --task "Revisar skills da Tier 2" \
  --priority high
```

### Marcar tarefa como concluída
```bash
python3 ~/.hermes/skills/arc-wake-state/scripts/wakestate.py task-done --id 1
```

### Listar tarefas pendentes
```bash
python3 ~/.hermes/skills/arc-wake-state/scripts/wakestate.py tasks
```

### Criar checkpoint nomeado
```bash
python3 ~/.hermes/skills/arc-wake-state/scripts/wakestate.py checkpoint --name "pre-atualizacao"
```

### Restaurar de checkpoint
```bash
python3 ~/.hermes/skills/arc-wake-state/scripts/wakestate.py restore --name "pre-atualizacao"
```

### Gravar heartbeat (marcar sessão como viva)
```bash
python3 ~/.hermes/skills/arc-wake-state/scripts/wakestate.py heartbeat
```

### Verificar estado de crash
```bash
python3 ~/.hermes/skills/arc-wake-state/scripts/wakestate.py crash-check
```

### Guardar par key-value
```bash
python3 ~/.hermes/skills/arc-wake-state/scripts/wakestate.py set \
  --key "ultimo_projeto" --value "voltagent-skills"
```

### Ler par key-value
```bash
python3 ~/.hermes/skills/arc-wake-state/scripts/wakestate.py get --key "ultimo_projeto"
```

## Armazenamento de Dados

Estado guardado em `~/.hermes/wake-state/`:
- `state.json` — estado atual (status, notes, key-values)
- `tasks.json` — fila de tarefas persistente
- `checkpoints/` — snapshots de checkpoints nomeados
- `heartbeat.json` — timestamps para deteção de crash

## Fluxo de Recovery

Ao iniciar, o agente deve:
1. Executar `crash-check` para ver se a última sessão terminou de forma limpa
2. Executar `read` para obter o estado atual
3. Executar `tasks` para ver trabalho pendente
4. Retomar de onde ficou

## Dicas
- Chama `heartbeat` em cada iteração — é assim que a deteção de crash funciona
- Chama `save` no final de cada tarefa importante
- Usa checkpoints antes de operações arriscadas (migrações, updates)
- Mantém descrições de status curtas mas específicas
- A fila de tarefas sobrevive a restarts — usa-a em vez de notas mentais
