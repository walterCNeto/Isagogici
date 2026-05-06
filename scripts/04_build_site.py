#!/usr/bin/env python3
"""
04_build_site.py - Constroi o site publico de docs/ a partir dos JSONs traduzidos.
"""
import argparse
import json
import re
from pathlib import Path
from html import escape

GITHUB_USER = "walterCNeto"
GITHUB_REPO = "Isagogici"
SITE_BASE = f"https://{GITHUB_USER.lower()}.github.io/{GITHUB_REPO}/"
ISSUE_BASE = f"https://github.com/{GITHUB_USER}/{GITHUB_REPO}/issues/new"

SISTER_PROJECT_URL = "https://waltercneto.github.io/Scaliger/"


CSS = """
:root {
  --paper: #faf7f2;
  --ink: #1a1614;
  --ink-soft: #4a443e;
  --ink-faint: #8a8278;
  --rule: #d4cdc0;
  --rule-soft: #e8e2d5;
  --accent: #2b4a6f;
  --accent-warm: #8b3a2f;
  --code-bg: #f0ebe0;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
html { font-size: 17px; scroll-behavior: smooth; }
body {
  font-family: 'EB Garamond', Georgia, serif;
  background: var(--paper);
  color: var(--ink);
  line-height: 1.65;
}
.display {
  font-family: 'Cormorant Garamond', serif;
  font-weight: 500;
  line-height: 1.1;
  letter-spacing: -0.02em;
}
.meta {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--ink-faint);
}
header {
  border-bottom: 1px solid var(--rule);
  padding: 1.2rem 0;
  background: rgba(250, 247, 242, 0.92);
  backdrop-filter: blur(8px);
  position: sticky;
  top: 0;
  z-index: 10;
}
.header-inner {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 2rem;
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 2rem;
  flex-wrap: wrap;
}
header .title {
  font-family: 'Cormorant Garamond', serif;
  font-size: 1.1rem;
  font-weight: 500;
  font-style: italic;
}
header nav a {
  color: var(--ink-soft);
  text-decoration: none;
  margin-left: 1.2rem;
  font-size: 0.88rem;
}
header nav a:hover { color: var(--accent); }

main { max-width: 1100px; margin: 0 auto; padding: 3rem 2rem; }

.hero {
  max-width: 900px;
  margin: 0 auto;
  padding: 5rem 2rem 3rem;
  border-bottom: 1px solid var(--rule);
}
.hero h1 { margin-bottom: 1.5rem; font-size: clamp(2rem, 5vw, 3.6rem); }
.hero h1 em { color: var(--accent); font-style: italic; }
.hero .lede {
  font-size: 1.2rem;
  color: var(--ink-soft);
  font-style: italic;
  max-width: 700px;
  line-height: 1.5;
}

.disclaimer-banner {
  background: #fff8dc;
  border-left: 4px solid #d4a017;
  padding: 1rem 1.4rem;
  margin: 2rem 0;
  font-size: 0.95rem;
}
.disclaimer-banner strong { color: #8b4513; }

.sister-link {
  background: #e8eef5;
  border-left: 4px solid var(--accent);
  padding: 1rem 1.4rem;
  margin: 2rem 0;
  font-size: 0.95rem;
}
.sister-link strong { color: var(--accent); }

.pages-section { max-width: 1100px; margin: 0 auto; padding: 3rem 2rem; }
.pages-section h2 { margin-bottom: 1.5rem; font-size: 2rem; }
.page-search {
  width: 100%;
  padding: 0.8rem 1rem;
  border: 1px solid var(--rule);
  background: white;
  font-family: inherit;
  font-size: 1rem;
  margin-bottom: 1.5rem;
  border-radius: 2px;
}
.page-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 0.5rem;
  margin-bottom: 3rem;
}
.page-grid a {
  display: block;
  padding: 0.6rem 0.5rem;
  background: white;
  border: 1px solid var(--rule);
  text-decoration: none;
  color: var(--ink);
  font-size: 0.85rem;
  text-align: center;
  border-radius: 2px;
  transition: all 0.15s;
}
.page-grid a:hover {
  background: var(--accent);
  color: white;
  border-color: var(--accent);
}
.page-grid a small {
  display: block;
  font-size: 0.65rem;
  color: var(--ink-faint);
  margin-top: 0.2rem;
  text-transform: uppercase;
}
.page-grid a:hover small { color: rgba(255,255,255,0.7); }

.page-nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 0;
  margin-bottom: 1rem;
  border-bottom: 1px solid var(--rule-soft);
  font-size: 0.9rem;
}
.page-nav a {
  color: var(--accent);
  text-decoration: none;
  padding: 0.4rem 0.8rem;
  border: 1px solid var(--rule);
  border-radius: 2px;
  background: white;
}
.page-nav a:hover { background: var(--accent); color: white; }
.page-nav .center {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
  color: var(--ink-faint);
}

.scan-link {
  display: inline-block;
  margin: 0 0 2rem 0;
  padding: 0.5rem 1rem;
  background: white;
  border: 1px solid var(--rule);
  border-radius: 2px;
  text-decoration: none;
  color: var(--accent);
  font-size: 0.9rem;
}
.scan-link:hover { background: var(--code-bg); }

.trilingual {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1.5rem;
  margin: 2rem 0;
}
.trilingual section {
  background: white;
  padding: 1.5rem 1.6rem;
  border: 1px solid var(--rule);
  border-radius: 2px;
}
.trilingual h3 {
  font-family: 'Cormorant Garamond', serif;
  font-size: 1.3rem;
  font-weight: 500;
  color: var(--accent);
  border-bottom: 1px solid var(--rule);
  padding-bottom: 0.6rem;
  margin-bottom: 1rem;
}
.trilingual p { font-size: 0.97rem; line-height: 1.6; }
.trilingual em { font-style: italic; }
.trilingual section.empty p { color: var(--ink-faint); font-style: italic; }

.definitions-block {
  background: #f0f7ff;
  padding: 1.2rem 1.5rem;
  border-left: 4px solid var(--accent);
  margin: 2rem 0;
  border-radius: 2px;
}
.definitions-block h4 {
  font-family: 'Cormorant Garamond', serif;
  font-size: 1.1rem;
  font-weight: 600;
  margin-bottom: 0.8rem;
  color: var(--accent);
}
.definition {
  margin: 0.6rem 0;
  padding: 0.8rem 1rem;
  background: white;
  border-radius: 2px;
}
.definition .term {
  font-weight: 600;
  color: var(--accent-warm);
  font-style: italic;
}
.definition .def-text {
  display: block;
  margin-top: 0.4rem;
  font-size: 0.95rem;
}

.cross-refs-block {
  background: #f5f0e8;
  padding: 1.2rem 1.5rem;
  border-left: 4px solid var(--ink-soft);
  margin: 2rem 0;
  border-radius: 2px;
}
.cross-refs-block h4 {
  font-family: 'Cormorant Garamond', serif;
  font-size: 1.1rem;
  font-weight: 600;
  margin-bottom: 0.8rem;
}
.cross-ref-item {
  margin: 0.4rem 0;
  font-size: 0.92rem;
  font-style: italic;
}

.events-list {
  background: #faf3e7;
  padding: 1.2rem 1.5rem;
  border-left: 4px solid var(--accent-warm);
  margin: 2rem 0;
  border-radius: 2px;
}
.events-list h4 {
  font-family: 'Cormorant Garamond', serif;
  font-size: 1.1rem;
  font-weight: 600;
  margin-bottom: 0.8rem;
  color: var(--accent-warm);
}
.event-item {
  margin: 0.5rem 0;
  padding: 0.6rem 0.8rem;
  background: white;
  border-radius: 2px;
  font-size: 0.92rem;
}

.flag-list {
  background: #fff0f0;
  padding: 1rem 1.4rem;
  border-left: 4px solid #c44;
  margin: 2rem 0;
  font-size: 0.92rem;
  border-radius: 2px;
}
.flag-list strong { color: #b22; }
.flag-list ul { margin: 0.6rem 0 0 1.2rem; }
.flag-list li { margin: 0.3rem 0; }

.notes-block {
  background: var(--rule-soft);
  padding: 1rem 1.4rem;
  margin: 2rem 0;
  font-size: 0.92rem;
  border-radius: 2px;
}

table {
  border-collapse: collapse;
  margin: 1.5rem 0;
  width: 100%;
  background: white;
  font-size: 0.88rem;
}
th, td {
  border: 1px solid var(--rule);
  padding: 0.5rem 0.8rem;
  text-align: left;
}
th { background: var(--code-bg); font-weight: 600; }

.contribute-block {
  margin-top: 4rem;
  padding: 1.8rem;
  background: var(--code-bg);
  border-radius: 4px;
  border: 1px solid var(--rule);
}
.contribute-block h4 {
  font-family: 'Cormorant Garamond', serif;
  font-size: 1.3rem;
  margin-bottom: 0.8rem;
  color: var(--accent);
}
.contribute-block a {
  display: inline-block;
  margin-right: 0.8rem;
  padding: 0.5rem 1rem;
  background: var(--accent);
  color: white;
  text-decoration: none;
  border-radius: 2px;
  font-size: 0.9rem;
}
.contribute-block a:hover { background: var(--accent-warm); }
.contribute-block a.secondary {
  background: white;
  color: var(--accent);
  border: 1px solid var(--accent);
}

footer {
  border-top: 1px solid var(--rule);
  margin-top: 5rem;
  padding: 3rem 2rem;
  background: var(--ink);
  color: var(--paper);
}
.footer-inner { max-width: 1100px; margin: 0 auto; }
footer h3 {
  font-family: 'Cormorant Garamond', serif;
  font-size: 1.4rem;
  margin-bottom: 1rem;
}
footer p {
  font-size: 0.9rem;
  color: rgba(250, 247, 242, 0.7);
  margin-bottom: 1rem;
  max-width: 700px;
}
footer a { color: rgba(250, 247, 242, 0.85); }

@media (max-width: 768px) {
  html { font-size: 15px; }
  .trilingual { grid-template-columns: 1fr; }
  .header-inner { flex-direction: column; align-items: flex-start; gap: 0.6rem; }
  header nav a { margin-left: 0; margin-right: 1rem; }
  main { padding: 2rem 1.2rem; }
}
"""


HEADER_TEMPLATE = """<header>
  <div class="header-inner">
    <span class="title">Isagogicorum chronologiae canonum &middot; Joseph Scaliger (1606)</span>
    <nav>
      <a href="{base}index.html">Inicio</a>
      <a href="{base}index.html#paginas">Paginas</a>
      <a href="{base}methodology.html">Metodo</a>
      <a href="{base}about.html">Sobre</a>
      <a href="https://waltercneto.github.io/Scaliger/" target="_blank">De Emendatione</a>
    </nav>
  </div>
</header>
"""

HYPOTHESIS_SCRIPT = '<script src="https://hypothes.is/embed.js" async></script>'

GOOGLE_FONTS = (
    '<link href="https://fonts.googleapis.com/css2?'
    'family=EB+Garamond:ital,wght@0,400;0,500;0,600;0,700;1,400;1,500&'
    'family=JetBrains+Mono:wght@400;500&'
    'family=Cormorant+Garamond:wght@500;700&'
    'display=swap" rel="stylesheet">'
)


def safe_text(s):
    if not s:
        return ""
    return escape(s).replace("\n", "<br>")


def issue_url(page_num):
    title = f"p.{page_num} - sugestao de revisao"
    body = (
        f"Pagina afetada: {page_num}\n\n"
        f"URL: {SITE_BASE}pages/{page_num:04d}.html\n\n"
        f"Trecho problematico:\n> \n\n"
        f"Problema identificado:\n\n\n"
        f"Correcao sugerida (se souber):\n\n\n"
    )
    from urllib.parse import quote
    return f"{ISSUE_BASE}?title={quote(title)}&body={quote(body)}&labels=correcao"


def render_table_html(table_data):
    md = table_data.get("markdown", "")
    rows = [r for r in md.split("\n") if r.strip().startswith("|")]
    if not rows:
        return ""
    html = "<table>"
    for j, row in enumerate(rows):
        cells = [c.strip() for c in row.strip("|").split("|")]
        if j == 1 and all(re.match(r"^[-:]+$", c) for c in cells if c):
            continue
        tag = "th" if j == 0 else "td"
        html += "<tr>" + "".join(f"<{tag}>{escape(c)}</{tag}>" for c in cells) + "</tr>"
    html += "</table>"
    return html


def render_page(data, prev_p, next_p, total):
    pn = data.get("page", 0)
    pt = (data.get("pt") or "").strip()
    en = (data.get("en") or "").strip()
    latin = (data.get("latin") or "").strip()
    tables = data.get("tables") or []
    figures = data.get("figures") or []
    events = data.get("astronomical_events") or []
    flags = data.get("uncertainty_flags") or []
    notes = (data.get("notes") or "").strip()
    definitions = data.get("definitions") or []
    cross_refs = data.get("cross_references") or []

    nav_prev = (f'<a href="{prev_p:04d}.html">p.{prev_p}</a>'
                if prev_p else '<span></span>')
    nav_next = (f'<a href="{next_p:04d}.html">p.{next_p}</a>'
                if next_p else '<span></span>')

    pt_html = (f'<section><h3>Portugues</h3><p>{safe_text(pt)}</p></section>'
               if pt else
               '<section class="empty"><h3>Portugues</h3><p>(pagina sem texto corrente - ver tabelas)</p></section>')
    en_html = (f'<section><h3>English</h3><p>{safe_text(en)}</p></section>'
               if en else
               '<section class="empty"><h3>English</h3><p>(no running text - see tables)</p></section>')
    lat_html = (f'<section><h3>Latim</h3><p>{safe_text(latin)}</p></section>'
                if latin else
                '<section class="empty"><h3>Latim</h3><p>(pagina sem texto latino corrente)</p></section>')

    defs_html = ""
    if definitions:
        items = ""
        for d in definitions:
            items += (f'<div class="definition"><span class="term">{escape(d.get("term", "?"))}</span>'
                      f'<span class="def-text">{escape(d.get("definition_pt") or d.get("definition_en") or "")}</span></div>')
        defs_html = (f'<div class="definitions-block">'
                     f'<h4>Definicoes nesta pagina</h4>{items}</div>')

    cr_html = ""
    if cross_refs:
        items = ""
        for cr in cross_refs:
            target = cr.get("target", "?")
            ctx = cr.get("context", "")
            cr_type = cr.get("type", "internal")
            label = "Interna" if cr_type == "internal" else "Externa"
            items += (f'<div class="cross-ref-item">{label}: <strong>{escape(target)}</strong>'
                      f' - <em>"{escape(ctx[:120])}"</em></div>')
        cr_html = (f'<div class="cross-refs-block">'
                   f'<h4>Referencias cruzadas</h4>{items}</div>')

    events_html = ""
    if events:
        items = ""
        for e in events:
            items += (f'<div class="event-item"><strong>{escape(e.get("type","?"))}</strong>: '
                      f'{escape((e.get("description") or "")[:300])}')
            if e.get("historical_date_as_cited"):
                items += f' <em>data: {escape(e["historical_date_as_cited"])}</em>'
            if e.get("ancient_source"):
                items += f' <em>fonte: {escape(e["ancient_source"])}</em>'
            items += '</div>'
        events_html = (f'<div class="events-list">'
                       f'<h4>Eventos astronomicos detectados</h4>{items}</div>')

    tables_html = ""
    if tables:
        tables_html = '<div class="tables-section">'
        for i, t in enumerate(tables, 1):
            cap = t.get("caption_pt", "") or t.get("caption_en", "")
            tables_html += f"<h4 style='margin-top:1.5rem;'>Tabela {i}</h4>"
            if cap:
                tables_html += f'<div style="font-style:italic;color:var(--ink-soft);font-size:.9rem;">{escape(cap)}</div>'
            tables_html += render_table_html(t)
        tables_html += "</div>"

    figures_html = ""
    for i, f in enumerate(figures, 1):
        desc = f.get('description_pt', '') or f.get('description_en', '')
        if desc:
            figures_html += f"<p><em>Figura {i}: {safe_text(desc)}</em></p>"

    flags_html = ""
    if flags:
        items = "".join(f"<li>{safe_text(fl)}</li>" for fl in flags)
        flags_html = (f'<div class="flag-list"><strong>'
                      f'Flags de incerteza (pontos para revisao humana)</strong>'
                      f'<ul>{items}</ul></div>')

    notes_html = ""
    if notes:
        notes_html = (f'<div class="notes-block"><strong>Notas do tradutor:</strong> '
                      f'{safe_text(notes)}</div>')

    body = f"""<main>
  <div class="page-nav">{nav_prev}<span class="center">p. {pn} de {total}</span>{nav_next}</div>

  <a href="../assets/scans/page-{pn:03d}.png" class="scan-link" target="_blank">Ver scan original (p.{pn})</a>

  <div class="trilingual">
    {pt_html}
    {en_html}
    {lat_html}
  </div>

  {defs_html}
  {cr_html}
  {tables_html}
  {figures_html}
  {events_html}
  {flags_html}
  {notes_html}

  <div class="page-nav" style="margin-top: 2rem;">{nav_prev}<span class="center">p. {pn} de {total}</span>{nav_next}</div>

  <div class="contribute-block">
    <h4>Encontrou um erro nesta pagina?</h4>
    <p>Esta traducao e texto-semente gerado por IA - erros sao esperados.</p>
    <a href="{issue_url(pn)}" target="_blank">Reportar no GitHub</a>
    <a href="https://hypothes.is" target="_blank" class="secondary">Hypothes.is</a>
    <a href="{SITE_BASE}about.html" class="secondary">Como contribuir</a>
  </div>
</main>"""

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>p. {pn} - Isagogici</title>
<link rel="stylesheet" href="../assets/style.css">
{GOOGLE_FONTS}
{HYPOTHESIS_SCRIPT}
</head>
<body>
{HEADER_TEMPLATE.format(base="../")}
{body}
{render_footer()}
</body>
</html>"""


def render_footer():
    return f"""<footer>
  <div class="footer-inner">
    <h3>Sobre o projeto</h3>
    <p>Traducao colaborativa do <em>Isagogicorum chronologiae canonum libri tres</em> de Joseph Scaliger (Leiden, 1606). Iniciativa pessoal de Walter C. Neto (Sao Paulo, 2026), patrocinio proprio. Traducao por IA (Claude Opus 4.7), publicada como texto-semente para revisao academica colaborativa.</p>
    <p>Projeto irmao (texto principal de Scaliger): <a href="https://waltercneto.github.io/Scaliger/" target="_blank">De Emendatione Temporum</a></p>
    <p>Repositorio: <a href="https://github.com/{GITHUB_USER}/{GITHUB_REPO}" target="_blank">github.com/{GITHUB_USER}/{GITHUB_REPO}</a></p>
    <p>Licenca <a href="https://creativecommons.org/licenses/by-sa/4.0/" target="_blank">CC BY-SA 4.0</a>. Texto original em dominio publico.</p>
  </div>
</footer>"""


def render_index(pages_meta):
    page_grid = ""
    for p in pages_meta:
        pn = p["page"]
        ptype = p["type"]
        page_grid += f'<a href="pages/{pn:04d}.html" data-page="{pn}">p. {pn}<small>{escape(ptype)}</small></a>'

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Isagogicorum chronologiae canonum - Traducao Colaborativa</title>
<link rel="stylesheet" href="assets/style.css">
{GOOGLE_FONTS}
{HYPOTHESIS_SCRIPT}
</head>
<body>
{HEADER_TEMPLATE.format(base="")}

<section class="hero">
  <div class="meta">Traducao colaborativa &middot; {len(pages_meta)} paginas trilingues &middot; Lancado em 2026</div>
  <h1 class="display">O <em>manual tecnico</em> que Scaliger escreveu para sistematizar a cronologia que ele inventou.</h1>
  <p class="lede">
    O <em>Isagogicorum chronologiae canonum libri tres</em> (1606) e o tratado didatico-sistematico que Joseph Scaliger escreveu como continuacao do <em>De Emendatione Temporum</em> (1583, 1598). Estilo geometrico-demonstrativo, com definicoes, demonstracoes e exemplos numericos. Manual tecnico de cronologia para a primeira geracao de cronologistas cientificos. Esta e uma primeira traducao em portugues e ingles.
  </p>
</section>

<main>

<div class="disclaimer-banner">
<strong>Aviso essencial.</strong> Esta traducao foi gerada por IA (Claude Opus 4.7). <strong>Contem erros.</strong> Nao cite passagens em trabalhos academicos sem verificar o original. Convite a especialistas para correcao via <a href="https://github.com/{GITHUB_USER}/{GITHUB_REPO}/issues" target="_blank">GitHub Issues</a> ou <a href="https://hypothes.is" target="_blank">Hypothes.is</a>.
</div>

<div class="sister-link">
<strong>Projeto irmao.</strong> O <em>Isagogici</em> e manual tecnico que pressupoe a leitura do <em>De Emendatione Temporum</em>. Quando Scaliger refere "ut in Opere de Emendatione demonstravimus", recomendamos consultar a <a href="{SISTER_PROJECT_URL}" target="_blank">traducao paralela do De Emendatione</a>.
</div>

<section class="pages-section" id="paginas">
  <h2>Navegar pelas {len(pages_meta)} paginas</h2>
  <input type="text" class="page-search" placeholder="Buscar pagina por numero (ex: 47) ou tipo" id="page-search-input">
  <div class="page-grid" id="page-grid">
    {page_grid}
  </div>
</section>

<div class="contribute-block">
  <h4>Quer contribuir?</h4>
  <p>Ha tres caminhos diferentes, do mais leve ao mais tecnico.</p>
  <a href="https://github.com/{GITHUB_USER}/{GITHUB_REPO}/issues/new/choose" target="_blank">Abrir issue no GitHub</a>
  <a href="https://hypothes.is" target="_blank" class="secondary">Hypothes.is</a>
  <a href="https://github.com/{GITHUB_USER}/{GITHUB_REPO}/blob/main/CONTRIBUTING.md" target="_blank" class="secondary">Guia</a>
</div>

</main>

{render_footer()}

<script>
const input = document.getElementById('page-search-input');
const grid = document.getElementById('page-grid');
const links = grid.querySelectorAll('a');
input.addEventListener('input', e => {{
  const q = e.target.value.toLowerCase().trim();
  links.forEach(a => {{
    const text = a.textContent.toLowerCase();
    a.style.display = text.includes(q) ? 'block' : 'none';
  }});
}});
</script>

</body>
</html>"""


def render_about():
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Sobre - Isagogici</title>
<link rel="stylesheet" href="assets/style.css">
{GOOGLE_FONTS}
{HYPOTHESIS_SCRIPT}
</head>
<body>
{HEADER_TEMPLATE.format(base="")}

<main>
<h1 class="display">Sobre o projeto</h1>

<h2 style="margin-top: 2rem; font-family: 'Cormorant Garamond', serif;">A obra</h2>
<p>O <em>Isagogicorum chronologiae canonum libri tres</em> ("Tres livros dos canones isagogicos da cronologia") e o tratado sistematico que Joseph Scaliger escreveu em 1606 para ensinar o metodo cronologico que ele havia desenvolvido no <em>De Emendatione Temporum</em>.</p>

<h2 style="margin-top: 2rem; font-family: 'Cormorant Garamond', serif;">Quem fez isto</h2>
<p>Iniciativa pessoal de <strong>Walter C. Neto</strong> (Sao Paulo, Brazil, 2026), com patrocinio proprio. Nao ha vinculo institucional. Em dialogo com Anthony Grafton (Princeton), referencia mundial em estudos sobre Scaliger.</p>

<h2 style="margin-top: 2rem; font-family: 'Cormorant Garamond', serif;">Por que</h2>
<p>O <em>Isagogici</em> nunca foi traduzido para nenhuma lingua vernacula em 420 anos. Junto com o <em>De Emendatione Temporum</em>, forma o corpus completo da fundacao humanista da cronologia cientifica moderna.</p>

<h2 style="margin-top: 2rem; font-family: 'Cormorant Garamond', serif;">Como contribuir</h2>
<p>Ha tres niveis de contribuicao. Detalhes em <a href="https://github.com/{GITHUB_USER}/{GITHUB_REPO}/blob/main/CONTRIBUTING.md" target="_blank">CONTRIBUTING.md</a>.</p>

<h2 style="margin-top: 2rem; font-family: 'Cormorant Garamond', serif;">Honestidade radical</h2>
<p>A traducao e gerada por IA. Nao ha garantia de fidelidade absoluta. Por isso a publicacao aberta com revisao publica e parte essencial do metodo, nao detalhe.</p>

<h2 style="margin-top: 2rem; font-family: 'Cormorant Garamond', serif;">Licenca</h2>
<p>Traducao: <strong>CC BY-SA 4.0</strong>. Texto original de Scaliger em dominio publico.</p>

<div class="contribute-block">
  <h4>Proximo passo</h4>
  <p>Veja tambem o <strong>projeto irmao</strong> dedicado ao <em>De Emendatione Temporum</em>:</p>
  <a href="{SISTER_PROJECT_URL}" target="_blank">De Emendatione Temporum</a>
</div>

</main>
{render_footer()}
</body>
</html>"""


def render_methodology():
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Metodologia - Isagogici</title>
<link rel="stylesheet" href="assets/style.css">
{GOOGLE_FONTS}
{HYPOTHESIS_SCRIPT}
</head>
<body>
{HEADER_TEMPLATE.format(base="")}

<main>
<h1 class="display">Metodologia</h1>

<h2 style="margin-top: 2rem; font-family: 'Cormorant Garamond', serif;">Pipeline</h2>
<ol style="margin-left: 1.5rem; line-height: 2;">
<li><strong>Rasterizacao</strong>: PDF do Google Books / Internet Archive em 390 PNGs em 200 DPI</li>
<li><strong>Traducao trilingue</strong>: cada PNG enviado a Claude Opus 4.7 com prompt customizado para o estilo didatico do Isagogici, gerando JSON estruturado: latim transcrito + traducao pt + traducao en + definicoes + cross-references + tabelas + flags de incerteza</li>
<li><strong>QA estrutural</strong>: validacao automatica</li>
<li><strong>Construcao do site</strong>: HTML estatico servido pelo GitHub Pages</li>
</ol>

<h2 style="margin-top: 2rem; font-family: 'Cormorant Garamond', serif;">Reprodutibilidade</h2>
<p>Todos os scripts no <a href="https://github.com/{GITHUB_USER}/{GITHUB_REPO}" target="_blank">repositorio GitHub</a>.</p>

</main>
{render_footer()}
</body>
</html>"""


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--src", default="translated")
    p.add_argument("--out", default="docs")
    args = p.parse_args()

    src = Path(args.src)
    out = Path(args.out)
    pages_dir = out / "pages"
    assets_dir = out / "assets"
    pages_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)

    (assets_dir / "style.css").write_text(CSS, encoding="utf-8")

    page_jsons = sorted(src.glob("page-*.json"))
    print(f"Encontrados {len(page_jsons)} JSONs em {src}/")

    pages_meta = []
    page_nums = []
    for jf in page_jsons:
        try:
            data = json.loads(jf.read_text(encoding="utf-8"))
            pages_meta.append({
                "page": data.get("page", -1),
                "type": data.get("page_type", "?"),
            })
            page_nums.append(data.get("page", -1))
        except json.JSONDecodeError:
            print(f"  JSON invalido: {jf}")
            continue

    page_nums.sort()
    pages_meta.sort(key=lambda x: x["page"])

    n_generated = 0
    for jf in page_jsons:
        try:
            data = json.loads(jf.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        pn = data.get("page", -1)
        idx = page_nums.index(pn) if pn in page_nums else -1
        prev_p = page_nums[idx - 1] if idx > 0 else None
        next_p = page_nums[idx + 1] if 0 <= idx < len(page_nums) - 1 else None
        html = render_page(data, prev_p, next_p, len(page_nums))
        (pages_dir / f"{pn:04d}.html").write_text(html, encoding="utf-8")
        n_generated += 1

    (out / "index.html").write_text(render_index(pages_meta), encoding="utf-8")
    (out / "about.html").write_text(render_about(), encoding="utf-8")
    (out / "methodology.html").write_text(render_methodology(), encoding="utf-8")
    (out / ".nojekyll").write_text("", encoding="utf-8")

    print(f"")
    print(f"OK Site gerado em {out}/")
    print(f"  {n_generated} paginas geradas")
    print(f"  index.html, about.html, methodology.html")
    print(f"")
    print(f"URL final: {SITE_BASE}")


if __name__ == "__main__":
    main()
