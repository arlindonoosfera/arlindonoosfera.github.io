#!/usr/bin/env python3
"""Construtor do site Arlindo Noosfera (sem dependências além do Python 3.9+).

    python3 build.py            valida tudo e gera os arquivos
    python3 build.py --check    só valida, sem escrever nada

Fonte dos dados: dados.json. Fonte das aulas: conteudo/aulas/*.md.
Gera: data.js, aulas.html, aulas/*.html, sitemap.xml, robots.txt.
Nunca apaga arquivos. Se houver QUALQUER erro, nada é escrito.
"""
import datetime, html, json, pathlib, re, sys
from urllib.parse import urlparse

RAIZ = pathlib.Path(__file__).resolve().parent
ORIGEM = RAIZ / "conteudo" / "aulas"
SITE_URL = "https://arlindonoosfera.github.io/"
ID_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


class Erros(list):
    def add(self, onde, campo, causa):
        self.append(f"{onde}: campo '{campo}': {causa}")


# ---------- validação ----------
def url_segura(v):
    try:
        u = urlparse(v)
    except ValueError:
        return False
    return u.scheme in ("http", "https") and bool(u.netloc)


def texto(e, onde, obj, campo, obrigatorio=True):
    v = obj.get(campo)
    if v is None:
        if obrigatorio: e.add(onde, campo, "obrigatório e ausente")
        return None
    if not isinstance(v, str) or not v.strip():
        e.add(onde, campo, "deve ser texto não vazio"); return None
    return v


def validar_dados(d):
    e = Erros()
    if not isinstance(d, dict): e.add("dados.json", "(raiz)", "deve ser um objeto"); return e
    estados = d.get("estados")
    ids = set()
    if not isinstance(estados, list) or not estados:
        e.add("dados.json", "estados", "lista obrigatória")
    else:
        for i, s in enumerate(estados):
            onde = f"dados.json estados[{i}]"
            if not isinstance(s, dict): e.add(onde, "(item)", "deve ser objeto"); continue
            sid = texto(e, onde, s, "id"); texto(e, onde, s, "rotulo"); texto(e, onde, s, "lua")
            if sid:
                if not ID_RE.match(sid): e.add(onde, "id", "use minúsculas sem acentos (ex.: concluido)")
                if sid in ids: e.add(onde, "id", f"duplicado: {sid}")
                ids.add(sid)
    for chave in ("projetos", "trajetoria", "interesses", "conexoes"):
        if not isinstance(d.get(chave), list): e.add("dados.json", chave, "lista obrigatória")
    for i, p in enumerate(d.get("projetos") or []):
        onde = f"dados.json projetos[{i}]"
        if not isinstance(p, dict): e.add(onde, "(item)", "deve ser objeto"); continue
        for c in ("titulo", "area", "resumo"): texto(e, onde, p, c)
        est = texto(e, onde, p, "estagio")
        if est and ids and est not in ids: e.add(onde, "estagio", f"estado desconhecido '{est}'; válidos: {sorted(ids)}")
        for c in ("metodo", "nota"): texto(e, onde, p, c, False)
        if "link" in p and not (isinstance(p["link"], str) and url_segura(p["link"])):
            e.add(onde, "link", "deve ser URL http(s) válida (omita o campo se não houver)")
    for i, g in enumerate(d.get("trajetoria") or []):
        onde = f"dados.json trajetoria[{i}]"
        if not isinstance(g, dict): e.add(onde, "(item)", "deve ser objeto"); continue
        texto(e, onde, g, "titulo")
        if not (isinstance(g.get("itens"), list) and all(isinstance(x, str) and x.strip() for x in g["itens"])):
            e.add(onde, "itens", "deve ser lista de textos (pode ser vazia)")
    for i, g in enumerate(d.get("interesses") or []):
        onde = f"dados.json interesses[{i}]"
        if not isinstance(g, dict): e.add(onde, "(item)", "deve ser objeto"); continue
        texto(e, onde, g, "grupo")
        if not (isinstance(g.get("itens"), list) and g["itens"] and all(isinstance(x, str) and x.strip() for x in g["itens"])):
            e.add(onde, "itens", "deve ser lista não vazia de textos")
    for i, c in enumerate(d.get("conexoes") or []):
        onde = f"dados.json conexoes[{i}]"
        if not isinstance(c, dict): e.add(onde, "(item)", "deve ser objeto"); continue
        texto(e, onde, c, "nome"); texto(e, onde, c, "nota")
        if c.get("url") not in (None, "") and not (isinstance(c["url"], str) and url_segura(c["url"])):
            e.add(onde, "url", "deve ser URL http(s) válida ou vazia")
    return e


# ---------- front matter ----------
def ler_meta(caminho, bruto, e):
    """Aceita só o formato usado no projeto: bloco '---' com linhas 'chave: valor'."""
    meta, corpo = {}, bruto
    if bruto.startswith("---\n"):
        fim = bruto.find("\n---\n", 4)
        if fim == -1:
            e.add(caminho, "(cabeçalho)", "bloco '---' aberto e não fechado"); return meta, bruto
        for n, linha in enumerate(bruto[4:fim].splitlines(), start=2):
            if not linha.strip(): continue
            m = re.match(r"^([a-z_]+):\s*(.*)$", linha)
            if not m: e.add(caminho, f"linha {n}", f"formato inválido: {linha!r}"); continue
            if m.group(1) in meta: e.add(caminho, m.group(1), "chave duplicada")
            meta[m.group(1)] = m.group(2).strip().strip('"')
        corpo = bruto[fim + 5:]
    return meta, corpo


def validar_meta(caminho, meta, ids, e):
    for c in meta:
        if c not in ("titulo", "ano", "estagio", "data"):
            e.add(caminho, c, "campo desconhecido (válidos: titulo, ano, estagio, data)")
    est = meta.get("estagio", "planejamento")
    if est not in ids: e.add(caminho, "estagio", f"estado desconhecido '{est}'; válidos: {sorted(ids)}")
    if "data" in meta:
        try: datetime.date.fromisoformat(meta["data"])
        except ValueError: e.add(caminho, "data", "use AAAA-MM-DD")


# ---------- Markdown (subconjunto seguro: tudo é escapado) ----------
def inline(t):
    t = html.escape(t, quote=False)
    def link(m):
        u = html.unescape(m.group(2))
        return f'<a href="{html.escape(u)}" rel="noopener noreferrer">{m.group(1)}</a>' if url_segura(u) else m.group(1)
    t = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", link, t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    return re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?!\w)", r"<em>\1</em>", t)


def markdown(texto_md):
    out, lista, par, tab, cit = [], None, [], [], []
    def fecha():
        nonlocal lista, par, tab, cit
        if par: out.append("<p>" + inline(" ".join(par)) + "</p>"); par = []
        if lista: out.append(f"</{lista}>"); lista = None
        if cit: out.append("<blockquote><p>" + inline(" ".join(cit)) + "</p></blockquote>"); cit = []
        if tab:
            l = [[c.strip() for c in r.strip().strip("|").split("|")] for r in tab if not re.match(r"^\s*\|?\s*:?-{2,}", r)]
            h = "".join(f"<th scope='col'>{inline(c)}</th>" for c in l[0])
            b = "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in l[1:])
            out.append(f"<div class='tabela' tabindex='0'><table><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table></div>"); tab = []
    for ln in texto_md.splitlines():
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


# ---------- páginas ----------
def pagina(titulo, desc, corpo, base, caminho):
    t, d = html.escape(titulo), html.escape(desc, quote=True)
    url = html.escape(SITE_URL + caminho, quote=True)
    return f"""<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{t} · Arlindo Noosfera</title><meta name="description" content="{d}">
<link rel="canonical" href="{url}"><meta property="og:type" content="website"><meta property="og:locale" content="pt_BR">
<meta property="og:title" content="{t}"><meta property="og:description" content="{d}"><meta property="og:url" content="{url}">
<link rel="stylesheet" href="{base}style.css"></head>
<body><a class="pular" href="#conteudo">Pular para o conteúdo</a>
<header class="topo"><a class="marca" href="{base}index.html"><span aria-hidden="true">🌒</span> Arlindo Noosfera</a>
<nav aria-label="Principal"><a href="{base}index.html#aulas">Aulas e educação</a><a href="{base}aulas.html">Todas as aulas</a><a href="{base}plano-biologia.html">Plano de Biologia</a></nav></header>
<main id="conteudo" class="plano prosa">{corpo}</main>
<footer class="rodape"><p>© Arlindo Noosfera. Material em rascunho; sem dados de estudantes.</p></footer></body></html>
"""


def slug_de(nome):
    return re.sub(r"[^a-z0-9]+", "-", nome.lower()).strip("-")


def construir(escrever=True):
    e = Erros()
    caminho_dados = RAIZ / "dados.json"
    try:
        dados = json.loads(caminho_dados.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return [f"{caminho_dados}: arquivo não encontrado"], None
    except json.JSONDecodeError as x:
        return [f"dados.json: JSON inválido (linha {x.lineno}, coluna {x.colno}): {x.msg}"], None
    e.extend(validar_dados(dados))
    ids = {s["id"] for s in dados.get("estados", []) if isinstance(s, dict) and "id" in s}
    rotulo = {s["id"]: s["rotulo"] for s in dados.get("estados", []) if isinstance(s, dict) and "id" in s}

    aulas, slugs = [], {}
    for f in sorted(ORIGEM.glob("*.md")):
        if f.name.startswith("_"): continue
        rel = f.relative_to(RAIZ).as_posix()
        meta, corpo = ler_meta(rel, f.read_text(encoding="utf-8"), e)
        validar_meta(rel, meta, ids, e)
        if not meta.get("titulo"):
            m = re.search(r"^#\s+(.*)", corpo, re.M)
            if m: meta["titulo"] = m.group(1).strip()
            else: e.add(rel, "titulo", "ausente (use 'titulo:' ou um '# Título')")
        slug = slug_de(f.stem)
        if not ID_RE.match(slug): e.add(rel, "(nome do arquivo)", "gera identificador inválido")
        if slug in slugs: e.add(rel, "(nome do arquivo)", f"gera o mesmo identificador de {slugs[slug]}")
        slugs[slug] = rel
        aulas.append((slug, meta, re.sub(r"^#\s+.*\n", "", corpo, count=1, flags=re.M)))

    if e: return list(e), None
    saidas = {}
    saidas["data.js"] = ("/* GERADO por build.py a partir de dados.json. Não edite à mão. */\n"
                         "window.DADOS = " + json.dumps(dados, ensure_ascii=False, indent=2) + ";\n")
    grupos, urls = {}, ["index.html", "plano-biologia.html", "aulas.html"]
    for slug, meta, corpo in sorted(aulas, key=lambda a: (a[1].get("ano", ""), a[1]["titulo"])):
        est = meta.get("estagio", "planejamento")
        cab = f"<p class='rotulo'>{html.escape(meta.get('ano', 'Aulas'))} · {html.escape(rotulo[est])}</p>"
        corpo_html = f"{cab}<h1>{html.escape(meta['titulo'])}</h1>{markdown(corpo)}"
        resumo = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", markdown(corpo))).strip()[:155]
        saidas[f"aulas/{slug}.html"] = pagina(meta["titulo"], resumo or meta["titulo"], corpo_html, "../", f"aulas/{slug}.html")
        grupos.setdefault(meta.get("ano", "Sem ano"), []).append((meta["titulo"], slug, est))
        urls.append(f"aulas/{slug}.html")
    lista = "<p class='lead'>Páginas de aula do Plano de Ensino de Biologia, cada uma com seu estágio.</p>"
    for ano in sorted(grupos):
        lista += f"<h2>{html.escape(ano)}</h2><ul class='lista-aulas'>" + "".join(
            f"<li><a href='aulas/{s}.html'>{html.escape(t)}</a> <span class='area'>{html.escape(rotulo[x])}</span></li>"
            for t, s, x in sorted(grupos[ano])) + "</ul>"
    if not aulas: lista += "<p>Nenhuma aula publicada ainda.</p>"
    saidas["aulas.html"] = pagina("Aulas e materiais", "Páginas de aula do Plano de Ensino de Biologia.",
                                  "<p class='rotulo'>Aulas e educação</p><h1>Aulas e materiais</h1>" + lista, "", "aulas.html")
    saidas["sitemap.xml"] = ('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                             + "".join(f"  <url><loc>{html.escape(SITE_URL + u)}</loc></url>\n" for u in sorted(urls)) + "</urlset>\n")
    saidas["robots.txt"] = f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}sitemap.xml\n"
    if escrever:
        for nome, conteudo in saidas.items():
            alvo = RAIZ / nome
            alvo.parent.mkdir(exist_ok=True)
            alvo.write_text(conteudo, encoding="utf-8")
    return [], saidas


def main(argv):
    erros, saidas = construir(escrever="--check" not in argv)
    if erros:
        print(f"{len(erros)} erro(s). Nada foi escrito:", file=sys.stderr)
        for x in erros: print("  - " + x, file=sys.stderr)
        return 1
    print(f"OK: {len(saidas)} arquivos " + ("validados." if "--check" in argv else "gerados."))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
