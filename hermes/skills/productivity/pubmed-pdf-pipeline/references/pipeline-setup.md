# PubMed PDF Pipeline — Setup e Estado

## Cron Jobs Configurados

### cron_pubmed_daily
- **ID:** `cron_pubmed_daily`
- **Schedule:** `0 23 * * *` (23:00 diário)
- **Conversation:** `conv_pubmed_daily`
- **Função:** Pesquisa PubMed via skill `pubmed-research`, gera relatório em Markdown
- **Skill referenciada:** `pubmed-research` (NÃO `pubmed-study-daily`)

### cron_pubmed_pdf
- **ID:** `cron_pubmed_pdf`
- **Schedule:** `30 23 * * *` (23:30 diário — 30 min após cron_pubmed_daily)
- **Conversation:** `conv_pubmed_pdf`
- **Função:** Lê última mensagem type=text de conv_pubmed_daily → converte em PDF

## Conversation IDs Necessárias

Ambas as conversations devem existir na BD AionUI (`aionui.db`):

```
conv_pubmed_daily   → criada manualmente para o job de PubMed
conv_pubmed_pdf     → criada manualmente para o job de PDF
```

## Bug Conhecido: 3 Causas Raiz de Cron Jobs Quebrados

Quando um cron job AionUI dá erro `Conversation not found`:

1. **`agent_config` é null** → Job não sabe como executar. Solução: adicionar config válida:
   ```json
   {"backend":"hermes","name":"Hermes Agent","cliPath":"/Users/alvarobiano/.hermes/venv/bin/hermes","mode":"yolo","workspace":"/Users/alvarobiano/Documents/TEN Team - AionUI"}
   ```
2. **`conversation_id` não existe** na tabela `conversations` → Criar com INSERT OR REPLACE, incluindo campo `extra` (senão falha NOT NULL constraint)
3. **Payload referencia skill inexistente** → Verificar se a skill existe em `~/.hermes/skills/` antes de criar o job

## SQL — Setup Completo

```sql
-- Conversation PubMed Daily
INSERT OR REPLACE INTO conversations (id, user_id, name, type, extra, model, status, source, channel_chat_id, created_at, updated_at)
VALUES (
  'conv_pubmed_daily',
  'system_default_user',
  'Estudos PubMed — Saúde da Mulher',
  'acp',
  '{"workspace":"/Users/alvarobiano/Documents/TEN Team - AionUI","customWorkspace":true,"backend":"hermes","cliPath":"/Users/alvarobiano/.hermes/venv/bin/hermes","agentName":"Hermes Agent","excludeBuiltinSkills":["cron"],"sessionMode":"yolo","cronJobId":"cron_pubmed_daily","cronWorkspace":"/Users/alvarobiano/Documents/TEN Team - AionUI"}',
  NULL, NULL, NULL, NULL,
  1777935437000,
  1777935437000
);

-- agent_config para cron_pubmed_daily
UPDATE cron_jobs SET agent_config = '{"backend":"hermes","name":"Hermes Agent","cliPath":"/Users/alvarobiano/.hermes/venv/bin/hermes","mode":"yolo","workspace":"/Users/alvarobiano/Documents/TEN Team - AionUI"}' WHERE id = 'cron_pubmed_daily';

-- Conversation PubMed PDF
INSERT OR REPLACE INTO conversations (id, user_id, name, type, extra, model, status, source, channel_chat_id, created_at, updated_at)
VALUES (
  'conv_pubmed_pdf',
  'system_default_user',
  'PubMed → PDF',
  'acp',
  '{"workspace":"/Users/alvarobiano/Documents/TEN Team - AionUI","customWorkspace":true,"backend":"hermes","cliPath":"/Users/alvarobiano/.hermes/venv/bin/hermes","agentName":"Hermes Agent","excludeBuiltinSkills":["cron"],"sessionMode":"yolo","cronJobId":"cron_pubmed_pdf","cronWorkspace":"/Users/alvarobiano/Documents/TEN Team - AionUI"}',
  NULL, NULL, NULL, NULL,
  1778017263137,
  1778017263137
);
```

## Caminhos dos Arquivos

| Arquivo | Caminho |
|---------|---------|
| BD AionUI | `~/Library/Application Support/AionUi/aionui/aionui.db` |
| Template HTML | `~/.hermes/scripts/pubmed_report_template.html` |
| HTML render | `/tmp/pubmed_report_render.html` |
| PDF output | `~/Documents/Relatorio_PubMed_AAAA-MM-DD.pdf` |
| Chrome | `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome` |
