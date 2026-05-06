---
name: ollama-vision-cpu
description: Tentativa de visão local com Ollama em CPU — gemma3/4 não funcionam bem em 16GB RAM sem GPU. Documenta o que foi tentado, o que falhou, e a solução alternativa.
category: mlops
tags:
  - ollama
  - vision
  - local-ai
  - cpu-only
  - multimodal
---

# Ollama Vision em CPU — Tentativa e Resultados

## Contexto
Álvaro queria análise local de imagens (zero custo, offline). Hardware: Linux Mint, i7, 16GB RAM, sem GPU dedicada.

## O que foi tentado

### 1. gemma4:e2b (~7GB)
- Download concluído com sucesso
- Carrega em RAM mas consome ~7GB do modelo + overhead do runner
- **Resultado:** Removido — RAM ficava com apenas ~1.5GB livre, sistema em swap

### 2. gemma3:4b (~3.3GB) — instalado
- Modelo mais leve, deveria caber em 16GB RAM
- API `/api/generate` com `images` parameter: **HTTP 500 após 3 min** (Ollama server aborta por timeout)
- API `/v1/chat/completions` com `image_url` base64: **HTTP 500**
- CLI `ollama run gemma3:4b` com imagem: **"Added image" sucesso**, mas modelo fica em spinner infinito — não produz texto

## Problema de fundo
- gemma3/4 são modelos grandes para CPU-only
- Sem GPU, a inferência é tão lenta que o Ollama aborta por timeout interno (~3 min)
- O runner fica em RAM (4.5GB) mas não gera output útil

## Estado atual do servidor
```
NAME         SIZE     MODIFIED
gemma3:4b    3.3 GB   instalado mas não funciona para visão
```
Ollama serve está a correr em `localhost:11434`.

## Soluções alternativas para próxima tentativa

### Opção 1: Modelo pequeno otimizado para CPU ✅ (recomendado)
```bash
ollama pull moondream
# moondream ~1GB, feito para CPU, multimodal
```
Alternativas leves: `llava:3b`, `qwen2.5vl:3b`

### Opção 2: Desativar RAM-heavy processes antes de carregar
Parar serviços desnecessários para ter mais RAM disponível antes de carregar modelo

### Opção 3: API key Gemini Flash (gratuita)
Obter em https://aistudio.google.com/apikey
Gemini Flash é totalmente gratuito para visão e mais rápido

## Lição aprendida
- **Não instalar gemma4:e2b em sistemas com <32GB RAM sem GPU** — ocupa 7GB+ do modelo
- **gemma3:4b para visão em CPU-only não funciona** — API retorna 500, CLI não produz texto
- Modelos de visão necessitam de GPU ou modelos especificamente otimizados para CPU

## Comandos úteis
```bash
# Ver estado do Ollama
ollama list
ps aux | grep ollama

# Parar Ollama
pkill -f "ollama serve"

# Remover modelo
ollama rm gemma3:4b

# Logs
tail -f ~/.hermes/logs/ollama.log
```
