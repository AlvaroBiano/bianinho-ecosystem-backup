---
name: security-audit
description: Auditoria de segurança automática do servidor — verificação de permissões, serviços, logs e correções automáticas
category: devops
tags: [segurança, servidor, permissões, cron]
---

# Security Audit — Auditoria Automática de Segurança

## Quando usar
Execute manualmente com `skill_view` + `delegate_task`, ou automaticamente via cron job diário às 22:00 BRT.

## O que faz

### Verificações
- Permissões de arquivos sensíveis (`.env`, tokens OAuth, logs, chaves SSH)
- Portas TCP abertas e serviços expostos
- Processos com alto uso de CPU/RAM
- Backups (Timeshift status)
- Logs SSH (tentativas de acesso)
- Atualizações de segurança pendentes
- Status do Tailscale VPN

### Correções automáticas
- Corrige permissões `chmod 600` em arquivos expostos
- Detecta processos suspeitos
- Reporta falhas de autenticação SSH

## Script
- `scripts/security_audit.sh` — script principal de auditoria

## Pitfalls encontrados
- **Processos suspeitos**: `grep` em processos normais gerava falsos positivos. Regex deve usar `nc ` (com espaço) para evitar matches em "cinnamon", "postgres", etc.
- **SSH failures**: Filtrar apenas `Failed password` ou `Failed publickey` — não usar `Failed` sozinho pois captura erros PAM não relacionados a SSH.
- **APT list**: Nem sempre disponível em todas as distros — usar `|| echo "Nenhuma atualização"` como fallback.

## Uso
```bash
# Manual
bash ~/.hermes/skills/security-audit/scripts/security_audit.sh

# Via cron (já configurado: 22:00 BRT diariamente)
```

## Saída
Relatório detalhado em `/home/alvarobiano/.hermes/logs/security_audit_YYYYMMDD.log`
