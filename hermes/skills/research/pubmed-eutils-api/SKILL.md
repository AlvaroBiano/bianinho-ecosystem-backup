---
name: pubmed-eutils-api
description: Search and retrieve scientific papers from PubMed using NCBI EUtils API. Covers all 8 endpoints, 48 searchable fields, rate limits, and verified Python code patterns. ALWAYS verify data before presenting.
category: research
tags: [pubmed, ncbi, scientific-papers, evidence-based, research]
---

# PubMed EUtils API — Bianinho Skill

## BASE_URL
```
https://eutils.ncbi.nlm.nih.gov/entrez/eutils/
```

## STATUS: OPERATIONAL (17/04/2026)
- Banco: PubMed
- Total artigos: 40.414.509
- Última atualização: 2026/04/17

---

## ⚠️ NORMA CRÍTICA — VERIFICAÇÃO DE DADOS

**NUNCA fabricate, invente, ou superponha dados.** Se não tem certeza absoluta:
- Use `retmode=json` com Python `requests` para verificar
- Busque PMIDs por DOI: `term=10.XXXX[aid]&retmode=json`
- Marque tudo não verificado como `[NAO VERIFICADO]`
- Álvaro não tolera dados fictícios — é questão de confiança

---

## 8 ENDPOINTS DA EUtils

### 1. EInfo — Databases e Campos
```
GET https://eutils.ncbi.nlm.nih.gov/entrez/eutils/einfo.fcgi?db=pubmed&retmode=json
```
Retorna: lista de databases e campos indexados (48 campos para pubmed).

### 2. ESearch — Buscar PMIDs ✅ PRIMEIRO PASSO
```
GET https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi
```
**Parâmetros:**
| Parâmetro | Descrição | Exemplo |
|-----------|-----------|---------|
| `db` | banco | `pubmed` |
| `term` | query | `fibromyalgia[tiab] AND trauma[tiab]` |
| `retmax` | máx resultados (default 20, max 100k) | `10` |
| `retmode` | `json` ✅ | `xml` |
| `sort` | `relevance`, `pub_date`, `author` | `relevance` |
| `mindate` / `maxdate` | range (YYYY ou YYYY/MM/DD) | `2019` / `2026` |
| `datetype` | `pdat` (publicação), `edat` (entrada) | `pdat` |
| `field` | campo específico | `tiab` |

**Resposta (JSON):**
```python
{
  "esearchresult": {
    "count": "97",
    "retmax": "3",
    "idlist": ["33918736", "34128995", "40186784"],
    "querytranslation": "\"fibromyalgia\"[MeSH Terms] OR..."
  }
}
```

### 3. ESummary — Metadados ✅ SEGUNDO PASSO
```
GET https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi
```
**Parâmetros:** `db=pubmed`, `id=PMID1,PMID2,...`, `retmode=json`

**Campos retornados:**
- `uid` — PMID
- `title` — Título do artigo
- `source` — Journal (nome abreviado)
- `fulljournalname` — Journal (nome completo)
- `pubdate` — Data de publicação
- `authors` — Lista [{name, authtype, clusterid}]
- `lastauthor` — Último autor
- `volume`, `issue`, `pages`
- `lang` — Idioma(s)
- `issn`, `essn`
- `pubtype` — Tipos [Journal Article, Review, etc.]
- `elocationid` — DOI (formato: `doi: 10.XXXX/...`)
- `pmcrefcount` — Número de citações
- `sortpubdate` — Data (para ordenação)

### 4. EFetch — Dados Completos (XML/Abstract)
```
GET https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi
```
**Parâmetros:** `db=pubmed`, `id=PMID`, `rettype=xml|medline|abstract`, `retmode=text|xml`

Retorna: abstract completo, MeSH Terms, keywords, affiliations, grants, conflict of interest.

### 5. ELink — Artigos Relacionados / Links
```
GET https://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi
```
**Parâmetros:** `dbfrom=pubmed`, `db=pmc|pubmed`, `id=PMID`, `linkname=pubmed_pubmed|pubmed_pmc`

### 6. EGQuery — Busca Global em Todos os Bancos
```
GET https://eutils.ncbi.nlm.nih.gov/entrez/eutils/egquery.fcgi?term=fibromyalgia&retmode=json
```
Retorna contagem de resultados em TODOS os databases simultaneamente.

### 7. ESpell — Correção Ortográfica
```
GET https://eutils.ncbi.nlm.nih.gov/entrez/eutils/espell.fcgi?db=pubmed&term=fibromialgia&retmode=json
```
Sugere correção para queries com erro de ortografia.

---

## 48 CAMPOS DE BUSCA DO PUBMED

### Principais:
| Campo | Código | Descrição |
|-------|--------|-----------|
| Title | `TI` ou `[ti]` | Palavras no título |
| Abstract | `AB` ou `[ab]` | Palavras no abstract |
| Title/Abstract | `TIAB` ou `[tiab]` | Busca combinada |
| MeSH Terms | `MH` ou `[mh]` | Termos MeSH (hierárquico) |
| MeSH Major Topic | `MAJR` ou `[majr]` | Tópicos principais |
| Author | `AU` ou `[au]` | Nome de autor |
| Journal | `TA` ou `[ta]` | Nome do journal |
| Publication Date | `DP` ou `[dp]` | Data de publicação |
| Entry Date | `EDAT` ou `[edat]` | Data de entrada no PubMed |
| Publication Type | `PT` ou `[pt]` | Tipo (Review, Clinical Trial, etc.) |
| DOI | `AID` ou `[aid]` | Article Identifier |
| PMID | `PMID` ou `[pmid]` | PubMed ID |
| Language | `LA` ou `[lang]` | Idioma |
| Affiliation | `AFFL` ou `[affl]` | Afiliação institucional |
| EC/RN Number | `ECNO` | Número CAS de chemicals |
| MeSH Subheading | `SUBH` ou `[sh]` | Subcategoria MeSH |

### Filtros úteis:
| Filtro | Código | Descrição |
|--------|--------|-----------|
| Free Full Text | `free[fulltext]` | Artigos gratuitos |
| Clinical Trial | `clinical[pt]` | Ensaios clínicos |
| Meta-Analysis | `meta-analysis[pt]` | Revisões meta-analíticas |
| Systematic Review | `systematic[pt]` | Revisões sistemáticas |
| Review | `review[pt]` | Artigos de revisão |
| Human | `human[ng]` | Estudos em humanos |

---

## CÓDIGO PYTHON VERIFICADO (FUNCIONA)

### Buscar artigos e obter metadados:
```python
import requests

def buscar_pubmed(query, mindate="2019", maxdate="2026", retmax=10):
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    
    # PASSO 1: Buscar PMIDs
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
    ids = r.json()['esearchresult']['idlist']
    count = r.json()['esearchresult']['count']
    
    if not ids:
        return {'count': 0, 'articles': []}
    
    # PASSO 2: Buscar metadados
    r = requests.get(
        f"{base_url}esummary.fcgi",
        params={
            'db': 'pubmed',
            'id': ','.join(ids),
            'retmode': 'json'
        },
        timeout=30
    )
    results = r.json()['result']
    
    articles = []
    for pmid in ids:
        data = results.get(pmid, {})
        doi = data.get('elocationid', 'N/A')
        if doi.startswith('doi: '):
            doi = doi[5:]
        articles.append({
            'pmid': pmid,
            'title': data.get('title', 'N/A'),
            'journal': data.get('source', 'N/A'),
            'pubdate': data.get('pubdate', 'N/A'),
            'authors': [a['name'] for a in data.get('authors', [])[:3]],
            'doi': doi,
            'pubtype': data.get('pubtype', []),
            'pmcrefcount': data.get('pmcrefcount', 0)
        })
    
    return {'count': count, 'articles': articles}
```

### Buscar PMID por DOI (validação):
```python
def validar_doi(doi):
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    r = requests.get(
        f"{base_url}esearch.fcgi",
        params={'db': 'pubmed', 'term': f'{doi}[aid]', 'retmode': 'json'},
        timeout=15
    )
    ids = r.json()['esearchresult']['idlist']
    return ids[0] if ids else None
```

### Buscar detalhes de PMIDs específicos:
```python
def detalhes_pmids(pmids):
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    r = requests.get(
        f"{base_url}esummary.fcgi",
        params={'db': 'pubmed', 'id': ','.join(pmids), 'retmode': 'json'},
        timeout=30
    )
    return r.json()['result']
```

---

## EXEMPLOS DE QUERIES VALIDADAS (2019-2026)

| Tema | Query | Artigos |
|------|-------|--------|
| Fibromialgia + Trauma | `fibromyalgia[tiab] AND trauma[tiab]` | 97 |
| SII + ACEs | `irritable bowel[tiab] AND childhood adversity[tiab]` | 4 |
| Enxaqueca + Violência Doméstica | `migraine[tiab] AND intimate partner violence[tiab]` | 2 |
| DTM + Estresse | `temporomandibular disorder[tiab] AND stress[tiab]` | 150 |
| Autoimune + Estresse | `autoimmune[tiab] AND psychological stress[tiab]` | 76 |
| C-PTSD | `complex ptsd[tiab] OR complex post-traumatic stress[tiab]` | 703 |
| DID + Trauma | `dissociative identity disorder[tiab] AND trauma[tiab]` | 77 |

### Estudos específicos verificados:
- **PMID 35086857** — Meta-analysis: childhood events + IBS (J Investig Med, 2022)
- **PMID 35780794** — Complex post-traumatic stress disorder (Lancet, 2022) DOI: 10.1016/S0140-6736(22)00821-2
- **PMID 33918736** — Fibromyalgia: Pathogenesis... (Int J Mol Sci, 2021) DOI: 10.3390/ijms22083891
- **PMID 38116333** — Dissociative Identity Disorder (Cureus, 2023) DOI: 10.7759/cureus.49057

---

## LIMITAÇÕES E REGRAS

### Rate Limiting:
- **3 requests/segundo** sem API key
- Com API key: **10 requests/segundo**
- Para evitar bloqueios: usar `retmax` alto em vez de múltiplas chamadas

### Maximum Results:
- Máximo 100.000 IDs por busca
- Para mais de 100k, usar paginação com `retstart`

### Formato de Data:
- `YYYY/MM/DD` ou apenas `YYYY`
- mindate=2019, maxdate=2026

---

## ANTIPATTERN (NÃO FAZER)

❌ **NUNCA chame curl via terminal e piping para python json** — funciona mal
❌ **NUNCA use retmode=xml** — JSON é mais fiável com requests
❌ **NUNCA assuma que um PMID existe** — sempre valide com ESearch
❌ **NUNCA fabricate DOIs ou PMIDs** — usar `validar_doi()` para verificar
❌ **NUNCA presente dados não verificados** — marcar como `[NAO VERIFICADO]`

---

## ARQUIVOS E RELATÓRIOS

- Relatório completo: `/home/alvarobiano/Desktop/RELATORIO_PUBMED_API.md`
- Validação de estudos: sempre usar `detalhes_pmids()` antes de apresentar

---

*Atualizado: 17/04/2026 — Inclui norma de conduta sobre dados fictícios*
