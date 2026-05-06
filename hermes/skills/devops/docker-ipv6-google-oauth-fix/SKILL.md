---
name: docker-ipv6-google-oauth-fix
description: Fix Docker containers unable to reach accounts.google.com for OAuth — caused by IPv6 preference
tags:
  - docker
  - networking
  - ipv6
  - oauth
  - google
---

# Docker IPv6 Google OAuth Fix

## Quando usar
Container Docker não consegue completar OAuth Google (login "Continue with Google") — timeout em `accounts.google.com` ou `oauth2.googleapis.com/token`, mas `www.google.com` funciona.

## Diagnóstico
```bash
# Testar do container
docker exec <container> sh -c "curl -v https://accounts.google.com 2>&1 | head -20"
# Timeout = problema IPv6

# Testar no host
curl -v --connect-timeout 5 https://accounts.google.com 2>&1 | head -10
# Funciona = rede do host OK, problema é do container
```

## Fix — Desabilitar IPv6 no servidor
```bash
# Temporário (até reiniciar)
sysctl -w net.ipv6.conf.all.disable_ipv6=1
sysctl -w net.ipv6.conf.default.disable_ipv6=1

# Permanente — adicionar a /etc/sysctl.conf:
net.ipv6.conf.all.disable_ipv6 = 1
net.ipv6.conf.default.disable_ipv6 = 1
```

## Porquê funciona
O Google tem IPv6 para `www.google.com` mas bloqueia/sempre responde em IPv4 para `accounts.google.com` e `oauth2.googleapis.com`. O container prefere IPv6 (devido a rotas de host) e falha. O host funciona porque usa IPv4 por defeito.

## Sintomas exacta
- `accounts.google.com` → timeout (DNS resolve para IPv6, conexão falha)
- `oauth2.googleapis.com/token` → POST funciona (GET falha)
- `www.google.com` → funciona
- `www.googleapis.com` → funciona

## Verificação pós-fix
```bash
sysctl net.ipv6.conf.all.disable_ipv6  # deve mostrar 1
sysctl net.ipv6.conf.default.disable_ipv6  # deve mostrar 1

# Testar do container
docker exec <container> sh -c "curl -s -o /dev/null -w '%{http_code}' https://accounts.google.com"
# Deve retornar 301 ou 302, não timeout
```

## Reboot containers após fix
```bash
cd /caminho/do/docker-compose
docker-compose down
docker-compose up -d
```
