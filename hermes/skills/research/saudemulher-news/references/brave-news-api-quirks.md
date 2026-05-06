# Brave News API — Quirks Descobertos (04/05/2026)

## Auth
```bash
source ~/.hermes/.env && echo $BRAVE_SEARCH_API_KEY
# Key starts with "BSA46H..." — free tier: 2,000 queries/month
```

## News API vs Web Search API
- **News API** (free tier OK): `https://api.search.brave.com/res/v1/news/search`
- **Web Search API** (requires paid plan): `https://api.search.brave.com/res/v1/search` → returns 301 redirect to dashboard

Always use the **News API**.

## freshness=pd — NÃO USAR
The `freshness=pd` (past day) parameter returns near-zero results for specialized health queries. The free tier handles it poorly.

**Solution:** Omit `freshness` entirely. Filter by `page_age` field instead:
```python
cutoff = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d")
if page_age < cutoff:
    continue  # skip old news
```

## Response Structure
```python
{
    "title": "...",
    "url": "https://...",           # Full article URL
    "description": "...",
    "page_age": "2026-05-04T...",  # ISO datetime
    "meta_url": {
        "scheme": "https",
        "netloc": "sciencedaily.com",    # ← use this for filtering
        "hostname": "www.sciencedaily.com",
        "path": "/news/..."
    },
    "profile": {...},
    "thumbnail": {...}
}
```
**Key:** `item.get("meta_url", {}).get("netloc", "")` gives the clean domain for filtering.

## Cross-check reliable sources list
```python
RELIABLE = [
    "who.int", "nih.gov", "pubmed",
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
    "sciencenews.org", "statnews.com",
    "nytimes.com", "theguardian.com", "mdpi.com",
    "hindustantimes.com", "euronews.com",
    "southcarolinapublicradio.org",
]
```

## Skip Patterns (Noise Filter)
Always filter out:
```python
skip = ["horoscope", "ganeshaspeaks", "zodiac",
        "celebrity", "kylie", "kim kardashian", "tom brady"]
if any(p in url.lower() or p in title.lower() for p in skip):
    continue
```

## Test results (04/05/2026)
- 6 queries × 10 results = 60 raw → ~43 deduplicated unique health news
- ~10-15% noise (horoscopes, celebrities) filtered by skip patterns
- Date filter (14 days): removes ~20% old results
- Reliable source filter: ~30-40% of remaining qualify

## Verified working query themes
```
"breast cancer women treatment 2026"
"endometriosis research treatment 2026"
"menopause symptoms women 2026"
"PCOS polycystic ovary women 2026"
"pregnancy maternal health 2026"
"women heart disease cardiovascular 2026"
"autoimmune disease women 2026"
"bone health osteoporosis women"
"thyroid disorder women research"
"postpartum depression maternal mental health 2026"
```
