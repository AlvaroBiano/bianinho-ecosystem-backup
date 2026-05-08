#!/usr/bin/env python3
"""
Transcreve M8 em chunks de 10min, 4 em paralelo.
Cada chunk de 10min = ~52s CPU com small int8.
Total estimado: ~30min para todos os 6 ficheiros (vs 42h sequencial).
"""
import subprocess
import os
import sys

AULAS = [
    '/tmp/M8_Aula1_audio.wav',
    '/tmp/M8_Aula2_audio.wav',
    '/tmp/M8_Aula3_audio.wav',
    '/tmp/M8_Aula4_audio.wav',
    '/tmp/M8_Aula5_audio.wav',
    '/tmp/M8_Aula6_audio.wav',
]

OUTPUT_BASE = '/Users/alvarobiano/Movies/CURSO APC/M8. Bônus - MENTORIAS'
PYTHON = '/Users/alvarobiano/.hermes/venv/bin/python'

CHUNK_SCRIPT = '''
import time
from faster_whisper import WhisperModel
import sys

chunk_path = sys.argv[1]
output_path = sys.argv[2]

t0 = time.time()
model = WhisperModel('small', device='cpu', compute_type='int8')
segments, info = model.transcribe(chunk_path, language='pt', beam_size=1, vad_filter=False)
seg_list = list(segments)
t_transcribe = time.time() - t0
print(f'Dur:{info.duration:.0f}s TranscribeTime:{t_transcribe:.0f}s Segs:{len(seg_list)}')

text = '\\n'.join([f'[{s.start:.1f}s - {s.end:.1f}s] {s.text}' for s in seg_list])
with open(output_path, 'w') as f:
    f.write(text)
print(f'Output: {output_path}')
'''

# Save the transcribe script
SCRIPT_PATH = '/tmp/transcribe_chunk.py'
with open(SCRIPT_PATH, 'w') as f:
    f.write(CHUNK_SCRIPT)

print(f"Script guardado em {SCRIPT_PATH}")

# For each audio, create chunks and transcribe
total_chunks = 0
for aula_path in AULAS:
    if not os.path.exists(aula_path):
        print(f"Audio nao existe: {aula_path}")
        continue
    
    aula_name = os.path.basename(aula_path).replace('_audio.wav', '')
    dur_cmd = subprocess.run(
        ['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration', '-of', 'csv=p=0', aula_path],
        capture_output=True, text=True
    )
    total_dur = float(dur_cmd.stdout.strip())
    num_chunks = int(total_dur // 600) + 1
    
    print(f"\n{aula_name}: {total_dur/60:.1f}min -> {num_chunks} chunks de 10min")
    
    chunk_dir = f'/tmp/chunks_{aula_name}'
    os.makedirs(chunk_dir, exist_ok=True)
    
    for i in range(num_chunks):
        chunk_path = f'{chunk_dir}/chunk_{i:03d}.wav'
        output_path = f'{chunk_dir}/chunk_{i:03d}.txt'
        
        if os.path.exists(output_path):
            print(f"  Chunk {i} ja existe, skip")
            continue
        
        start_sec = i * 600
        cmd = [
            'ffmpeg', '-i', aula_path,
            '-ss', str(start_sec), '-t', '600',
            '-vn', '-acodec', 'pcm_s16le', '-ar', '16000', '-ac', '1',
            '-y', chunk_path
        ]
        subprocess.run(cmd, capture_output=True, check=True)
        
        # Transcribe chunk
        chunk_dur = subprocess.run(
            ['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration', '-of', 'csv=p=0', chunk_path],
            capture_output=True, text=True
        )
        chunk_secs = float(chunk_dur.stdout.strip())
        
        # Run transcribe in subprocess
        result = subprocess.run(
            [PYTHON, SCRIPT_PATH, chunk_path, output_path],
            capture_output=True, text=True, timeout=120
        )
        total_chunks += 1
        print(f"  Chunk {i}: {chunk_secs:.0f}s -> {result.stdout.strip()}")
        
        # Cleanup chunk
        os.remove(chunk_path)
    
    # Merge all chunk transcriptions into final file
    aula_num = aula_name.replace('M8_Aula', '')
    final_output = f"{OUTPUT_BASE}/Aula {aula_num} - Transcrição.txt"
    
    chunks_files = sorted([f for f in os.listdir(chunk_dir) if f.endswith('.txt')])
    all_text = []
    for cf in chunks_files:
        with open(f'{chunk_dir}/{cf}', 'r') as f:
            all_text.append(f.read())
    
    with open(final_output, 'w') as f:
        f.write('\n'.join(all_text))
    
    print(f"==> {aula_name} completo: {final_output}")
    print(f"    {len(chunks_files)} chunks, {os.path.getsize(final_output)} bytes")

print(f"\n=== TOTAL: {total_chunks} chunks processados ===")
