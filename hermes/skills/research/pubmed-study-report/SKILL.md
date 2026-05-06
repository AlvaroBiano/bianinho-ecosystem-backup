---
name: pubmed-study-report
description: "Gera relatórios de estudos científicos do PubMed com estrutura fixa — títulos original/traduzido, data, DOI, resumo de 3 parágrafos densos, conclusões e link PDF. Ativada quando o utilizador pede estudos científicos."
category: research
tags: [pubmed, relatorio, estudos-cientificos, evidence-based]
---

# PubMed Study Report — Bianinho Skill

## MANDATO

Receber um pedido de estudos científicos, pesquisar no PubMed via EUtils API, filtrar os mais relevantes (priorizando free full text e revisões), e gerar um relatório estruturado com formato fixo. **Mesmo formato, mesma qualidade, toda vez.**

---

## QUANDO ATIVAR

Quando o utilizador pedir:
- "traga X estudos sobre [tema]"
- "relatório PubMed: [tema]"
- "pesquise estudos sobre [tema]"
- "gere um relatório de estudos científicos sobre [tema]"
- Qualquer variação similar

---

## ESTRUTURA FIXA DO RELATÓRIO

### Cada estudo inclui:

1. **Título Original** (em inglês — conforme publicado)
2. **Título Traduzido para Português do Brasil**
3. **Data de publicação** (formato: XX de [mês] de [ano] ou [mês]/[ano] se dia indisponível)
4. **DOI** (formato: `10.XXXX/...`)
5. **Resumo em 3 parágrafos densos** — cada parágrafo com pelo menos 4-5 frases substantivas. Primeiro parágrafo: contexto e objetivos. Segundo: métodos e descobertas principais. Terceiro: implicações e significado.
6. **Conclusões do Estudo** (1 parágrafo)
7. **Link direto para PDF** via PubMed Central (PMC) — formato: `https://www.ncbi.nlm.nih.gov/pmc/articles/PMC[NUMERO]/pdf/`

### Header do relatório:
```
# 🔬 [TÍTULO DO TEMA]

## Estudos Científicos de Livre Acesso (#[ano]-#[ano])
```

### Footer do relatório:
```
## Referências PMIDs

| # | PMID | Título |
|---|------|--------|
| 1 | XXXXXXXX | [Título resumido] |
...

**Todos os X estudos são free full text via PubMed Central (PMC).**
```

---

## WORKFLOW — PASSO A PASSO

### PASSO 1: Analisar o pedido
- Identificar o tema central
- Identificar o número de estudos pedidos (default: 5)
- Identificar filtros especiais (ex: "mulheres", "revisão", "free full text", período de anos)

### PASSO 2: Definir queries de busca
Prioridade para queries que retornem **free full text** (PubMed Central):

```
autoimmune disease[tiab] AND women[tiab] AND free[fulltext]
sex[tiab] AND autoimmune[tiab] AND inflammation[tiab] AND free[fulltext]
female[tiab] AND autoimmune disease[tiab] AND free[fulltext]
chronic inflammation[tiab] AND autoimmune disease[tiab] AND free[fulltext]
immune[tiab] AND inflammation[tiab] AND women[tiab] AND free[fulltext]
```

Sempre combinar com filtros de período: `AND 2021:2026[dp]` para estudos = 5 anos ou menos.

Se há filtro de género/idade específico, ajustar a query:
- `women[tiab]` / `female[tiab]` / `men[tiab]` / `male[tiab]`
- `children[tiab]` / `adolescent[tiab]` / `elderly[tiab]`

### PASSO 3: Executar queries em paralelo
```python
import requests

def buscar_pubmed(query, mindate="2021", maxdate="2026", retmax=80):
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    r = requests.get(
        f"{base_url}esearch.fcgi",
        params={
            'db': 'pubmed',
            'term': query,
            'mindate': mindate,
            'maxdate': maxdate,
            'retmax': retmax,
            'retmode': 'json',
            'sort': 'relevance'
        },
        timeout=30
    )
    try:
        result = r.json()['esearchresult']
        return {'count': int(result.get('count', 0)), 'ids': result.get('idlist', [])}
    except:
        return {'count': 0, 'ids': []}
```

Executar 3-5 queries em paralelo para captar máxima cobertura.

### PASSO 4: Agregar IDs únicos e remover duplicados

### PASSO 5: Obter metadados de TODOS os IDs
```python
def get_metadados(pmids):
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    r = requests.get(
        f"{base_url}esummary.fcgi",
        params={'db': 'pubmed', 'id': ','.join(pmids), 'retmode': 'json'},
        timeout=90
    )
    return r.json()['result']
```

### PASSO 6: Classificar por relevância
Usar scoring manual:
```python
def score_relevancia(data):
    title = data.get('title', '').lower()
    score = 0
    if any(k in title for k in ['women', 'female', 'sex', 'gender']): score += 5
    if any(k in title for k in ['autoimmune', 'autoimmunity']): score += 4
    if any(k in title for k in ['inflammation', 'inflammatory', 'chronic']): score += 3
    if any(k in title for k in ['review', 'overview', 'perspective']): score += 2
    pubtypes = data.get('pubtype', [])
    if 'Review' in pubtypes or 'Systematic Review' in pubtypes or 'Meta-Analysis' in pubtypes: score += 3
    return score
```

Selecionar os **top N** (conforme pedido do utilizador, default 5) com maior score.

### PASSO 7: Verificar PMC free full text para cada artigo selecionado
```python
def get_pmc_link(pmid):
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    r = requests.get(
        f"{base_url}esearch.fcgi",
        params={'db': 'pmc', 'term': f'{pmid}[pmid]', 'retmode': 'json'},
        timeout=15
    )
    try:
        result = r.json()['esearchresult']
        ids = result.get('idlist', [])
        if ids:
            pmcid = ids[0]
            return f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/pdf/"
    except:
        pass
    return None
```

Se um artigo não tem PMC: substituí-lo pelo próximo melhor classificado que tenha PMC.

### PASSO 8: Obter abstracts completos em XML
```python
def get_abstracts_xml(pmids):
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    r = requests.get(
        f"{base_url}efetch.fcgi",
        params={
            'db': 'pubmed',
            'id': ','.join(pmids),
            'rettype': 'abstract',
            'retmode': 'xml'
        },
        timeout=30
    )
    return r.text
```

Parsear com `xml.etree.ElementTree`. Extrair todas as secções do abstract.

### PASSO 9: Construir resumos de 3 parágrafos densos

**Parágrafo 1 — Contextualização e Objetivos:**
Frases que estabelecem o problema, a lacuna no conhecimento, e o objetivo do estudo. Mínimo 4 frases.

**Parágrafo 2 — Métodos e Descobertas Principais:**
Descrever brevemente a abordagem/metodologia e listar as principais descobertas quantitativas ou qualitativas. Mínimo 4 frases.

**Parágrafo 3 — Implicações e Significado:**
O que os resultados significam para o campo, para a prática clínica, ou para políticas de saúde. Mínimo 4 frases.

**NORMAS CRÍTICAS:**
- NUNCA escrever frases vazias ou genéricas ("Os resultados foram significativos")
- NUNCA inventar dados, números, nomes de genes ou mecanismos
- NUNCA usar jargão excessivo que não seja explicado
- Usar os dados concretos do abstract real
- Traduzir conceitos técnicos com explicação breve
- Manter o tom académico mas acessível

### PASSO 10: Gerar conclusões (1 parágrafo)
Extrair do abstract ou construir com base nos dados disponíveis. Uma frase de fechamento que sintetize o achado central.

### PASSO 11: Montar o relatório final
Usar a estrutura fixa definida acima. Escrever em **português do Brasil** para todos os elementos excepto o título original.

---

## REGRAS DE CONDUTA

- **NUNCA fabricate, invente, ou superponha dados.** Se o abstract está incompleto no PubMed, usar apenas o que está disponível e indicar que o abstract original está parcial.
- **Sempre traduzir títulos para pt-BR** — não usar tradução automática.
- **Sempre verificar PMC** antes de incluir link PDF.
- **Priorizar revisões e meta-análises** quando disponíveis e relevantes.
- **Período default: 5 anos (2021-2026)** — pedir confirmação se o tema requer período diferente.
- **Mínimo: 5 estudos, máximo: dependente do pedido do utilizador.**

---

## ANTIPATTERNS

- Não usar `curl` via terminal com piping para Python JSON — usar `requests`
- Não usar `retmode=xml` para ESearch — usar sempre `retmode=json`
- Não assumir que PMC ID = PDF disponível — confirmar via ESearch
- Não apresentar estudos sem abstract ou com abstract truncado como se estivessem completos
- Não usar português de Portugal — o relatório é sempre em **pt-BR**

---

## EXEMPLO DE ESTRUTURA DO OUTPUT

```
# 🔬 [TÍTULO DO TEMA]

## Estudos Científicos de Livre Acesso (2021-2026)

---

## ESTUDO 1

**Título Original:** [Título em inglês]
**Título em Português:** [Título traduzido para pt-BR]
**Data de Publicação:** XX de [mês] de [ano]
**DOI:** 10.XXXX/...
**Link PDF:** https://www.ncbi.nlm.nih.gov/pmc/articles/PMCXXXXX/pdf/

### Resumo

[Parágrafo 1: contextualização e objetivos — mínimo 4 frases]

[Parágrafo 2: métodos e descobertas principais — mínimo 4 frases]

[Parágrafo 3: implicações e significado — mínimo 4 frases]

### Conclusões do Estudo

[1 parágrafo de conclusão síntese]

---

## ESTUDO 2

[...]

## Referências PMIDs

| # | PMID | Título |
|---|------|--------|
| 1 | XXXXXXXX | [Título resumido] |
| 2 | XXXXXXXX | [Título resumido] |

**Todos os 5 estudos são free full text via PubMed Central (PMC).**
```

---

*Skill criada: $(date +%d/%m/%Y) — Bianinho OS*
