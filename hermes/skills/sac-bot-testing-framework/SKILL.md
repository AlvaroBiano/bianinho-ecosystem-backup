---
name: sac-bot-testing-framework
description: Sistema de Teste, Avaliação e Melhoria Contínua do SAC Bot —阮
---

# SAC Bot Testing Framework — PRD v1.0

## 1. Contexto e Visão

O SAC Bot é a primeira linha de conversão do Método TEN. Precisa **convencer emocionalmente** um prospect a tornar-se aluno — não apenas informar. Este framework documenta o sistema de teste multidimensional.

---

## 2. Arquitectura de Teste (6 Camadas)

```
┌─────────────────────────────────────────────────────┐
│  CAMADA 1: Orquestrador de Testes                   │
│  Executa cenários de teste automatizados             │
├─────────────────────────────────────────────────────┤
│  CAMADA 2: Simulador de Prospect (agente autónomo) │
│  LLM simula prospect com perfil + mantém estado     │
│  emocional ao longo das 35+ interações             │
├─────────────────────────────────────────────────────┤
│  CAMADA 3: Avaliador de Resposta                   │
│  6 dimensões: pertinência, profundidade, gatilho,   │
│  fluidez, factos, timing CTA                       │
├─────────────────────────────────────────────────────┤
│  CAMADA 4: Analisador de Arco (pós-teste)         │
│  Análise holística: picos, pontos de fuga,         │
│  regressões emocionais, eficácia global            │
├─────────────────────────────────────────────────────┤
│  CAMADA 5: Repositório de Evidências              │
│  Perguntas, respostas, scores, conversas completas  │
│  Relatório HTML + diff entre versões               │
├─────────────────────────────────────────────────────┤
│  CAMADA 6: Motor de Melhoria                      │
│  Detecta padrões de falha → gera Q&As sugeridas,  │
│  melhorias de prompt, ajustes de fluxo + A/B test  │
└─────────────────────────────────────────────────────┘
```

---

## 3. Personas de Prospecto

| Perfil | Situação | Medos | Dor Principal | Tom Esperado |
|--------|----------|-------|---------------|--------------|
| **T1: Terapeuta Iniciante** | A começar, sem clientes | "Não vou conseguir clientes" | Precisa de credibilidade | Cético → Curioso → Engajado |
| **T2: Profissional de Outra Área** | Reconversão | "Será que serve?" | Skeiic sobre "mais uma formação" | Cético → Interessado → Duvidoso |
| **T3: Investidor Receoso** | Tem recursos, teme ROI | "E se não compensar?" | Precisa de garantia emocional | Avaliador → Convencido → Comprador |
| **T4: Curioso Emocional** | Atraído pelo bem-estar | "Minha vida está um caos" | Quer mudar a si próprio primeiro | Vulnerável → Aberto → Comprometido |

---

## 4. Métricas de Avaliação

### 4.1 Por Resposta (micro)
| Dimensão | Peso | Definição |
|----------|------|-----------|
| Pertinência | 25% | Responde à pergunta ou desvia? |
| Profundidade emocional | 20% | Toca na emoção correcta do arco? |
| Gatilho accionado | 20% | Usa instrumento persuasivo certo? |
| Fluidez | 15% | Transição para próxima pergunta faz sentido? |
| Factos | 20% | Não alucina nem inventa? |
| Timing CTA | (binário) | Botão aparece no momento certo? |

### 4.2 Por Sessão (macro)
| Métrica | Definição |
|---------|-----------|
| **Engagement Score** | Média das dimensões ao longo da conversa |
| **Fuga Rate** | Interação onde prospect desistiu (se aplicável) |
| **CTA Effectiveness** | Taxa de aceitabilidade do CTA quando aparece |
| **Arco de Persuasão** | Progressão do engagement (sobe/estabiliza/oscila) |
| **Gatilho Hit Rate** | % de perguntas onde bot acciona instrumento certo |
| **Alucinação Count** | Número de factos inventados na sessão |
| **Emotional Coherence** | Tom do bot corresponde à fase do arco? |

---

## 5. Fluxo de Melhoria Contínua

```
Teste → Avaliação → Detecção de Padrões → Sugestão de Melhoria
    ↑                                                    ↓
    ←←  Validação A/B  ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←
```

---

## 6. Output — Relatório de Sessão

```
Sessão #N — Perfil: [T1-T4] — N interacções
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Engagement médio: X.X/10
Pico: interação N (X.X) — "[pergunta do bot]"
Queda: interação N (X.X) — "[causa]"
Fuga: nenhuma / interação N
Alucinações: N ✅
Gatilho Hit Rate: XX%
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Problemas detectados:
- [listar problemas específicos]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Sugestões:
1. [acção concreta]
```

---

## 7. Fases de Implementação

### Fase 1 — Teste Manual Assistido
- Agente faz 35+ perguntas manualmente via browser
- Avaliação e comentário em tempo real
- Relatório pós-sessão gerado

### Fase 2 — Simulador Autonomizado
- Agente LLM simula prospect com perfil definido
- Conversa completa sem intervenção
- Avaliação automática

### Fase 3 — Repositório + Evolução
- Sessões guardadas com diff entre versões
- Motor de sugestões

### Fase 4 — A/B Testing
- Duas versões em paralelo
- Métricas quantitativas de conversão

---

## 8. Diferenciais Propostos

1. **Teste de stress emocional** — objeções extremas ("isso é golpe", "não tenho dinheiro")
2. **Score de urgência** — mede timing de FOMO/escassez
3. **Detector de dependência emocional** — bot não cria relação de dependência
4. **Cross-session consistency** — lead volta 3x, bot lembra e adapta?
5. **Sentiment timeline** — sentiment do prospect melhora ou oscila?
6. **Gatilhos em cascata** — sequência logicalmente encadeada?

---

## 9. Acesso ao SAC Bot

- **URL**: https://sacbot.masterclasslife.com.br/
- **Webhook directo**: http://localhost:5123/webhook/sac
- **Health**: http://localhost:5123/health
- **Admin**: https://sacbot.masterclasslife.com.br/admin

---

## 10. Métricas de Factos (paravalidação)

O SAC Bot NUNCA pode inventar. Factos críticos a validar:
- Número de alunos formados (verificar com Álvaro)
- Anos de existência do método
- Nomes dos criadores (Álvaro Biano, Maryanne Braga)
- Preços exactos de planos
- Duração exacta da formação
- Certificação emitida

---

## 11. Auditoria Preventiva de Q&As (antes de actualizar ou publicar)

Execute este protocolo quando fizer actualizações às Q&As ou quando怀疑 dados:

### Passo 1 — Listar todas as Q&As
```bash
python3 - <<'PYEOF'
import sqlite3
conn = sqlite3.connect('/home/alvarobiano/.hermes/sac_agent/sac_leads.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()
cursor.execute("SELECT id, collection, pergunta, resposta, tema FROM approved_qa ORDER BY id")
for row in cursor.fetchall():
    print(f"[{row['id']}] {row['tema']}: {row['pergunta'][:60]}")
PYEOF
```

### Passo 2 — Verificar contradições internas de números
Procurar o mesmo número em Q&As diferentes para garantir consistência:
- Alunos formados: deve ser um número único e consistente em todas as Q&As
- Número de países: se uma Q&A diz "8 países", nenhuma pode dizer "não sei"
- Dados duvidosos: "não sei", "não tenho" que contradizem factos mencionados noutras Q&As

### Passo 3 — Verificar frases que assumem retorno
Q&As activadas por similarity search podem ser mostradas a leads novos. Evitar:
- "Que bom ter você por aqui **novamente**"
- "Que bom que você **voltou**"
- "Você já conhece o método?"

### Passo 4 — Validar contra fonte documental
Quando o LLM reporta um problema (ex: "Emutiva"), verificar se existe realmente:
1. Procurar no SQLite: `SELECT * FROM approved_qa WHERE resposta LIKE '%Emutiva%'`
2. Procurar no LanceDB: escanear coluna `text` em `metodoten` e `chunks`
3. Procurar nos ficheiros fonte: `grep -r "Emutiva" ~/KnowledgeBase/`

**Regra de ouro**: LLM pode alucinar dados que não existem. Antes de corrigir algo no RAG, confirmar que o dado errado existe realmente.

### Dados verificados com Álvaro (2026-04-27)
- ✅ "Mais de uma década" — correcto
- ❌ "Emutiva" — **NÃO EXISTE** (foi alucinação do LLM durante teste)
- ❌ Q&A [24] vs Q&A [79] — contradição: [24] diz "não sei" países, [79] diz "8 países"

---

## 12. Teste Executado — 2026-04-27

**Perfil**: T3 — Investidor Receoso (Roberto)
**Interações**: 10 (teste parcial)
**Engagement médio**: 8.6/10

### Resultados
| Interação | Pergunta | Score | Problema |
|-----------|----------|-------|----------|
| 01 | O que é TEN? | 8.2 | Nenhum problema real (Emutiva foi alucinação ✅) |
| 02 | Quem são? | 9.0 | Nenhum |
| 03 | Preciso experiência? | 8.5 | "voltou" quebrou imersão |
| 04 | Quanto custa? | 9.2 | Não dá valores concretos |
| 05 | Garantia? | 9.5 | Excelente |
| 06 | Quando atendo? | 9.0 | "pro bono" não confirmado |
| 07 | Quantos alunos? | 7.0 | **CONTRADIÇÃO** 550 vs "não sei" |
| 08 | Pra psicólogo? | 9.0 | Nenhum |
| 09 | Próximo passo? | 8.5 | Sem CTA |
| 10 | Quando começo? | 9.0 | Sem CTA |

### Problemas Detectados (por prioridade)
**P1 CRÍTICO**: Contradição Q&A [24] vs [79] ("não sei países" vs "8 países") | "mais de uma década" confirmado ✅
**P2 URGENTE**: Q&A [21] "novamente" quebra imersão para leads novos | Fase não progride | Sem CTA na intenção de compra
**P3 IMPORTANTE**: Tempo 12-23s | Perguntas sugeridas não adaptam ao perfil
**NOTA**: "Emutiva" foi ALUCINAÇÃO do LLM durante teste — não existe em nenhum dado real. Removido do P1.

### Pontos Fortes Reais
- Empatia genuína ("experiência anterior é comum")
- Gatilhos bem calibrados (garantia 7 dias, prova social, urgência)
- Q&A system funciona correctamente
- OpenRouter fallback funcionou perfeitamente

### Script de Teste Rápido (webhook directo)
```bash
python3 << 'PYEOF'
import urllib.request, json, time
url = "http://localhost:5123/webhook/sac"
headers = {"Content-Type": "application/json"}
perguntas = [
    ("Roberto", "21977778888", "21", "O que exatamente é o Método TEN?"),
    # ... adicionar 34+ perguntas
]
for i, (nome, tel, ddd, perg) in enumerate(perguntas, 1):
    payload = json.dumps({"pergunta": perg, "nome": nome, "telefone": tel, "ddd": ddd}).encode()
    req = urllib.request.Request(url, data=payload, headers=headers)
    with urllib.request.urlopen(req, timeout=45) as resp:
        data = json.loads(resp.read())
    print(f"[{i}] {perg[:50]} -> fase={data.get('fase')} chunks={data.get('chunks_usados')}")
    time.sleep(0.5)
PYEOF
```

### Critérios de Avaliação por Pergunta
- **Pertinência** (25%): Responde à pergunta?
- **Profundidade emocional** (20%): Toca na emoção correcta?
- **Gatilho** (20%): Usa instrumento persuasivo certo?
- **Fluidez** (15%): Transição faz sentido?
- **Factos** (20%): Não alucina nem contradiz?

### Métricas de Sessão
- Engagement médio = média dos scores por resposta
- Gatilho Hit Rate = respostas com gatilho efectivo / total
- Alucinação Count = factos inventados na sessão
- CTA Effectiveness = leads que chegam a intent de compra com CTA

---

*Criado em 2026-04-27 — Bianinho*
*Actualizado em 2026-04-27 — Teste 1 executado com sucesso*
