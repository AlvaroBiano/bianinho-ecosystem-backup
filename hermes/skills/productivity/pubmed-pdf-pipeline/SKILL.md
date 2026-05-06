---
name: pubmed-pdf-pipeline
description: Gera PDF profissional de relatórios científicos PubMed — extrai Markdown da conversation AionUI, transforma em HTML com template样式 profissional, usa Chrome headless para renderizar PDF A4 sem linhas órfãs.
category: productivity
---

# PubMed → PDF Profissional Pipeline

## Visão Geral

Pipeline de 2 cron jobs no AionUI:
1. **23:00** — `cron_pubmed_daily` → pesquisa PubMed, gera relatório em Markdown
2. **23:30** — `cron_pubmed_pdf` → converte Markdown → HTML profissional → PDF via Chrome headless

## Pré-requisitos

- Chrome installed at `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`
- AionUI SQLite DB: `~/Library/Application Support/AionUi/aionui/aionui.db`
- Template HTML: `~/.hermes/scripts/pubmed_report_template.html`
- Output PDF: `~/Documents/Relatorio_PubMed_AAAA-MM-DD.pdf`

## Geração de PDF (Chrome Headless)

```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --headless --no-sandbox --disable-gpu \
  --print-to-pdf=~/Documents/Relatorio_PubMed_$(date +%Y-%m-%d).pdf \
  --print-to-pdf-no-header /tmp/pubmed_report_render.html
```

⚠️ **WeasyPrint não funciona** em venv Python 3.14 — falha com `OSError: cannot load library 'libgobject-2.0-0'`. Chrome headless é o workaround.

## Template HTML — Requisitos CSS

```css
@page {
  size: A4;
  margin: 25mm 20mm 25mm 20mm;
  @bottom-center {
    content: "Página " counter(page) " de " counter(pages);
    font-family: 'Inter', sans-serif;
    font-size: 9pt;
    color: #888;
  }
}

body {
  font-family: 'Inter', Arial, sans-serif;
  font-size: 10pt;
  line-height: 1.6;
  color: #222;
  orphans: 0;   /* NUNCA linha órfã */
  widows: 0;    /* NUNCA linha viúva */
}

/* Estudo: evitar quebra dentro do box */
.study {
  page-break-inside: avoid;
}
.conclusion-box {
  page-break-inside: avoid;
}
```

## Cores e Estilos do Template

- **Separador/color accent**: `#1a5f4a` (verde escuro)
- **Badge de data**: fundo `#1a5f4a`, texto branco, border-radius 4pt
- **Box de conclusão**: fundo `#f0f7f4`, borda-left 3px solid `#1a5f4a`
- **Numeração circular**: fundo `#1a5f4a`, círculo branco 18pt, centered
- **Fonte títulos**: Playfair Display (serif) para títulos principais
- **Fonte corpo**: Inter (sans-serif), 10pt, line-height 1.6

## Arquivos da Skill

- `pubmed_report_template.html` — Template HTML base (em `~/.hermes/scripts/`)
- `references/pipeline-setup.md` — Setup completo dos 2 cron jobs + conversation

## Pipeline de Debugging (quando o PDF falha)

1. Verificar se Chrome existe: `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome --version`
2. Ver se HTML interim foi gerado em `/tmp/pubmed_report_render.html`
3. Testar Chrome isolated: `chrome --headless --no-sandbox --dump-dom /tmp/test.html > /tmp/test.pdf`
4. Verificar permissões de escrita em `~/Documents/`
