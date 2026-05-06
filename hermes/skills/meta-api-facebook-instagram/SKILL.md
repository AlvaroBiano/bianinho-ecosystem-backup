---
name: meta-api-facebook-instagram
description: Guia completo para acessar Facebook/Instagram via Meta Graph API — setup, tokens e limitações
---

# Meta Graph API — Acesso ao Facebook/Instagram

## O que é
Usar a API oficial do Meta (Facebook/Instagram) via Access Token para buscar dados, analisar perfis, grupos, páginas e afiliados.

## Dados do Cliente ( Álvaro Biano — exemplo )
- **APP ID:** 2636008266800424
- **APP SECRET:** 951c4d4ae3304aa127408dfdf7b8530c
- **Access Token:** Salvar em `~/.facebook_token.txt`
- **App:** "Método TEN - Afiliados" (tipo: Marketing)
- **Email:** alvarobiano@gmail.com

## Passo a Passo — Setup Inicial

### 1. Criar App no Meta for Developers
1. Ir em: **developers.facebook.com**
2. "Meus Apps" → "Criar App" → tipo "Gestão de Marketing"
3. Nome: "Nome do Cliente - Afiliados" ou similar
4. Preencher email de contato
5. Ir em Configurações → Básico → copiar App ID e App Secret

### 2. Gerar Access Token (User Token)
1. Ir em: **developers.facebook.com/tools/explorer**
2. Selecionar o app criado
3. Clicar em "Adicionar Permissões":
   - `public_profile` ✅ (padrão)
   - `pages_read_engagement` ✅ (padrão)
   - `instagram_basic` ✅ (para Instagram)
   - `pages_show_list` ✅ (padrão)
4. Clicar em **"Generate Access Token"**
5. Autorizar com login Facebook
6. Copiar o token completo (começa com `EAA...`)

### 3. Testar Token
```bash
curl -s "https://graph.facebook.com/v18.0/me?access_token=SEU_TOKEN" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('name',''), '|', d.get('id',''))"
```

### 4. Verificar Permissões
```bash
curl -s "https://graph.facebook.com/v18.0/me/permissions?access_token=SEU_TOKEN" | python3 -c "import sys,json; d=json.load(sys.stdin); [print(p.get('permission',''), '|', p.get('status','')) for p in d.get('data',[])]"
```

## Permissões — O Que Precisa Saber

### Permissões "fáceis" (disponíveis via Graph Explorer)
- `public_profile` ✅
- `pages_read_engagement` ✅
- `pages_show_list` ✅
- `instagram_basic` ✅

### Permissões BLOQUEADAS (precisam App Review)
- `groups_access_member_info` — **NÃO APARECE** nem no Graph API Explorer
  - Meta RESTRINGIU COMPLETAMENTE em 2024-2025
  - Não aparece na lista de permissões, mesmo no Graph API Explorer
  - Não é possível gerar sem App Review completo
  - Requer: site verificado (HTTPS), política de privacidade, vídeo explicando uso
  - Pode levar 2-7 dias, e PODE SER RECUSADO
  - Alternativa: usar browser automation ou busca web
- `pages_manage` — precisa App Review
- `instagram_manage_comments` — precisa App Review
- `instagram_manage_messages` — precisa App Review

### Alternativa: Buffer API (mais fácil, sem App Review)
- Ver skill `buffer-api-connection`
- Buffer.com tem API GraphQL com API key simples
- Suporta: Facebook, Instagram, TikTok, LinkedIn, YouTube, etc.
- Limitações: não busca membros de grupos, não envia DMs
- `pages_manage` — precisa App Review
- `instagram_manage_comments` — precisa App Review
- `instagram_manage_messages` — precisa App Review

### O Que Funciona Sem App Review
```bash
# Ver dados básicos do usuário
curl "https://graph.facebook.com/v18.0/me?access_token=TOKEN"

# Ver páginas (se o app tiver acesso)
curl "https://graph.facebook.com/v18.0/me/accounts?access_token=TOKEN"

# Ver posts e engajamento (páginas que o app administra)
curl "https://graph.facebook.com/v18.0/PAGE_ID/posts?access_token=TOKEN"

# Buscar perfis públicos
curl "https://graph.facebook.com/v18.0/search?q=terapia+emocional&type=page&access_token=TOKEN"
```

## Problemas Comuns e Soluções

### `me/accounts` retorna `{"data": []}`
- **Causa:** App não tem acesso às páginas
- **Solução:** No Business Suite (business.meta.com), adicionar o app como Parceiro/Gerenciador da página
- Ou: Gerar **Page Access Token** específico (não User Token)

### Instagram não conecta
- Instagram precisa estar como **Conta Profissional/Corporativa**
- Deve estar vinculado a uma **Página do Facebook**
- Configurar em: Configurações da Página → Instagram

### `groups_access_member_info` não aparece
- **Normal** — Meta restringiu essa permissão
- **Opções:**
  1. Fazer App Review (lento, pode não aprovar)
  2. Usar browser automation (risco de suspensão)
  3. Fazer manualmente e passar dados ao agente

## Arquivos de Referência
- Token salvo em: `~/.facebook_token.txt`
- Banco de sessões: `~/.hermes/hermes_sessions.db`
- Logger: `~/.hermes/hermes_logger.py`

## Quando Usar
- Buscar afiliados no Facebook/Instagram
- Analisar engajamento de páginas
- Identificar potenciais parceiros
- Monitorar comentários e menções
