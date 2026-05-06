---
name: sac-bot-persuasion-flow
description: Complete SAC Bot with lead capture, RAG, star rating, dynamic questions, persuasion frameworks (PAS/AIDA), compact bottom-action UI.
---

# SAC Bot Persuasion Flow — Método TEN

## Context
Built for Álvaro's Método TEN SAC Bot. Portuguese-Brazilian only. No English, no Latin characters, no invented information.

## Architecture

### Files
- `~/.hermes/sac_agent/sac_agent.py` — Flask webhook (port 5123), RAG integration, persuasion injection
- `~/.hermes/sac_agent/sac_persuasao.py` — Persuasion module: PAS, AIDA, objection handling, star rating, suggested questions
- `~/.hermes/sac_agent/sac_db.py` — SQLite: leads, conversations, approved_qa, ratings
- `~/.hermes/sac_agent/templates/index.html` — Dark theme chat UI
- `~/.hermes/sac_agent/sac_leads.db` — SQLite database

### Key Rules (in system prompt)
1. NEVER use English words
2. NEVER invent information — only use RAG content
3. "psicoterapia" is NOT restricted — only "psicólogo" (CRP) is
4. "Marielena" → corrected to "membro da equipe" automatically
5. First person singular prohibited ("eu", "meu", "comigo")
6. Generic team references only: "a equipe", "a gente", "nós"

## Persuasion Frameworks

### PAS (Problem-Agitate-Solution)
Used in "descoberta" phase. Names problem → agitates pain → positions method.

### AIDA
Used in "interesse" phase. Attention → Interest → Desire → Action.

### Objection Handling
7 objection types detected by keyword matching:
- `nao_tenho_dinheiro`, `vou_pensar`, `nao_tenho_tempo`
- `ja_fiz_outro_curso`, `nao_sei_se_consigo`
- `medo_de_nao_conseguir_apos`, `valor_caro`

### Lead Phases
- **descoberta** (score < 20): PAS framework
- **qualificacao** (score 20-50): Social proof
- **interesse** (score 50-75): Differential + social proof
- **decisao** (score > 75): Urgency + CTA

### Score Calculation
```
score = interacoes*8 (max 40) + formacao(+15) + trabalho(+15) + medo(+10) + dor(+10) + metodo_pergunta(+10)
CTA shown when: score >= 70 OR interacoes >= 7
```

## Star Rating System

### DB Schema
```sql
ALTER TABLE leads ADD COLUMN avaliacao_nota INTEGER DEFAULT NULL;
ALTER TABLE leads ADD COLUMN avaliado_em TEXT DEFAULT NULL;
CREATE TABLE avaliacoes (id, lead_id, nota 1-5, comentario, criado_em);
```

### Rules
- Minimum 2 interactions before showing
- Never rated → show
- Rated < 4 stars → show again
- Rated >= 4 stars → hide

### UI
- Side-by-side with WhatsApp CTA in `#bottom-actions` container (flex row)
- Click star → immediate save + "Obrigado!" message

## Dynamic Suggested Questions

### Questions the LEAD clicks to ask the BOT (NOT bot asking lead)

**Critical rule:** Suggested questions are things the LEAD wants to know — they appear as clickable options
after the bot's response. When clicked, the bot answers that question. They are NEVER the bot interrogating
the lead.

**Anti-pattern (do not generate):**
- ❌ *"Álvaro, me conta: o que te fez se interessar pelo Método TEN agora?"*
- ❌ *"Você já conhece um pouco sobre como funciona o método?"*
- ❌ Questions addressed to the lead or using the lead's name

**Correct pattern:**
- ✅ *"Como funciona a formação em Método TEN?"*
- ✅ *"Quanto custa?"*
- ✅ *"Preciso ter experiência prévia?"*
- ✅ *"A formação é online ou presencial?"*

**Rule 7 (critical):** Questions must NEVER use "você", the lead's name, or any second-person address.
They are questions the lead has about the method — framed from the lead's perspective.

### PERGUNTAS_SOCRATICAS dict per phase — questions the LEAD would ask the BOT
`PERGUNTAS_SOCRATICAS` dict per phase — questions the LEAD would ask the BOT:
- **descoberta**: Como funciona?, Preciso ter experiência?, Quanto tempo dura?, O que vou aprender?
- **qualificacao**: Quanto custa?, Suporte?, Posso atender durante?, Online ou presencial?
- **interesse**: Como funciona matrícula?, Condições de pagamento?, Ajudam com marketing?, Posso falar com alguém antes de decidir?
- **decisao**: Como faço pra garantir minha vaga?, Posso falar com a Maria Helena antes de decidir?, Quando começa a próxima turma?, Qual é o investimento e como parcelar?

### PERGUNTAS_DECISAO — Arma de Conversão
**Regra inviolável:** Na fase "decisão", usar APENAS `PERGUNTAS_DECISAO`:
```python
PERGUNTAS_DECISAO = [
    "Como faço pra garantir minha vaga ainda hoje?",
    "Posso falar com a equipe antes de eu decidir?",
    "Quando começa a próxima turma?",
    "Tem condição de pagamento facilitada?",
    "Se eu começar agora, quanto tempo leva pra estar atendendo?",
]
```
- Estas perguntas são a **força de conversão** — aparecem apenas quando lead está em decisão
- `get_perguntas_sugeridas(fase, limite=4)` verifica: se `fase=="decisao"` → usa `PERGUNTAS_DECISAO`
- Embaralhadas com `random.shuffle()` para não parecer repetitivo

### Implementation
- `get_perguntas_sugeridas(fase, limite=4)` returns shuffled questions from correct list
- Rendered as buttons with `.perg-sug` class (cyan pills)
- Click sends question automatically

### Typewriter Callback — Timing das Ações
**Problema:** Bottom-actions apareciam ANTES do efeito typewriter terminar → glitch visual.
**Solução:** `typewriterHTML(el, html)` → `typewriterHTML(el, html, onDone)` com callback.

```javascript
function typewriterHTML(el, html, onDone) {
    // ... typewriter logic ...
    function tick() {
        if (index >= html.length) {
            el.innerHTML = html;
            if (onDone) onDone();  // ← ações só aqui, após efeito terminar
            return;
        }
        // ... chars progressivos ...
    }
    tick();
}
```

**Fluxo:**
1. Bot responde → `typewriterHTML` começa a revelar texto
2. Após último caractere → `onDone()` disparado
3. Callback mostra: `#bottom-actions` + `#perguntas-sugeridas`
4. Experiência: mensagem aparece → efeito termina → botões surgem

**Regras do callback:**
- `mostrarTudo = mostrar_cta || mostrar_avaliacao || temPerguntas`
- Se houver perguntas sugeridas → `bottom-actions` visível mesmo sem CTA/avaliação
- Isto é **regra inviolável**: perguntas aparecem sempre a partir da 3ª troca

## Bottom Actions Layout
```
#bottom-actions (flex row, gap 8px, margin 10px 16px 0)
  ├── #whatsapp-cta (flex:1, green gradient)
  └── #avaliacao-box (flex:1, stars + label)
```
Both elements share the row to save vertical chat space.

## API Endpoints
- `POST /webhook/sac` — main chat endpoint
- `POST /webhook/sac/init` — identify/create lead
- `POST /webhook/sac/avaliar` — register star rating

## Running
```bash
systemctl --user restart sac-agent.service
```

## Critical Mistakes Made (learned)
1. Suggested questions were initially questions the BOT would ask the USER — must be questions the USER asks the BOT
2. "psicoterapia" was incorrectly stated as a restricted term — only "psicólogo" is
3. English word appeared in response — strictly prohibited
4. Vertical stacking of CTA + stars wasted chat space — use flex row side-by-side
5. **Typewriter callback missing**: bottom-actions appeared BEFORE typewriter finished → use `onDone` callback to defer
6. **Decisão phase questions weak**: generic questions like "Como me matricular?" don't convert → use `PERGUNTAS_DECISAO` with urgency + social proof
