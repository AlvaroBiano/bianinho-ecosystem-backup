#!/usr/bin/env python3
"""
PubMed PDF Report Generator
Gera PDF profissional de relatórios PubMed da conversation conv_pubmed_daily.
Garantia: PDF nunca fica em branco — validação de tamanho após geração.
"""
import sqlite3, json, ssl, re, subprocess, os, sys
from urllib.request import Request, urlopen
from datetime import datetime

# ── Config ─────────────────────────────────────────────────────────
DB_PATH = "/Users/alvarobiano/Library/Application Support/AionUi/aionui/aionui.db"
CONV_ID = "conv_pubmed_daily"
OUTPUT_DIR = "/Users/alvarobiano/Desktop/Estudos Profissionais"
TELEGRAM_TOKEN = "8109921192:AAHc_kzlkMNPSXahkSmOq8jSnUoV_xv1MtY"
TELEGRAM_CHAT = "435025823"
GREEN = "#1a5f4a"
LIGHT_GREEN = "#f0f7f4"
MIN_PDF_SIZE = 50_000  # 50 KB — abaixo disso é PDF em branco

# ── Helpers ────────────────────────────────────────────────────────
def extract(text, key):
    marker = f"**{key}:**"
    if marker not in text: return "—"
    start = text.index(marker) + len(marker)
    end = text.find("\n\n", start)
    return text[start:end].strip() if end != -1 else text[start:].strip()

def get_latest_report(conv_id):
    """Lê o último relatório Markdown da conversation."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT id, content, created_at FROM messages
        WHERE conversation_id = ? AND type = 'text'
        ORDER BY created_at DESC
    """, (conv_id,))
    all_msgs = cur.fetchall()
    conn.close()
    # Procura a mensagem com relatório estruturado
    for row in all_msgs:
        content = json.loads(row[1])["content"]
        if "Compilando o relatório" in content or "Relatório PubMed" in content:
            # Extrai o relatório após o delimiter
            try:
                idx = content.index("Compilando o relatório")
                marker = content[idx:idx+30]
                report_md = content[content.index(marker) + len(marker):]
                return report_md, row[2]
            except ValueError:
                # Tenta outro padrão
                if "Relatório PubMed" in content and "Estudo" in content:
                    idx = content.index("Relatório PubMed")
                    report_md = content[idx:]
                    return report_md, row[2]
    return None, None

def parse_studies(report_md):
    """Extrai lista de estudos do markdown."""
    study_blocks, current_title, current_body = [], "", ""
    for line in report_md.split("\n"):
        m = re.match(r"^## (\d+)\. (.*)", line)
        if m:
            if current_title:
                study_blocks.append((current_title, current_body))
            current_title, current_body = m.group(2).strip(), ""
        elif current_title:
            current_body += line + "\n"
    if current_title:
        study_blocks.append((current_title, current_body))
    
    studies = []
    for i, (title, body) in enumerate(study_blocks):
        studies.append({
            "num": i + 1,
            "title": title,
            "original": extract(body, "Título original (inglês)").replace("*", ""),
            "translated": extract(body, "Título traduzido (pt-BR)").replace("*", ""),
            "pub_date": extract(body, "Data de publicação"),
            "doi": extract(body, "DOI"),
            "pubmed": extract(body, "PubMed Link"),
            "abstract": extract(body, "Resumo/Abstract"),
            "conclusions": extract(body, "Conclusões"),
        })
    return studies

def build_html(studies, date_str, topic):
    """Constrói HTML completo com conteúdo rico — sem dependência de ficheiros externos."""
    study_parts = []
    for s in studies:
        meta = f'''<div class="study-meta">
<span><strong>Publicação:</strong> {s["pub_date"]}</span>
<span><strong>DOI:</strong> <a href="https://doi.org/{s["doi"]}">{s["doi"]}</a></span>
<span><strong>PubMed:</strong> <a href="{s["pubmed"]}">Ver artigo</a></span>
</div>
<div class="study-orig"><em>Original: {s["original"]}</em></div>
<div class="study-orig"><em>Tradução: {s["translated"]}</em></div>'''
        sections = f'''<div class="study-section"><div class="section-label">Resumo / Abstract</div><p>{s["abstract"]}</p></div>
<div class="study-section"><div class="section-label">Conclusões</div><p>{s["conclusions"]}</p></div>
<div class="study-section imp"><div class="section-label">🔬 Importância Clínica</div><p>{s.get("importance", "")}</p></div>
<div class="study-section ten"><div class="section-label">🏥 Relevância para o Método TEN</div><p>{s.get("ten_relevance", "")}</p></div>
<div class="conclusion-box"><strong>✓ Síntese Clínico-Terapêutica:</strong> {s["conclusions"][:200]}...</div>'''
        study_parts.append(
            f'<div class="study">'
            f'<div class="sc">{s["num"]}</div>'
            f'<h2 class="st">{s["title"]}</h2>'
            f'{meta}{sections}</div>'
            f'<div class="sep"></div>'
        )
    
    return f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>Relatório PubMed — {topic} — {date_str}</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Playfair+Display:wght@700&display=swap');
:root {{ --g: {GREEN}; --bg: #f8fafa; --lg: {LIGHT_GREEN}; }}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ font-family: 'Inter', sans-serif; font-size: 10pt; color: #222; background: var(--bg); orphans: 0; widows: 0; }}
@page {{ size: A4; margin: 15mm 18mm; @bottom-center {{ content: "Página " counter(page) " de " counter(pages); font-size: 8pt; color: #888; }} }}
.header {{ background: var(--g); color: white; padding: 18px 26px; border-bottom: 5px solid #0d3d2e; }}
.header .t {{ font-family: 'Playfair Display', serif; font-size: 15pt; font-weight: 700; }}
.header .s {{ font-size: 11pt; opacity: 0.9; margin-top: 3px; }}
.bar {{ background: #0d3d2e; color: white; padding: 9px 26px; font-size: 9pt; }}
.bar strong {{ color: #a8e6cf; }}
.study {{ background: white; margin: 10px 0; padding: 18px 22px; border-radius: 8px; box-shadow: 0 1px 4px rgba(0,0,0,0.08); position: relative; }}
.sc {{ position: absolute; top: 14px; right: 16px; width: 32px; height: 32px; background: var(--g); color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 13pt; font-weight: 700; }}
.st {{ font-family: 'Playfair Display', serif; font-size: 12pt; color: var(--g); margin-bottom: 10px; padding-right: 40px; line-height: 1.3; }}
.study-meta {{ display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 8px; font-size: 8pt; color: #555; border-bottom: 1px solid #e8e8e8; padding-bottom: 8px; }}
.study-meta a {{ color: var(--g); text-decoration: none; }}
.study-orig {{ font-size: 7.8pt; color: #777; margin: 2px 0; }}
.section-label {{ font-size: 7.5pt; font-weight: 700; color: var(--g); text-transform: uppercase; letter-spacing: 0.8px; margin-top: 12px; margin-bottom: 4px; }}
.study-section p {{ font-size: 9.2pt; line-height: 1.6; color: #333; }}
.study-section.imp {{ background: var(--lg); margin: 10px -10px; padding: 10px; border-radius: 5px; border-left: 4px solid var(--g); }}
.study-section.ten {{ background: #fff8e8; margin: 8px -10px; padding: 10px; border-radius: 5px; border-left: 4px solid #e07b39; }}
.study-section.ten .section-label {{ color: #c0682a; }}
.conclusion-box {{ background: var(--lg); border: 1.5px solid var(--g); border-radius: 5px; padding: 9px 12px; margin-top: 12px; font-size: 8.8pt; color: #1a4a3a; }}
.sep {{ height: 2px; background: linear-gradient(to right, var(--g), transparent); margin: 4px 0; }}
</style>
</head>
<body>
<div class="header">
  <div class="t">📋 Relatório PubMed — Saúde da Mulher</div>
  <div class="s">{topic} — {date_str}</div>
</div>
<div class="bar"><strong>Tema do dia:</strong> {topic} — {len(studies)} estudos científicos selecionados</div>
{''.join(study_parts)}
</body>
</html>'''

def generate_pdf(html_path, pdf_path):
    """Gera PDF via Chrome headless. Retorna tamanho do ficheiro."""
    result = subprocess.run(
        ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
         "--headless", "--no-sandbox", "--disable-gpu",
         f"--print-to-pdf={pdf_path}",
         "--print-to-pdf-no-header", html_path],
        capture_output=True, text=True
    )
    # Procura linha com "bytes written"
    for line in result.stderr.split("\n"):
        if "bytes written" in line:
            size = int(line.strip().split()[0])
            return size
    return 0

def send_telegram(pdf_path, caption):
    """Envia PDF para Telegram via API directa."""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    boundary = "----WebKitFormBoundary7MA4YWfQ2v1Bx9e6"
    with open(pdf_path, "rb") as f:
        pdf_data = f.read()
    body = (f"--{boundary}\r\n"
            f"Content-Disposition: form-data; name=\"chat_id\"\r\n\r\n{TELEGRAM_CHAT}\r\n"
            f"--{boundary}\r\n"
            f"Content-Disposition: form-data; name=\"caption\"\r\n\r\n{caption}\r\n"
            f"--{boundary}\r\n"
            f"Content-Disposition: form-data; name=\"document\"; filename=\"{os.path.basename(pdf_path)}\"\r\n"
            f"Content-Type: application/pdf\r\n\r\n").encode() + pdf_data + f"\r\n--{boundary}--\r\n".encode()
    req = Request(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendDocument",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}
    )
    resp = urlopen(req, context=ctx, timeout=30)
    result = json.loads(resp.read())
    return result.get("result", {}).get("message_id", "N/A")

def run(date_override=None):
    # 1. Obter relatório
    report_md, created_at = get_latest_report(CONV_ID)
    if not report_md:
        print("❌ Nenhum relatório encontrado na conversation.")
        sys.exit(1)
    
    # 2. Parsear data do relatório
    date_match = re.search(r"\d{2} de \w+ de \d{4}", report_md)
    if date_match:
        date_str = date_match.group()
    elif date_override:
        date_str = date_override
    else:
        date_str = datetime.now().strftime("%d de %B de %Y")
    
    # 3. Extrair tópico
    topic_match = re.search(r"\*\*Tema do dia:\*\* (.+?)(?:\n|$)", report_md)
    topic = topic_match.group(1).strip() if topic_match else "Saúde da Mulher"
    
    # 4. Parsear estudos
    studies = parse_studies(report_md)
    if not studies:
        print("❌ Nenhum estudo encontrado no relatório.")
        sys.exit(1)
    
    print(f"📰 Relatório: {topic} — {date_str} — {len(studies)} estudos")
    
    # 5. Gerar HTML (com inline CSS — sem ficheiros externos)
    html = build_html(studies, date_str, topic)
    date_file = datetime.now().strftime("%Y-%m-%d")
    html_path = os.path.join(OUTPUT_DIR, f"Relatorio_PubMed_{date_file}.html")
    pdf_path = os.path.join(OUTPUT_DIR, f"Relatorio_PubMed_{date_file}.pdf")
    
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ HTML: {len(html)} bytes → {html_path}")
    
    # 6. Gerar PDF com validação
    size = generate_pdf(html_path, pdf_path)
    print(f"📄 PDF gerado: {size:,} bytes → {pdf_path}")
    
    if size < MIN_PDF_SIZE:
        print(f"❌ PDF em branco detectado ({size:,} < {MIN_PDF_SIZE:,} bytes). A regenerar…")
        # Regenera com timeout maior
        size = generate_pdf(html_path, pdf_path)
        if size < MIN_PDF_SIZE:
            print(f"❌ REGENERAÇÃO FALHOU. PDF com apenas {size:,} bytes. Abandonar.")
            sys.exit(1)
    
    # 7. Enviar Telegram
    caption = f"📋 Relatório PubMed — {topic} — {date_str} ({len(studies)} estudos)"
    msg_id = send_telegram(pdf_path, caption)
    print(f"✅ Telegram: message_id={msg_id}")
    
    return pdf_path, msg_id

if __name__ == "__main__":
    date_arg = sys.argv[1] if len(sys.argv) > 1 else None
    run(date_override=date_arg)