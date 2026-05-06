---
name: research-spa-api-docs
description: Research API capabilities when documentation is a SPA (JavaScript-rendered) — use browser tools instead of curl/wget.
---

# Research API Capabilities from SPA Documentation

## When to Use
Quando precisar pesquisar capabilities, features ou detalhes de uma API cuja documentação é uma **SPA (Single Page Application)** — onde o conteúdo é renderizado por JavaScript e não vem no HTML inicial.

Sinais de SPA: `curl` ou `fetch` retornam HTML vazio/com skeleton, sem conteúdo real; titles e metadata repetidas mas sem dados de tabela.

## Método

### Passo 1: Tentar fetch simples primeiro
```bash
curl -s "https://api-docs.provedor.com/" | grep -i -E "vision|image|multimodal" | head -20
```
Se retorna só HTML shell → seguir para passo 2.

### Passo 2: Usar browser_navigate + browser_snapshot
```python
browser_navigate(url="https://api-docs.provedor.com/")
# Esperar carregar
browser_snapshot(full=true)
```
O snapshot vai conter o conteúdo renderizado pelo JS.

### Passo 3: Navegar pelas páginas relevantes
- Models/Pricing page → tabela de features
- Changelog/News page → announcements oficiais
- FAQ page → limitações conhecidas

### Passo 4: Verificar API endpoint diretamente (se disponível)
```bash
curl -s "https://api.provedor.com/v1/models" -H "Authorization: Bearer test" 2>/dev/null
```
Mesmo com API key inválida, muitos endpoints retornam erro 401 com estrutura JSON que revela os modelos disponíveis.

### Passo 5: Cross-reference
Confrontar findings da tabela de features com changelog oficial para confirmar ausências (se uma feature não está na tabela E não foi anunciada → provavelmente não existe).

## Verificação de Vision/Multimodal
Para verificar se um modelo suporta imagem/vision, procurar na tabela de features por:
- "Vision" / "Image Input" / "Multimodal" / "Image Understanding"
Se não estiver na tabela de features E não houver guia separado de "Vision" na sidebar → provavelmente não suporta.

## Casos de Estudo
- **DeepSeek API Docs** (api-docs.deepseek.com): SPA pura — tabelas de features só visíveis via browser_snapshot
- **Many Chinese AI providers** (DeepSeek, MiniMax, StepFun): frequentemente usam SPAs com Docusaurus

## Armadilhas
- Não confiar em `curl` puro para docs de IA — quase sempre SPA
- Não confiar em search genérico da web — resultados podem ser de versões antigas da doc
- changelog mais recente que a tabela de features → a feature pode ter sido removida ou nunca existiu na API
