# Repositórios do Ecossistema Bianinho

## Repos Principais

| Repo | URL | Conteúdo | Estado |
|---|---|---|---|
| `bianinho-backup-1777760438` | github.com/AlvaroBiano/bianinho-backup-1777760438 | Backup completo (skills, config, autonomous, SYNC.sh) | **ACTIVO** |
| `hermes-agent` (fork) | github.com/AlvaroBiano/hermes-agent | Fork do Hermes Agent com personalizações | Customizações aplicadas |
| `bianinho-backup` | github.com/AlvaroBiano/bianinho-backup | Alias/backup adicional | Verificar conteúdo |
| `icon-assets` | github.com/AlvaroBiano/icon-assets | Ícones SVG (36K+ localmente) | OK |

## Repos Que NÃO Existen (nunca criar expectativa de usar)

- `bianinho-consciousness` — **não existe**, usar `bianinho-backup-1777760438`
- Qualquer repo com nome `consciousness` que não seja o backup

## URLs RAW

```
# SYNC.sh
https://raw.githubusercontent.com/AlvaroBiano/bianinho-backup-1777760438/main/SYNC.sh

# Skills (via git clone do backup)
git clone --depth=1 https://github.com/AlvaroBiano/bianinho-backup-1777760438.git ~/backup_temp
```

##estado dos repos (02/Mai/2026)

- `bianinho-backup-1777760438`: 1 commit para SYNC.sh, backup com 66 skills, 13 categorias config
- `hermes-agent` fork: vazio (sem commits), mas as customizações estão em `customizations.patch` no backup
- Customizations.patch: 4 commits de personalização ao Hermes Agent, 60KB

## Backup do RAG (~2GB)

O RAG **não está no GitHub** (muito grande). Está num tarball no Google Drive:

```bash
# Criar
tar -czvf rag_backup.tar.gz ~/KnowledgeBase/
rclone copy rag_backup.tar.gz gdrive:bianinho-backup/

# Restaurar
rclone copy gdrive:bianinho-backup/rag_backup.tar.gz ./
tar -xzvf rag_backup.tar.gz -C ~/
```
