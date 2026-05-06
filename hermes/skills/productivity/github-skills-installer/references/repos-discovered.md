# Repositórios GitHub Skills Descobertos — Bianinho OS

## Como usar esta referência

Verificar sempre contagem de skills após instalação:
```bash
ls ~/.aionui-config/skills/ | wc -l
```
Antes: ~153 (skills AionUI marketplace)  
Depois de todos os repos: ~2,362

---

## Antigravity Awesome Skills ⭐36k

**O mais importante.** 1,445+ skills cobrando tudo: dev, security, product, marketing, research.

```bash
npx antigravity-awesome-skills --path ~/.aionui-config/skills
```
- Pode demorar ~1 min
- Executar em background: `background=true` na chamada terminal
- Enquanto corre, clonar os outros repos em paralelo
- Formato: `SKILL.md` padrão agentskills.io — 100% compatível com AionUI

Categorias disponíveis: development, backend, security, infrastructure, product, marketing, data, testing, debugging, design, writing, research, analytics

---

## addyosmani/agent-skills ⭐28k

Ciclo de desenvolvimento completo codificado como skills:
`spec → plan → build → test → review → code-simplify → ship`

Skills: api-and-interface-design, frontend-ui-engineering, test-driven-development, security-and-hardening, debugging-and-error-recovery, ci-cd-and-automation, documentation-and-adrs, git-workflow-and-versioning, planning-and-task-breakdown, incremental-implementation, code-review-and-quality, performance-optimization, shipping-and-launch, deprecation-and-migration, source-driven-development, spec-driven-development, context-engineering, idea-refine

---

## Orchestra AI Research SKILLs ⭐7.8k

90 skills para pesquisa AI autónoma — do conceito ao paper.

Estrutura: directórios numerados (`01-model-architecture/`, `06-post-training/`, etc.)
Não tem `skills/` à raiz — cada categoria é um subdireitório.

Categorias: Autoresearch, Model Architecture, Tokenization, Fine-Tuning, Mechanistic Interpretability, Data Processing, Post-Training (RLHF/DPO/GRPO), Safety & Alignment, Distributed Training, Infrastructure (Modal, SkyPilot, Lambda), Optimization (Flash Attention, bitsandbytes, AWQ, GPTQ, GGUF), Evaluation, Inference Serving (vLLM, TensorRT-LLM, llama.cpp), MLOps (W&B, MLflow), Agents (LangChain, LlamaIndex, CrewAI), RAG (Chroma, FAISS, Pinecone, Qdrant), Prompt Engineering (DSPy, Instructor, Guidance, Outlines), Observability (LangSmith, Phoenix), Multimodal (CLIP, Whisper, LLaVA, Stable Diffusion, SAM), Emerging Techniques, ML Paper Writing

**Instalação correcta:**
```bash
for dir in /tmp/ai-research-skills/*/; do
    skill_name=$(basename "$dir" | sed 's/^[0-9]*-//')
    cp -r "$dir" ~/.aionui-config/skills/"$skill_name"
done
```

---

## Anthropic Cybersecurity Skills ⭐6k

754 structured cybersecurity skills. Mapeadas para 5 frameworks:
- MITRE ATT&CK (14 tactics, 200+ techniques)
- NIST CSF 2.0 (6 functions, 22 categories)
- MITRE ATLAS (16 tactics, 84 techniques)
- MITRE D3FEND (7 categories, 267 techniques)
- NIST AI RMF

26 domínios de segurança. Compatível com: Claude Code, GitHub Copilot, Codex CLI, Cursor, Gemini CLI + 20+ plataformas.

---

## Last30days Skill ⭐24k

Agente de pesquisa multi-plataforma — Reddit, HN, Polymarket, GitHub, X, YouTube, TikTok.

README menciona suporte explícito para Hermes:
```bash
# No Hermes: sync.sh auto-deploys
# Ou copiar manualmente para ~/.hermes/skills/research/last30days/
```

---

## Taste Skill ⭐15k

Anti-slop frontend skills. Melhora outputs de design/UI:
- Layout premium, tipografia, motion, spacing
- Funciona com Codex, Cursor, Claude Code
- Página: https://tasteskill.dev

---

## Marketing Skills ⭐26k

Skills CRO, copywriting, SEO, analytics, growth engineering.

Contém também: 51 CLI tools em `tools/clis/` (Node.js zero-dependency) + integração Composio para HubSpot, Salesforce, Meta Ads, LinkedIn Ads, Google Sheets, Slack.

---

## Pitfall: Estruturas de Repos Variam

**Sempre verificar a estrutura antes de copiar:**
```bash
ls /tmp/repo-name/   # ver se tem skills/ à raiz
find /tmp/repo-name -name "SKILL.md" | head -3   # encontrar SKILL.md
```

Padrões comuns:
- `repo/skills/` → copy directamente
- `repo/01-category/` (numerado) → iterar + sed rename
- `repo/skill-name/` → copiar repo inteiro
