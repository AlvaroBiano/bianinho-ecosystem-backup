# PubMed → PMC Free Full Text Pipeline (03/05/2026)

## Contexto da Sessão

Álvaro pediu 5 estudos free full text sobre "Autoimunidade e inflamação crônica: Mulheres representam 80% dos casos de doenças autoimunes, exigindo diagnóstico precoce."

Problema descoberto: artigos marcados `free[fulltext]` pelo PubMed podem ser free no site do editor mas **não** ter versão no PubMed Central. PMC é o único guaranteed free PDF.

## 5 Estudos Entregues (PMID)

| # | PMID | PMC ID | Journal | DOI |
|---|------|--------|---------|-----|
| 1 | 39457311 | PMC11506982 | Int J Environ Res Public Health | 10.3390/ijerph21101339 |
| 2 | 33436077 | PMC7802252 | Biology of Sex Differences | 10.1186/s13293-021-00358-3 |
| 3 | 39885993 | PMC11779622 | Frontiers in Immunology | 10.3389/fimmu.2024.1501364 |
| 4 | 35966636 | PMC9358995 | Immunometabolism | 10.1097/IN9.000000000000004 |
| 5 | 38489782 | PMC12788399 | Canadian J Physiology & Pharmacology | 10.1139/cjpp-2023-0420 |

**PDF URLs:** `https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{ID}/pdf/`

## Artigos que Pareciam Free Mas Não Têm PMC

- **PMID 41173353** — *Autoimmunity Reviews* — DOI 10.1016/j.autrev.2025.103955
  - Motivo: Autoimmunity Reviews é free on publisher mas NÃO está no PMC
  - Tentativa inicial foi弃 (artigo descartado e substituído por 38489782)

## Queries que Funcionalam (2021–2026, free full text)

```python
# Mais produtivas para temamulheres + autoimunidade:
queries = [
    "autoimmune disease[tiab] AND women[tiab] AND free[fulltext]",           # 51 results
    "autoimmune[tiab] AND chronic inflammation[tiab] AND sex[tiab] AND women[tiab]",  # 8 results
    "immune dysregulation[tiab] AND women[tiab] AND free[fulltext]",        # 8 results
    "sex[tiab] AND immune[tiab] AND autoimmune disease[tiab] AND free[fulltext]",      # 7 results
    "female[tiab] AND autoimmune disease[tiab] AND free[fulltext]",           # 55 results
    "immune[tiab] AND inflammation[tiab] AND women[tiab] AND free[fulltext]",         # 74 results
    "autoimmune[tiab] AND inflammation[tiab] AND free[fulltext]",             # 107 results (muito amplo)
]
```

## Scoring de Relevância Aplicado

```python
def score_relevancia(title, pubtypes):
    title_lower = title.lower()
    score = 0
    if any(k in title_lower for k in ['women', 'female', 'sex', 'gender']): score += 5
    if any(k in title_lower for k in ['autoimmune', 'autoimmunity']): score += 4
    if any(k in title_lower for k in ['inflammation', 'inflammatory', 'chronic']): score += 3
    if any(k in title_lower for k in ['review', 'overview', 'perspective', 'consensus']): score += 2
    if any(k in title_lower for k in ['diagnosis', 'early', 'preclinical', 'prevalence', 'epidemiology']): score += 1
    if 'Review' in pubtypes or 'Systematic Review' in pubtypes or 'Meta-Analysis' in pubtypes: score += 3
    return score
```

Artigos com score >= 3 foram priorizados. Score de 10-12 = artigo ideal.

## EFetch XML Parsing — Armadilha

Ao fazer EFetch com `retmode=xml` e `rettype=abstract`, alguns resultados são `PubmedBookArticle` (não `PubmedArticle`). PubmedBookArticle pode não ter `AbstractText` tags. Código deve usar `.//PubmedArticle'` como seletor principal e não asumir que todo artigo tem abstract estruturado.

## Validação DOI

O campo `elocationid` do ESummary pode conter DOIs inválidos (ex: PMID 38489782 — journal "Canadian J Physiology & Pharmacology" com DOI `10.1056/NEJMoa2109927` que é na verdade um NEJM DOI). **Cross-reference sempre journal name + DOI.**

## Estrutura de Output para Álvaro

Formato esperado (dito por Álvaro implicitamente no pedido):
1. Título original
2. Título traduzido para PT-BR
3. Data de publicação
4. DOI
5. Resumo em 3 parágrafos densos (obtidos do abstract do EFetch)
6. Conclusões do estudo
7. Link direto para PDF (só depois de verificar PMC)
