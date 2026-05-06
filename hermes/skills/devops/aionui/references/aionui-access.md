# AionUI — Access Reference (01/05/2026)

## Resumo da Sessão

O Álvaro precisava de aceder ao AionUI remotamente. Após várias tentativas:

### O que NÃO funcionou:
- **Screenshot streaming CDP** (aionui-web-viewer.py porta 8765): mostra imagem mas sem interatividade
- **Screenshot via cloudflared tunnel**: mesmo resultado
- **noVNC**: interação possível mas Álvaro rejeitou ("essa bosta")

### O que FUNCIONA:
- **VNC/noVNC**:唯一 que permite interatividade real

### Arquitectura aprendida:
- AionUI é frontend Electron + Hermes é backend Python
- Conexão entre eles é via `aionrs_bridge.py` (subprocesso stdio local)
- O Hermes NÃO é um servidor HTTP — é um processo Python que comunica por JSON stream

## Keys aprendidas

1. **Screenshot streaming ≠ interatividade** — para GUI apps, screenshot é só espelho
2. **VNC é necessário** quando precisas de clicar em apps Electron num servidor headless
3. **Cloudflared URL capture**: usar `subprocess.Popen` com `readline()` em vez de background terminal tool
4. **AionUI no Mac** não dá acesso ao Hermes do servidor — arquitectura é local

## Estados Finais

```
x11vnc: PID 486711, display :99, rfbport 5900
websockify: PID 508508, porta 6080, → localhost:5900
AionUi Electron: PIDs 731772/731773/732064/732070
aionui-web-viewer.py: PID 732204, porta 8765
Xvfb: display :99

Cloudflared noVNC tunnel activo:
URL: ver /tmp/novnc-tunnel-url.txt
Restart: bash /home/alvarobiano/.hermes/scripts/novnc-tunnel.sh
```
