---
name: pubmed-research
description: Pesquisa científica avançada na PubMed com rate limiting, validação de dados e coleta completa de metadados. Ideal para coletar referências para livros, artigos, vídeos e materiais científicos.
category: research
---

# PubMed Research Skill

## Propósito
Busca científica avançada na PubMed com:
- Rate limiting integrado (3 req/s respeitado)
- Validação obrigatória de todos os dados
- Coleta completa de metadados
- Suporte a múltiplas queries simultâneas
- Deduplicação automática de resultados
- Exportação em JSON e Markdown

## API Base
`https://eutils.ncbi.nlm.nih.gov/entrez/eutils/`

## Rate Limiting
- **OBRIGATÓRIO**: `time.sleep(0.34)` entre cada chamada HTTP
- Nunca fazer requisições paralelas
- Priorizar: ESearch + ESummary (2 chamadas por lote)

## Como usar

### Via terminal (script direto)
```bash
python3 ~/.hermes/skills/pubmed-research/pubmed_researcher.py --queries "thyroid cancer natural treatment,thyroid cancer supplementation,thyroid cancer intermittent fasting" --min-date 2019 --max-date 2026 --per-query 10 --output thyroid_research
```

### Via código Python
```python
from pubmed_research import PubMedResearch

researcher = PubMedResearch()

queries = [
    {"termo": "thyroid cancer natural treatment", "tema": "Tratamento Natural"},
    {"termo": "thyroid cancer supplementation", "tema": "Suplementação"},
    {"termo": "thyroid cancer intermittent fasting", "tema": "Jejum Intermitente"},
    {"termo": "thyroid cancer selenium", "tema": "Selênio"},
    {"termo": "thyroid cancer vitamin D", "tema": "Vitamina D"},
    {"termo": "thyroid cancer curcumin", "tema": "Curcumina"},
    {"termo": "thyroid cancer immunotherapy", "tema": "Imunoterapia"},
    {"termo": "thyroid cancer autophagy", "tema": "Autofagia"},
    {"termo": "thyroid cancer dietary intervention", "tema": "Intervenção Dietética"},
    {"termo": "thyroid cancer botanical", "tema": "Plantas Medicinais"},
]

resultados = researcher.pesquisar_robusta(
    queries=queries,
    min_date="2019",
    max_date="2026",
    por_query=10,
    total_desejado=100
)

researcher.salvar_json(resultados, "resultados.json")
researcher.salvar_markdown(resultados, "resultados.md")
```

## Queries Recomendadas para Câncer de Tireoide

### Tratamento Natural
- `thyroid cancer[tiab] AND natural treatment[tiab]`
- `thyroid cancer[tiab] AND herbal medicine[tiab]`
- `thyroid cancer[tiab] AND essential oil[tiab]`
- `thyroid cancer[tiab] AND botanical[tiab]`
- `thyroid cancer[tiab] AND medicinal plant[tiab]`
- `thyroid cancer[tiab] AND complementary therapy[tiab]`

### Suplementação
- `thyroid cancer[tiab] AND supplementation[tiab]`
- `thyroid cancer[tiab] AND selenium[tiab]`
- `thyroid cancer[tiab] AND vitamin D[tiab]`
- `thyroid cancer[tiab] AND curcumin[tiab]`
- `thyroid cancer[tiab] AND antioxidant[tiab]`
- `thyroid cancer[tiab] AND omega-3[tiab]`
- `thyroid cancer[tiab] AND zinc[tiab]`
- `thyroid cancer[tiab] AND magnesium[tiab]`

### Jejum e Dieta
- `thyroid cancer[tiab] AND intermittent fasting[tiab]`
- `thyroid cancer[tiab] AND fasting[tiab]`
- `thyroid cancer[tiab] AND calorie restriction[tiab]`
- `thyroid cancer[tiab] AND autophagy[tiab]`
- `thyroid cancer[tiab] AND ketogenic diet[tiab]`
- `thyroid cancer[tiab] AND plant-based diet[tiab]`

### Imunoterapia e Integrative Oncology
- `thyroid cancer[tiab] AND immunotherapy[tiab]`
- `thyroid cancer[tiab] AND integrative oncology[tiab]`
- `thyroid cancer[tiab] AND lifestyle intervention[tiab]`
- `thyroid cancer[tiab] AND mind-body[tiab]`
- `thyroid cancer[tiab] AND stress management[tiab]`

## Campos de Busca do PubMed

| Código | Campo | Uso |
|--------|-------|-----|
| `ALL` | Todos os campos | Busca geral |
| `TIAB` | Title/Abstract | Busca ampla |
| `MH` | MeSH Terms | Busca hierárquica |
| `PT` | Publication Type | Filtrar tipo |
| `DP` | Publication Date | Filtrar por data |
| `AID` | Article ID (DOI) | Validar DOI |

### Publication Types úteis
- `systematic[pt]` — Revisão sistemática
- `meta-analysis[pt]` — Meta-análise
- `review[pt]` — Revisão
- `clinical trial[pt]` — Ensaio clínico
- `randomized controlled trial[pt]` — RCT

## Validação de Dados (OBRIGATÓRIO)

### Regras
1. **NUNCA fabricar** PMID, DOI, título, autor
2. Verificar PMID via ESummary antes de usar
3. Validar DOI via busca `DOI[aid]`
4. Se artigo não encontrado → descartar, não inventar
5. Se不确定 → marcar `[NAO VERIFICADO]`

### Checklist de Validação
- [ ] PMID existe no PubMed?
- [ ] Título corresponde ao PMID?
- [ ] DOI é válido?
- [ ] Autores estão listados?
- [ ] Journal é reconhecido?
- [ ] Data está no range?
- [ ] Abstract disponível?

## Estrutura de Dados

```python
{
    "pmid": str,
    "title": str,
    "authors": List[str],
    "journal": str,
    "pubdate": str,
    "doi": str,
    "abstract": str,
    "pubtype": List[str],
    "mesh_terms": List[str],
    "pmc_id": str,
    "full_text_url": str,
    "query_origem": str,
    "tema": str,
    "validado": bool,
    "data_coleta": str  # ISO timestamp
}
```

## Endpoints da API

### ESearch — Buscar PMIDs
```
GET https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi
Params: db=pubmed&term=QUERY&mindate=YYYY&maxdate=YYYY&retmax=N&retmode=json&sort=relevance
```

### ESummary — Resumo bibliográfico
```
GET https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi
Params: db=pubmed&id=PMID1,PMID2&retmode=json
```

### EFetch — Dados completos (inclui abstract)
```
GET https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi
Params: db=pubmed&id=PMID&rettype=abstract&retmode=text
```

### ELink — Full text no PMC
```
GET https://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi
Params: dbfrom=pubmed&db=pmc&id=PMID&linkname=pubmed_pmc
```

## Rate Limiting Implementado

```python
import time

def rate_limited_call(func, *args, **kwargs):
    """Executa função com rate limit de 3 req/s"""
    result = func(*args, **kwargs)
    time.sleep(0.34)  # 3 req/s = 0.333...s entre calls
    return result
```

## Output Formats

### JSON
```json
{
  "metadata": {
    "total_resultados": 50,
    "data_coleta": "2026-04-17T12:00:00",
    "queries_executadas": 10,
    "tempo_total_segundos": 30
  },
  "resultados": [...]
}
```

### Markdown
```markdown
# Referências Científicas — Câncer de Tireoide

## 1. Título do Estudo
- **PMID**: 12345678
- **DOI**: 10.xxxx/xxxxx
- **Autores**: Silva et al.
- **Journal**: Journal X (2024)
- **Tipo**: Revisão Sistemática
- **Abstract**: ...
- **MeSH**: Term1, Term2
- **Full Text**: [Link PMC]
```

## Troubleshooting

### "Rate limit exceeded"
→ Aumentar sleep para 0.5s entre chamadas

### "Too many requests"
→ Parar por 60 segundos e continuar

### PMID não encontrado
→ Descartar, não fabricar dados

### Abstract vazio
→ Buscar via EFetch com rettype=abstract

## Arquivos da Skill
- `pubmed_researcher.py` — Script principal
- `SKILL.md` — Esta documentação
