---
name: sac-qa-approved
description: 30 Q&As aprovadas do SAC Bot do Método TEN (23/04/2026). Base de conhecimento validada para leads do SAC Agent.
---

# SAC Bot — Q&As Aprovadas

## 30 Q&As validadas e aprovadas (23/04/2026)

| ID | Tema | Pergunta |
|----|------|----------|
| 1 | O que é o Método TEN | O que é o Método TEN? |
| 2 | Origem e história | Qual é a origem e história do Método TEN? |
| 3 | Significado de TEN | O que significa TEN? |
| 4 | Diferenciais | Em que o Método TEN se diferencia de outras abordagens terapêuticas? |
| 5 | Para quem é | Para quem é indicado o Método TEN? |
| 6 | Para quem é | O Método TEN serve para qualquer tipo de problema psicológico? |
| 7 | Para quem é | Pessoas sem formação em psicologia podem fazer a formação? |
| 8 | Estrutura e formato | A formação é 100% online ou tem encontros presenciais? |
| 9 | Estrutura e formato | Qual é a carga horária total da formação? |
| 10 | Certificação | A formação oferece certificado? Qual tipo? |
| 11 | Certificação | O certificado de extensão universitária tem validade no mercado de trabalho? |
| 12 | Certificação | Quanto tempo leva para receber o certificado após concluir a formação? |
| 13 | Estrutura e formato | Como funciona a avaliação durante a formação? |
| 14 | Pagamento | Quais são as formas de pagamento disponíveis? |
| 15 | Pagamento | Quanto custa a formação? Qual o valor? |
| 16 | Garantia | Qual é a garantia oferecida? |
| 17 | Suporte | A formação oferece suporte? Como funciona? |
| 18 | Carreira | Posso trabalhar como psicoterapeuta depois da formação? |
| 19 | Estrutura e formato | E se eu não conseguir acompanhar o ritmo da formação? |
| 20 | Matrícula | Como funciona o processo de matrícula? |
| 21 | Estrutura e formato | Posso fazer download das aulas? |
| 22 | Certificação | A formação é reconhecida fora do Brasil? |
| 23 | Carreira | Quantos países estão ativos na formação? |
| 24 | Estrutura e formato | Tem material de apoio? |
| 25 | Para quem é | O Método TEN funciona para quem não tem experiência nenhuma em terapia? |
| 26 | O que é o Método TEN | O Método TEN é baseado em qual abordagem terapêutica? |
| 27 | Carreira | Como o Método TEN ajuda na prática clínica do dia a dia? |
| 28 | Estrutura e formato | A formação é atualizada com novos conteúdos? |
| 29 | O que é o Método TEN | Quem são os criadores do Método TEN? |

## Dados técnicos

- **DB**: `~/.hermes/sac_agent/sac_leads.db` → tabela `approved_qa`
- **SAC Agent**: `~/.hermes/sac_agent/sac_agent.py` (porta 5123)
- **Retry**: 10 tentativas nas chamadas MiniMax (`llm_generate` e `llm_generate_qa`)
- **RAG**: LanceDB em `~/KnowledgeBase/knowledge_db/metodoten.lance`

## Termos e informações proibidos

- **Preço**: NUNCA fornecer. Redireccionar para `www.alvarobiano.com.br`
- **"mentoria"** → usar **"interações directas"**
- **"pace"** → usar **"tempo"**
- **"quiz" / "múltipla escolha" / "nota"** → usar **"autoavaliação sem nota"**
- **"atendimento supervisionado a pacientes reais"** → usar **"atendimentos pro bono"**
- Anglcismos banidos: `pace`, `feedback`, `familiarity`, `upgrade`, `knowing`, `helpful`, `thank you`

## Modelo de atendimento pro bono

Os alunos fazem atendimentos gratuitos para adquirir experiência prática. Depois de cada atendimento, podem trazer as dúvidas para as aulas de acompanhamento, onde os professores respondem e sanam as questões juntos.

## Avaliação

Contínua e prática. Não há quizzes, não há nota. O foco é a autoavaliação e a participação nas dinâmicas.

## Nomes corretos

- "Maryanne Braga e Álvaro Biano" — usar primeiro nome OK em contexto informal
- Instituição: "Faculdade FEx" (não só "FEx")

## Regra de consistência

Ao corrigir uma Q&A:
1. Actualizar `approved_qa` na base SQLite
2. Limpar a mesma informação da fonte (`~/.hermes/cache/documents/doc_alvarobiano_site_completo.md`)
3. Deletar o chunk do LanceDB pelo `chunk_hash`
4. Verificar Q&As relacionadas que podem ter a mesma info errada
