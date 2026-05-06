---
name: saudemulher-news
description: "Gera relatório diário de 15 notícias de alta relevância sobre saúde feminina — pesquisadas em fontes especializadas (Brave News API), verificadas com estudos científicos (PubMed) e cross-check em múltiplos sites. Usado pelo cron Saúde da Mulher (22:45)."
tags: [saude-da-mulher, noticias, pesquisa, cron]
---

# Saúde da Mulher — Skill de Pesquisa Diária

## Mandato

Pesquisar, seleccionar e formatar 15 notícias de alta relevância sobre saúde feminina.
**Fluxo correcto:**
1. Buscar notícias REAIS em sites de saúde na internet (Brave News API)
2. Para cada notícia, verificar com estudos científicos no PubMed
3. Cross-check em sites especializados

**Formato fixo, todo dia igual.**

---

## Quando Actvar

Quando o cron "Saúde da Mulher" dispara — todos os dias às 22:45.

---

## Output Esperado

```
🌸 SAÚDE DA MULHER — NOTÍCIAS DO DIA [DATA]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[NOTÍCIA 1]

📌 Título (pt-BR): [título da notícia original traduzido]
📰 Fonte: [Nome do site] — [URL]
📝 Resumo: [3-5 frases do artigo original]

📚 Estudos Científicos:
1. [Título do estudo] — PMID: XXXXX | DOI: 10.XXXX | https://pubmed.ncbi.nlm.nih.gov/XXXXX/
[... até 5 estudos ...]

🔍 Verificação Cruzada (4+ sites):
1. [Site 1] — https://...
[... pelo menos 4 sites que noticiaram o mesmo tema ...]

🏷️ Tags: [8 tags separadas por vírgula]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[NOTÍCIA 2]
[... repetir até 15 ...]
```

---

## Workflow — Passo a Passo

### PASSO 1: Buscar Notícias Reais na Brave News API

```python
import os
import requests
import time
from datetime import datetime, timedelta

def search_brave_news(query, num_results=20):
    """Buscar notícias de saúde feminina na Brave News API.
    
    A Brave News API retorna notícias reais de sites de saúde.
    NÃO usar freshness=pd — limita demasiado os resultados.
    NÃO usar a API web search ( requer plano pago).
    Usar apenas a News API.
    """
    api_key = os.environ.get("BRAVE_SEARCH_API_KEY") or os.environ.get("BRAVE_API_KEY")
    if not api_key:
        return []
    
    headers = {"Accept": "application/json", "X-Subscription-Token": api_key}
    params = {
        "q": query,
        "count": min(num_results, 20),
        "offset": 0,
    }
    
    r = requests.get(
        "https://api.search.brave.com/res/v1/news/search",
        headers=headers, params=params, timeout=15
    )
    if r.status_code != 200:
        return []
    
    results = r.json().get("results", [])
    
    filtered = []
    cutoff = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d")
    
    for item in results:
        page_age = item.get("page_age", "")[:10]  # YYYY-MM-DD
        url = item.get("url", "")
        title = item.get("title", "")
        
        # Skip horoscopes, celebrity gossip, irrelevant topics
        skip_patterns = ["horoscope", "ganeshaspeaks", "zodiac", "celebrity",
                         "kylie jenner", "kim kardashian", "tom brady"]
        if any(p in url.lower() or p in title.lower() for p in skip_patterns):
            continue
        
        # Filter out old news (>14 days)
        if page_age and page_age < cutoff:
            continue
        
        filtered.append({
            "title": title,
            "url": url,
            "description": item.get("description", ""),
            "page_age": page_age,
            "meta_url": item.get("meta_url", {}).get("netloc", url),
            "source": item.get("meta_url", {}).get("netloc", "unknown")
        })
    
    return filtered
```

**Queries de pesquisa para Brave News (usar todas para maximizar cobertura):**

```python
queries = [
    # Saúde feminina geral
    "women's health news today",
    "female health research breakthrough 2026",
    "gynecology news today",
    # Oncologia feminina
    "breast cancer research 2026",
    "ovarian cancer treatment breakthrough",
    "cervical cancer prevention news",
    # Condições femininas
    "endometriosis new treatment 2026",
    "polycystic ovary syndrome PCOS news",
    "menopause symptoms research",
    # Saúde mental feminina
    "women's mental health study 2026",
    "postpartum depression research",
    # Cardiologia feminina
    "women heart disease research 2026",
    "female cardiovascular health news",
    # Saúde reprodutiva
    "fertility treatment breakthrough 2026",
    "pregnancy complications research news",
    # Outros temas relevantes
    "autoimmune disease women 2026",
    "bone health osteoporosis women",
    "thyroid disorder women research",
]
```

### PASSO 2: Agregar e Deduplicar

```python
def aggregate_and_deduplicate(all_results):
    """Agregar resultados de todas as queries e remover duplicados."""
    seen_urls = set()
    unique = []
    
    for item in all_results:
        url = item["url"]
        # Normalize URL for dedup
        normalized = url.split("?")[0].rstrip("/")
        if normalized not in seen_urls:
            seen_urls.add(normalized)
            unique.append(item)
    
    # Ordenar por data (mais recente primeiro)
    unique.sort(key=lambda x: x["page_age"] or "", reverse=True)
    return unique
```

### PASSO 3: Filtrar por Relevância e Qualidade

```python
# Sites de saúde confiáveis para filtrar
HEALTH_SOURCES = [
    "who.int", "nih.gov", "pubmed.ncbi.nlm.nih.gov",
    "medscape.com", "thelancet.com", "sciencedirect.com",
    "nejm.org", "acog.org", "mayoclinic.org",
    "medicalnewstoday.com", "sciencedaily.com",
    "healthline.com", "reuters.com", "bbc.com",
    "nytimes.com", "theguardian.com",
    "nature.com", "frontiersin.org", "plos.org",
    "hopkinsmedicine.org", "clevelandclinic.org",
    "webmd.com", "health.harvard.edu",
    "g1.globo.com", "folha.uol.com.br", "veja.com.br",
    "scielo.br", "britannica.com",
    "contemporaryobgyn.net", "medicinenet.com",
]

def is_health_source(item):
    url = item.get("url", "").lower()
    source = item.get("source", "").lower()
    return any(s in url or s in source for s in HEALTH_SOURCES)

def filter_relevant(results, max_items=25):
    """Filtrar apenas notícias de saúde feminina relevantes."""
    relevant = []
    female_keywords = [
        "women", "woman", "female", "breast", "ovarian", "cervical",
        "endometriosis", "menopause", "pcos", "polycystic",
        "maternal", "pregnancy", "pregnant", "postpartum",
        "gynecolog", "reproductive", "uterus", "vaginal",
        "postmenopausal", "perimenopause",
        "thyroid", "autoimmune", "lupus",
        "heart disease women", "cardiovascular women",
        "depression women", "anxiety women",
        "osteoporosis", "bone density",
        "hpv", "cervix", "womb",
    ]
    
    for item in results:
        title = item.get("title", "").lower()
        desc = item.get("description", "").lower()
        
        # Deve ter keyword feminina OU ser de source de saúde
        if is_health_source(item):
            relevant.append(item)
        elif any(kw in title or kw in desc for kw in female_keywords):
            relevant.append(item)
    
    return relevant[:max_items]
```

### PASSO 4: Para Cada Notícia — Verificação Científica no PubMed

```python
def verify_with_pubmed(news_title, news_url):
    """Verificar a notícia com estudos científicos no PubMed.
    
    Estratégia: Extrair as 2 principais keywords do título e fazer
    queries específicas combinando-as com "women" ou "female" e
    o tema principal da notícia.
    """
    # Extrair keywords do título (palavras relevantes > 4 chars)
    words = news_title.lower().split()
    stopwords = {"the", "a", "an", "in", "on", "at", "to", "for", "of", "and",
                 "is", "are", "with", "that", "this", "from", "by", "as",
                 "new", "study", "research", "news", "report", "how", "what",
                 "why", "can", "may", "could", "shows", "potential",
                 "boosts", "linked", "associated", "treatment", "effects"}
    keywords = [w for w in words if len(w) > 4 and w not in stopwords]
    
    if not keywords:
        keywords = [w for w in words if len(w) > 3 and w not in stopwords]
    
    all_ids = set()
    
    # Queries específicas: combinar keywords + filtro mulheres/fêmeas
    if len(keywords) >= 2:
        queries = [
            f"({keywords[0]} AND {keywords[1]}) AND (women OR female) AND 2024:2026[dp]",
            f"{keywords[0]} AND {keywords[-1]} AND (women OR female) AND 2024:2026[dp]",
            f"{keywords[0]} AND treatment AND women[Title/Abstract] AND 2024:2026[dp]",
        ]
    elif len(keywords) == 1:
        queries = [
            f"{keywords[0]} AND (women OR female) AND 2024:2026[dp]",
            f"{keywords[0]} AND treatment AND 2024:2026[dp]",
        ]
    else:
        return []
    
    for query in queries:
        try:
            r = requests.get(
                "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
                params={
                    "db": "pubmed",
                    "term": query,
                    "retmax": 12,
                    "retmode": "json",
                    "sort": "pub_date"
                },
                timeout=20
            )
            ids = r.json().get("esearchresult", {}).get("idlist", [])
            all_ids.update(ids)
        except:
            pass
    
    if not all_ids:
        return []
    
    # Obter detalhes dos top 10
    try:
        r = requests.get(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi",
            params={
                "db": "pubmed",
                "id": ",".join(list(all_ids)[:10]),
                "retmode": "json"
            },
            timeout=30
        )
        results = r.json().get("result", {})
    except:
        return []
    
    estudos = []
    for pmid in list(all_ids)[:10]:
        data = results.get(pmid, {})
        if not data or data.get("title") == "Loading...":
            continue
        doi = data.get("elocationid", "N/A")
        if isinstance(doi, str) and doi.startswith("doi: "):
            doi = doi[5:]
        
        # Filtrar: só incluir se abstract existe
        abstract = data.get("title", "")  # summary não tem abstract
        pubdate = data.get("pubdate", "")
        
        estudos.append({
            "pmid": pmid,
            "title": data.get("title", ""),
            "journal": data.get("source", ""),
            "pubdate": pubdate,
            "doi": doi if doi != "N/A" else "",
            "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
        })
        
        if len(estudos) >= 5:
            break
    
    return estudos
```

### PASSO 5: Cross-Check em Múltiplos Sites via Brave News

```python
def cross_check(news_title, num_results=15):
    """Verificar se o tema da notícia aparece em múltiplos sites.
    
    Usa Brave News API para buscar o tema em diferentes fontes.
    Filtra para fontes de saúde confiáveis.
    """
    api_key = os.environ.get("BRAVE_SEARCH_API_KEY") or os.environ.get("BRAVE_API_KEY")
    if not api_key:
        return []
    
    headers = {"Accept": "application/json", "X-Subscription-Token": api_key}
    
    # Usar keywords do título para buscar
    words = news_title.lower().split()
    stopwords = {"the", "a", "an", "in", "on", "at", "to", "for", "of", "and",
                 "is", "are", "with", "that", "this", "new", "study", "news"}
    keywords = [w for w in words if len(w) > 4 and w not in stopwords][:3]
    query = " AND ".join(keywords) if keywords else news_title[:50]
    
    params = {"q": query, "count": num_results, "offset": 0}
    
    r = requests.get(
        "https://api.search.brave.com/res/v1/news/search",
        headers=headers, params=params, timeout=15
    )
    if r.status_code != 200:
        return []
    
    results = r.json().get("results", [])
    
    # Fontes de saúde confiáveis para cross-check
reliable = [
    # Major medical/health organizations
    "who.int", "nih.gov", "pubmed.ncbi.nlm.nih.gov",
    "medscape.com", "thelancet.com", "sciencedirect.com",
    "nejm.org", "acog.org", "mayoclinic.org",
    "medicalnewstoday.com", "sciencedaily.com",
    "healthline.com", "reuters.com", "bbc.com",
    "nature.com", "frontiersin.org", "plos.org",
    "hopkinsmedicine.org", "clevelandclinic.org",
    "webmd.com", "onclive.com", "everydayhealth.com",
    "patientcareonline.com", "medicalxpress.com",
    "earth.com", "newsnationnow.com", "dagens.com",
    "contemporaryobgyn.net", "medicinenet.com",
    "thecardiologyadvisor.com", "scitechdaily.com",
    "sciencenews.org", "statnews.com", "npr.org",
    "nytimes.com", "theguardian.com",
    "mdpi.com", "frontiersin.org",
]
    
    fontes = []
    seen_sources = set()
    
    for item in results:
        url = item.get("url", "")
        netloc = item.get("meta_url", {}).get("netloc", url)
        
        # Normalize
        for rel in reliable:
            if rel in netloc.lower():
                if netloc not in seen_sources:
                    seen_sources.add(netloc)
                    fontes.append({
                        "site": netloc,
                        "title": item.get("title", "")[:100],
                        "url": url
                    })
                break
    
    return fontes[:8]  # Máximo 8 fontes
```

### PASSO 6: Verificar PDF Free Full Text

```python
def get_pmc_link(pmid):
    """Verificar se o estudo tem PMC free full text."""
    r = requests.get(
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
        params={"db": "pmc", "term": f"{pmid}[pmid]", "retmode": "json"},
        timeout=15
    )
    try:
        ids = r.json()["esearchresult"].get("idlist", [])
        if ids:
            return f"https://www.ncbi.nlm.nih.gov/pmc/articles/{ids[0]}/pdf/"
    except:
        pass
    return None
```

### PASSO 7: Gerar Tags

```python
def generate_tags(news_title, keywords):
    """Gerar 8 tags em pt-BR para a notícia."""
    tag_map = {
        "breast cancer": "câncer de mama",
        "breast": "câncer de mama",
        "ovarian": "câncer de ovário",
        "cervical": "câncer cervical",
        "endometriosis": "endometriose",
        "menopause": "menopausa",
        "menopausal": "menopausa",
        "pcos": "SOP",
        "polycystic": "síndrome dos ovários policísticos",
        "pregnancy": "gravidez",
        "pregnant": "gravidez",
        "maternal": "saúde materna",
        "postpartum": "pós-parto",
        "depression": "depressão",
        "anxiety": "ansiedade",
        "mental health": "saúde mental",
        "cardiovascular": "saúde cardiovascular",
        "heart": "doença cardíaca",
        "thyroid": "tireoide",
        "autoimmune": "doença autoimune",
        "lupus": "lúpus",
        "osteoporosis": "osteoporose",
        "bone": "saúde óssea",
        "hpv": "HPV",
        "fertility": "fertilidade",
        "reproductive": "reprodução",
        "gynecology": "ginecologia",
        "treatment": "tratamento",
        "diagnosis": "diagnóstico",
        "prevention": "prevenção",
        "research": "pesquisa",
        "study": "estudo",
        "clinical trial": "ensaio clínico",
        "symptoms": "sintomas",
        "risk": "fatores de risco",
        "women": "saúde da mulher",
        "female": "saúde feminina",
    }
    
    title_lower = news_title.lower()
    found_tags = set()
    
    for eng, pt in tag_map.items():
        if eng in title_lower:
            found_tags.add(pt)
    
    # Adicionar keywords do PubMed
    for kw in keywords[:3]:
        if kw not in tag_map:
            found_tags.add(kw)
    
    # Preencher até 8 tags
    default_tags = ["saúde da mulher", "pesquisa", "prevenção", "tratamento"]
    for tag in default_tags:
        if len(found_tags) >= 8:
            break
        found_tags.add(tag)
    
    return list(found_tags)[:8]
```

### PASSO 8: Montar Output Final

```
🌸 SAÚDE DA MULHER — NOTÍCIAS DO DIA [DATA]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[NOTÍCIA 1]

📌 Título (pt-BR): [título da notícia traduzido para pt-BR]
📰 Fonte: [Nome do site] — [URL]
📝 Resumo: [do próprio artigo ou descrição da Brave]

📚 Estudos Científicos:
1. [Título] — PMID: XXXXX | DOI: 10.XXXX | https://pubmed.ncbi.nlm.nih.gov/XXXXX/
[... até 5 estudos ...]

🔍 Verificação Cruzada (X sites):
1. [Site 1] — [URL]
[... pelo menos 4 sites ...]

🏷️ Tags: [8 tags em pt-BR]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Regras para o output:**
- Título: traduzir para pt-BR com precisão
- Fonte: usar o nome do site real e URL da notícia
- Resumo: do próprio artigo (description da Brave) ou abstract do PubMed
- Estudos: os 5 mais recentes/relevantes do PubMed
- Cross-check: mínimo 4 sites que noticiaram o tema (pode incluir a fonte original se for de saúde)
- Tags: exactamente 8 em pt-BR

---

## Regras de Conduta

- **NUNCA fabricar notícias.** Se não há 15 notícias que passem no filtro num dia, entregar apenas as que passam (mesmo que sejam 8 ou 10).
- **NUNCA fabricar estudos.** Todos os PMIDs e DOIs devem ser validados via EUtils.
- **NUNCA fabricar fontes de cross-check.** Se uma notícia só aparece em 1 site, indicar isso.
- **Se uma notícia não tem 5 estudos:** incluir apenas os que existem e indicar "(apenas X estudos disponíveis)"
- **Sempre traduzir títulos para pt-BR** — tradução precisa, não automática.
- **Data do relatório:** `DD de [mês] de [ano]`

---

## CRITICAL PITFALLS (learned 04/05/2026)

### ⚠️ WRONG FLOW: PubMed as primary news source
**Problem:** Earlier version used PubMed as the source of "news" — outputting PubMed journal articles as if they were news. Cross-check then returned PubMed links too. This is WRONG.

**Correct flow (permanent):**
1. `Brave News API` → real news from health sites (ScienceDaily, Nature, MedicalXpress, etc.)
2. `PubMed EUtils` → validate each news item with 5 scientific studies
3. `Brave News API` → cross-check: find 4+ other news sites that covered the same topic

**Never:** Use PubMed as the "news" itself. PubMed is a scientific database, not a news source.

### ⚠️ Brave News: freshness=pd returns almost nothing
**Problem:** `freshness=pd` returns near-zero results for specialized health queries on free tier.
**Solution:** Omit `freshness`. Filter by `page_age` field instead (14-day cutoff).

### ⚠️ Brave Web Search API requires paid plan
**Problem:** `https://api.search.brave.com/res/v1/search` → HTTP 301 redirect.
**Solution:** Always use `https://api.search.brave.com/res/v1/news/search` (free tier works).

### ⚠️ Use meta_url.netloc for source filtering
**Problem:** Filtering on full URL string is fragile.
**Solution:** Use `item.get("meta_url", {}).get("netloc", "")` → clean domain like `"sciencedaily.com"`.

### ⚠️ Cross-check: PubMed is NOT a news source
**Problem:** Earlier version returned PubMed links in the cross-check section.
**Solution:** Cross-check must return actual news sites. PubMed links go ONLY in "Estudos Científicos".

### ⚠️ Ahead-of-Print articles: empty abstracts
**Problem:** PubMed 2026 articles often have 0-char abstracts (ahead of print).
**Solution:** See `references/ahead-of-print-articles.md` — combine 2026 + 2025 articles.

---

## Anti-Padrões

- **NÃO usar PubMed como fonte primária de notícias** — PubMed é para validação científica, não para notícias
- **NÃO incluir links do PubMed como "fontes de cross-check"** — cross-check deve ser sites de notícias/jornais
- **NÃO aceitar horóscopos, notícias de celebridades** ou topics não relacionados a saúde feminina
- **NÃO incluir PubMed como "notícia"** — PubMed é base de dados científica, não site de notícias
- **NÃO usar freshness=pd** — usar filtro de page_age

---

*Skill reescrita: 04/05/2026 — Bianinho OS*
*Fluxo: Brave News (notícias reais) → PubMed (validação científica) → Cross-check (Brave News)*
