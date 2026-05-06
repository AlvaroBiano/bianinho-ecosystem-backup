---
name: sqlite-tools
description: SQLite development and debugging patterns — gaps detection, phone/DDD extraction, orphaned row deletion
tags: [sqlite, database, debugging, brasil]
---

# SQLite Tools — Development & Debugging Patterns

Coleção de padrões SQLite para debugging e desenvolvimento no ecossistema Hermes/SAC Bot.

---

## ◆ Audit — Detectar Lacunas e Duplicados em IDs Sequenciais

**Skill original:** `sqlite-audit-gaps`

### Contexto
Ao auditar a tabela `approved_qa` no `sac_leads.db`, descobriu-se que había 90 registos mas os IDs iam de 1 a 93 (faltando 17, 51, 69). A memória antiga estava desactualizada com valores errados.

### Query básica de estado
```bash
sqlite3 /path/to/database.db "SELECT COUNT(*) FROM tabela; SELECT MIN(id), MAX(id) FROM tabela;"
```

### Detectar IDs em falta (gaps)
```bash
sqlite3 /path/to/database.db "SELECT id FROM tabela ORDER BY id;" | awk 'NR==1{prev=$1;next} {if($1!=prev+1) print "FALTA: " prev+1 " até " $1-1; prev=$1} END{print "ULTIMO: " prev}'
```

### Verificar duplicados
```bash
sqlite3 /path/to/database.db "SELECT id FROM tabela ORDER BY id;" | tr '|' '\n' | sort -n | uniq -c | awk '{if($1>1) print "DUPLICADO: ID "$2}'
```

### Schema da tabela
```bash
sqlite3 /path/to/database.db "PRAGMA table_info(nome_tabela);"
```

### Caso de uso
- Auditoria de qualquer tabela com IDs sequenciais (Q&As, leads, mensagens)
- Verificar integridade da base antes de inserir novos registos
- Confirmar que memória/sistema está sincronizado com estado real da DB

---

## ◆ Phone — Extrair DDD de Telefones Brasileiros Formatados

**Skill original:** `sqlite-ddd-from-formatted-phone`

### Problema
Telefones brasileiros armazenados no SQLite com formatação visual:
```
(48) 92000-8284
(11) 99999-1234
(101) 90001-1000
```
`substr(telefone, 2, 2)` retorna `48)` (com parêntese) em vez de `48`.

### Solução Correta
Antes de extrair, remover todos os caracteres não-numéricos:

```sql
SELECT DISTINCT(
    substr(
        replace(replace(replace(telefone,'(',''),')',''),'-',''),
    1,2)
) as ddd 
FROM leads 
ORDER BY ddd;
```

Passo a passo para `(48) 92000-8284`:
1. `replace(telefone,'(','')` → `48) 92000-8284`
2. `replace(...,')','')` → `48 92000-8284`
3. `replace(...,'-','')` → `48920008284`
4. `substr(...,1,2)` → `48` ✓

### Regra
Sempre usar:
```sql
substr(replace(replace(replace(telefone,'(',''),')',''),'-',''),1,2)
```
em vez de:
```sql
substr(telefone, 2, 2)
```

**Nota:** Brazilian phone format: `(DDD) XXXXX-XXXX`. Some leads have extended format where DDD can be 3 digits (e.g., `101`). Always strip formatting chars before extracting DDD.

---

## ◆ Delete — Linhas Órfãs e Foreign Keys Desativadas

**Skill original:** `sqlite-delete-orphaned-rows`

### Problema
Ao apagar um lead, as tabelas relacionadas (`conversas`, `avaliacoes`) ficavam com registos órfãos mesmo havendo `FOREIGN KEY` definida.

### Causa Raiz
**`PRAGMA foreign_keys = 0`** — SQLite tem foreign keys desativadas por padrão. Sem isto, o `ON DELETE CASCADE` não funciona e os registos relacionados ficam órfãos.

### Como Diagnosticar
```sql
PRAGMA foreign_keys;
-- Se retorna 0 → FK desativadas
```

### Solução: DELETE manual em cascata
```python
conn.execute("DELETE FROM conversas WHERE lead_id=?", (lead_id,))
conn.execute("DELETE FROM avaliacoes WHERE lead_id=?", (lead_id,))  # ← nunca esquecer
conn.execute("DELETE FROM leads WHERE id=?", (lead_id,))
conn.commit()
```

**Ordem correta:** tabelas filhas primeiro → tabela pai por último.

### Sintomas no Sistema Real
- SAC Bot: `admin_delete_lead` apagava `conversas` e `leads` mas deixava `avaliacoes` órfã
- "Erro de conexão" no front-end era confundido com bug de rede — era realmente o DELETE a falhar silenciosamente
- Corrigido 25/04/2026 em `~/.hermes/sac_agent/sac_agent.py`

### Regra
Sempre que o SQLite não tiver FK activas e precisar de apagar um registo pai, apagar manualmente TODAS as tabelas filhas pela ordem correcta. Não confiar em `ON DELETE CASCADE`.
