---
name: server-health
description: Verificação completa de saúde do servidor — temperatura, CPU, RAM, disco, processos, serviços, e limpeza automática do sistema
category: devops
tags: [servidor, saúde, temperatura, manutenção, cron]
---

# Server Health — Verificação de Saúde do Servidor

## Quando usar
Execute manualmente ou automaticamente via cron. Ideal para rodar antes de sessões pesadas de uso do servidor.

## O que faz

### Verificações
- **Temperaturas**: CPU, GPU, fans (verificação de todas as zonas térmicas)
- **CPU**: frequência, governor, uso por core
- **RAM/Swap**: uso total e por processo
- **Disco**: espaço e inodes
- **Processos**: top 10 CPU/RAM
- **Serviços**: status de serviços críticos (thermald, tailscaled, ssh, etc)
- **Logs**: últimos erros do sistema
- **Rede**: conectividade

### Limpeza automática
- Cache APT (até 1.4GB)
- Arquivos tempórios antigos
- Caches do npm/node
- Caches do Python (se aplicável)
- Cache de thumbnails do sistema
- **Hermes `request_dump*`** — dumps de debugging de sessões em `~/.hermes/sessions/`. Acumulam 300–520 KB por ficheiro. Política: remover automaticamente os mais antigos que 7 dias. Mantém `sessions.json` e `session_*.json` (dados reais).

### Controle térmico
- Monitora temperaturas e alerta se acima de 70°C
- Sugere ações caso temperatura esteja alta
- Verifica se thermald está ativo
- Verifica se há processos com alto uso fazendo temperatura subir

## Script
- `scripts/server_health.sh` — script principal

## Uso
```bash
# Manual
bash ~/.hermes/skills/server-health/scripts/server_health.sh

# Via cron (sugerido: 08:00 e 20:00 BRT diariamente)
```

## Saída
Relatório em `/home/alvarobiano/.hermes/logs/server_health_YYYYMMDD.log`

## Pitfalls encontrados
- **CPU parsing**: Em Macs via BootCamp, `grep "Model name"` e `grep "cpu MHz"` podem retornar linhas vazias. Usar `sed 's/.*: //'` em vez de `awk -F: '{print $2}'` com `sed 's/^ //'` para evitar espaços.
- **Thermal zones**: Leitura de `/sys/class/thermal/thermal_zone0/temp` retorna valor em millidegrees — dividir por 1000.
- **Gateway ping**: Em notebooks, gateway pode não responder ping (100% packet loss). Não é crítico se DNS (8.8.8.8) responde — indica apenas que o gateway específico não responde ICMP.
- **Drop caches**: Só funciona como root. Se executado como usuário, o script ignora erro silenciosamente.
- **APT cache**: Apt-get clean precisa de sudo — script usa `sudo apt-get clean` mesmo em contexto onde pode não funcionar sem senha. fallback: ignorar erro.

