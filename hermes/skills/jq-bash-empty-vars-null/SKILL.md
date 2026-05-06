---
name: jq-bash-empty-vars-null
description: How to pass potentially empty bash variables to jq as proper JSON null (not string "null" or empty string)
tags: [bash, jq, json, shell, scripting]
category: devops
version: "1.0"
author: Bianinho
created: 2026-04-21
---

# jq + Bash: Passando Variáveis Vazias como JSON null

## O Problema

Ao usar `jq -n --arg var "$bash_var"`, se `$bash_var` estiver **vazia**, jq recebe `""` (string vazia), **não** `null`.

```bash
# ❌ ERRADO — variável vazia vira string "", não null
NAME=""
jq -n --arg name "${NAME:-null}" '{ name: $name }'
# Output: {"name":""}

# ❌ TAMBÉM ERRADO — se usar :~null como fallback, jq recebe a string literal "null"
NAME=""
jq -n --arg name "${NAME:-null}" '{ name: (if $name == "null" then null else $name end) }'
# Output: {"name":""}  — continua errado porque "null" em string é diferente de null em jq
```

## A Solução Correta

Usar uma **variável bash intermédia** e uma **expressão jq condicional**:

```bash
# ✅ CORRETO
name_val="${NAME:-}"          # vazio = string vazia "", não a palavra "null"
desc_val="${DESCRIPTION:-}"

jq -n \
    --arg name "$name_val" \
    --arg desc "$desc_val" \
    '{
        name: (if $name == "" then null else $name end),
        description: (if $desc == "" then null else $desc end)
    }'
```

**Princípio:** `$bash_var` vazia passa `""` para `--arg`, e a **expressão jq condicional** `(if $cond then null else $value end)` converte `""` → `null`.

## Porquê Funciona

| Bash var | Passado a jq como | jq expressão | Resultado |
|----------|-------------------|--------------|-----------|
| `NAME="algo"` | string `"algo"` | `if $name == ""` | `false` → usa `$name` |
| `NAME=""` | string `""` | `if $name == ""` | `true` → `null` |
| `NAME` (unset) | `""` | `if $name == ""` | `true` → `null` |

## Armadilha Comum

`${VAR:-null}` parece útil mas **não funciona** — passa a **palavra literal** `"null"` (uma string de 4 caracteres), não o valor JSON `null`:

```bash
# ❌ Armadilha — "null" é string, não JSON null
jq -n --arg x "${UNSET_VAR:-null}" '{v: $x}'
# {"v":"null"}  ← é uma string, não null!

# ✅ Correto — sem fallback, deixa vazio, jq converte
jq -n --arg x "${UNSET_VAR:-}" '{v: (if $x == "" then null else $x end)}'
# {"v":null}
```

## Aplicações

- Manifestos JSON com campos opcionais (name, description, etc.)
- Config backup scripts com campos que podem estar vazios
- API request bodies com parâmetros opcionais
- State files onde valores nulos devem ser representados como JSON null

## Ficheiros de Referência

- `~/.hermes/scripts/backup_restore/backup.sh` — exemplo real com manifest.json
