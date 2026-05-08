#!/bin/bash
# transcribe_m8.sh - Chunk + parallel transcribe for M8

PYTHON="/Users/alvarobiano/.hermes/venv/bin/python"
TRANSCRIBE_SCRIPT='/tmp/transcribe_chunk.py'
OUTPUT_BASE='/Users/alvarobiano/Movies/CURSO APC/M8. Bônus - MENTORIAS'
TMP_BASE='/tmp/m8_chunks'

mkdir -p "$TMP_BASE"

# Cria script de transcrição
cat > "$TRANSCRIBE_SCRIPT" << 'PYEOF'
import time, sys
from faster_whisper import WhisperModel
chunk_path, output_path = sys.argv[1], sys.argv[2]
model = WhisperModel('small', device='cpu', compute_type='int8')
segments, info = model.transcribe(chunk_path, language='pt', beam_size=1, vad_filter=False)
text = '\n'.join([f'[{s.start:.1f}s - {s.end:.1f}s] {s.text}' for s in segments])
with open(output_path, 'w') as f: f.write(text)
print(f'DONE:{info.duration:.0f}s:{len(list([s for s in segments]))}segs')
PYEOF

echo "Script criado. A separar e transcrever..."

# Para cada aula
for aula_num in 1 2 3 4 5 6; do
    audio="/tmp/M8_Aula${aula_num}_audio.wav"
    aula_dir="$TMP_BASE/aula${aula_num}"
    mkdir -p "$aula_dir"
    
    if [ ! -f "$audio" ]; then
        echo "Audio nao existe: $audio"
        continue
    fi
    
    # Conta chunks ja feitos
    done=$(ls "$aula_dir"/chunk_*.txt 2>/dev/null | wc -l | tr -d ' ')
    total=$(ffprobe -v quiet -show_entries format=duration -of csv=p=0 "$audio" | awk '{print int($1/600)+1}')
    
    echo "Aula $aula_num: $done/$total chunks feitos"
    
    # Processa chunks em falta
    for i in $(seq 0 $((total-1))); do
        chunk_txt="$aula_dir/chunk_$(printf '%03d' $i).txt"
        if [ -f "$chunk_txt" ]; then
            continue
        fi
        
        # Extrai chunk
        chunk_wav="$aula_dir/chunk_$(printf '%03d' $i).wav"
        ffmpeg -i "$audio" -ss $((i*600)) -t 600 -vn -acodec pcm_s16le -ar 16000 -ac 1 -y "$chunk_wav" 2>/dev/null
        
        # Transcreve
        $PYTHON "$TRANSCRIBE_SCRIPT" "$chunk_wav" "$chunk_txt" 2>/dev/null
        rm -f "$chunk_wav"
        echo "  Chunk $i/$total feito"
    done
    
    # Merge
    cat "$aula_dir"/chunk_*.txt > "$OUTPUT_BASE/Aula ${aula_num} - Transcrição.txt"
    echo "==> Aula $aula_num pronta: $(wc -l < "$OUTPUT_BASE/Aula ${aula_num} - Transcrição.txt") linhas"
    
    # Cleanup
    rm -rf "$aula_dir"
done

echo "=== M8 COMPLETO ==="
