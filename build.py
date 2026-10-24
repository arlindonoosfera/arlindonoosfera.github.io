#!/usr/bin/env python3
"""Gera as páginas de aula a partir dos arquivos .md em conteudo/aulas/.
Uso:  python3 build.py        (sem dependências externas)
Cada .md pode começar com um bloco opcional:
---
titulo: ...
ano: 1º ano · Unidade 2
estagio: planejamento
---
Exporte páginas do Notion como "Markdown & CSV" e coloque os .md aqui."""
import html, re, json, pathlib

RAIZ = pathlib.Path(__file__).parent
ORIGEM = RAIZ / "conteudo" / "aulas"
SAIDA = RAIZ / "aulas"
ROTULO = {"proposta": "Proposta", "planejamento": "Material planejado",
          "desenvolvimento": "Em desenvolvimento", "aplicado": "Aplicado em sala"}

def inline(t):
    t = html.escape(t, quote=False)
    t = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", r'<a href="\2" rel="noopener">\1</a>', t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?!\w)", r"<em>\1</em>", t)
    return t

def md(texto):
    out, lista, par, tab, cit = [], None, [], [], []
    def fecha():
        nonlocal lista, par, tab, cit
        if par: out.append("<p>" + inline(" ".join(par)) + "</p>"); par = []
        if lista: out.append(f"</{lista}>"); lista = None
        if cit: out.append("<blockquote><p>" + inline(" ".join(cit)) + "</p></blockquote>"); cit = []
        if tab:
            l = [[c.strip() for c in r.strip().strip("|").split("|")] for r in tab if not re.match(r"^\s*\|?\s*-{2,}", r)]
            h = "".join(f"<th scope='col'>{inline(c)}</th>" for c in l[0])
            b = "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in l[1:])
            out.append(f"<div class='tabela'><table><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table></div>"); tab = []
    for ln in texto.splitlines():
        s = ln.rstrip()
        if not s.strip(): fecha(); continue
        m = re.match(r"^(#{1,6})\s+(.*)", s)
        if m: fecha(); n = min(len(m.group(1)) + 1, 6); out.append(f"<h{n}>{inline(m.group(2))}</h{n}>"); continue
        if re.match(r"^-{3,}$", s.strip()): fecha(); out.append("<hr>"); continue
        if s.lstrip().startswith("|"): 
            if par or lista or cit: fecha()
            tab.append(s); continue
        m = re.match(r"^\s*([-*]|\d+\.)\s+(.*)", s)
        if m:
            tipo = "ol" if m.group(1)[0].isdigit() else "ul"
            if par or tab or cit: fecha()
            if lista != tipo:
                if lista: out.append(f"</{lista}>")
                out.append(f"<{tipo}>"); lista = tipo
            out.append(f"<li>{inline(m.group(2))}</li>"); continue
        if s.startswith(">"): 
            if par or lista or tab: fecha()
            cit.append(s.lstrip("> ").strip()); continue
        if lista or tab or cit: fecha()
        par.append(s.strip())
    fecha()
    return "\n".join(out)

def meta(texto):
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", texto, re.S)
    d = {}
    if m:
        for l in m.group(1).splitlines():
            if ":" in l: k, v = l.split(":", 1); d[k.strip()] = v.strip()
        texto = m.group(2)
    if "titulo" not in d:
        t = re.search(r"^#\s+(.*)", texto, re.M)
        d["titulo"] = t.group(1).strip() if t else "Sem título"
    return d, texto

def pagina(titulo, corpo, base):
    return f"""<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(titulo)} · Arlindo Noosfera</title><link rel="stylesheet" href="{base}style.css"></head>
<body><a class="pular" href="#conteudo">Pular para o conteúdo</a>
<header class="topo"><a class="marca" href="{base}index.html"><span aria-hidden="true">🌒</span> Arlindo Noosfera</a>
<nav aria-label="Principal"><a href="{base}index.html#aulas">Aulas e educação</a><a href="{base}aulas.html">Todas as aulas</a><a href="{base}plano-biologia.html">Plano de Biologia</a></nav></header>
<main id="conteudo" class="plano prosa">{corpo}</main>
<footer class="rodape"><p>© Arlindo Noosfera. Material em rascunho; sem dados de estudantes.</p></footer></body></html>"""

def main():
    SAIDA.mkdir(exist_ok=True)
    itens = []
    for f in sorted(ORIGEM.glob("*.md")):
        if f.name.startswith("_"): continue
        d, corpo = meta(f.read_text(encoding="utf-8"))
        slug = re.sub(r"[^a-z0-9]+", "-", f.stem.lower()).strip("-")
        est = d.get("estagio", "planejamento")
        cab = f"<p class='rotulo'>{html.escape(d.get('ano','Aulas'))} · {ROTULO.get(est, est)}</p>"
        corpo = re.sub(r"^#\s+.*\n", "", corpo, count=1, flags=re.M)
        (SAIDA / f"{slug}.html").write_text(pagina(d["titulo"], f"{cab}<h1>{html.escape(d['titulo'])}</h1>{md(corpo)}", "../"), encoding="utf-8")
        itens.append((d.get("ano", "Sem ano"), d["titulo"], slug, est))
    grupos = {}
    for ano, t, s, e in itens: grupos.setdefault(ano, []).append((t, s, e))
    corpo = "<p class='rotulo'>Aulas e educação</p><h1>Aulas e materiais</h1><p class='lead'>Páginas de aula do Plano de Ensino de Biologia, cada uma com seu estágio.</p>"
    for ano in sorted(grupos):
        corpo += f"<h2>{html.escape(ano)}</h2><ul class='lista-aulas'>" + "".join(
            f"<li><a href='aulas/{s}.html'>{html.escape(t)}</a> <span class='area'>{ROTULO.get(e, e)}</span></li>" for t, s, e in grupos[ano]) + "</ul>"
    if not itens: corpo += "<p>Nenhuma aula ainda.</p>"
    (RAIZ / "aulas.html").write_text(pagina("Aulas e materiais", corpo, ""), encoding="utf-8")
    print(f"{len(itens)} páginas de aula geradas.")

if __name__ == "__main__": main()
