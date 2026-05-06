---
name: typebot-self-hosted-ipv6-fix
description: Fix IPv6 blocking Google OAuth in Typebot Docker containers
triggers:
  - Typebot OAuth "Could not resolve host" accounts.google.com
  - Docker container can't reach Google OAuth endpoint
  - Google OAuth timeout inside Docker container
---

# Typebot Self-Hosted — IPv6 + OAuth Fix

## Contexto
Typebot self-hosted em Docker num servidor Linux Mint 22. O container do builder não consegue alcançar `accounts.google.com` para completar o Google OAuth, resultando em timeout.

## Sintomas
- Login com Google OAuth começa mas o callback never completes
- `curl accounts.google.com` dentro do container dá "Could not resolve host" ou timeout
- `curl www.google.com` funciona, `curl oauth2.googleapis.com/token` funciona
- É um bloqueio selectivo de `accounts.google.com` dentro do container

## Root Cause
IPv6 está habilitado no servidor. O container tenta IPv6 primeiro, o router/modem bloqueia o AAAA lookup para `accounts.google.com`, e mesmo quando há fallback para IPv4 algo no caminho está partido.

## Fix

```bash
# Desabilitar IPv6 globalmente no servidor
sudo sysctl -w net.ipv6.conf.all.disable_ipv6=1
sudo sysctl -w net.ipv6.conf.default.disable_ipv6=1

# Para persistir após reboot, adicionar a /etc/sysctl.conf:
# net.ipv6.conf.all.disable_ipv6 = 1
# net.ipv6.conf.default.disable_ipv6 = 1

# Reiniciar os containers Docker
cd ~/typebot
sudo docker compose restart
```

## Verificação
```bash
# Testar dentro do container
sudo docker exec typebot-typebot-builder-1 sh -c "curl -sI https://accounts.google.com 2>&1 | head -3"
# Esperado: HTTP/2 302
```

## Notas
- Afecta todo o servidor (IPv6 desabilitado globalmente)
- Alternativa mais cirúrgica: `--sysctl net.ipv6.conf.all.disable_ipv6=1` só no container no docker-compose
