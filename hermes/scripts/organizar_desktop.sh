#!/bin/bash
# Organiza arquivos do Desktop sem apagar nada

DESKTOP="$HOME/Desktop"
MESA="$HOME/Documents/Mesa"

mkdir -p "$MESA/Capturas"
mkdir -p "$MESA/Documentos"
mkdir -p "$MESA/Screen Recordings"

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

# Pastas (não apps, não "Estudos Profissionais")
for f in "$DESKTOP"/*/; do
  [ -d "$f" ] && echo "$f" | grep -qE "Estudos Profissionais/$" && continue
  [ -d "$f" ] && ! echo "$f" | grep -qE "\.(app|Downie|localized)$" && mv "$f" "$MESA/" 2>/dev/null && ((movidos++))
done

echo "Desktop organizado. Ficheiros movidos: $movidos"
