---
name: end-of-session-trust-protocol
description: Protocolo de fim de sessão para garantir que tudo é gravado no cérebro GitHub — responde à desconfiança do Álvaro na memória.
---

# End-of-Session Trust Protocol

**Quando usar:** No final de qualquer sessão significativa com o Álvaro, especialmente quando ele pede para guardar algo, quando há decisões importantes, ou quando o sistema faz alterações.

**NOTA:** A memória HOT tem limite de 2.200 caracteres. Não é infinita. Entries redundantes ou muito longas precisam de ser removidas antes de adicionar novas.

## Passo 1 — Verificar espaço na memória HOT
```
memory (tool) → olhar "usage"
```
Se >90%: fazer espaço primeiro (remover entries redundantes ou muito longas).

## Passo 2 — Actualizar memória HOT
- Decisions-chave da sessão
- Alterações de estado (novos serviços, problemas resolvidos, etc.)
- Qualquer coisa que o Álvaro pediu para lembrar

## Passo 3 — Actualizar cérebro GitHub
```
cd ~/bianinho-cerebro
git add -A
git commit -m "feat: [resumo curto da sessão]"
git push origin main
```
Se não há changes: fazer `git status` para confirmar.

**Exemplos de commit messages:**
- `feat: SAC Bot HTML format + decisões 24/04`
- `feat: Método TEN Q&A IDs 1-30 aprovadas`
- `fix: cloudflared tunnel restaurado`

## Passo 4 — Verificar push
Confirmar que o push foi bem sucedido (output contém `main -> main`).

## Erros comuns
- **"Memory at 99%"**: Não conseguir adicionar notas → fazer espaço primeiro
- **"Nothing to commit"**: Confirma com `git status` se realmente não há changes
- **Push falha por auth**: `gh auth status` → fazer login se necessário

## Para recover sessões passadas
Se precisares de reconstruir o que aconteceu numa sessão anterior:
```
ls -lt ~/.hermes/sessions/compressed/ | head -10
```
Ler o ficheiro `.json` da sessão (são JSON com transcripts + facts).

---

**Motivação:** Álvaro não confiava na memória. Precisava de provas concretas de que tudo era guardado. Este protocolo garante que no final de cada sessão significativa há prova tangível (commit no GitHub) de que o trabalho foi gravado.
