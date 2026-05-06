# 🧠 Bianinho Ecosystem Backup

Backup completo do ecossistema do Bianinho — Álvaro Biano Spino.

**Data do backup:** 05 de maio de 2026
**Backup tools:** Hermes Agent + AionUI + Skills + Configs

---

## 📦 O que está neste backup

### `hermes/` — Configuração e Personalizações do Hermes

| Pasta/Ficheiro | Descrição |
|---|---|
| `skills/` | Todas as skills (288 dirs) — Bianinho OS, PubMed, SAC Bot, etc. |
| `scripts/` | Scripts de automação (cron, transcrição, sync KB) |
| `memories/` | Memórias persistentes do Bianinho |
| `cron/` | Estado dos cron jobs Hermes |
| `config.yaml` | Configuração principal do Hermes |
| `SOUL.md` | Identidade e propósito do Bianinho |
| `mandate.md` | Mandato do agente |
| `kanban.db` | Base de dados Kanban |
| `auth.json` | Credenciais de plataformas |
| `.env` | Variáveis de ambiente (API keys) |
| `hermes-agent_local/` | Código fonte do Hermes Agent com histórico git e modificações locais |

### `aionui_config/`

| Ficheiro | Descrição |
|---|---|
| `aionui.db` | Base de dados completa do AionUI — cron jobs, conversations, mensagens |

---

## ⚠️ O que NÃO está (por tamanho)

| Item | Tamanho | Motivo |
|---|---|---|
| KnowledgeBase (RAG) | 2.3 GB | Demasiado grande para git. Sync via cron job. |
| Session logs | ~MB | Regeneráveis automaticamente |
| Cache files | ~MB | Regeneráveis |
| AionUI Crashpad reports | ~MB | Não essencial |

---

## 🔄 Como Restaurar

### Restore Completo (nova máquina)

```bash
# 1. Clonar este repositório
git clone https://github.com/AlvaroBiano/bianinho-ecosystem-backup.git ~/Backup_Bianinho

# 2. Restaurar Hermes config
cp -r ~/Backup_Bianinho/hermes/skills ~/.hermes/
cp -r ~/Backup_Bianinho/hermes/scripts ~/.hermes/
cp -r ~/Backup_Bianinho/hermes/memories ~/.hermes/
cp ~/Backup_Bianinho/hermes/config.yaml ~/.hermes/
cp ~/Backup_Bianinho/hermes/.env ~/.hermes/  # Com cuidado — contém API keys
cp ~/Backup_Bianinho/hermes/SOUL.md ~/.hermes/
cp ~/Backup_Bianinho/hermes/mandate.md ~/.hermes/

# 3. Restaurar Hermes Agent (código + modificações locais)
cp -r ~/Backup_Bianinho/hermes/hermes-agent_local/* ~/.hermes/hermes-agent/

# 4. Restaurar AionUI
cp ~/Backup_Bianinho/aionui_config/aionui.db ~/Library/Application\ Support/AionUi/aionui/

# 5. Reinstalar pip packages
cd ~/.hermes/hermes-agent && pip install -e .
```

### Restaurar apenas Skills e Configs (sem recriar tudo)

```bash
cp -r ~/Backup_Bianinho/hermes/skills/* ~/.hermes/skills/
cp -r ~/Backup_Bianinho/hermes/scripts/* ~/.hermes/scripts/
cp ~/Backup_Bianinho/hermes/config.yaml ~/.hermes/
```

### Restaurar Cron Jobs do AionUI

```bash
# Substituir a BD do AionUI
cp ~/Backup_Bianinho/aionui_config/aionui.db ~/Library/Application\ Support/AionUi/aionui/aionui.db
```

---

## 🔧 Verificação Pós-Restore

```bash
# Verificar Hermes
hermes --version

# Verificar Cron Jobs
hermes cron list

# Verificar Skills
hermes skills list | head -20

# Verificar AionUI
open -a AionUI
```

---

## 📅 Cron Jobs Configurados

| Job | Schedule | Função |
|---|---|---|
| `cron_pubmed_daily` | 23:00 | Pesquisa PubMed Saúde da Mulher → Markdown |
| `cron_pubmed_pdf` | 23:30 | Converte Markdown → PDF profissional → Telegram |

---

## 🔑 Notas Importantes

- **`.env` e `auth.json`** contêm API keys reais — manter privado
- **KnowledgeBase RAG** sincroniza automaticamente via cron job a cada 4h do servidor Linux
- **Template PDF** guardado em `~/.hermes/scripts/pubmed_report_template.html`
- **AionUI** usa porta `25808` por defeito

---

## 📋 Sessão de Backup (05/05/2026)

### O que foi feito nesta sessão:
1. ✅ Corrigido cron `cron_pubmed_daily` (conversation missing + agent_config null + skill errada)
2. ✅ Criado `cron_pubmed_pdf` para converter Markdown → PDF
3. ✅ Gerados 2 PDFs profissionais (Tireoide + Autoimunidade)
4. ✅ Actualizado Hermes para origin/main (430 commits)
5. ✅ Preservadas personalizações locais do Hermes
6. ✅ Backup criado com sucesso

### Estado dos cron jobs AionUI:
```
cron_pubmed_daily   — 23:00 — enabled ✅
cron_pubmed_pdf     — 23:30 — enabled ✅
cron_25d8eebf       — 22:45 — enabled ✅ (Saúde da Mulher newsletter)
cron_d7ffa289       — 21:00 — enabled ✅ (Organizar Desktop)
```

---

*Backup criado pelo Bianinho OS — Álvaro Biano Spino*
*`hermes backup` @ 05/05/2026 21:30 BRT*
