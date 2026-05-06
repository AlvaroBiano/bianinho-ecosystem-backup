# ahead-of-print-articles — PubMed timing issue

## O problema

Artigos PubMed muito recentes (especialmente Abril–Maio 2026) frequentemente aparecem no PubMed com:
- DOI ✅
- Metadata (título, journal, data, authors) ✅
- **Abstract: VAZIO (0 chars)** ❌

O PubMed marca estes como *"Ahead of Print"* ou *"Epub ahead of print"* — o abstract ainda não foi publicado no PubMed mesmo quando o DOI do journal já existe.

## Diagnóstico

```python
def is_ahead_of_print(pmid):
    abstract = get_abstract(pmid)  # EFetch
    return len(abstract) < 100  # ahead-of-print se abstract vazio
```

## Solução: combinar 2026 + 2025

Na prática, para o workflow de 15 notícias:

1. **Buscar PMIDs** com queries de 2025:2026
2. **Filtrar** os top 30 por score de relevância
3. **Validar abstract** de cada um com EFetch
4. **Substituir** os que têm abstract < 100 chars por artigos de 2024-2025 que já tenham abstract completo

```python
# Exemplo de combinação (teste real 04/05/2026):
artigos_2026_ok = [
    '42074694',  # abstract 2045 chars ✅
    '42076785',  # abstract 3659 chars ✅
    '41961399',  # abstract 2019 chars ✅
    '42063789',  # abstract 2013 chars ✅
    '42062769',  # abstract 1307 chars ✅
    '42073634',  # abstract 1797 chars ✅
    '41961878',  # abstract 3042 chars ✅
    '42072331',  # abstract 2068 chars ✅
    '42074393',  # abstract 2014 chars ✅
    '42072936',  # abstract 1804 chars ✅
    '42072806',  # abstract 1990 chars ✅
    '42071031',  # abstract 1419 chars ✅
    '42067880',  # abstract 2041 chars ✅
]
# Completar com artigos de 2025 que tinham abstract
artigos_2025_complemento = [
    '41473631',  # abstract 1378 chars — Thyroid + Gestational Diabetes
    '41299347',  # abstract 1959 chars — Postpartum Depression EPDS
]
```

## Queries que mais retornam ahead-of-print

Artigos de journals como **Nutrients**, **J Clin Med**, **Frontiers** que publicam online-first frequentemente ficam 2-4 semanas sem abstract no PubMed.

**Estratégia:** sempre buscar 50% mais PMIDs do que o necessário e ter uma lista de replacements de 2024-2025 pronta.

## Referência

Teste real: 04/05/2026 — 15/30 PMIDs eram ahead-of-print (abstract 0 chars). Complementados com 2 artigos de 2025.
