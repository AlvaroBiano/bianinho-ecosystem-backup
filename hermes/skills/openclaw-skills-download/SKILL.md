---
name: openclaw-skills-download
description: Download and install skills from the OpenClaw/VoltAgent ecosystem — naviga o repo de índice + repo real de skills
category: productivity
---

# OpenClaw Skills — Download & Install

## Arquitetura dos Repos

O ecossistema OpenClaw tem **2 repos diferentes**:

| Repo | URL | Conteúdo | Size |
|------|-----|----------|------|
| Índice | `VoltAgent/awesome-openclaw-skills` | README + markdown files com links para skills | 3MB |
| **Real** | `openclaw/skills` | **61.234 SKILL.md** (ficheiros reais) | **4,6GB** |

O repo `awesome-openclaw-skills` é apenas uma curadoria/listagem — não contém os ficheiros SKILL.md.

---

## Download Completo (61k+ skills)

```bash
cd ~/repos
git clone --depth 1 --single-branch https://github.com/openclaw/skills.git
```

Resultado:
- 61.234 ficheiros SKILL.md
- 4,6 GB
- 19.076 directorias (uma por autor)
- Path: `~/repos/skills/`

---

## Encontrar Skills Específicas

As skills estão em `skills/{author}/{skill-name}/SKILL.md`:

```bash
# Procurar por nome/autor
find ~/repos/skills -path "*/agent-autopilot/SKILL.md"
find ~/repos/skills -path "*/adaptive-reasoning/SKILL.md"
find ~/repos/skills -path "*/globalcaos*/SKILL.md"

# Listar categorias do índice (links → authors)
ls ~/repos/awesome-openclaw-skills/categories/

# Extrair URLs de uma categoria
grep -roh 'https://clawskills\.sh/skills/[^)]*' ~/repos/awesome-openclaw-skills/categories/productivity-and-tasks.md

# Total de skills únicas indexadas
grep -roh 'https://clawskills\.sh/skills/[^)]*' ~/repos/awesome-openclaw-skills/categories/ | sort -u | wc -l
# → 5.127 URLs únicas
```

---

## Instalar uma Skill no Hermes

1. Copiar o diretório da skill para `~/.hermes/skills/{skill-name}/`
2. Ou criar symlink: `ln -s ~/repos/skills/{author}/{skill-name} ~/.hermes/skills/{skill-name}`

---

## Descobertas Chave

- `clawskills.sh/skills/{author}-{skill}` é a página de apresentação
- O SKILL.md real está sempre em `github.com/openclaw/skills/tree/main/skills/{author}/{skill}/SKILL.md`
- Shallow clone (`--depth 1 --single-branch`) é necessário — repo tem 379k objetos
- O repo de índice `awesome-openclaw-skills` tem 30 categorias markdown com links; cada link corresponde a uma entry no repo real
