---
name: backup
description: Backup e restore do ecossistema Hermes — SOUL workspace files e património digital completo
tags: [backup, restore, devops, github]
---

# Backup — SOUL Workspace & Empresa Digital

Coleção completa de padrões de backup e restore para o ecossistema Hermes. Dois níveis distintos:
1. **Workspace SOUL** — ficheiros críticos do workspace (SOUL.md, USER.md, etc.)
2. **Empresa Digital** — património completo (sac_agent, knowledge base, cerebro, scripts, skills)

---

## ◆ SOUL Workspace Backup & Restore

**Skill original:** `backup-restore`

### O Que Faz
Backup, restore, validate, e GitHub-sync do workspace SOUL (SOUL.md, USER.md, AGENTS.md, IDENTITY.md, TOOLS.md, HEARTBEAT.md, BOOTSTRAP.md) com versioning, rollback, e recuperação off-machine.

### O Que É Backupado
Ficheiros core do workspace:
- `SOUL.md` — personalidade e missão do agent
- `USER.md` — perfil e preferências do utilizador
- `AGENTS.md` — instruções e workflows dos agents
- `IDENTITY.md` — configuração de identidade
- `TOOLS.md` — configuração de ferramentas locais
- `HEARTBEAT.md` — configuração de tarefas periódicas
- `BOOTSTRAP.md` — instruções de inicialização

### Backup
```bash
# Com timestamp
bash ~/.hermes/scripts/backup_restore/backup.sh

# Named backup
bash ~/.hermes/scripts/backup_restore/backup.sh --name "pre-migration"

# Com descrição
bash ~/.hermes/scripts/backup_restore/backup.sh --desc "Before major refactor"

# Daily GitHub backup
bash ~/.hermes/scripts/backup_restore/backup.sh --push --remote origin
```

### Listar Backups
```bash
bash ~/.hermes/scripts/backup_restore/list-backups.sh --verbose
```

### Restore
```bash
# Latest backup
bash ~/.hermes/scripts/backup_restore/restore.sh

# Specific backup
bash ~/.hermes/scripts/backup_restore/restore.sh --timestamp 2026-03-05T00-51-30

# Named backup
bash ~/.hermes/scripts/backup_restore/restore.sh --name "pre-migration"

# Dry run
bash ~/.hermes/scripts/backup_restore/restore.sh --dry-run
```

### Validação
```bash
bash ~/.hermes/scripts/backup_restore/validate.sh
```

### Estrutura
```
~/.hermes/backups/
├── 2026-03-05T00-51-30/
│   ├── manifest.json
│   ├── SOUL.md, USER.md, AGENTS.md, ...
├── named/
│   └── pre-migration/
```

### Cron (Recomendado)
```cron
# Daily backup at 2 AM
0 2 * * * bash ~/.hermes/scripts/backup_restore/backup.sh --name "daily-$(date +\%Y-\%m-\%d)"

# Weekly backup on Sunday
0 3 * * 0 bash ~/.hermes/scripts/backup_restore/backup.sh --name "weekly-$(date +\%Y-W\%V)"
```

### Cenários de Recuperação

**1. SOUL.md apagado acidentalmente:**
```bash
bash ~/.hermes/scripts/backup_restore/restore.sh --file SOUL.md
```

**2. Mudança de configuração má:**
```bash
bash ~/.hermes/scripts/backup_restore/restore.sh --dry-run
bash ~/.hermes/scripts/backup_restore/restore.sh --timestamp <previous-backup>
```

**3. Perda completa do workspace:**
```bash
mkdir -p ~/.hermes/workspace-YOUR-AGENT
cd ~/.hermes/workspace-YOUR-AGENT
git clone <backup-repo-url> backup-restore
cd backup-restore
bash ~/.hermes/scripts/backup_restore/restore.sh
```

---

## ◆ Empresa Digital — Backup Completo para GitHub

**Skill original:** `backup-empresa-github`

### O Que Faz
Cria um backup completo de todo o património digital e faz push para um repo privado no GitHub.

### Componentes Incluídos
- `sac_agent/` — SAC Bot completo (código + templates)
- `knowledge_base/` — Pipeline RAG, vector brain (LanceDB)
- `cerebro/` — Memória unificada Bianinho
- `scripts/` — Proactive monitor, guardian, health check
- `skills/` — skills do Bianinho OS
- `config/` — configs não-sensíveis

### Excluídos (segurança)
- Credenciais, API keys, tokens (.env, auth.json, google_token.json)
- Dados pessoais de leads (sac_leads.db)
- Bases LanceDB grandes (.lance via git lfs)
- Sessões e logs privados
- Framework hermes-agent (external)

### Fluxo Completo

```bash
BACKUP=~/backup-empresa-$(date +%Y%m%d)
mkdir -p "$BACKUP"

# Sync componentes
rsync -av --exclude='backups/' --exclude='__pycache__/' \
  ~/.hermes/sac_agent/ "$BACKUP/sac_agent/"

rsync -av --exclude='__pycache__/' --exclude='.hub/' \
  ~/.hermes/scripts/ "$BACKUP/scripts/"

rsync -av --exclude='__pycache__/' --exclude='.hub/' \
  ~/.hermes/skills/ "$BACKUP/skills/"

rsync -av --exclude='__pycache__/' --exclude='.session_bridge/' \
  --exclude='sessions/' --exclude='reflections/' \
  ~/KnowledgeBase/ "$BACKUP/knowledge_base/"

rsync -av ~/bianinho-cerebro/ "$BACKUP/cerebro/"

# Criar repo GitHub
TOKEN=$(git credential fill << 'CRED' | grep '^password=' | cut -d= -f2-
protocol=https
host=github.com
CRED
)
curl -s -X POST "https://api.github.com/user/repos" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"name":"backup-empresa","private":true}'

cd "$BACKUP"
git init && git add . && git commit -m "Backup $(date +%Y-%m-%d)"
git remote add origin "https://github.com/AlvaroBiano/backup-empresa.git"
git push -u origin main
```

### Restore
```bash
cp -r backup/sac_agent/* ~/.hermes/sac_agent/
cp -r backup/scripts/* ~/.hermes/scripts/
cp -r backup/knowledge_base/* ~/KnowledgeBase/
cp -r backup/cerebro/* ~/bianinho-cerebro/
cp -r backup/skills/* ~/.hermes/skills/
systemctl --user restart sac-agent
```

---

## Boas Práticas

1. **Backup antes de mudanças grandes** — sempre criar named backup antes de refactoring
2. **Validar regularmente** — correr `validate.sh` semanalmente
3. **Manter 30 dias de backups** — limpar backups antigos mensalmente
4. **Testar processo de restore** — praticar recuperação trimestralmente
5. **GitHub backup diário** — usar cron para push automático

## Segurança
- Backups contêm configuração sensível (API keys em TOOLS.md, info em USER.md)
- Não fazer commit de backups para repos públicos
- Proteger directorio de backup com as mesmas permissões do workspace
