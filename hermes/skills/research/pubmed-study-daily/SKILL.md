---
name: pubmed-study-daily
description: "Pesquisa diária de 5 estudos científicos recentes sobre um tema rotativo de saúde feminina — PubMed, livre acesso, com análise detalhada em português do Brasil. Cron: diario às 23:00."
tags: [pubmed, saúde-da-mulher, pesquisa, cron, estudos-científicos]
---

# PubMed Study Daily — Pesquisa Diária de Estudos Científicos

## Mandato

Todos os dias às 23:00, seleccionar um título da lista de 50 temas de saúde feminina e pesquisar os 5 estudos mais recentes (≤5 anos), de livre acesso (Open Access / Free Full Text), que tragam maior entendimento sobre o tema.

Formato de entrega em **português do Brasil** — todos os títulos, resumos e conclusões traduzidos.

---

## Os 50 Títulos de Saúde Feminina

Cada título tem:
- **PT-BR**: para exibição no relatório
- **EN**: para query PubMed (inglês)

```
1.  PT: Autoimunidade e inflamação crónica na mulher
    EN: autoimmune AND chronic inflammation AND women

2.  PT: Doenças autoimunes e risco cardiovascular feminino
    EN: autoimmune disease AND cardiovascular risk AND women

3.  PT: Tireoidite de Hashimoto e saúde reprodutiva
    EN: hashimoto thyroiditis AND reproductive health AND women

4.  PT: Lúpus eritematoso sistémico e gravidez
    EN: systemic lupus erythematosus AND pregnancy AND women

5.  PT: Síndrome de Sjögren e qualidade de vida na mulher
    EN: sjogrens syndrome AND quality of life AND women

6.  PT: Endometriose: mecanismos imunológicos e inflamatórios
    EN: endometriosis AND immune mechanisms AND inflammation

7.  PT: SOP e inflamação de baixo grau: novas perspectivas
    EN: PCOS AND low grade inflammation AND women

8.  PT: Miomas uterinos e microambiente inflamatório
    EN: uterine fibroids AND inflammatory microenvironment AND women

9.  PT: Adenomiose: base inflamatória e clínica
    EN: adenomyosis AND inflammation AND women

10. PT: Menopausa e inflamação sistémica
    EN: menopause AND systemic inflammation AND women

11. PT: Envelhecimento ovariano e estrés oxidativo
    EN: ovarian aging AND oxidative stress AND women

12. PT: Reserva ovariana e biomarcadores imunológicos
    EN: ovarian reserve AND immunological biomarkers AND women

13. PT: Infertilidade de causa imune: diagnóstico e tratamento
    EN: immune infertility AND diagnosis AND treatment AND women

14. PT: Falência ovariana prematura e autoanticorpos
    EN: premature ovarian failure AND autoantibodies AND women

15. PT: Trombocitopenia imune e gravidez
    EN: immune thrombocytopenia AND pregnancy AND women

16. PT: Pré-eclâmpsia como estado inflamatório
    EN: preeclampsia AND inflammatory state AND pregnancy

17. PT: Diabetes gestacional e resposta imune
    EN: gestational diabetes AND immune response AND pregnancy

18. PT: Infecções na gravidez e programação fetal imune
    EN: pregnancy infection AND fetal immune programming AND women

19. PT: Microbiota intestinal e saúde feminina
    EN: gut microbiota AND women health AND female

20. PT: Eixo intestino-cérebro na depressão pós-parto
    EN: gut brain axis AND postpartum depression AND women

21. PT: Probióticos e prevenção de infeções genitais
    EN: probiotics AND genital infection prevention AND women

22. PT: Vacinação HPV e resposta imune na mulher
    EN: HPV vaccination AND immune response AND women

23. PT: Cancro de mama triplo negativo e microambiente imune
    EN: triple negative breast cancer AND immune microenvironment AND women

24. PT: Imunoterapia no cancro de ovário
    EN: immunotherapy AND ovarian cancer AND women

25. PT: Biomarcadores imunes no cancro endometrial
    EN: immune biomarkers AND endometrial cancer AND women

26. PT: Carga alostática na mulher: inflamação crónica e saúde mental
    EN: allostatic load AND chronic inflammation AND women mental health

27. PT: Fibromialgia e disregulação imune feminina
    EN: fibromyalgia AND immune dysregulation AND women

28. PT: Enxaqueca crónica e inflamação neurogénica
    EN: chronic migraine AND neurogenic inflammation AND women

29. PT: Osteoporose pós-menopausa e citoquinas
    EN: postmenopausal osteoporosis AND cytokines AND women

30. PT: Perda gestacional recorrente e etiologia imune
    EN: recurrent pregnancy loss AND immune etiology AND women

31. PT: Síndrome de antifosfolípido e trombose
    EN: antiphospholipid syndrome AND thrombosis AND women

32. PT: Infertilidade inexplicada e tratamento imune
    EN: unexplained infertility AND immune treatment AND women

33. PT: Cell-free DNA e rastreamento pré-natal não invasivo
    EN: cell-free DNA AND non-invasive prenatal testing AND women

34. PT: Exposição a ftalatos e desregulação endócrina
    EN: phthalate exposure AND endocrine disruption AND women

35. PT: Disruptores endócrinos e saúde reprodutiva feminina
    EN: endocrine disruptors AND female reproductive health AND women

36. PT: Poluentes ambientais e menopausa precoce
    EN: environmental pollutants AND early menopause AND women

37. PT: Obesidade e inflamação na síndrome metabólica feminina
    EN: obesity AND inflammation AND metabolic syndrome AND women

38. PT: Síndrome metabólica e risco de cancro endometrial
    EN: metabolic syndrome AND endometrial cancer risk AND women

39. PT: Resistência à insulina na SOP: mecanismos inflamatórios
    EN: insulin resistance AND PCOS AND inflammatory mechanisms AND women

40. PT: Esteatose hepática não alcoólica na mulher
    EN: non-alcoholic fatty liver disease AND women AND inflammation

41. PT: Doença cardiovascular na mulher: papel da inflamação
    EN: cardiovascular disease AND women AND inflammation AND role

42. PT: AVC isquémico e factores de risco inflamatórios na mulher
    EN: ischemic stroke AND inflammatory risk factors AND women

43. PT: Depressão e inflamação: diferenças de género
    EN: depression AND inflammation AND gender differences AND women

44. PT: Ansiedade crónica e marcadores inflamatórios femininos
    EN: chronic anxiety AND inflammatory markers AND women

45. PT: Perturbações do sono e inflamação na mulher
    EN: sleep disorders AND inflammation AND women

46. PT: Exercício físico e modulação imune na mulher
    EN: exercise AND immune modulation AND women

47. PT: Nutracêuticos anti-inflamatórios na saúde feminina
    EN: anti-inflammatory nutraceuticals AND women health AND female

48. PT: Jejum intermitente e inflamação na menopausa
    EN: intermittent fasting AND inflammation AND menopause AND women

49. PT: Suplementação com vitamina D e sistema imune feminino
    EN: vitamin D supplementation AND immune system AND women

50. PT: Mind-body interventions e redução de inflamação na mulher
    EN: mind body interventions AND inflammation reduction AND women
```

---

## Os 50 Títulos como Lista Python

```python
TOPICS = [
    {"pt": "Autoimunidade e inflamação crónica na mulher",
     "en": "autoimmune AND chronic inflammation AND women"},
    {"pt": "Doenças autoimunes e risco cardiovascular feminino",
     "en": "autoimmune disease AND cardiovascular risk AND women"},
    {"pt": "Tireoidite de Hashimoto e saúde reprodutiva",
     "en": "hashimoto thyroiditis AND reproductive health AND women"},
    {"pt": "Lúpus eritematoso sistémico e gravidez",
     "en": "systemic lupus erythematosus AND pregnancy AND women"},
    {"pt": "Síndrome de Sjögren e qualidade de vida na mulher",
     "en": "sjogrens syndrome AND quality of life AND women"},
    {"pt": "Endometriose: mecanismos imunológicos e inflamatórios",
     "en": "endometriosis AND immune mechanisms AND inflammation"},
    {"pt": "SOP e inflamação de baixo grau: novas perspectivas",
     "en": "PCOS AND low grade inflammation AND women"},
    {"pt": "Miomas uterinos e microambiente inflamatório",
     "en": "uterine fibroids AND inflammatory microenvironment AND women"},
    {"pt": "Adenomiose: base inflamatória e clínica",
     "en": "adenomyosis AND inflammation AND women"},
    {"pt": "Menopausa e inflamação sistémica",
     "en": "menopause AND systemic inflammation AND women"},
    {"pt": "Envelhecimento ovariano e estrés oxidativo",
     "en": "ovarian aging AND oxidative stress AND women"},
    {"pt": "Reserva ovariana e biomarcadores imunológicos",
     "en": "ovarian reserve AND immunological biomarkers AND women"},
    {"pt": "Infertilidade de causa imune: diagnóstico e tratamento",
     "en": "immune infertility AND diagnosis AND treatment AND women"},
    {"pt": "Falência ovariana prematura e autoanticorpos",
     "en": "premature ovarian failure AND autoantibodies AND women"},
    {"pt": "Trombocitopenia imune e gravidez",
     "en": "immune thrombocytopenia AND pregnancy AND women"},
    {"pt": "Pré-eclâmpsia como estado inflamatório",
     "en": "preeclampsia AND inflammatory state AND pregnancy"},
    {"pt": "Diabetes gestacional e resposta imune",
     "en": "gestational diabetes AND immune response AND pregnancy"},
    {"pt": "Infecções na gravidez e programação fetal imune",
     "en": "pregnancy infection AND fetal immune programming AND women"},
    {"pt": "Microbiota intestinal e saúde feminina",
     "en": "gut microbiota AND women health AND female"},
    {"pt": "Eixo intestino-cérebro na depressão pós-parto",
     "en": "gut brain axis AND postpartum depression AND women"},
    {"pt": "Probióticos e prevenção de infeções genitais",
     "en": "probiotics AND genital infection prevention AND women"},
    {"pt": "Vacinação HPV e resposta imune na mulher",
     "en": "HPV vaccination AND immune response AND women"},
    {"pt": "Cancro de mama triplo negativo e microambiente imune",
     "en": "triple negative breast cancer AND immune microenvironment AND women"},
    {"pt": "Imunoterapia no cancro de ovário",
     "en": "immunotherapy AND ovarian cancer AND women"},
    {"pt": "Biomarcadores imunes no cancro endometrial",
     "en": "immune biomarkers AND endometrial cancer AND women"},
    {"pt": "Carga alostática na mulher: inflamação crónica e saúde mental",
     "en": "allostatic load AND chronic inflammation AND women mental health"},
    {"pt": "Fibromialgia e disregulação imune feminina",
     "en": "fibromyalgia AND immune dysregulation AND women"},
    {"pt": "Enxaqueca crónica e inflamação neurogénica",
     "en": "chronic migraine AND neurogenic inflammation AND women"},
    {"pt": "Osteoporose pós-menopausa e citoquinas",
     "en": "postmenopausal osteoporosis AND cytokines AND women"},
    {"pt": "Perda gestacional recorrente e etiologia imune",
     "en": "recurrent pregnancy loss AND immune etiology AND women"},
    {"pt": "Síndrome de antifosfolípido e trombose",
     "en": "antiphospholipid syndrome AND thrombosis AND women"},
    {"pt": "Infertilidade inexplicada e tratamento imune",
     "en": "unexplained infertility AND immune treatment AND women"},
    {"pt": "Cell-free DNA e rastreamento pré-natal não invasivo",
     "en": "cell-free DNA AND non-invasive prenatal testing AND women"},
    {"pt": "Exposição a ftalatos e desregulação endócrina",
     "en": "phthalate exposure AND endocrine disruption AND women"},
    {"pt": "Disruptores endócrinos e saúde reprodutiva feminina",
     "en": "endocrine disruptors AND female reproductive health AND women"},
    {"pt": "Poluentes ambientais e menopausa precoce",
     "en": "environmental pollutants AND early menopause AND women"},
    {"pt": "Obesidade e inflamação na síndrome metabólica feminina",
     "en": "obesity AND inflammation AND metabolic syndrome AND women"},
    {"pt": "Síndrome metabólica e risco de cancro endometrial",
     "en": "metabolic syndrome AND endometrial cancer risk AND women"},
    {"pt": "Resistência à insulina na SOP: mecanismos inflamatórios",
     "en": "insulin resistance AND PCOS AND inflammatory mechanisms AND women"},
    {"pt": "Esteatose hepática não alcoólica na mulher",
     "en": "non-alcoholic fatty liver disease AND women AND inflammation"},
    {"pt": "Doença cardiovascular na mulher: papel da inflamação",
     "en": "cardiovascular disease AND women AND inflammation AND role"},
    {"pt": "AVC isquémico e factores de risco inflamatórios na mulher",
     "en": "ischemic stroke AND inflammatory risk factors AND women"},
    {"pt": "Depressão e inflamação: diferenças de género",
     "en": "depression AND inflammation AND gender differences AND women"},
    {"pt": "Ansiedade crónica e marcadores inflamatórios femininos",
     "en": "chronic anxiety AND inflammatory markers AND women"},
    {"pt": "Perturbações do sono e inflamação na mulher",
     "en": "sleep disorders AND inflammation AND women"},
    {"pt": "Exercício físico e modulação imune na mulher",
     "en": "exercise AND immune modulation AND women"},
    {"pt": "Nutracêuticos anti-inflamatórios na saúde feminina",
     "en": "anti-inflammatory nutraceuticals AND women health AND female"},
    {"pt": "Jejum intermitente e inflamação na menopausa",
     "en": "intermittent fasting AND inflammation AND menopause AND women"},
    {"pt": "Suplementação com vitamina D e sistema imune feminino",
     "en": "vitamin D supplementation AND immune system AND women"},
    {"pt": "Mind-body interventions e redução de inflamação na mulher",
     "en": "mind body interventions AND inflammation reduction AND women"},
]

def get_daily_topic():
    """Selecionar tema do dia (rotação cíclica pelos 50)."""
    from datetime import datetime
    day_of_year = datetime.now().timetuple().tm_yday
    index = (day_of_year - 1) % 50
    return TOPICS[index]
```

### PASSO 2: Pesquisar no PubMed (EUtils)

```python
import requests

def search_pubmed_free(topic_en, max_results=50):
    """Buscar artigos de livre acesso no PubMed, últimos 5 anos.
    
    Args:
        topic_en: query em INGLÊS (do campo 'en' do TOPICS)
    
    Filtros:
    - free[fulltext] (apenas artigos com PDF livre)
    - 2021:2026[dp] (últimos 5 anos)
    - Humans + Female
    """
    searches = [
        f"({topic_en}) AND free[fulltext] AND 2021:2026[dp] AND Female[Mesh] AND Humans[Mesh]",
        f"({topic_en}) AND free[fulltext] AND women[tiab] AND 2021:2026[dp]",
        f"({topic_en}) AND free[fulltext] AND female[tiab] AND 2021:2026[dp]",
    ]
    
    all_ids = []
    for q in searches:
        try:
            r = requests.get(
                "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
                params={"db": "pubmed", "term": q, "retmax": max_results,
                        "retmode": "json", "sort": "pub_date"},
                timeout=30
            )
            ids = r.json().get("esearchresult", {}).get("idlist", [])
            all_ids.extend(ids)
        except:
            pass
    
    # Deduplicate preserving order (most recent first)
    seen = set()
    unique = []
    for pid in all_ids:
        if pid not in seen:
            seen.add(pid)
            unique.append(pid)
    
    return unique[:max_results]
```

### PASSO 3: Obter Detalhes Completos via EFetch (com Abstract)

```python
def get_full_article_details(pmids):
    """Obter abstract e metadados completos via EFetch XML."""
    if not pmids:
        return []
    
    r = requests.get(
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi",
        params={
            "db": "pubmed",
            "id": ",".join(pmids),
            "rettype": "abstract",
            "retmode": "xml"
        },
        timeout=60
    )
    
    articles = parse_efetch_xml(r.text)
    return articles

def parse_efetch_xml(xml_content):
    """Parsear XML do EFetch para extrair dados estruturados."""
    from xml.etree import ElementTree as ET
    root = ET.fromstring(xml_content)
    articles = []
    
    for art in root.findall('.//PubmedArticle'):
        pmid = art.findtext('.//PMID')
        title = art.findtext('.//ArticleTitle', '')
        abstract_parts = []
        for abs_el in art.findall('.//AbstractText'):
            text = abs_el.text or ''
            abstract_parts.append(text.strip())
        abstract = ' '.join(abstract_parts)
        
        # Journal info
        journal = art.findtext('.//Journal/Title', '')
        pubdate_el = art.find('.//PubDate')
        if pubdate_el is not None:
            year = pubdate_el.findtext('Year', '')
            month = pubdate_el.findtext('Month', '01')
            day = pubdate_el.findtext('Day', '01')
            pubdate = f"{year}-{month}-{day}"
        else:
            pubdate = ''
        
        # DOI
        doi = ''
        for id_el in art.findall('.//ArticleId'):
            if id_el.get('IdType') == 'doi':
                doi = id_el.text or ''
                break
        
        # Authors (first 3)
        authors = []
        for aut in art.findall('.//Author')[:3]:
            last = aut.findtext('LastName', '')
            fore = aut.findtext('ForeName', '')
            if last:
                authors.append(f"{fore} {last}".strip())
        
        articles.append({
            'pmid': pmid,
            'title': title,
            'abstract': abstract,
            'journal': journal,
            'pubdate': pubdate,
            'doi': doi,
            'authors': authors
        })
    
    return articles
```

### PASSO 4: Verificar PDF e Link de Download

```python
def get_pmc_and_pdf_link(pmid):
    """Verificar se existe free full text no PMC e construir link PDF."""
    r = requests.get(
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
        params={"db": "pmc", "term": f"{pmid}[pmid]", "retmode": "json"},
        timeout=15
    )
    try:
        ids = r.json().get("esearchresult", {}).get("idlist", [])
        if ids:
            pmcid = ids[0]
            return {
                "pdf_url": f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/pdf/",
                "pmc_url": f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/"
            }
    except:
        pass
    
    # Fallback: tentar DOI direto para publisher
    return {"pdf_url": None, "pmc_url": None}

def get_article_pdf_via_doi(doi):
    """Tentar obter link PDF via DOI.org ou publisher."""
    if not doi:
        return None
    try:
        r = requests.get(f"https://doi.org/{doi}", timeout=10, allow_redirects=True)
        if r.status_code == 200:
            # DOI redirect para publisher — nem sempre dá PDF direto
            return r.url
    except:
        pass
    return None
```

### PASSO 5: Selecionar os 5 Melhores Estudos

```python
def select_best_articles(articles, top_n=5):
    """Selecionar os 5 artigos mais relevantes.
    
    Critérios:
    1. Deve ter abstract (sem abstract = descartar)
    2. Priorizar artigos com PMC free full text
    3. Priorizar os mais recentes
    4. Priorizar ensaios clínicos, meta-análises, revisões sistemáticas
    """
    scored = []
    for art in articles:
        if not art.get('abstract') or len(art['abstract']) < 100:
            continue
        
        score = 0
        # Abstract completo existe
        score += 10
        
        # Recência (mais recente = mais pontos)
        year = art.get('pubdate', '')[:4]
        if year:
            score += int(year) - 2020  # 2021=1, 2022=2, etc.
        
        # Keywords que indicam alta relevância
        title_lower = art.get('title', '').lower()
        high_value = ['systematic review', 'meta-analysis', 'clinical trial',
                      'randomized', 'cohort study', 'prospective', 'longitudinal']
        for kw in high_value:
            if kw in title_lower:
                score += 3
        
        scored.append((score, art))
    
    scored.sort(key=lambda x: -x[0])
    return [art for score, art in scored[:top_n]]
```

### PASSO 6: Traduzir para Português do Brasil

```python
TRANSLATIONS = {
    # Título original → tradução pt-BR
    # Manter como referência; a tradução é feita pelo LLM na saída final
}

def translate_title(title_en):
    """Traduzir título do inglês para português do Brasil.
    
    Regras:
    - Manter fidelidade ao conteúdo científico
    - Adaptar expressões idiomáticas
    - Usar terminologia médica brasileira padrão
    - Não usar tradução literal automática
    """
    # TRANSLATIONS é usado pelo LLM para referência
    # Esta função é placehold — a tradução real é feita na montagem final
    return title_en  # Placeholder
```

### PASSO 7: Montar Output Final

```
🔬 PESQUISA DIÁRIA — ESTUDOS CIENTÍFICOS
📅 [DATA] | Tema do dia: [TÍTULO DO DIA]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📚 ESTUDO 1

📖 Título original:
[Título em inglês]

📖 Título traduzido (pt-BR):
[Tradução precisa para português do Brasil]

📅 Data de publicação: [DD de Mês de AAAA]
📐 DOI: [DOI]
📰 Revista: [Nome da revista]

📝 Resumo:

[Parágrafo 1 — contexto e objectivos do estudo]

[Parágrafo 2 — metodologia e principais achados]

[Parágrafo 3 — implicações clínicas e limitações]

✅ Conclusões:
[Conclusões principais do estudo em 2-3 frases densas]

📥 PDF (livre acesso):
[Link direto para download do PDF — PMC ou publisher]
🔗 PubMed: https://pubmed.ncbi.nlm.nih.gov/[PMID]/

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[... repetir para os 5 estudos ...]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Pesquisa gerada automaticamente via PubMed EUtils API
Tema do dia {n/50}: {título}
"""
```

---

## Regras de Conduta

- **NUNCA fabricar estudos.** Todos os PMIDs, DOIs e abstracts devem ser reais e validados via EUtils.
- **NUNCA publicar sem abstract.** Se um estudo não tem abstract disponível, substituí-lo pelo próximo mais relevante.
- **Se houver menos de 5 estudos com PDF livre:** incluir apenas os disponíveis e indicar "(apenas X estudos com PDF livre disponíveis)".
- **Traduzir com precisão científica** — não usar tradução automática.
- **Sempre incluir link PDF funcional** — verificar antes de publicar.

---

## Anti-Padrões

- Não incluir artigos sem abstract (muitos "ahead of print" não têm abstract)
- Não aceitar DOIs de paywalled articles
- Não usar sites de盗墓 (ResearchGate, Academia.edu) como fonte de PDF
- Não incluir resumos de Congress or Conferences sem peer review

---

## Notas Técnicas

- PubMed EUtils ESearch: https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi
- PubMed EUtils EFetch: https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi
- PMC: https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pmc
- Rate limit: ~3 req/s; usar delays de 0.3-0.5s entre chamadas
- DOI API: https://doi.org/[DOI] → redirect para publisher

---

*Skill criada: 04/05/2026 — Bianinho OS*
*Pesquisa: PubMed EUtils API (100% livre) | 5 estudos Open Access | Temas de saúde feminina*
