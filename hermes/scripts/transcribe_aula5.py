import time
from faster_whisper import WhisperModel

video = '/Users/alvarobiano/Movies/CURSO APC/M2. A Mente Humana/Aula 5.mp4'
output = '/Users/alvarobiano/Movies/CURSO APC/M2. A Mente Humana/Aula 5 - Transcrição.txt'

print('Aula 5 (30min)...')
t0 = time.time()
model = WhisperModel('medium', device='cpu', compute_type='int8')
print(f'Modelo: {time.time()-t0:.1f}s')

segments, info = model.transcribe(video, language='pt', beam_size=1, vad_filter=True)
seg_list = list(segments)
t_total = time.time() - t0
print(f'OK: {info.duration:.0f}s / {t_total:.0f}s ({t_total/info.duration:.2f}xRT), {len(seg_list)} segs')

text = '\n'.join([f'[{s.start:.1f}s - {s.end:.1f}s] {s.text}' for s in seg_list])
with open(output, 'w') as f:
    f.write(text)
print('Gravado!')
