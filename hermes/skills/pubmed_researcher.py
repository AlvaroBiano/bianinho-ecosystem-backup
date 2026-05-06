#!/usr/bin/env python3
"""
PubMed Research Tool — Busca científica avançada com rate limiting
17/04/2026

Uso:
    python3 pubmed_researcher.py --queries "thyroid cancer treatment,thyroid cancer fasting" --per-query 10 --min-date 2019 --max-date 2026
"""

import requests
import time
import json
import argparse
import sys
import re
from datetime import datetime
from typing import List, Dict, Any, Optional

# ========================
# CONSTANTES
# ========================
BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
RATE_LIMIT = 0.34  # segundos entre chamadas (3 req/s)
TIMEOUT = 30

# ========================
# CLASSES
# ========================

class PubMedResearch:
    """Ferramenta de pesquisa científica na PubMed com rate limiting."""

    def __init__(self, api_key: Optional[str] = None):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'PubMed-Research-Tool/1.0 (research purposes)'
        })
        self.api_key = api_key
        self.stats = {
            'total_calls': 0,
            'artigos_coletados': 0,
            'tempo_total': 0,
            'queries_executadas': 0
        }

    def _rate_limited_get(self, url: str, params: dict = None) -> requests.Response:
        """Faz GET com rate limiting obrigatório."""
        time.sleep(RATE_LIMIT)
        self.stats['total_calls'] += 1
        response = self.session.get(url, params=params, timeout=TIMEOUT)
        response.raise_for_status()
        return response

    def validar_pmid(self, pmid: str) -> bool:
        """Valida se PMID existe na PubMed."""
        try:
            r = self._rate_limited_get(
                f"{BASE_URL}esummary.fcgi",
                params={'db': 'pubmed', 'id': pmid, 'retmode': 'json'}
            )
            data = r.json()
            return pmid in data.get('result', {})
        except Exception:
            return False

    def validar_doi(self, doi: str) -> Optional[str]:
        """Valida DOI e retorna PMID se existir."""
        try:
            clean_doi = doi.replace('doi: ', '').strip()
            r = self._rate_limited_get(
                f"{BASE_URL}esearch.fcgi",
                params={
                    'db': 'pubmed',
                    'term': f'{clean_doi}[aid]',
                    'retmax': 1,
                    'retmode': 'json'
                }
            )
            result = r.json().get('esearchresult', {})
            ids = result.get('idlist', [])
            if ids:
                return ids[0]
            return None
        except Exception:
            return None

    def buscar_pmids(self, query: str, min_date: str = "2019", max_date: str = "2026",
                    retmax: int = 20, sort: str = "relevance") -> List[str]:
        """Busca PMIDs por query."""
        try:
            r = self._rate_limited_get(
                f"{BASE_URL}esearch.fcgi",
                params={
                    'db': 'pubmed',
                    'term': query,
                    'mindate': min_date,
                    'maxdate': max_date,
                    'retmax': retmax,
                    'retmode': 'json',
                    'sort': sort
                }
            )
            result = r.json().get('esearchresult', {})
            return result.get('idlist', [])
        except Exception as e:
            print(f"    [ERRO] Busca falhou: {e}")
            return []

    def buscar_pmids_pubtype(self, query: str, pubtype: str,
                            min_date: str = "2019", max_date: str = "2026",
                            retmax: int = 10) -> List[str]:
        """Busca PMIDs por query + tipo de publicação."""
        full_query = f"{query} AND {pubtype}[pt]"
        return self.buscar_pmids(full_query, min_date, max_date, retmax)

    def coletar_metadados(self, pmids: List[str]) -> List[Dict]:
        """Coleta metadados de uma lista de PMIDs via ESummary."""
        if not pmids:
            return []

        # Batch de até 100 PMIDs por chamada
        resultados = []
        batch_size = 100

        for i in range(0, len(pmids), batch_size):
            batch = pmids[i:i+batch_size]
            ids_str = ','.join(batch)

            try:
                r = self._rate_limited_get(
                    f"{BASE_URL}esummary.fcgi",
                    params={'db': 'pubmed', 'id': ids_str, 'retmode': 'json'}
                )
                data = r.json().get('result', {})

                for pmid in batch:
                    if pmid in data:
                        artigo = self._parse_esummary(pmid, data[pmid])
                        if artigo:
                            resultados.append(artigo)

            except Exception as e:
                print(f"    [ERRO] Coleta de metadados falhou: {e}")

        return resultados

    def _parse_esummary(self, pmid: str, data: dict) -> Optional[Dict]:
        """Parseia dados do ESummary."""
        try:
            # Extrair DOI
            eloc = data.get('elocationid', '')
            doi = ''
            if 'doi:' in eloc:
                doi = eloc.replace('doi:', '').strip()
            elif eloc.startswith('10.'):
                doi = eloc.strip()

            # Extrair autores
            authors = []
            for a in data.get('authors', []):
                name = a.get('name', '')
                if name:
                    authors.append(name)

            # PMC ID
            pmc_id = ''
            articleids = data.get('articleids', [])
            for ai in articleids:
                if ai.get('idtype') == 'pmc':
                    pmc_id = ai.get('value', '')
                    break

            return {
                'pmid': pmid,
                'title': data.get('title', '').strip(),
                'authors': authors,
                'lastauthor': data.get('lastauthor', ''),
                'journal': data.get('source', ''),
                'full_journal_name': data.get('fulljournalname', ''),
                'pubdate': data.get('pubdate', ''),
                'epubdate': data.get('epubdate', ''),
                'doi': doi,
                'pmc_id': pmc_id,
                'pubtype': data.get('pubtype', []),
                'lang': data.get('lang', []),
                'pmc_ref_count': data.get('pmcrefcount', 0),
                'record_status': data.get('recordstatus', ''),
                'sort_pubdate': data.get('sortpubdate', ''),
            }
        except Exception as e:
            print(f"    [ERRO] Parse de {pmid}: {e}")
            return None

    def coletar_abstract(self, pmid: str) -> str:
        """Coleta abstract de um artigo via EFetch."""
        try:
            r = self._rate_limited_get(
                f"{BASE_URL}efetch.fcgi",
                params={
                    'db': 'pubmed',
                    'id': pmid,
                    'rettype': 'abstract',
                    'retmode': 'text'
                }
            )
            return r.text.strip()
        except Exception:
            return ''

    def coletar_mesh(self, pmid: str) -> List[str]:
        """Coleta MeSH terms de um artigo via EFetch."""
        try:
            r = self._rate_limited_get(
                f"{BASE_URL}efetch.fcgi",
                params={
                    'db': 'pubmed',
                    'id': pmid,
                    'rettype': 'xml',
                    'retmode': 'xml'
                }
            )
            # Parse simples de XML
            import xml.etree.ElementTree as ET
            root = ET.fromstring(r.text)
            mesh_terms = []
            for mesh in root.iter('MeshHeading'):
                desc = mesh.find('DescriptorName')
                if desc is not None and desc.text:
                    mesh_terms.append(desc.text)
            return mesh_terms
        except Exception:
            return []

    def encontrar_fulltext_pmc(self, pmid: str) -> str:
        """Encontrar link full-text no PMC."""
        try:
            r = self._rate_limited_get(
                f"{BASE_URL}elink.fcgi",
                params={
                    'dbfrom': 'pubmed',
                    'db': 'pmc',
                    'id': pmid,
                    'linkname': 'pubmed_pmc'
                }
            )
            import xml.etree.ElementTree as ET
            root = ET.fromstring(r.text)
            for link in root.iter('Link'):
                pmc_id = link.find('Id')
                if pmc_id is not None and pmc_id.text:
                    return f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pmc_id.text}/"
            return ''
        except Exception:
            return ''

    def enriquecer_resultado(self, artigo: Dict) -> Dict:
        """Enriquece resultado com abstract, MeSH e full-text."""
        pmid = artigo['pmid']
        time.sleep(RATE_LIMIT)

        # Abstract
        artigo['abstract'] = self.coletar_abstract(pmid)
        self.stats['total_calls'] += 1

        # MeSH terms
        time.sleep(RATE_LIMIT)
        artigo['mesh_terms'] = self.coletar_mesh(pmid)
        self.stats['total_calls'] += 1

        # PMC full-text
        if not artigo.get('pmc_id'):
            time.sleep(RATE_LIMIT)
            ft_url = self.encontrar_fulltext_pmc(pmid)
            artigo['full_text_url'] = ft_url
            self.stats['total_calls'] += 1
        else:
            artigo['full_text_url'] = f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{artigo['pmc_id']}/"

        artigo['data_coleta'] = datetime.now().isoformat()
        return artigo

    def pesquisar_robusta(self, queries: List[Dict], min_date: str = "2019",
                         max_date: str = "2026", por_query: int = 10,
                         total_desejado: int = 50,
                         enriquecer: bool = True) -> Dict:
        """
        Busca robusta com múltiplas queries e deduplicação.

        Args:
            queries: Lista de dicts com 'termo' e 'tema'
            min_date/max_date: Range de anos
            por_query: Quantos artigos por query
            total_desejado: Meta total
            enriquecer: Buscar abstract e MeSH
        """
        inicio = time.time()
        todos_pmids = {}  # {pmid: {query, tema}}
        resultados_finais = []

        print(f"\n{'='*60}")
        print(f"  PUBMED RESEARCH TOOL")
        print(f"{'='*60}")
        print(f"  Meta: {total_desejado} artigos")
        print(f"  Queries: {len(queries)}")
        print(f"  Período: {min_date} - {max_date}")
        print(f"{'='*60}\n")

        # FASE 1: Coletar PMIDs de todas as queries
        for q_info in queries:
            termo = q_info['termo']
            tema = q_info.get('tema', '')
            self.stats['queries_executadas'] += 1

            print(f"[{self.stats['queries_executadas']}/{len(queries)}] {tema}")
            print(f"  Query: {termo}")

            # Busca principal
            pmids = self.buscar_pmids(termo, min_date, max_date, por_query, "relevance")
            print(f"  Encontrados: {len(pmids)} (relevância)")

            for p in pmids:
                if p not in todos_pmids:
                    todos_pmids[p] = {'query': termo, 'tema': tema}

            # Busca por revisões sistemáticas (se quiser mais)
            if len(pmids) < por_query:
                time.sleep(RATE_LIMIT)
                pmids_review = self.buscar_pmids_pubtype(termo, "systematic", min_date, max_date, por_query - len(pmids))
                print(f"  Revisões sistemáticas: {len(pmids_review)}")
                for p in pmids_review:
                    if p not in todos_pmids:
                        todos_pmids[p] = {'query': termo, 'tema': tema}

            # Busca por meta-análises
            time.sleep(RATE_LIMIT)
            pmids_meta = self.buscar_pmids_pubtype(termo, "meta-analysis", min_date, max_date, 3)
            if pmids_meta:
                print(f"  Meta-análises: {len(pmids_meta)}")
                for p in pmids_meta:
                    if p not in todos_pmids:
                        todos_pmids[p] = {'query': termo, 'tema': tema}

            print(f"  Acumulado total: {len(todos_pmids)} PMIDs\n")

            if len(todos_pmids) >= total_desejado * 2:
                break

        print(f"\nTotal de PMIDs únicos: {len(todos_pmids)}")

        # FASE 2: Coletar metadados
        pmids_unicos = list(todos_pmids.keys())
        pmid_list = []
        for p in pmids_unicos:
            if len(resultados_finais) < total_desejado:
                pmid_list.append(p)

        print(f"\nColetando metadados de {len(pmid_list)} artigos...")
        artigos = self.coletar_metadados(pmid_list)

        for art in artigos:
            query_info = todos_pmids.get(art['pmid'], {})
            art['query_origem'] = query_info.get('query', '')
            art['tema'] = query_info.get('tema', '')
            resultados_finais.append(art)
            self.stats['artigos_coletados'] += 1

        # FASE 3: Enriquecer (abstract + MeSH)
        if enriquecer and resultados_finais:
            print(f"\nEnriquecendo {len(resultados_finais)} artigos com abstract e MeSH...")
            for i, art in enumerate(resultados_finais):
                print(f"  [{i+1}/{len(resultados_finais)}] PMID {art['pmid']}: {art['title'][:50]}...")
                art = self.enriquecer_resultado(art)

        tempo_total = time.time() - inicio
        self.stats['tempo_total'] = tempo_total

        print(f"\n{'='*60}")
        print(f"  RESUMO")
        print(f"{'='*60}")
        print(f"  Artigos coletados: {len(resultados_finais)}")
        print(f"  Chamadas à API: {self.stats['total_calls']}")
        print(f"  Tempo total: {tempo_total:.1f}s")
        print(f"{'='*60}\n")

        return {
            'metadata': {
                'data_coleta': datetime.now().isoformat(),
                'total_resultados': len(resultados_finais),
                'queries_executadas': self.stats['queries_executadas'],
                'chamadas_api': self.stats['total_calls'],
                'tempo_total_segundos': round(tempo_total, 1),
                'min_date': min_date,
                'max_date': max_date
            },
            'resultados': resultados_finais
        }

    def salvar_json(self, dados: Dict, nome_arquivo: str) -> str:
        """Salva resultados em JSON."""
        # Se for path absoluto, usa; senão, usa Desktop
        import os
        if not os.path.isabs(nome_arquivo):
            desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
            nome_arquivo = os.path.join(desktop, nome_arquivo)

        with open(nome_arquivo, 'w', encoding='utf-8') as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)

        print(f"✅ JSON salvo: {nome_arquivo}")
        return nome_arquivo

    def salvar_markdown(self, dados: Dict, nome_arquivo: str) -> str:
        """Salva resultados em Markdown formatado."""
        import os
        if not os.path.isabs(nome_arquivo):
            desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
            nome_arquivo = os.path.join(desktop, nome_arquivo)

        linhas = [
            f"# Referências Científicas — Câncer de Tireoide",
            f"\n**Data de coleta:** {dados['metadata']['data_coleta']}",
            f"**Total de referências:** {dados['metadata']['total_resultados']}",
            f"**Período:** {dados['metadata']['min_date']} - {dados['metadata']['max_date']}",
            f"\n---\n"
        ]

        for i, art in enumerate(dados['resultados'], 1):
            title = art.get('title', 'SEM TÍTULO')
            pmid = art.get('pmid', '')
            doi = art.get('doi', '')
            journal = art.get('journal', '')
            pubdate = art.get('pubdate', '')
            authors = art.get('authors', [])
            pubtype = art.get('pubtype', [])
            mesh = art.get('mesh_terms', [])
            abstract = art.get('abstract', '')
            full_url = art.get('full_text_url', '')
            tema = art.get('tema', '')

            linhas.append(f"## [{i}] {title}")
            linhas.append(f"")
            linhas.append(f"- **PMID:** [{pmid}](https://pubmed.ncbi.nlm.nih.gov/{pmid}/)")
            if doi:
                linhas.append(f"- **DOI:** [{doi}](https://doi.org/{doi})")
            linhas.append(f"- **Autores:** {', '.join(authors[:5])}{' et al.' if len(authors) > 5 else ''}")
            linhas.append(f"- **Journal:** {journal} ({pubdate})")
            if pubtype:
                linhas.append(f"- **Tipo:** {', '.join(pubtype)}")
            if tema:
                linhas.append(f"- **Tema:** {tema}")
            if mesh:
                linhas.append(f"- **MeSH:** {', '.join(mesh[:8])}")
            if abstract:
                # Limitar abstract a 500 chars
                abstract_lim = abstract[:500] + '...' if len(abstract) > 500 else abstract
                linhas.append(f"- **Abstract:** {abstract_lim}")
            if full_url:
                linhas.append(f"- **Full Text:** [Acessar no PMC]({full_url})")
            linhas.append(f"- **PubMed:** [Ver artigo](https://pubmed.ncbi.nlm.nih.gov/{pmid}/)")
            linhas.append(f"")
            linhas.append(f"---")
            linhas.append(f"")

        with open(nome_arquivo, 'w', encoding='utf-8') as f:
            f.write('\n'.join(linhas))

        print(f"✅ Markdown salvo: {nome_arquivo}")
        return nome_arquivo

    def salvar_csv(self, dados: Dict, nome_arquivo: str) -> str:
        """Salva resultados em CSV simples."""
        import os
        import csv
        if not os.path.isabs(nome_arquivo):
            desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
            nome_arquivo = os.path.join(desktop, nome_arquivo)

        with open(nome_arquivo, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['PMID', 'Título', 'DOI', 'Journal', 'Data', 'Autores', 'Tipo', 'Tema', 'MeSH', 'Full-Text URL'])

            for art in dados['resultados']:
                writer.writerow([
                    art.get('pmid', ''),
                    art.get('title', ''),
                    art.get('doi', ''),
                    art.get('journal', ''),
                    art.get('pubdate', ''),
                    '|'.join(art.get('authors', [])[:5]),
                    '|'.join(art.get('pubtype', [])),
                    art.get('tema', ''),
                    '|'.join(art.get('mesh_terms', [])[:5]),
                    art.get('full_text_url', '')
                ])

        print(f"✅ CSV salvo: {nome_arquivo}")
        return nome_arquivo


# ========================
# CLI
# ========================

def main():
    parser = argparse.ArgumentParser(description='PubMed Research Tool')
    parser.add_argument('--queries', required=True, help='Queries separadas por vírgula')
    parser.add_argument('--min-date', default='2019', help='Ano mínimo (default: 2019)')
    parser.add_argument('--max-date', default='2026', help='Ano máximo (default: 2026)')
    parser.add_argument('--per-query', type=int, default=10, help='Artigos por query')
    parser.add_argument('--total', type=int, default=50, help='Total desejado')
    parser.add_argument('--output', default='pubmed_research', help='Nome base dos arquivos')
    parser.add_argument('--no-enrich', action='store_true', help='Pular enriquecimento (abstract/MeSH)')

    args = parser.parse_args()

    # Parsear queries
    query_strings = [q.strip() for q in args.queries.split(',')]
    queries = []
    temas = [
        "Tratamento Natural", "Suplementação", "Jejum Intermitente",
        "Selênio", "Vitamina D", "Curcumina", "Imunoterapia",
        "Autofagia", "Plantas Medicinais", "Dieta Cetogênica",
        "Estresse Oxidativo", "Omega-3", "Antioxidantes",
        "Terapia Integrativa", "Estilo de Vida"
    ]
    for i, q in enumerate(query_strings):
        tema = temas[i] if i < len(temas) else f"Query {i+1}"
        queries.append({'termo': q, 'tema': tema})

    # Executar pesquisa
    researcher = PubMedResearch()
    resultados = researcher.pesquisar_robusta(
        queries=queries,
        min_date=args.min_date,
        max_date=args.max_date,
        por_query=args.per_query,
        total_desejado=args.total,
        enriquecer=not args.no_enrich
    )

    # Salvar
    researcher.salvar_json(resultados, f"{args.output}.json")
    researcher.salvar_markdown(resultados, f"{args.output}.md")
    researcher.salvar_csv(resultados, f"{args.output}.csv")

    print(f"\n🎉 Pesquisa concluída! {resultados['metadata']['total_resultados']} artigos coletados.")


if __name__ == '__main__':
    main()
