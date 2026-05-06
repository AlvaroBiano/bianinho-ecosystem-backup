---
name: typebot-oauth-ipv6-fix
description: Fix Docker container failing to reach accounts.google.com for OAuth — disable IPv6 on host
tags: [typebot, docker, google-oauth, ipv6, network-troubleshooting]
created: 2026-04-22
---

# Typebot Local + Google OAuth — IPv6 Network Fix

## Situation
Typebot container (Docker) cannot reach `accounts.google.com` for Google OAuth login, throwing `fetch failed` errors in the NextAuth callback. `oauth2.googleapis.com/token` works fine (IPv4), but `accounts.google.com` fails (tries IPv6).

## Root Cause
Docker container uses IPv6 AAAA lookups for `accounts.google.com`, which is blocked in the container's network path, while the host machine uses IPv4 successfully.

## Fix — Disable IPv6 on the Host

```bash
sudo sysctl -w net.ipv6.conf.all.disable_ipv6=1
```

Make persistent:
```bash
echo "net.ipv6.conf.all.disable_ipv6 = 1" | sudo tee -a /etc/sysctl.d/99-disable-ipv6.conf
```

To re-enable if needed:
```bash
sudo sysctl -w net.ipv6.conf.all.disable_ipv6=0
```

## Verify from Inside the Container

```bash
docker exec typebot-builder-1 curl -s -o /dev/null -w "%{http_code}" https://accounts.google.com
# Should return 302 (redirect to login), not a fetch error
```

## Full Typebot Setup Context

- Docker Compose: `/home/alvarobiano/typebot/docker-compose.yml`
- PostgreSQL: host `localhost`, port `5433`, password `typebot2026`
- Cloudflare Tunnel: background process, URL via `docker logs cloudflared` or `ps aux | grep cloudflared`
- OAuth Client: Google Cloud Console Web application, redirect URIs must include both `http://localhost:8080/api/auth/callback/google` AND the Cloudflare tunnel URL
- IPv6 must stay disabled for OAuth to work — if the server reboots, re-apply the sysctl

## Tags
#typebot #docker #google-oauth #ipv6 #network-troubleshooting
