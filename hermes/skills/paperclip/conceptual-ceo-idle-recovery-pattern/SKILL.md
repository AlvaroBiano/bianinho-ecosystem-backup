---
name: conceptual-ceo-idle-recovery-pattern
description: Padrão conceitual para recuperar agent CEO idle em sistemas de orquestração AI
category: conceptual
tags:
  - pattern
  - recovery
  - orchestration
  - conceptual
---

# conceptual-ceo-idle-recovery-pattern

## Visão geral
Padrão conceitual para diagnosticar e resolver situações onde um agent CEO/orquestrador principal está idle (inativo) em sistemas de orquestração AI.

## Contexto do padrão
Em sistemas onde um agent CEO/orquestrador coordena outros agents, é comum encontrar situações onde:
1. O CEO completou work documental mas não work substantivo
2. Tasks anteriores foram marcadas como concluídas prematuramente
3. Não há tasks ativas atribuídas ao CEO
4. O sistema está em estado de "stall" onde documentação existe mas implementação não ocorreu

## Sintomas do padrão

### Sintoma 1: Completeness Illusion
- Documentação/planos existem e estão completos
- Tasks documentais foram marcadas como Done
- Mas work substantivo (criação de agents, configuração de sistemas) não ocorreu

### Sintoma 2: Assignment Gap
- CEO não tem tasks ativas atribuídas
- Sistema mostra CEO como "idle" ou "waiting"
- Não há trigger claro para próxima ação

### Sintoma 3: Phase Misalignment
- Fase de planejamento/documentação foi tratada como "task completa"
- Fase de implementação não foi iniciada ou não tem task dedicada
- Gap entre documentação e execução

## Estrutura do padrão de recuperação

### Princípio 1: Phase Separation
**Problema**: Documentação e implementação tratadas como uma única phase.

**Solução**: Tratar como fases separadas com artifacts separados:
- **Phase 1**: Documentação/planejamento (cria planos, define estratégia)
- **Phase 2**: Implementação/execução (cria sistemas, configura agents)

**Regra**: Cada phase deve ter seu próprio tracking item (issue, task, etc.)

### Princípio 2: Context Preservation
**Problema**: Nova task criada sem contexto da work anterior.

**Solução**: Nova task deve incluir:
- Referência à work documental anterior
- Contexto de por que implementação é necessária agora
- Clear linkage entre documentação e implementação

### Princípio 3: Infrastructure Precedence
**Problema**: CEO tenta executar work sem infrastructure necessária.

**Solução**: Verificar e criar infrastructure necessária antes de atribuir work substantiva:
- Memory structures (se aplicável)
- Configuration consistency
- Access permissions
- Dependencies

### Princípio 4: Explicit Activation
**Problema**: CEO idle esperando por trigger automático que não ocorre.

**Solução**: Trigger manual explícito para iniciar próxima phase:
- Manual heartbeat/activation
- Explicit assignment
- Status change trigger

## Fluxo de aplicação do padrão

### Passo 1: Diagnosticar phase completion
- Qual phase foi completada? (documentação vs. implementação)
- O que foi realmente realizado vs. o que foi planejado?
- Há gap entre documentação e implementação?

### Passo 2: Criar nova task para próxima phase
**Não** reabrir task antiga se:
- Ela foi marcada como completa para uma phase específica
- Nova phase tem work substantivamente diferente
- Há risco de confusion no tracking

**Em vez disso**, criar nova task com:
- Título que descreve ação concreta da nova phase
- Prioridade apropriada (geralmente alta para implementação)
- Atribuição clara ao CEO/orquestrador
- Contexto que referencia work documental anterior

### Passo 3: Estruturar task description
**Estrutura ideal**:
```
**Objective**: [Resultado concreto e mensurável da phase de implementação]

**Context**: 
- Previous phase: [Referência à phase documental anterior]
- Current status: [Status atual do sistema]
- Why now: [Por que implementação é necessária agora]

**Implementation Tasks**:
1. [Task concreta de implementação 1]
2. [Task concreta de implementação 2]
3. [Task concreta de implementação 3]

**Success Criteria**:
- [Critério mensurável 1 - focado em implementação]
- [Critério mensurável 2 - focado em outcome]
- [Critério mensurável 3 - focado em operação]
```

### Passo 4: Preparar infrastructure
Antes de ativar CEO para nova task:
1. Verificar memory structures (se aplicável ao sistema)
2. Verificar consistency de configuration
3. Verificar dependencies
4. Criar missing infrastructure necessária

### Passo 5: Ativação explícita
**Em Paperclip**:
1. Aceder à UI em `http://localhost:3100/BRA/agents/ceo`
2. Clicar no botão **"Run Heartbeat"** (não "Pause")
3. Aguardar ~10s e verificar se o CEO passa a "active"
4. Confirmar que goals estão a ser processados via `/api/companies/{id}/dashboard`

**Via API** (alternativa):
```bash
# Ver estado actual dos agents
curl -s "http://localhost:3100/api/companies/{companyId}/agents"

# Dashboard mostra tasks em progresso
curl -s "http://localhost:3100/api/companies/{companyId}/dashboard"
```

**Verificação**:
- CEO status muda de `idle` → `active` (via heartbeat trigger)
- Sub-agents começam a receber tasks atribuídas
- Goals mudam de `planned` → `in_progress`

### Notas sobre Paperclip
- **UI**: `http://localhost:3100/BRA` (porta 3100 em `local_trusted`)
- **Empresa ID**: encontrado no URL após login ou via API `/api/companies`
- **Agents**: CEO, Content Agent, Product Agent, Social Agent
- **CEO role**: ORQUESTRADOR - delega, não executa trabalho individual
- **Heartbeat interval**: 300s (5 min) - pode ser mais curto para maior reactividade
- **Trigger**: "Run Heartbeat" força wake-up imediato independent do interval

## Variações do padrão

### Variação A: Multi-agent Activation
**Cenário**: CEO precisa criar/ativar múltiplos agents subordinates.

**Aplicação**:
- Task title: "Activate [number] [type] agents"
- Tasks incluem criação individual de cada agent
- Success criteria incluem todos agents operacionais

### Variação B: System Configuration
**Cenário**: CEO precisa configurar sistemas/infrastructure.

**Aplicação**:
- Task title: "Configure [system] for [purpose]"
- Tasks focadas em configuration steps
- Success criteria focados em operational readiness

### Variação C: Workflow Establishment
**Cenário**: CEO precisa estabelecer workflows/routines.

**Aplicação**:
- Task title: "Establish [workflow] routines"
- Tasks focadas em routine creation
- Success criteria focados em routine execution

## Anti-patterns a evitar

### Anti-pattern 1: Reopening Done Tasks
Reabrir tasks marcadas como Done causa:
- Confusion no historical tracking
- Difficulty distinguishing documentação vs. implementação
- Risk de missing context

### Anti-pattern 2: Assuming Automatic Transition
Assumir que CEO automaticamente transiciona de documentação para implementação causa:
- Stalls no sistema
- Idle time não produtivo
- Missed implementation windows

### Anti-pattern 3: Incomplete Context
Nova task sem contexto completo causa:
- Misaligned execution
- Repeated work ou missed dependencies
- Frustration do agent

### Anti-pattern 4: Missing Infrastructure
Atribuir work substantiva sem infrastructure causa:
- Execution failures
- Partial implementations
- Need for rework

## Checklist de aplicação

### Diagnóstico
- [ ] Identificar phase completada (documentação/implementação)
- [ ] Identificar gap entre phases
- [ ] Verificar se CEO tem tasks ativas
- [ ] Analisar historical tracking

### Criação de Task
- [ ] Criar nova task (não reabrir antiga)
- [ ] Definir título descritivo da nova phase
- [ ] Atribuir prioridade apropriada
- [ ] Atribuir ao CEO/orquestrador
- [ ] Incluir contexto completo

### Preparação
- [ ] Verificar memory structures
- [ ] Verificar configuration consistency
- [ ] Verificar/criar dependencies
- [ ] Preparar infrastructure necessária

### Ativação
- [ ] Trigger manual de activation
- [ ] Verificar que CEO pegou a task
- [ ] Monitorar início de execução
- [ ] Verificar progresso inicial

## Lições conceituais

### 1. Phase Awareness
Sistemas de orquestração AI beneficiam de clear phase separation com tracking separado.

### 2. Context Continuity
Contexto deve fluir entre phases através de referências explícitas, não através de reabertura de tasks.

### 3. Infrastructure First
Work substantiva requer infrastructure preparada - verificar antes de atribuir.

### 4. Explicit Transitions
Transições entre phases requerem triggers explícitos, não assumir automaticidade.

### 5. Clean Tracking
Tracking limpo (nova task por nova phase) facilita monitoring e historical analysis.

## Aplicabilidade
Este padrão aplica-se a:
- Sistemas de orquestração AI com agent hierarquias
- Situações onde documentação e implementação são phases separadas
- Cenários onde agents podem ficar idle entre phases
- Sistemas que beneficiam de clear phase tracking

O padrão é agnóstico à tecnologia específica, focando em princípios conceituais de workflow design para sistemas de orquestração AI.