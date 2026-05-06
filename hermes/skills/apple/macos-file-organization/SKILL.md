---
name: macos-file-organization
description: Organização de arquivos macOS — estruturar Desktop, Documents, Downloads, criar tarefas cron de limpeza automática.
trigger: Quando o utilizador pede organizar arquivos, organizar desktop, organizar documentos, limpar mesa, mover arquivos, criar tarefa de organização, cron de limpeza
category: apple
tags: [macos, files, organization, desktop, folders, cron, automation]
owner: bianinho
---

# macOS File Organization

## Princípio Fundamental

**NUNCA apagar arquivos.** Sempre mover para pastas organizadas. O utilizador (Álvaro) enfatiza: "garantindo que não irá apagar nada."

## Workflow Completo (3 Fases)

### Fase 1: Diagnosticar Estado Atual

```bash
# Ver Desktop
ls -la ~/Desktop/
du -sh ~/Desktop/*

# Ver Documents
ls -la ~/Documents/

# Ver Downloads
ls -la ~/Downloads/

# Contar arquivos soltos na home
find ~ -maxdepth 1 -type f ! -name ".*" | wc -l
find ~ -maxdepth 1 -type d ! -name ".*" ! -name ".." | grep -v Library | grep -v ".Trash"
```

### Fase 2: Apresentar Plano ao Utilizador

**Antes de mover qualquer coisa**, apresentar:
1. O que existe agora (inventário)
2. Para onde cada coisa vai (mapa de destino)
3. O que NÃO vai ser mexido (symlinks, configs, projetos ativos)
4. Perguntar se deve incluir projetos de desenvolvimento (pastas de coding ativo na home)

**Formato de relatório:**
```
ANTES: N itens soltos na home
DEPOIS: Tudo categorizado em ~/Documents/

Opção: Mover também projetos de desenvolvimento para ~/Documents/Projects/?
```

### Fase 3: Executar com Confirmação

```bash
# Criar pastas de destino
mkdir -p ~/Documents/Mesa
mkdir -p ~/Documents/Mesa/Capturas
mkdir -p ~/Documents/Mesa/Documentos
mkdir -p ~/Documents/Mesa/Screen Recordings
mkdir -p ~/Documents/Projects
mkdir -p ~/Documents/Sistemas

# Mover arquivos soltos da home
for f in ~/*.md; do [ -f "$f" ] && mv "$f" ~/Documents/Método\ TEN/; done

# Mover projetos (se confirmado)
mv ~/bolt.diy ~/Documents/Projects/
mv ~/cTrader ~/Documents/Projects/
# ... etc
```

## Estrutura de Pastas Recomendada

```
~/Documents/
├── Mesa/                      # Desktop原来的内容
│   ├── Capturas/             # Imagens (png, jpg, gif, webp)
│   ├── Documentos/           # Arquivos (pdf, docx, xlsx, txt, md)
│   ├── Screen Recordings/    # Vídeos (mp4, mov, avi)
│   └── [outras pastas do Desktop original]
├── Projects/                  # Projetos de desenvolvimento
├── Sistemas/                 # Installers, ferramentas de sistema
├── Método TEN/               # Documentos do método
└── [outras pastas existentes]

~/Desktop/                     # Deve ficar VAZIO (só .localized, .DS_Store)
```

## Subcategorias Típicas para Mesa

| Tipo | Extensões | Pasta destino |
|---|---|---|
| Capturas de tela | png, jpg, gif | ~/Documents/Mesa/Capturas |
| Documentos | pdf, docx, xlsx, txt, md | ~/Documents/Mesa/Documentos |
| Vídeos | mp4, mov, avi, mkv | ~/Documents/Mesa/Screen Recordings |
| Pastas genéricas | - | ~/Documents/Mesa/ (raiz) |

## NÃO MEXER

| Item | Motivo |
|---|---|
| Symlinks (.aionui, KnowledgeBase, Google Drive) | Links de sistema |
| Pastas .ssh/, .config/, .hermes/ | Configurações |
| Pasta Library/ | Sistema macOS |
| node_modules/, venv/, .venv/ | Dependências de projetos |
| Aplicativos (.app) | Apps macOS |
| miniconda3/, python envs | Ambientes Python |
| BibliotecaCalibre/, wallet/, Monero/ | Dados específicos de apps |

## Automação com Cron Job

### Script de Limpeza Automática do Desktop

```bash
# Criar script em ~/.hermes/scripts/
cat << 'SCRIPT' > ~/.hermes/scripts/organizar_desktop.sh
#!/bin/bash
DESKTOP="$HOME/Desktop"
MESA="$HOME/Documents/Mesa"

mkdir -p "$MESA/Capturas" "$MESA/Documentos" "$MESA/Screen Recordings"

movidos=0

# Imagens
for ext in png jpg jpeg gif webp bmp; do
  for f in "$DESKTOP"/*."$ext"; do
    [ -f "$f" ] && mv "$f" "$MESA/Capturas/" 2>/dev/null && ((movidos++))
  done
done

# Documentos
for ext in pdf doc docx xlsx txt md epub zip; do
  for f in "$DESKTOP"/*."$ext"; do
    [ -f "$f" ] && mv "$f" "$MESA/Documentos/" 2>/dev/null && ((movidos++))
  done
done

# Vídeos
for ext in mp4 mov avi mkv; do
  for f in "$DESKTOP"/*."$ext"; do
    [ -f "$f" ] && mv "$f" "$MESA/Screen Recordings/" 2>/dev/null && ((movidos++))
  done
done

# Pastas (não apps)
for f in "$DESKTOP"/*/; do
  [ -d "$f" ] && ! echo "$f" | grep -qE "\.(app|Downie|localized)" && \
    mv "$f" "$MESA/" 2>/dev/null && ((movidos++))
done

echo "Desktop organizado. Ficheiros movidos: $movidos"
SCRIPT

chmod +x ~/.hermes/scripts/organizar_desktop.sh
```

### Criar Cron Job

```bash
hermes cron create \
  --name "Organizar Desktop automaticamente" \
  --deliver local \
  --workdir ~/Documents/Mesa \
  --script organizar_desktop.sh \
  -- "0 * * * *" \
  "Execute o script organizar_desktop.sh para organizar o Desktop sem apagar nada."
```

**Nota**: `schedule` vai por último, depois de `--`. O `prompt` (texto depois de `--`) é obrigatório.

## Pitfalls

1. **Não perguntar antes de mover projetos** - Álvaro usa muitos projetos ativos na home (bolt.diy, cTrader, dyad-apps). Perguntar sempre se deve mover para ~/Documents/Projects/.
2. **Apagar em vez de mover** - regra: ZERO deletes. Sempre mover.
3. **Mover symlinks** - não mexer em .aionui, KnowledgeBase, Google Drive (são symlinks).
4. **Scripts cron com path errado** - o script deve estar em `~/.hermes/scripts/` e no `--script` usar apenas o nome do ficheiro, não o path completo.
5. **Cron job sem prompt** - `--prompt` ou `--skill` é obrigatório no `hermes cron create`. Não funciona sem.
