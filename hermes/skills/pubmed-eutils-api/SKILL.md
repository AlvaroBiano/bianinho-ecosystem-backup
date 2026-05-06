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

## STATUS: OPERATIONAL (04/05/2026)
- Banco: PubMed
- Total artigos: ~40M+
- Última atualização: 2026/05/04
- ⚠️ IMPORTANTE: EUtils é 100% LIVRE — NÃO precisa de conta nem API key
  - Sem key: 3 pedidos/segundo (suficiente para a maioria dos fluxos)
  - Com key opcional: 10 pedidos/segundo (pedir só se necessário via `hermes config`)

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

## ARMADILHAS CRÍTICAS (DESTA SESSÃO 04/05/2026)

### Armadilha: PubMed NÃO entende Português — usar INGLÊS

PubMed é uma base de dados americana e só entende **inglês**. Se a query for em português (ex: "autoimunidade e inflamação crónica na mulher"), ESearch retorna **0 resultados** — não é erro, é simplesmente porque não há indexação em português.

**Sintoma:** `idlist: []` com count = 0, mesmo com query aparentemente correcta.

**Solução:** Traduzir sempre para inglês antes de fazer a query. Manter o texto original em PT-BR para exibição, mas usar a versão inglesa para pesquisa.

```python
# ❌ ERRADO — retorna 0 resultados
query = "autoimunidade e inflamação crónica"
r = esearch("pubmed", query)  # idlist: []

# ✅ CORRECTO — English only
query_en = "autoimmune AND chronic inflammation AND women"
r = esearch("pubmed", query_en)  # retorna resultados
```

**Implicação:** Quando um tema está em PT-BR, ter sempre uma versão EN correspondente para pesquisa. Exemplo:
- PT: "Autoimunidade e inflamação crónica na mulher"  
- EN: "autoimmune AND chronic inflammation AND women"
- Query PubMed: usar a versão EN

### Armadilha: `freshness=pd` no Brave Search API

O parâmetro `freshness=pd` ("past day") na Brave News Search API **retorna quase nada** — tipicamente só 1 resultado irrelevante (ex: horóscopo do dia).

**Não usar `freshness=pd` na Brave News API.** Buscar SEM freshness e filtrar por `page_age` no código depois.

```python
# ❌ ERRADO — retorna ~1 resultado
params = {"q": query, "count": 20, "freshness": "pd"}

# ✅ CORRECTO — sem freshness, filtrar por page_age depois
params = {"q": query, "count": 20}
# depois: if '2026' in item.get('page_age', '')
```

### Armadilha: Brave Web Search API vs News API

A Brave **Web Search API** (`/res/v1/search`) retorna 301 redirect para plano pago no tier gratuito — **não funciona**.

A Brave **News Search API** (`/res/v1/news/search`) funciona com o plano gratuito (2.000 queries/mês).

**Para cross-check de notícias: usar Brave News API, não Web Search.**

### Armadilha: AionUI cron jobs NÃO estão no Hermes cron

Jobs de cron criados no AionUI (ex: "Saúde da Mulher") vivem no SQLite do AionUI, **não** no cron do Hermes.

**Locais:**
- AionUI SQLite: `~/Library/Application Support/AionUI/aionui/aionui.db`
- Tabela: `cron_jobs`
- Hermes cron (outro job): `~/.hermes/cron/jobs.json` ou via `hermes cron list`

**Para consultar/actualizar cron jobs do AionUI:**
```bash
# Ver cron job
sqlite3 "~/Library/Application Support/AionUI/aionui/aionui.db" \
  "SELECT id, name, payload_message, schedule_kind, schedule_value FROM cron_jobs;"

# Para updates: usar UPDATE SQL directamente na tabela
```

### Armadilha: Artigos "Ahead of Print" sem Abstract
Artigos muito recentes (2026, especialmente Abril/Maio) frequentemente têm DOI e metadata mas **NÃO têm abstract publicado** — o PubMed retorna `abstract: ""` ou `0 chars`.
- **Sintoma:** ESearch devolve PMID mas EFetch devolve abstract vazio
- **Solução:** SEMPRE validar cada PMID com EFetch antes de usar. Se abstract = 0 chars, substituir o artigo por um mais antigo (2024-2025) que já tenha abstract publicado.
- **Código de validação:**
```python
def validar_abstract(pmid):
    """Retorna (abstract, length). Se length=0, artigo é ahead-of-print."""
    abstract = get_abstract(pmid)  # via EFetch
    return abstract, len(abstract)

# Exemplo: filtrar apenas artigos com abstract
pmids_candidatos = [...]
artigos_validos = []
for pmid in pmids_candidatos:
    abstract, length = validar_abstract(pmid)
    if length > 200:  # abstract real tem pelo menos 200 chars
        artigos_validos.append(pmid)
    # else: skip, artigo ahead-of-print
```

---

## ⚠️ armadilha crítica: free[fulltext] NÃO garante PMC

O filtro `free[fulltext]` na ESearch retorna artigos marcados como free full text pelo PubMed, **mas isso não significa que estão no PubMed Central (PMC)**. Journals como *Autoimmunity Reviews*, *BMJ*, *The Lancet* e outros permitem free full text no site do editor mas **não** no PMC.

**Para garantir acesso real ao PDF, SEMPRE verificar PMC:**

```python
import requests

def verificar_pmc(pmid):
    """Retorna (tem_pmc, pmcid) para um PMID. Só PMCs são free full text garantido."""
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    r = requests.get(
        f"{base_url}esearch.fcgi",
        params={'db': 'pmc', 'term': f'{pmid}[pmid]', 'retmode': 'json'},
        timeout=15
    )
    try:
        ids = r.json()['esearchresult']['idlist']
        if ids:
            return True, ids[0]
    except:
        pass
    return False, None

# Uso:
tem_pmc, pmcid = verificar_pmc("41173353")
if tem_pmc:
    pdf_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/pdf/"
    html_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/"
else:
    print("ARTIGO NÃO TEM ACESSO LIVRE NO PMC — pode não ser realmente free")
```

**Na prática:** filtrar resultados com PMC → só esses são guaranteed free PDF.

---

## PIPELINE COMPLETO: Buscar estudos free full text com abstracts

Para pedidos de Álvaro do tipo "N estudos sobre X" com requirement de PDF:

### Passo 1: Buscar PMIDs com filtro free[fulltext]
```python
def buscar_pmids(query, mindate="2021", maxdate="2026", retmax=80):
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    r = requests.get(
        f"{base_url}esearch.fcgi",
        params={
            'db': 'pubmed', 'term': query,
            'mindate': mindate, 'maxdate': maxdate,
            'retmax': retmax, 'retmode': 'json', 'sort': 'relevance'
        },
        timeout=30
    )
    return r.json()['esearchresult'].get('idlist', [])
```

### Passo 2: Classificar por relevância
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

### Passo 3: Verificar PMC (CRÍTICO)
```python
def filtrar_com_pmc(pmids):
    """Retorna apenas os PMIDs que têm PMC ID = free full text garantido."""
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    com_pmc = []
    for pmid in pmids:
        r = requests.get(
            f"{base_url}esearch.fcgi",
            params={'db': 'pmc', 'term': f'{pmid}[pmid]', 'retmode': 'json'},
            timeout=15
        )
        try:
            ids = r.json()['esearchresult']['idlist']
            if ids:
                com_pmc.append((pmid, ids[0]))
        except:
            pass
    return com_pmc
```

### Passo 4: Obter abstracts completos via EFetch XML
```python
from xml.etree import ElementTree as ET

def get_full_abstracts(pmids):
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    r = requests.get(
        f"{base_url}efetch.fcgi",
        params={'db': 'pubmed', 'id': ','.join(pmids), 'rettype': 'abstract', 'retmode': 'xml'},
        timeout=30
    )
    root = ET.fromstring(r.text)
    artigos = []
    for article in root.findall('.//PubmedArticle'):
        pmid = article.find('.//PMID').text
        title = article.find('.//ArticleTitle').text or 'N/A'
        # Abstract pode vir em secções — Collecting all text
        abstract_parts = []
        for abs_el in article.findall('.//AbstractText'):
            abstract_parts.append(abs_el.text or '')
        abstract = '\n'.join(abstract_parts)
        # DOI
        doi = 'N/A'
        for aid in article.findall('.//ArticleId'):
            if aid.get('IdType') == 'doi':
                doi = aid.text
        # Data
        pubdate_el = article.find('.//PubDate')
        year = pubdate_el.find('Year').text if pubdate_el.find('Year') is not None else ''
        month = pubdate_el.find('Month').text if pubdate_el.find('Month') is not None else ''
        day = pubdate_el.find('Day').text if pubdate_el.find('Day') is not None else ''
        pubdate = f"{year}/{month}/{day}".strip('/')
        # Autores
        authors = []
        for auth in article.findall('.//Author'):
            last = auth.find('LastName')
            fore = auth.find('ForeName')
            if last is not None and fore is not None:
                authors.append(f"{last.text} {fore.text}")
        # Keywords
        keywords = [kw.text for kw in article.findall('.//Keyword') if kw.text]
        artigos.append({
            'pmid': pmid, 'title': title, 'abstract': abstract,
            'pubdate': pubdate, 'doi': doi, 'authors': authors,
            'keywords': keywords
        })
    return artigos
```

---

## ARQUIVOS E RELATÓRIOS

- Relatório completo: `/home/alvarobiano/Desktop/RELATORIO_PUBMED_API.md`
- Validação de estudos: sempre usar `detalhes_pmids()` antes de apresentar
- **references/pubmed-pmc-pipeline.md** — pipeline completo de verificação PMC + queries do dia (03/05/2026)

---

*Atualizado: 03/05/2026 — PMC verification mandatory antes de garantir PDF; pipeline completo free full text*
