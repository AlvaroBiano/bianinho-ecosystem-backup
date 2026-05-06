---
name: sac-rag-qa-workflow
description: Workflow para criar Q&As aprovadas no SAC Bot — pergunta por pergunta com SAC Bot real
triggers:
  - trabalho RAG Q&A
  - criar Q&A approved
  - 100 perguntas método TEN
---

## Obter resposta do SAC Bot — duas opções

### Opção 1: Webhook (rápido, retorna JSON)
```bash
curl -s -X POST "https://sacbot.masterclasslife.com.br/webhook/sac" \
  -H "Content-Type: application/json" \
  -d '{"pergunta": "TEXTO", "nome": "Bianinho", "telefone": "11999999999", "ddd": "11"}'
```
Retorna JSON com `resposta`, `score`, `chunks_usados`, `fontes`.

### Opção 2: Browser (mostra a experiência real do lead)
Quando quiseres ver a resposta exactamente como o lead recebe (formatação, layout, CTA):
1. Navegar a https://sacbot.masterclasslife.com.br/
2. Preencher campos via JS (não estão acessíveis por ref normal):
   ```js
   document.getElementById('campo-nome').value = 'Nome';
   document.getElementById('campo-telefone').value = '11999999999';
   document.getElementById('btn-iniciar').disabled = false;
   document.getElementById('btn-iniciar').click();
   ```
3. Esperar chat abrir, digitar pergunta e enviar
4. Ler resposta com `document.getElementById('chat-mensagens').innerText`
5._scroll down se não vir a mensagem

## SAC RAG Q&A Workflow

## Passo a passo — sempre nesta ordem

### 1. Fazer pergunta ao SAC Bot
Usar o URL público do SAC Bot (cloudflared tunnel):

```bash
curl -s -X POST "https://sacbot.masterclasslife.com.br/webhook/sac" \
  -H "Content-Type: application/json" \
  -d '{"pergunta": "TEXTO DA PERGUNTA", "nome": "Bianinho", "telefone": "11999999999", "ddd": "11"}'
```

### 2. Formatar resposta para o Álvaro

**P:** [pergunta]

---

> [resposta integral do SAC Bot]

---

**Análise:**

| Aspecto | Avaliação |
|---------|-----------|
| Precisão do dado | ✅/⚠️ [comentário] |
| Tom | ✅/⚠️ [comentário] |
| Encaminhamento | ✅/⚠️ [comentário] |
| Potenciais problemas | ⚠️ [notas] |

**Aprovas para gravar?**

### 3. Após aprovação — gravar na base

```python
import sqlite3

resposta = """[resposta integral]"""

conn = sqlite3.connect('/home/alvarobiano/.hermes/sac_agent/sac_leads.db')
cur = conn.cursor()
cur.execute("""
    INSERT INTO approved_qa (pergunta, resposta, tema, aprovado_em)
    VALUES (?, ?, 'tema-da-pergunta', datetime('now'))
""", ("[pergunta exacta]", resposta))
conn.commit()
conn.close()
```

### 4. Após gravar — sync do RAG (2 camadas)
O bot lê `approved_qa` directamente do SQLite em cada pedido — **não precisa de reload**.
Mas se a resposta veio do Álvaro (não do bot), actualizar também o documento fonte:

**Limpeza de expressões banidas — 2 camadas:**
1. `approved_qa` (SQLite) → UPDATE/DELETE directo
2. Documento fonte em `~/.hermes/cache/documents/*.md` → patch manual se existir lá

Se a expressão banida estiver no documento fonte, o bot vai continuar a gerar a resposta incorrecta porque o RAG procura nesses documentos. Exemplo: "nada é repassado para terceiros" existia no `.md` fonte — o bot continuava a usá-lo.

**Verificar fontes contaminadas:**
```bash
grep -r "repassado" ~/.hermes/cache/documents/
grep -r "terceiros" ~/.hermes/cache/documents/
```

### 5. Re-indexar após limpar fontes
Após modificar documentos fonte, o bot pode continuar a usar a versão antiga cached. Testar com pergunta idêntica ao webhook — se continuar a mesma resposta errada, o chunk vectorizado pode estar cached no LanceDB. Verificar com `sac-qa-sync-cleanup` skill.

## Regras
- Sempre usar o SAC Bot real (webhook cloudflared), não responder internamente
- Sempre perguntar ao Álvaro antes de gravar
- Sempre apresentar: pergunta, citação da resposta, análise
- Na análise: identificar erros, propor correcções, esperar aprovação antes de gravar
- Só passar para a próxima após aprovação
- Tema/tags: usar kebab-case (ex: `taxa-sucesso`, `formacao`, `criadores`)

## Regras de correcção de texto (aprender com experiência)
- "movimentospráticos" → "ações concretas" (erro de concatenação do SAC Bot)
- "nada é repassado para terceiros" → REMOVER de TUDO: approved_qa, documentos fonte em cache, e qualquer output do bot — é contaminação do RAG, não apenas geração (24/04/2026)
- Termos técnicos vagos → substituir por linguagem prática e acessível
- Erros de concatenação detectáveis (palavras coladas sem espaço) → corrigir sempre
- "Duo/Trio" → REMOVER sempre (informação inexistente — hallucinação do modelo, não existe nos fontes RAG)
- "posso verificar para você" / "posso checar" → REMOVER (promessa operacional falsa — o bot não tem essa capacidade); substituir por "converse directamente com a equipe"
- Respostas que pedem "quer que eu faça isso?" no final → REMOVER quando pressupõe capacidade inexistente do bot
- Quando o bot não tem a informação → redicionar para "fale com a equipe" — nunca criar promessa falsa de verificação
- Tom: respostas devem ter calor humano, frases conversacionais ("de uma forma bem interessante", "é justo que você pergunte")
- **Padrão de qualidade para todas as Q&As: cada resposta deve levar o interessado mais perto do fecho (matrícula)** — usar gatilhos mentais e emocionais de forma natural, quebra de objeções empática, proximidade genuína. Nunca parecer que está a empurrar venda. Exemplo: "a gente não quer que você se sinta desamparado" é gatilho emocional correcto.
 Erro ortográfico recorrente: "interactionar" → corrigir para "interagir" sempre que aparecer
 Erro: "alumnus" (inglês) → corrigir para "ex-aluno" sempre que aparecer
 "livre acesso" → CORRIGIR para "livre formação" — "acesso" pode dar a entender "gratuito", o que é falso. O Método TEN usa "livre formação" para significar "sem pré-requisitos formais". Se vir "livre acesso" em qualquer resposta, substituir por "livre formação".
- **OBRIGATÓRIO: Pergunta reflexiva de fecho em TODAS as Q&As** — cada resposta deve terminar com uma pergunta pessoal e reflexiva que:
  - Faz o lead identificar-se com a transformação descrita
  - Move o lead emocionalmente para o desejo de se tornar um psicoterapeuta formado
  - É aberta e acolhedora, nunca forçada
  - Conecta a resposta ao contexto pessoal do lead
  - Exemplos de padrão: *"E aí, faz sentido pra você essa ideia de que a mente pode mudar — e que esse é o ponto de partida pra qualquer transformação real?"*, *"Você já reparou como isso se aplica à sua vida?"*, *"Isso te faz querer conhecer mais sobre como se tornar um terapeuta que ajuda pessoas assim?"*
  - Regras: usar "você" (não "tu"), ser natural e conversacional, evitar perguntas retóricas vazias

- **Perguntas de fecho são ferramentas de persuasão** — NÃO remover. Quando o SAC Bot gerar uma resposta com pergunta final ("Quer saber mais?" etc.), essa pergunta É o mecanismo de convencimento e deve ser mantida E melhorada com a pergunta reflexiva.

- **Respostas NÃO devem criar objeções.** Frases como "quem mais se beneficia são pessoas que já têm contacto com X" ou "pessoas que já têm algum contacto com o universo do cuidado humano" devem ser removidas e substituídas por "o método foi criado para funcionar para todos, independente do ponto de partida." Regra: nunca excluir ninguém do público-alvo dentro de uma resposta do RAG.

- **Actualização em batch de Q&As existentes:** quando for preciso adicionar perguntas reflexivas a Q&As já gravadas, apresentar todas num único batch ao Álvaro para aprovação antes de actualizar no RAG. Não actualizar sem aprovação (24/04/2026).

- **"Não é invasão de privacidade" — qualificação do lead:** Perguntas que pedem ao lead para partilhar a sua situação (ex: "Me conta: qual é a sua situação?", "O que te trouxe até aqui?") são perguntas de QUALIFICAÇÃO e devem ser MANTIDAS. Distinguir entre:
  - Invasivas: pedem dados pessoais sem valor claro para o lead ("qual é o seu CPF?", "quanto ganha?")
  - Qualificação/engajamento: pedem contexto para personalizar a resposta ("qual é a sua situação?", "o que te trouxe até aqui?") — estas DEVEM ser mantidas e são ferramentas de persuasão
  - Regra: se uma pergunta do lead faz sentido como qualificação dentro do contexto da resposta, manter e dar como exemplo no fecho (24/04/2026)

- **Padrão de workflow: após aprovação → INSERT → fetch next imediatamente:** Não perguntar "prossiga" ou "seguinte". Após o Álvaro aprovar: (1) INSERT na base, (2) fetch next question do SAC Bot, (3) apresentar análise. Eliminar intermediate steps (24/04/2026).

- **Reformulação de perguntas do documento:** Se uma pergunta do documento estiver confusa, ambígua ou desatualizada, REFORMULAR antes de submeter ao SAC Bot. Obter aprovação do Álvaro para a nova formulação antes de prosseguir. Exemplo: "O que o Método TEN tem que outras técnicas não têm?" → "O que diferencia o Método TEN das outras abordagens terapêuticas?" (24/04/2026).

- **Perguntas irrelevantes para o scope:** Se uma pergunta do documento é sobre biografia/experiência pessoal dos criadores e não tem valor de conversão para a formação (ex: "O Álvaro já aplicou o método nele mesmo?"), MARCAR como irrelevante e ELIMINAR da lista. Não criar Q&A sobre isso. Exemplo: Q81 foi eliminada porque era sobre a experiência pessoal do criador, não sobre a formação.

- **Aprovação com correcções:** Quando Álvaro aprova "com correcções", apresentar a versão corrigida para aprovação final antes de fazer o INSERT. Não fazer INSERT da versão provisória (24/04/2026).

- **"Aprovado" pode esconder contaminacao:** Quando Álvaro aprova uma resposta, se a versão proposta ainda tinha vestígios de contamination (ex: ">99,8%"), MOSTRAR a versão corrigida ao Álvaro ANTES de fazer o INSERT. "Aprovado" significa "aprovado para gravar" — se a versão aprovada tinha contamination, o INSERT não é feito até apresentar a versão limpa.

 "pro bono" = atendimentos totalmente gratuitos dentro da formação (para o paciente). Confirmado pelo Álvaro em 24/04/2026.

 Quando uma pergunta do documento tem resposta outdated (ex: "existem turmas?") mas a realidade mudou → redesenhar a Q&A com a nova realidade e apresentar ao Álvaro para aprovação antes de gravar. Não guardar resposta incorrecta apenas para seguir a lista.
 ID do approved_qa NÃO corresponde ao número da pergunta do documento — confirmar ID máximo antes de gravar
- Quando o Álvaro fornece conteúdo directamente (ex: via ficheiro .txt/.rtf), usar esse conteúdo como source of truth em vez da resposta do SAC Bot — especialmente quando o bot tem informação incompleta ou hallucina

## ⚠️ Cache Virtual Hermes — Ficheiros Inacessíveis

Os ficheiros listados no directório virtual `.hermes/cache/documents/` (ex: `doc_*.txt`, `doc_*.md`) **parecem existir no `ls` mas NÃO são acessíveis** por nenhum método de leitura — shell commands (`cat`, `head`, `stat`), Python (`open()`), ou tools nativas retornam "ficheiro não encontrado".

**Causa:** São entradas de cache interno do Hermes, não ficheiros regulares no filesystem.

**Workaround:**
1. Pedir ao utilizador para partilhar o conteúdo directamente na conversa (Telegram/CLI)
2. Ou pedir para gravar num path已知 (ex: `~/.hermes/sac_agent/100_perguntas.txt`)
3. Documentar sempre o workaround na memória e no cérebro GitHub

**Como detectar:** `ls` mostra o ficheiro mas qualquer comando de leitura falha.

## ⚠️ Corrupção de Resposta do Webhook (tempo >15s)

Quando o SAC Bot demora mais de ~15 segundos para responder, o output do `curl` no terminal pode ser **truncado ou mostrar uma resposta completamente diferente** da resposta real no JSON. Appearece como "timeout" ou resposta com conteúdo estranho.

**Como verificar:** Sempre extrair a resposta com `python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('resposta'))"` OU usar `repr()` para ver o JSON raw — nunca confiar no output truncado do terminal.

**Exemplo de output corrupto:**
```
# Terminal mostra (FALSO):
"Que pergunta interessante! No Método TEN..."
# JSON real era (CERTO):
"No Método TEN, a relação entre terapeuta e cliente..."
```

**Workaround:** Usar sempre `--max-time 30` no curl e pipe para `python3 -c "import sys,json; d=json.load(sys.stdin); print(d['resposta'])"` para extrair o campo `resposta` do JSON directamente.

**403 Forbidden:** O webhook pode retornar 403 Forbidden quando chamado via Python `urllib` mas funcionar com `curl`. Usar SEMPRE `curl` no terminal em vez de código Python para chamadas ao webhook.

## ⚠️ Duplicados de ID — Prevenir Sempre

Antes de fazer INSERT, verificar sempre o ID máximo actual:

```python
cur.execute("SELECT MAX(id) FROM approved_qa")
max_id = cur.fetchone()[0]
print(f"Current max ID: {max_id}")
```

Se houver duplicados, apagar antes de continuar:
```python
# Apagar duplicado (ex: ID 69)
cur.execute("DELETE FROM approved_qa WHERE id = 69")
```

**Causa de duplicados:** Processar perguntas em paralelo ou em múltiplas sessões sem verificar o estado da base.

## ⚠️ Regra de Âmbito: FORMAÇÃO vs. EXPERIÊNCIA EM TERAPIA

**100% das 100 perguntas devem ser sobre a FORMAÇÃO DE PSICOTERAPEUTAS — converter leads em alunos. NENHUMA pergunta deve ser sobre a experiência do cliente em terapia.**

### Como distinguir

| Tipo | Pergunta | Exemplo de reformulação |
|------|----------|------------------------|
| ❌ Experiência do cliente | "E se eu não sentir nada na primeira sessão?" | Reformular para o olhar da formação |
| ✅ Formação | "A formação oferece suporte se eu tiver dificuldades?" | ✅ Correcto |
| ❌ Experiência do cliente | "Quantas sessões são necessárias?" | Cliente pergunta ao terapeuta |
| ❌ Experiência do cliente | "O que eu preciso sentir para saber que funciona?" |Cliente pergunta ao terapeuta |
| ✅ Formação | "Como é a relação terapeuta-cliente no TEN?" | O lead quer saber como vai ser como terapeuta |

### Sinais de alerta
- A pergunta começa com "e se eu..." (cliente vulnerável)
- Pergunta sobre resultados/sentimentos do cliente
- "Como cliente, posso..."
- Perguntas que pressupõem que o lead já é cliente

### O que fazer
1. Identificar se a pergunta é sobre formação ou sobre terapia
2. Se for sobre terapia → reformular para o ângulo da formação
3. Apresentar a reformulação ao Álvaro para aprovação ANTES de submeter ao SAC Bot
4. Opções de reformulação: dar 3-4 alternativas e pedir para escolher

### Exemplo real (24/04/2026)
- **Original (ERRADO):** "E se eu não sentir nada na primeira sessão?" → sobre experiência do cliente
- **Reformulação (CERTO - Opção C):** "A formação oferece suporte se eu tiver dificuldades com o conteúdo?" → sobre a formação

## ⚠️ Números e Dados — Precisão Absoluta

**Regra de ferro:** NUNCA usar um número não verificado, mesmo em proposta ou draft.

- Se não tenho o dado confirmado → dizer "não tenho esse dado" ou "não posso confirmar"
- NUNCA aproximar ("cerca de 200 horas") quando o número real é diferente (390 horas)
- Sempre verificar números críticos nos fontes antes de usar
- Se o Álvaro me corrigir num número → auditoria IMEDIATA de toda a base para o mesmo erro

**Quando o Álvaro corrigir um número:**
1. Não argumentar — aceitar a correcção
2. Auditar IMMEDIATAMENTE toda a base (approved_qa) para o mesmo erro
3. Verificar também os documentos fonte em `~/.hermes/cache/documents/*.md`
4. Corrigir em ambas as camadas (base + fontes)
5. Push para o cérebro GitHub

**Auditar números na base:**
```python
import sqlite3
conn = sqlite3.connect('/home/alvarobiano/.hermes/sac_agent/sac_leads.db')
cur = conn.cursor()
cur.execute("SELECT id, pergunta, resposta FROM approved_qa WHERE resposta LIKE '%200%' OR resposta LIKE '%99%'")
for row in cur.fetchall():
    print(f"ID {row[0]}: {row[2][:200]}")
conn.close()
```

### Caso real (24/04/2026)
- Erro: propus "cerca de 200 horas" → Álvaro corrigiu: é ~390 horas
- Auditoria feita: IDs 9 e 45 já tinham "390 horas" (correcto). "200" só estava na proposta nunca foi gravada.
- Lição: se não sei o número exacto, não invento. Perguntar ao Álvaro ou verificar no documento.

## ⚠️ Auditoria de Âmbito — Quando Fazer

Quando o Álvaro fizer uma correcção de scope:
1. **Parar imediatamente** o trabalho de criação
2. **Auditar TODAS as Q&As já criadas** no batch actual
3. **Listar** todas as que estão no scope errado
4. **Apresentar** ao Álvaro com proposta de reformulação (3-4 opções)
5. **Só depois** de approved, gravar as correcções e retomar

**Q&As já redesenhadas (24/04/2026):**
| ID | Antes (terapia) | Depois (formação) |
|----|-----------------|-------------------|
| 67 | "O método serve para coaches e mentores?" | "Que tipo de profissional se beneficia mais?" |
| 70 | "O cliente precisa fazer lição de casa?" | "A formação exige dedicação prática fora das aulas?" |
| 73 | "A primeira sessão traz resultado?" | "Em quanto tempo posso ver primeiros resultados?" |
| 74 | "Quantas sessões são necessárias?" | "Qual é a duração e estrutura da formação?" |
| 75 | "O que preciso sentir para saber que funciona?" | "Como sei que estou a acompanhar bem a formação?" |

**Não continuar criando novas Q&As** enquanto Q&As existentes estiverem com scope errado.

## ⚠️ ARQUITECTURA CRÍTICA: Q&A Approved + RAG = COMBINADAS, não Fallback

**Lição aprendida em 25/04/2026 (com dor):** O sistema de approved_qa existia e estava bem feito, mas era **efectivamente inútil** porque a arquitectura usava Fallback (approved_qa **OU** LanceDB) — se approved_qa retornasse resultados, LanceDB era ignorado completamente. E o threshold Jaccard 0.45 era demasiado alto.

**Problema real:**
- "Como posso me matricular?" (pergunta do lead) vs "Como faço pra me matricular?" (Q&A approved) → Jaccard < 0.45 → approved_qa era ignorada → bot usava só RAG LanceDB → resposta com membro da equipe (contaminada no chunk)

**Arquitectura correcta implementada:**
1. `rag_sac()` busca SEMPRE ambas: approved_qa (Jaccard, top_k=5) E LanceDB (vector, top_k=5)
2. Nova função `llm_generate_combined()` recebe ambos e passa tudo ao LLM junto
3. Q&A approved = base preferida, chunks LanceDB = complemento
4. O LLM decide o que usar — nunca fallback

**Threshold Jaccard:** 0.20 (não 0.45) — 20% de overlap é suficiente para variações linguísticas ("como posso" vs "como faço pra")

**Como verificar se está a funcionar:** Ler o log `~/.hermes/logs/sac_agent.log` — deve mostrar `"1 Q&As + 5 chunks"` (não apenas `"5 chunks"`)

```
# Log CORRECTO (ambas fontes):
[QA] 1 Q&As encontradas para: Como faço pra me matricular?
RAG completo em 9.49s — 1 Q&As + 5 chunks

# Log ERRADO (só RAG, approved_qa ignorada):
RAG completo em 14.97s — 5 chunks
```

**Se vir só chunks sem Q&A:** threshold Jaccard está alto demais ou arquitectura está em modo fallback.

## Hallucinations do SAC Bot — padrões identificados
O SAC Bot pode inventar informação que NÃO existe no RAG. Quando detectar:
1. Verificar se a informação existe em `approved_qa` (SELECT ... LIKE '%termo%')
2. Verificar se existe nos documentos fonte (`~/.hermes/cache/documents/`)
3. Se não existe em nenhum lugar → é hallucinação → **remover da resposta e gravar correctamente**
4. Se existe num documento mas está desatualizada → corrigir fonte primeiro

### Hallucinations/Contaminações conhecidas:
- **Duo/Trio como planos de pagamento**: O SAC Bot inventou "planos Duo ou Trio" que NÃO existem em nenhum documento indexado. Remover sempre e corrigir.
- **">99,8% de eficácia"**: Número não verificado que aparece em `doc_alvarobiano_site_completo.md` (5 ocorrências). O bot gera-o a partir do RAG. Remover sempre — não existe prova desta estatística. Usar "taxa de eficácia elevada" ou "resultados consistentes".
- **"Nada é repassado para terceiros"**: Frase que EXISTE no documento fonte `doc_5a0127413e50_maryanne-braga-alvaro-biano-metodo-ten.md` — o bot usa-a do RAG, não é alucinação pura. Há que limpar tanto o fonte (.md) quanto a approved_qa.
- **"membro da equipe" como nome de contacto**: O bot tinha 10+ referências a "membro da equipe" no código (`sac_persuasao.py`) e 3 Q&As approved com esse nome. Todas substituídas por "um membro da equipe" (25/04/2026). Se "membro da equipe" aparecer numa resposta, significa que (a) o replace no código ainda existe, (b) a approved_qa ainda tem o nome, ou (c) o chunk RAG tem o nome e a Q&A approved não foi encontrada (threshold alto ou arquitectura fallback). Corrigir: substituir no código, na base, e no documento fonte se existir lá.

### Substituição em batch — scope completo (25/04/2026)

Quando for preciso substituir um nome/termo em TODO o sistema:

| Camada | Local | Comandos |
|--------|-------|---------|
| SQLite: conversas | `sac_leads.db` | `REPLACE(mensagem, 'velho', 'novo')` |
| SQLite: approved_qa | `sac_leads.db` | `REPLACE(pergunta\|resposta, ...)` |
| SQLite: Hermes sessions | `hermes_sessions.db` | `UPDATE events SET content\|details = REPLACE(...)` |
| SQLite: state | `state.db` | `UPDATE messages SET content = REPLACE(...)` |
| Ficheiros de sessão | `~/.hermes/sessions/**/*.json` | `grep -rl "termo" \| xargs sed -i 's/termo/novo/g'` |
| Skills | `~/.hermes/skills/**/*.md` | Python batch replace |
| Memories | `~/.hermes/memories/*.md` | Python batch replace |
| Cerebro GitHub | `~/bianinho-cerebro/` | git add + commit + push |

**Não alterar:** Mensagens do utilizador nos logs (são dele). Referências documentais no cérebro (legítimas como registo histórico).

**Verificação final:**
```bash
# Confirmar que não há restos
grep -rn "Maria Helena" ~/.hermes/sac_agent/
grep -rn "Maria Helena" ~/.hermes/skills/
```
- **"200 horas"**: O número correcto é ~390 horas. Se aparecer "200 horas" numa resposta, é dado errado — usar o número do Álvaro ou do documento verificado.
- Nota: Os matches de "duo/trio" no LanceDB (328 linhas na tabela `chunks`) são de livros externos (ex:现金流, 巴比伦) — NUNCA de documentos do Método TEN. Verificar sempre a `source` antes de assumir que um chunk veio do RAG do método.
