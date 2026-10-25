#!/usr/bin/env python3
"""Construtor do site Arlindo Noosfera. Apenas biblioteca padrão (Python 3.9+).

    python3 build.py            valida tudo e gera o site
    python3 build.py --check    só valida, sem escrever nada

Entradas : dados.json (estados, áreas, relações, fórum) e conteudo/<tipo>/*.md
Saídas   : páginas .html, indice.js, sitemap.xml, robots.txt, 404.html
Regras   : se houver QUALQUER erro, nada é escrito; o build nunca apaga arquivos.
"""
import datetime, html, json, pathlib, re, sys
from urllib.parse import urlparse

RAIZ = pathlib.Path(__file__).resolve().parent
SITE_URL = "https://arlindonoosfera.github.io/"
NOME = "Arlindo Noosfera"
ID_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
DATA_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# tipo -> (pasta em conteudo/, pasta de saída, rótulo)
TIPOS = {"aula": ("aulas", "aulas"), "projeto": ("projetos", "projetos"), "escrito": ("escritos", "escritos"),
         "resenha": ("resenhas", "resenhas"), "livro": ("biblioteca", "biblioteca")}
ENUM = {
    "recurso": ["aula", "atividade", "guia", "avaliacao", "material", "roteiro", "plano"],
    "categoria": ["ensaio", "noticia", "relato", "reflexao", "texto"],
    "tipo": ["livro", "filme", "serie"],
    "leitura": ["por-ler", "a-ler", "lendo", "concluido", "abandonado"],
}
ROTULOS = {
    "recurso": {"aula": "Aula", "atividade": "Atividade", "guia": "Guia de estudo", "avaliacao": "Avaliação", "material": "Material", "roteiro": "Roteiro", "plano": "Plano de ensino"},
    "categoria": {"ensaio": "Ensaio", "noticia": "Notícia comentada", "relato": "Relato de experiência", "reflexao": "Reflexão filosófica", "texto": "Texto autoral"},
    "tipo": {"livro": "Livro", "filme": "Filme", "serie": "Série"},
    "leitura": {"por-ler": "Por ler", "a-ler": "A ler", "lendo": "Em leitura", "concluido": "Concluído", "abandonado": "Abandonado"},
}
CAMPOS = {  # obrigatórios, opcionais
    "aula": (["titulo"], ["estado", "ano", "unidade", "recurso", "disciplina", "nivel", "duracao", "tags", "data", "atualizado", "resumo", "arquivo", "relacionados", "ordem"]),
    "projeto": (["titulo", "estado", "area", "resumo"], ["tags", "inicio", "atualizado", "destaque", "link", "relacionados"]),
    "escrito": (["titulo", "categoria", "data", "resumo"], ["subtitulo", "tags", "atualizado", "imagem", "fonte_titulo", "fonte_url", "fonte_data", "relacionados"]),
    "resenha": (["titulo", "tipo", "autoria", "ano", "data", "resumo"], ["spoilers", "nota", "capa", "tags", "relacionados", "atualizado"]),
    "livro": (["titulo", "autor", "leitura"], ["edicao", "editora", "ano", "isbn", "inicio", "fim", "tags", "resenha", "relacionados", "resumo", "atualizado", "capa"]),
}
ORDEM_ANO = ["Visão geral", "Todos os anos", "1º ano", "2º ano", "3º ano", "Extensão", "A organizar"]
DATAS = ("data", "atualizado", "inicio", "fim", "fonte_data")
LISTAS = ("tags", "relacionados")


class Erros(list):
    def add(self, onde, campo, causa):
        self.append(f"{onde}: {campo}: {causa}")


def esc(t): return html.escape(str(t), quote=True)
def slug_de(nome):
    return re.sub(r"[^a-z0-9]+", "-", nome.lower()).strip("-")
def url_segura(v):
    try: u = urlparse(v)
    except ValueError: return False
    return u.scheme in ("http", "https") and bool(u.netloc)


# ===================== dados.json =====================
def validar_dados(d):
    e = Erros()
    if not isinstance(d, dict): e.add("dados.json", "(raiz)", "deve ser um objeto"); return e
    def lista(chave, campos):
        v = d.get(chave)
        if not isinstance(v, list) or not v: e.add("dados.json", chave, "lista obrigatória e não vazia"); return []
        vistos = set()
        for i, x in enumerate(v):
            for c in campos:
                if not isinstance(x, dict) or not isinstance(x.get(c), str) or not x[c].strip():
                    e.add(f"dados.json {chave}[{i}]", c, "texto obrigatório")
            if isinstance(x, dict) and isinstance(x.get("id"), str):
                if not ID_RE.match(x["id"]): e.add(f"dados.json {chave}[{i}]", "id", "use minúsculas, números e hífens")
                if x["id"] in vistos: e.add(f"dados.json {chave}[{i}]", "id", f"duplicado: {x['id']}")
                vistos.add(x["id"])
        return v
    lista("estados", ["id", "rotulo", "lua"]); grupos = lista("grupos", ["id", "nome"]); areas = lista("areas", ["id", "nome", "grupo"])
    gids = {g.get("id") for g in grupos if isinstance(g, dict)}; aids = {a.get("id") for a in areas if isinstance(a, dict)}
    for i, a in enumerate(areas):
        if isinstance(a, dict) and a.get("grupo") not in gids: e.add(f"dados.json areas[{i}]", "grupo", f"grupo inexistente: {a.get('grupo')}")
    for i, r in enumerate(d.get("relacoes") or []):
        if not (isinstance(r, list) and len(r) == 2 and all(x in aids for x in r)): e.add(f"dados.json relacoes[{i}]", "(par)", "deve ser [id_area, id_area] existentes")
    f = d.get("forum")
    if f is not None:
        if not isinstance(f, dict) or not all(isinstance(f.get(k), str) and f[k].strip() for k in ("repo", "repo_id", "categoria", "categoria_id")):
            e.add("dados.json", "forum", "null (desativado) ou objeto com repo, repo_id, categoria, categoria_id")
    return e


# ===================== front matter =====================
def ler_meta(rel, bruto, e):
    meta, corpo = {}, bruto
    if bruto.startswith("---\n"):
        fim = bruto.find("\n---\n", 4)
        if fim == -1: e.add(rel, "(cabeçalho)", "bloco '---' aberto e não fechado"); return meta, bruto
        for n, linha in enumerate(bruto[4:fim].splitlines(), start=2):
            if not linha.strip(): continue
            m = re.match(r"^([a-z_]+):\s*(.*)$", linha)
            if not m: e.add(rel, f"linha {n}", f"formato inválido: {linha!r}"); continue
            if m.group(1) in meta: e.add(rel, m.group(1), "chave duplicada")
            meta[m.group(1)] = m.group(2).strip().strip('"')
        corpo = bruto[fim + 5:]
    return meta, corpo


def validar_meta(rel, tipo, meta, estados, e):
    obrig, opc = CAMPOS[tipo]
    for c in obrig:
        if not meta.get(c) and c != "titulo": e.add(rel, c, "obrigatório e ausente")
    for c in meta:
        if c not in obrig + opc: e.add(rel, c, f"campo desconhecido (válidos: {', '.join(obrig + opc)})")
    for campo, validos in ENUM.items():
        if campo in meta and meta[campo] not in validos and not (campo == "tipo" and tipo != "resenha") and not (campo == "recurso" and tipo != "aula"):
            e.add(rel, campo, f"valor inválido '{meta[campo]}'; válidos: {validos}")
    if "estado" in meta and meta["estado"] not in estados: e.add(rel, "estado", f"estado desconhecido '{meta['estado']}'; válidos: {sorted(estados)}")
    for c in DATAS:
        if c in meta and not DATA_RE.match(meta[c]): e.add(rel, c, "use AAAA-MM-DD")
        elif c in meta:
            try: datetime.date.fromisoformat(meta[c])
            except ValueError: e.add(rel, c, "data inexistente")
    for c in ("destaque", "spoilers"):
        if c in meta and meta[c] not in ("sim", "nao"): e.add(rel, c, "use 'sim' ou 'nao'")
    if "nota" in meta:
        try:
            if not 0 <= float(meta["nota"]) <= 5: raise ValueError
        except ValueError: e.add(rel, "nota", "número de 0 a 5")
    for c in ("link", "fonte_url"):
        if c in meta and not url_segura(meta[c]): e.add(rel, c, "deve ser URL http(s) válida")
    if tipo == "escrito" and meta.get("categoria") == "noticia":
        for c in ("fonte_titulo", "fonte_url", "fonte_data"):
            if not meta.get(c): e.add(rel, c, "obrigatório para notícias comentadas (preserva a atribuição)")
    if "ordem" in meta and not meta["ordem"].isdigit(): e.add(rel, "ordem", "número inteiro")
    for c in LISTAS:
        meta[c] = [x.strip() for x in meta.get(c, "").split(",") if x.strip()]
    for t in meta["tags"]:
        if not ID_RE.match(t): e.add(rel, "tags", f"tag inválida '{t}' (use minúsculas sem acento, com hífens)")


# ===================== Markdown seguro =====================
INTERNO = re.compile(r"^(aulas|projetos|escritos|resenhas|biblioteca)/([a-z0-9-]+)(#[\w-]+)?$")


class Ctx:
    def __init__(self, rel, base, destinos, e):
        self.rel, self.base, self.destinos, self.e = rel, base, destinos, e

    def href(self, h):
        h = html.unescape(h)
        m = INTERNO.match(h)
        if m:
            if f"{m.group(1)}/{m.group(2)}" not in self.destinos:
                self.e.add(self.rel, "link", f"página inexistente: {h}"); return None
            return f"{self.base}{m.group(1)}/{m.group(2)}.html{m.group(3) or ''}"
        if h.startswith("#"): return h
        if url_segura(h): return h
        if (RAIZ / h).is_file(): return self.base + h
        self.e.add(self.rel, "link", f"destino inválido ou inexistente: {h}"); return None


def inline(t, ctx):
    t = html.escape(t, quote=False)
    def link(m):
        alvo = ctx.href(m.group(2))
        if alvo is None: return m.group(1)
        rotulo = m.group(1) or html.escape(html.unescape(m.group(2)))
        rel = ' rel="noopener noreferrer"' if alvo.startswith("http") else ""
        return f'<a href="{esc(alvo)}"{rel}>{rotulo}</a>'
    t = re.sub(r"\[([^\]]*)\]\(([^)\s]+)\)", link, t)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?!\w)", r"<em>\1</em>", t).replace("**", "")
    return t.replace("&lt;u&gt;", "<u>").replace("&lt;/u&gt;", "</u>")


def markdown(texto, ctx):
    """Devolve (html, cabeçalhos[(nível, id, texto)]). Tudo é escapado; só http(s) e destinos locais viram links."""
    linhas = texto.splitlines()
    nivs = [len(m.group(1)) for l in linhas if (m := re.match(r"^(#{1,6})\s", l))]
    deslocamento = 2 - min(nivs) if nivs else 0
    out, heads, ids, anterior = [], [], {}, 1
    pilha, par, tab, cit, cod = [], [], [], [], None

    def fecha_lista():
        while pilha: out.append(f"</li></{pilha.pop()[1]}>")
    def fecha():
        nonlocal par, tab, cit
        if par: out.append("<p>" + inline(" ".join(par), ctx) + "</p>"); par = []
        if cit:
            out.append("<blockquote>" + "".join("<p>" + inline(" ".join(p.split("\n")), ctx) + "</p>" for p in "\n".join(cit).split("\n\n") if p.strip()) + "</blockquote>"); cit = []
        if tab:
            l = [[c.strip() for c in r.strip().strip("|").split("|")] for r in tab if not re.match(r"^\s*\|?\s*:?-{2,}", r)]
            h = "".join(f"<th scope='col'>{inline(c, ctx)}</th>" for c in l[0])
            b = "".join("<tr>" + "".join(f"<td>{inline(c, ctx)}</td>" for c in r) + "</tr>" for r in l[1:])
            out.append(f"<div class='tabela' tabindex='0' role='region' aria-label='Tabela'><table><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table></div>"); tab = []

    for ln in linhas:
        s = ln.rstrip()
        if cod is not None:
            if s.strip().startswith("```"): out.append("<pre><code>" + html.escape("\n".join(cod)) + "</code></pre>"); cod = None
            else: cod.append(ln)
            continue
        if s.strip().startswith("```"): fecha(); fecha_lista(); cod = []; continue
        if not s.strip():
            if cit and cit[-1] != "": cit.append("")
            elif par or tab: fecha()
            continue
        m = re.match(r"^(#{1,6})\s+(.*)", s)
        if m:
            fecha(); fecha_lista()
            n = max(2, min(6, len(m.group(1)) + deslocamento, anterior + 1)); anterior = n; txt = re.sub(r"\*\*|`", "", m.group(2)).strip()
            base = slug_de(re.sub(r"[^\w\s-]", "", txt.lower().encode("ascii", "ignore").decode() or "secao")) or "secao"
            ids[base] = ids.get(base, 0) + 1; hid = base if ids[base] == 1 else f"{base}-{ids[base]}"
            heads.append((n, hid, txt)); out.append(f'<h{n} id="{hid}">{inline(m.group(2), ctx)}</h{n}>'); continue
        if re.match(r"^-{3,}$", s.strip()): fecha(); fecha_lista(); out.append("<hr>"); continue
        im = re.match(r'^!\[(.*?)\]\(([^\s)]+)(?: "(.*?)")?\)$', s.strip())
        if im:
            fecha(); fecha_lista()
            if not (RAIZ / im.group(2)).is_file(): ctx.e.add(ctx.rel, "imagem", f"arquivo inexistente: {im.group(2)}"); continue
            leg = f"<figcaption>{html.escape(im.group(3))}</figcaption>" if im.group(3) else ""
            out.append(f'<figure><img src="{esc(ctx.base + im.group(2))}" alt="{esc(im.group(1))}" loading="lazy" decoding="async">{leg}</figure>'); continue
        if s.lstrip().startswith("|"):
            if par or cit: fecha()
            fecha_lista(); tab.append(s); continue
        it = re.match(r"^(\s*)([-*]|\d+\.)\s+(.*)", s)
        if it:
            fecha()
            ind = len(it.group(1).expandtabs(4)); tag = "ol" if it.group(2)[0].isdigit() else "ul"
            while pilha and ind < pilha[-1][0]: out.append(f"</li></{pilha.pop()[1]}>")
            if pilha and ind == pilha[-1][0]: out.append("</li>")
            elif not pilha or ind > pilha[-1][0]: out.append(f"<{tag}>"); pilha.append((ind, tag))
            out.append("<li>" + inline(it.group(3), ctx)); continue
        if s.startswith(">"):
            if par or tab: fecha()
            fecha_lista(); cit.append(s[1:].strip()); continue
        if pilha and s.startswith((" ", "\t")): out.append("<br>" + inline(s.strip(), ctx)); continue
        if cit: fecha()
        fecha_lista(); par.append(s.strip())
    fecha(); fecha_lista()
    return "\n".join(out), heads


def texto_puro(h): return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", h))).strip()


# ===================== carregamento =====================
def resumo_de(h, limite=170):
    m = re.search(r"<p>(.*?)</p>", h, re.S)
    t = texto_puro(m.group(1)) if m else ""
    return t if len(t) <= limite else t[:limite].rsplit(" ", 1)[0] + "…"


def carregar(e, estados):
    itens = []
    for tipo, (pasta, saida) in TIPOS.items():
        for f in sorted((RAIZ / "conteudo" / pasta).glob("*.md")):
            if f.name.startswith("_"): continue
            rel = f.relative_to(RAIZ).as_posix()
            meta, corpo = ler_meta(rel, f.read_text(encoding="utf-8"), e)
            validar_meta(rel, tipo, meta, estados, e)
            if not meta.get("titulo"):
                m = re.search(r"^#\s+(.*)", corpo, re.M)
                if m: meta["titulo"] = m.group(1).strip()
                else: e.add(rel, "titulo", "ausente (use 'titulo:' ou um '# Título')")
            corpo = re.sub(r"^#\s+.*\n", "", corpo, count=1, flags=re.M)
            slug = slug_de(f.stem)
            if not ID_RE.match(slug): e.add(rel, "(nome do arquivo)", "gera identificador inválido")
            meta.setdefault("estado", "planejamento") if tipo == "aula" else None
            itens.append({"tipo": tipo, "slug": slug, "pasta": saida, "url": f"{saida}/{slug}.html", "chave": f"{saida}/{slug}",
                          "rel": rel, "meta": meta, "corpo": corpo, "titulo": meta.get("titulo", slug)})
    return itens


def verificar_referencias(itens, e):
    chaves = {i["chave"] for i in itens}
    for i in itens:
        m, rel = i["meta"], i["rel"]
        for r in m.get("relacionados", []):
            if r not in chaves: e.add(rel, "relacionados", f"item inexistente: {r}")
        if m.get("resenha") and f"resenhas/{m['resenha']}" not in chaves: e.add(rel, "resenha", f"resenha inexistente: {m['resenha']}")
        for c in ("imagem", "capa"):
            if c in m and not (RAIZ / m[c]).is_file(): e.add(rel, c, f"arquivo inexistente: {m[c]}")
        if "arquivo" in m:
            caminho = m["arquivo"].split("|")[0].strip()
            if not (RAIZ / caminho).is_file(): e.add(rel, "arquivo", f"arquivo inexistente: {caminho}")
    return chaves


def carregar_frases(e):
    f = RAIZ / "conteudo" / "frases.json"
    if not f.exists(): return []
    try: v = json.loads(f.read_text(encoding="utf-8"))
    except json.JSONDecodeError as x: e.add("conteudo/frases.json", f"linha {x.lineno}", x.msg); return []
    if not isinstance(v, list): e.add("conteudo/frases.json", "(raiz)", "deve ser uma lista"); return []
    for i, x in enumerate(v):
        for c in ("texto", "autor", "fonte"):
            if not (isinstance(x, dict) and isinstance(x.get(c), str) and x[c].strip()):
                e.add(f"conteudo/frases.json[{i}]", c, "obrigatório (frase, autoria e fonte verificável)")
        if isinstance(x, dict) and x.get("url") and not url_segura(x["url"]): e.add(f"conteudo/frases.json[{i}]", "url", "URL http(s) inválida")
    return v


# ===================== HTML: peças =====================
NAV = [("index.html", "Início", "inicio"), ("projetos.html", "Projetos", "projetos"), ("aulas.html", "Aulas e educação", "aulas"),
       ("escritos.html", "Escritos", "escritos"), ("resenhas.html", "Resenhas", "resenhas"), ("biblioteca.html", "Biblioteca", "biblioteca"),
       ("mapa.html", "Mapa de interesses", "mapa"), ("estudos.html", "Estudos e fórum", "estudos")]
LOGO = ('<svg class="logo" viewBox="0 0 32 32" width="28" height="28" aria-hidden="true" focusable="false"><circle cx="16" cy="16" r="8" fill="none" stroke="currentColor" stroke-width="2"/>'
        '<ellipse cx="16" cy="16" rx="14" ry="5" fill="none" stroke="currentColor" stroke-width="1" transform="rotate(-25 16 16)"/><circle cx="27" cy="10" r="2" fill="currentColor"/></svg>')


def layout(titulo, desc, corpo, base, caminho, ativo="", dados_js=False, indexar=True):
    url = SITE_URL + ("" if caminho == "index.html" else caminho)
    atual = ' aria-current="page"'
    nav = "".join('<li><a href="%s%s"%s>%s</a></li>' % (base, h, atual if a == ativo else "", r) for h, r, a in NAV)
    t = titulo if titulo == NOME else f"{titulo} · {NOME}"
    robots = "" if indexar else '<meta name="robots" content="noindex">'
    script_dados = '<script src="%sindice.js"></script>' % base if dados_js else ""
    return f"""<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(t)}</title><meta name="description" content="{esc(desc)}">{robots}
<link rel="canonical" href="{esc(url)}"><meta property="og:type" content="website"><meta property="og:locale" content="pt_BR">
<meta property="og:site_name" content="{NOME}"><meta property="og:title" content="{esc(t)}"><meta property="og:description" content="{esc(desc)}"><meta property="og:url" content="{esc(url)}">
<meta name="color-scheme" content="light dark"><link rel="icon" href="{base}favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="{base}style.css">
<script>document.documentElement.classList.add("js")</script></head>
<body><a class="pular" href="#conteudo">Pular para o conteúdo</a>
<header class="cabecalho"><div class="cabecalho-in">
<a class="marca" href="{base}index.html">{LOGO}<span>{NOME}</span></a>
<button class="menu-btn" type="button" aria-expanded="false" aria-controls="menu">Menu</button>
<nav id="menu" aria-label="Principal"><ul>{nav}</ul>
<form class="busca" role="search" action="{base}busca.html" method="get"><label class="sr" for="q">Buscar no site</label><input id="q" name="q" type="search" placeholder="Buscar" autocomplete="off"><button type="submit">Buscar</button></form></nav>
</div></header>
<main id="conteudo">{corpo}</main>
<footer class="rodape"><p>© {NOME}. Textos e materiais autorais, salvo indicação. Imagens ilustrativas são identificadas como tais.</p>
<p><a href="https://github.com/arlindonoosfera/arlindonoosfera.github.io" rel="noopener noreferrer">Código-fonte do site</a></p></footer>
{script_dados}<script src="{base}site.js" defer></script></body></html>
"""


def selo_estado(est, estados):
    s = estados.get(est, {"rotulo": est, "lua": "◌"})
    return f'<span class="selo estado-{esc(est)}"><span aria-hidden="true">{s["lua"]}</span> {esc(s["rotulo"])}</span>'


def fmt_data(d):
    a, m, dia = d.split("-")
    meses = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
    return f"{int(dia)} de {meses[int(m) - 1]} de {a}"


def cartao(i, estados, base="", nivel=3):
    m, t = i["meta"], i["tipo"]
    href = f'{base}{i["url"]}'
    if t == "aula":
        meta = f'{esc(m.get("ano", ""))} · {esc(ROTULOS["recurso"].get(m.get("recurso", "material"), "Material"))}'
        extra = f'<p class="area">{esc(m["unidade"])}</p>' if m.get("unidade") else ""
        selo = selo_estado(m["estado"], estados)
    elif t == "projeto":
        meta, extra, selo = esc(m["area"]), "", selo_estado(m["estado"], estados)
    elif t == "escrito":
        meta, extra, selo = f'{ROTULOS["categoria"][m["categoria"]]} · {fmt_data(m["data"])}', "", ""
    elif t == "resenha":
        meta, extra, selo = f'{ROTULOS["tipo"][m["tipo"]]} · {esc(m["autoria"])} · {esc(m["ano"])}', "", ""
    else:
        meta, extra, selo = f'{esc(m["autor"])}', "", f'<span class="selo">{ROTULOS["leitura"][m["leitura"]]}</span>'
    return (f'<article class="cartao"><p class="meta">{meta}</p><h{nivel}><a href="{esc(href)}">{esc(i["titulo"])}</a></h{nivel}>{extra}'
            f'<p>{esc(i["resumo"])}</p>{selo}</article>')


def attrs_filtro(i):
    m, t = i["meta"], i["tipo"]
    if t == "aula": campos = {"ano": m.get("ano", ""), "recurso": m.get("recurso", "material"), "estado": m.get("estado", "")}
    elif t == "projeto": campos = {"estado": m.get("estado", ""), "area": m["area"].split("·")[0].strip()}
    elif t == "escrito": campos = {"categoria": m.get("categoria", "")}
    elif t == "resenha": campos = {"tipo": m.get("tipo", "")}
    else: campos = {"leitura": m.get("leitura", "")}
    texto = " ".join([i["titulo"], i["resumo"], " ".join(m.get("tags", []))])
    return campos, texto


def pagina_lista(cfg, itens, estados, base=""):
    """cfg: titulo, intro, vazio, caminho, ativo, filtros[(campo, rótulo, valores_ordenados, rotulos)], agrupar(campo|None)."""
    corpo = f'<div class="pagina"><header class="topo-pagina"><p class="rotulo">{esc(cfg["rotulo"])}</p><h1>{esc(cfg["titulo"])}</h1><p class="lead">{cfg["intro"]}</p></header>'
    if not itens:
        return corpo + f'<div class="vazio">{cfg["vazio"]}</div></div>'
    ctrl = '<div class="controles" data-controles><div class="campo"><label for="f-busca">Buscar nesta lista</label><input id="f-busca" type="search" autocomplete="off"></div>'
    for campo, rotulo, valores, rot in cfg["filtros"]:
        if len(valores) < 2: continue
        ctrl += f'<div class="campo"><label for="f-{campo}">{esc(rotulo)}</label><select id="f-{campo}" data-campo="{campo}"><option value="">Todos</option>'
        ctrl += "".join(f'<option value="{esc(v)}">{esc(rot.get(v, v))}</option>' for v in valores) + "</select></div>"
    ctrl += '<button type="button" class="limpar" data-limpar hidden>Limpar filtros</button></div><p class="status" role="status" data-status></p>'
    grupos = {}
    for i in itens: grupos.setdefault(i["meta"].get(cfg["agrupar"], "") if cfg.get("agrupar") else "", []).append(i)
    ordem = sorted(grupos, key=lambda g: ORDEM_ANO.index(g) if g in ORDEM_ANO else 99) if cfg.get("agrupar") == "ano" else sorted(grupos)
    cont = ""
    for g in ordem:
        cards = ""
        for i in grupos[g]:
            campos, texto = attrs_filtro(i)
            da = "".join(f' data-{k}="{esc(v)}"' for k, v in campos.items())
            cards += cartao(i, estados, base, 3 if cfg.get("agrupar") else 2).replace('<article class="cartao"', f'<article class="cartao" data-item data-texto="{esc(texto)}"{da}', 1)
        cont += f'<section class="grupo" data-grupo>{"<h2>" + esc(g) + "</h2>" if g else ""}<div class="grade">{cards}</div></section>'
    vazio = '<p class="vazio" data-sem-resultado hidden>Nenhum resultado. Tente outros termos ou limpe os filtros.</p>'
    return corpo + ctrl + cont + vazio + "</div>"


def secao_relacionados(i, itens_por_chave, todos):
    m, lista = i["meta"], []
    for c in m.get("relacionados", []): lista.append(itens_por_chave[c])
    tags = set(m.get("tags", []))
    if tags:
        for o in todos:
            if o is not i and o not in lista and tags & set(o["meta"].get("tags", [])): lista.append(o)
    lista = lista[:6]
    if not lista: return ""
    rot = {"aula": "Aula", "projeto": "Projeto", "escrito": "Escrito", "resenha": "Resenha", "livro": "Biblioteca"}
    return ('<aside class="relacionados" aria-labelledby="rel-t"><h2 id="rel-t">Relacionados</h2><ul>' +
            "".join(f'<li><a href="../{o["url"]}">{esc(o["titulo"])}</a> <span class="area">{rot[o["tipo"]]}</span></li>' for o in lista) + "</ul></aside>")


def pagina_item(i, html_corpo, heads, estados, rel_html):
    m, t = i["meta"], i["tipo"]
    toc = ""
    tops = [h for h in heads if h[0] in (2, 3)]
    if len([h for h in heads if h[0] == 2]) >= 3 or len(tops) >= 6:
        toc = '<nav class="sumario" aria-labelledby="sum-t"><h2 id="sum-t">Neste texto</h2><ol>' + "".join(
            f'<li class="n{h[0]}"><a href="#{h[1]}">{esc(h[2])}</a></li>' for h in tops) + "</ol></nav>"
    voltar = {"aula": ("aulas.html", "Aulas e educação"), "projeto": ("projetos.html", "Projetos"), "escrito": ("escritos.html", "Escritos"),
              "resenha": ("resenhas.html", "Resenhas"), "livro": ("biblioteca.html", "Biblioteca")}[t]
    cab, extra_antes, extra_depois = "", "", ""
    if t == "aula":
        fichas = [("Ano", m.get("ano")), ("Unidade", m.get("unidade")), ("Tipo", ROTULOS["recurso"].get(m.get("recurso", "material"))),
                  ("Disciplina", m.get("disciplina")), ("Nível", m.get("nivel")), ("Duração", m.get("duracao"))]
        cab = f'<p class="rotulo">{esc(m.get("ano", "Aula"))}</p>'
        extra_antes = ('<dl class="ficha">' + "".join(f"<div><dt>{a}</dt><dd>{esc(b)}</dd></div>" for a, b in fichas if b) + "</dl>"
                       f'<p>{selo_estado(m["estado"], estados)}</p>')
        if m.get("arquivo"):
            c, _, r = m["arquivo"].partition("|")
            extra_antes += f'<p class="download"><a href="../{esc(c.strip())}" download>⬇ {esc(r.strip() or "Baixar material")}</a></p>'
    elif t == "projeto":
        cab = f'<p class="rotulo">{esc(m["area"])}</p>'
        ds = [f"Início: {fmt_data(m['inicio'])}" if m.get("inicio") else "", f"Atualizado: {fmt_data(m['atualizado'])}" if m.get("atualizado") else ""]
        extra_antes = f'<p>{selo_estado(m["estado"], estados)}</p>' + (f'<p class="meta">{" · ".join(x for x in ds if x)}</p>' if any(ds) else "")
        if m.get("link"): extra_antes += f'<p><a href="{esc(m["link"])}" rel="noopener noreferrer">Repositório ou página do projeto (externo)</a></p>'
    elif t == "escrito":
        cab = f'<p class="rotulo">{ROTULOS["categoria"][m["categoria"]]}</p>'
        extra_antes = f'<p class="meta"><time datetime="{m["data"]}">{fmt_data(m["data"])}</time>' + (f' · atualizado em {fmt_data(m["atualizado"])}' if m.get("atualizado") else "") + "</p>"
        if m.get("subtitulo"): extra_antes = f'<p class="subtitulo">{esc(m["subtitulo"])}</p>' + extra_antes
        if m["categoria"] == "noticia":
            extra_antes += (f'<aside class="fonte" aria-label="Notícia original"><h2>Notícia original</h2><p><a href="{esc(m["fonte_url"])}" rel="noopener noreferrer">{esc(m["fonte_titulo"])}</a>'
                            f'<br><span class="meta">Publicada em {fmt_data(m["fonte_data"])}. Leia a fonte completa no endereço original.</span></p></aside><h2>Comentário</h2>')
        if m.get("imagem"): extra_antes += f'<figure><img src="../{esc(m["imagem"])}" alt="" loading="lazy"></figure>'
    elif t == "resenha":
        cab = f'<p class="rotulo">Resenha · {ROTULOS["tipo"][m["tipo"]]}</p>'
        extra_antes = f'<p class="meta">{esc(m["autoria"])} · {esc(m["ano"])} · <time datetime="{m["data"]}">{fmt_data(m["data"])}</time>' + (f' · nota {esc(m["nota"])}/5' if m.get("nota") else "") + "</p>"
        if m.get("capa"): extra_antes += f'<figure class="capa"><img src="../{esc(m["capa"])}" alt="Capa ou cartaz de {esc(i["titulo"])}" loading="lazy"></figure>'
        if m.get("spoilers") == "sim": extra_antes += '<p class="aviso-spoiler" role="note"><strong>Aviso:</strong> este texto contém spoilers.</p>'
    else:
        cab = f'<p class="rotulo">Biblioteca · {ROTULOS["leitura"][m["leitura"]]}</p>'
        fichas = [("Autor", m["autor"]), ("Edição", m.get("edicao")), ("Editora", m.get("editora")), ("Ano", m.get("ano")), ("ISBN", m.get("isbn")),
                  ("Início", fmt_data(m["inicio"]) if m.get("inicio") else ""), ("Conclusão", fmt_data(m["fim"]) if m.get("fim") else "")]
        extra_antes = '<dl class="ficha">' + "".join(f"<div><dt>{a}</dt><dd>{esc(b)}</dd></div>" for a, b in fichas if b) + "</dl>"
        if m.get("capa"): extra_antes += f'<figure class="capa"><img src="../{esc(m["capa"])}" alt="Capa de {esc(i["titulo"])}" loading="lazy"></figure>'
        if m.get("resenha"): extra_antes += f'<p><a href="../resenhas/{esc(m["resenha"])}.html">Ler a resenha deste livro →</a></p>'
    return (f'<article class="pagina leitura"><p class="migalha"><a href="../{voltar[0]}">← {voltar[1]}</a></p><header class="topo-pagina">{cab}<h1>{esc(i["titulo"])}</h1></header>'
            f'{extra_antes}{toc}<div class="prosa">{html_corpo}</div>{rel_html}</article>')


# ===================== mapa de interesses =====================
def montar_mapa(dados, itens):
    import math
    areas = {a["id"]: a for a in dados["areas"]}
    liga = {k: [] for k in areas}
    for i in itens:
        for t in i["meta"].get("tags", []):
            if t in liga and i not in liga[t]: liga[t].append(i)
    ativas = [a for a in dados["areas"] if liga[a["id"]]]
    W, H, cx, cy = 760, 580, 380, 290
    gs = [g for g in dados["grupos"] if any(a["grupo"] == g["id"] for a in ativas)]
    pos, linhas, nos = {}, [], []
    for gi, g in enumerate(gs):
        ang = -math.pi / 2 + 2 * math.pi * gi / max(len(gs), 1)
        hx, hy = cx + 130 * math.cos(ang), cy + 130 * math.sin(ang)
        linhas.append(f'<line x1="{cx}" y1="{cy}" x2="{hx:.0f}" y2="{hy:.0f}" class="l-hub"/>')
        nos.append(f'<g class="hub"><circle cx="{hx:.0f}" cy="{hy:.0f}" r="6"/><text x="{hx:.0f}" y="{hy - 12:.0f}" text-anchor="middle">{esc(g["nome"])}</text></g>')
        ag = [a for a in ativas if a["grupo"] == g["id"]]
        k = len(ag); spread = min(math.radians(150), math.radians(38) * max(k - 1, 1))
        for j, a in enumerate(ag):
            aa = ang + (0 if k == 1 else -spread / 2 + spread * j / (k - 1))
            pos[a["id"]] = (hx + 112 * math.cos(aa), hy + 112 * math.sin(aa), math.cos(aa))
            linhas.append(f'<line x1="{hx:.0f}" y1="{hy:.0f}" x2="{pos[a["id"]][0]:.0f}" y2="{pos[a["id"]][1]:.0f}" class="l-area"/>')
    for a, b in dados.get("relacoes", []):
        if a in pos and b in pos:
            linhas.append(f'<line x1="{pos[a][0]:.0f}" y1="{pos[a][1]:.0f}" x2="{pos[b][0]:.0f}" y2="{pos[b][1]:.0f}" class="l-rel"/>')
    for a in ativas:
        x, y, c = pos[a["id"]]; n = len(liga[a["id"]]); r = 6 + min(n, 8)
        anc, dx = ("start", r + 5) if c >= 0 else ("end", -(r + 5))
        t = f'{a["nome"]}: {n} {"conteúdo" if n == 1 else "conteúdos"}'
        nos.append(f'<a href="#area-{a["id"]}" class="no"><title>{esc(t)}</title><circle cx="{x:.0f}" cy="{y:.0f}" r="{r}"/><text x="{x + dx:.0f}" y="{y + 4:.0f}" text-anchor="{anc}">{esc(a["nome"])}</text></a>')
    svg = (f'<svg class="mapa-svg" viewBox="0 0 {W} {H}" role="group" aria-labelledby="mapa-t"><title id="mapa-t">Rede de áreas de interesse com produção associada</title>'
           f'<circle cx="{cx}" cy="{cy}" r="26" class="centro"/><text x="{cx}" y="{cy + 4}" text-anchor="middle" class="centro-t">Noosfera</text>' + "".join(linhas) + "".join(nos) + "</svg>")
    rot = {"aula": "Aula", "projeto": "Projeto", "escrito": "Escrito", "resenha": "Resenha", "livro": "Biblioteca"}
    texto = ""
    for g in dados["grupos"]:
        texto += f'<section class="grupo-area"><h2>{esc(g["nome"])}</h2>'
        for a in [x for x in dados["areas"] if x["grupo"] == g["id"]]:
            vizinhas = [b if a["id"] == c else c for c, b in dados["relacoes"] if a["id"] in (c, b)]
            viz = ('<p class="area">Áreas próximas: ' + ", ".join(f'<a href="#area-{v}">{esc(areas[v]["nome"])}</a>' for v in vizinhas) + "</p>") if vizinhas else ""
            if liga[a["id"]]:
                conteudo = "<ul>" + "".join(f'<li><a href="{i["url"]}">{esc(i["titulo"])}</a> <span class="area">{rot[i["tipo"]]}</span></li>' for i in liga[a["id"]]) + "</ul>"
                estado = ""
            else:
                conteudo, estado = "", '<p class="vazio-area">Interesse em desenvolvimento: ainda sem produção associada.</p>'
            texto += f'<article class="area-bloco {"com" if liga[a["id"]] else "sem"}" id="area-{a["id"]}"><h3>{esc(a["nome"])}</h3>{conteudo}{estado}{viz}</article>'
        texto += "</section>"
    return svg, texto, len(ativas)


def pagina_mapa(dados, itens):
    svg, texto, n = montar_mapa(dados, itens)
    corpo = ('<div class="pagina"><header class="topo-pagina"><p class="rotulo">Mapa de interesses</p><h1>Áreas e conexões</h1>'
             '<p class="lead">Cada área leva ao que existe de fato no site. Círculos cheios têm produção associada; as demais estão listadas abaixo como interesses em desenvolvimento.</p></header>'
             f'<figure class="mapa-fig">{svg}<figcaption>Linhas contínuas ligam grupos e áreas. Linhas tracejadas indicam relações conceituais entre áreas, não produção. O tamanho do círculo cresce com o número de conteúdos. Em telas pequenas, use a lista abaixo.</figcaption></figure>'
             f'<p class="meta">{n} áreas com conteúdo associado.</p><div class="lista-areas">{texto}</div></div>')
    return corpo


# ===================== estudos, busca, início =====================
def plural(n, um, varios): return f"{n} {um if n == 1 else varios}"


def pagina_estudos(dados, por_tipo):
    anos = sorted({i["meta"].get("ano") for i in por_tipo["aula"] if i["meta"].get("ano") in ("1º ano", "2º ano", "3º ano")})
    atalhos = "".join(f'<li><a href="aulas.html?ano={esc(a.replace(" ", "+"))}">{esc(a)} do Ensino Médio</a></li>' for a in anos)
    cartoes = [("aulas.html", "Aulas e materiais", plural(len(por_tipo["aula"]), "página", "páginas") + " de ensino de Biologia"),
               ("resenhas.html", "Resenhas", "Livros, filmes e séries" if por_tipo["resenha"] else "Em preparação"),
               ("escritos.html", "Ensaios e escritos", "Textos autorais" if por_tipo["escrito"] else "Em migração"),
               ("biblioteca.html", "Biblioteca comentada", "Fichamentos e anotações" if por_tipo["livro"] else "Em construção"),
               ("mapa.html", "Mapa de interesses", "Explore por tema")]
    grade = "".join(f'<article class="cartao"><h3><a href="{h}">{t}</a></h3><p>{d}</p></article>' for h, t, d in cartoes)
    f = dados.get("forum")
    if f:
        forum = (f'<div id="forum" data-repo="{esc(f["repo"])}" data-repo-id="{esc(f["repo_id"])}" data-categoria="{esc(f["categoria"])}" data-categoria-id="{esc(f["categoria_id"])}">'
                 '<p>As discussões usam o <strong>giscus</strong>, que guarda os comentários no GitHub Discussions. Para participar é preciso ter uma conta no GitHub. '
                 'Ao carregar, o navegador se conecta ao serviço externo giscus.app.</p><button type="button" class="botao" data-forum-carregar>Carregar discussão</button></div>')
    else:
        forum = '<p class="vazio">O fórum ainda não foi aberto. Quando estiver ativo, as dúvidas e discussões aparecerão aqui.</p>'
    return ('<div class="pagina"><header class="topo-pagina"><p class="rotulo">Estudos e fórum</p><h1>Central de estudos</h1>'
            '<p class="lead">Para quem chega querendo estudar: comece pelas aulas, aprofunde com ensaios, resenhas e a biblioteca comentada, e explore os temas pelo mapa.</p></header>'
            + (f'<section><h2>Estudar Biologia no Ensino Médio</h2><ul class="atalhos">{atalhos}</ul></section>' if atalhos else "")
            + f'<section><h2>Por onde explorar</h2><div class="grade">{grade}</div></section>'
            f'<section><h2>Fórum de dúvidas e discussões</h2>{forum}</section></div>')


def pagina_busca():
    return ('<div class="pagina"><header class="topo-pagina"><p class="rotulo">Busca</p><h1>Buscar no site</h1></header>'
            '<form class="busca-grande" role="search" action="busca.html" method="get"><label for="q-busca">Termos de busca</label>'
            '<input id="q-busca" name="q" type="search" autocomplete="off"><button type="submit" class="botao">Buscar</button></form>'
            '<p class="status" role="status" data-busca-status></p><ul class="resultados" data-busca-resultados></ul>'
            '<noscript><p>A busca precisa de JavaScript. Use o menu para navegar pelas seções.</p></noscript></div>')


def pagina_index(dados, itens, por_tipo, estados, frases):
    P, A, E, R, L = (por_tipo[k] for k in ("projeto", "aula", "escrito", "resenha", "livro"))
    areas_com = len({t for i in itens for t in i["meta"].get("tags", [])} & {a["id"] for a in dados["areas"]})
    def contagem(n, um, varios, vazio="Em construção"): return plural(n, um, varios) if n else vazio
    atalhos = [("estudos.html", "Estudar", "Central de estudos e fórum"), ("projetos.html", "Projetos", contagem(len(P), "projeto", "projetos")),
               ("aulas.html", "Aulas e educação", contagem(len(A), "página", "páginas")), ("escritos.html", "Escritos", contagem(len(E), "texto", "textos", "Em migração")),
               ("resenhas.html", "Resenhas", contagem(len(R), "resenha", "resenhas")), ("biblioteca.html", "Biblioteca", contagem(len(L), "livro", "livros")),
               ("mapa.html", "Mapa de interesses", contagem(areas_com, "área com conteúdo", "áreas com conteúdo"))]
    grade = "".join(f'<li><a class="atalho" href="{h}"><strong>{t}</strong><span>{d}</span></a></li>' for h, t, d in atalhos)
    corpo = ('<section class="heroi"><p class="rotulo">Noosfera · arquivo vivo de investigação e criação</p><h1>Perguntar. Investigar. Construir. Partilhar.</h1>'
             '<p class="lead">Um espaço para registrar o que estudo, ensino e crio entre ciência, tecnologia, filosofia e arte, mostrando em que etapa está cada trabalho.</p>'
             '<p class="acoes"><a class="botao" href="estudos.html">Quero estudar</a> <a class="botao secundario" href="projetos.html">Ver projetos</a></p></section>')
    corpo += f'<section class="bloco"><h2 class="sr">Seções do site</h2><ul class="atalhos-grade">{grade}</ul></section>'
    dest = [i for i in P if i["meta"].get("destaque") == "sim"] or P[:3]
    if dest:
        corpo += '<section class="bloco"><div class="bloco-cab"><h2>Projetos em destaque</h2><a href="projetos.html">Todos os projetos</a></div><div class="grade">' + "".join(cartao(i, estados) for i in dest) + "</div></section>"
    plano = [i for i in A if i["meta"].get("recurso") == "plano"]
    if plano:
        corpo += ('<section class="bloco"><div class="bloco-cab"><h2>Aulas e educação</h2><a href="aulas.html">Todos os materiais</a></div><div class="grade">' + "".join(cartao(i, estados) for i in plano[:1])
                  + f'<article class="cartao"><p class="meta">Do 1º ao 3º ano</p><h3><a href="aulas.html">Materiais por ano e unidade</a></h3><p>{plural(len(A), "página", "páginas")} entre aulas, atividades, guias e avaliações de Biologia.</p></article></div></section>')
    for titulo, lista, destino in (("Escritos recentes", [i for i in E if i["meta"]["categoria"] != "noticia"], "escritos.html"),
                                   ("Notícias comentadas", [i for i in E if i["meta"]["categoria"] == "noticia"], "escritos.html"), ("Resenhas recentes", R, "resenhas.html")):
        if lista: corpo += f'<section class="bloco"><div class="bloco-cab"><h2>{titulo}</h2><a href="{destino}">Ver todos</a></div><div class="grade">' + "".join(cartao(i, estados) for i in lista[:3]) + "</div></section>"
    if frases: corpo += '<section class="bloco frase" data-frase aria-labelledby="fr-t"><h2 id="fr-t">Frase do dia</h2><blockquote><p data-frase-texto></p><footer data-frase-fonte></footer></blockquote></section>'
    datas = [i["meta"].get(c) for i in itens for c in ("atualizado", "data") if i["meta"].get(c)]
    if datas: corpo += f'<p class="meta atualizado">Última atualização de conteúdo: {fmt_data(max(datas))}.</p>'
    return corpo


# ===================== construção =====================
def construir(escrever=True):
    e = Erros()
    try: dados = json.loads((RAIZ / "dados.json").read_text(encoding="utf-8"))
    except FileNotFoundError: return ["dados.json: arquivo não encontrado"], None
    except json.JSONDecodeError as x: return [f"dados.json: JSON inválido (linha {x.lineno}, coluna {x.colno}): {x.msg}"], None
    e.extend(validar_dados(dados))
    if e: return list(e), None
    estados = {s["id"]: s for s in dados["estados"]}
    itens = carregar(e, set(estados))
    chaves = verificar_referencias(itens, e)
    frases = carregar_frases(e)
    if e: return list(e), None
    for i in itens:
        i["html"], i["heads"] = markdown(i["corpo"], Ctx(i["rel"], "../", chaves, e))
        i["resumo"] = i["meta"].get("resumo") or resumo_de(i["html"]) or i["titulo"]
        i["plain"] = texto_puro(i["html"])
    if e: return list(e), None

    def ordena(t):
        L = [i for i in itens if i["tipo"] == t]
        if t == "aula": return sorted(L, key=lambda i: (ORDEM_ANO.index(i["meta"].get("ano")) if i["meta"].get("ano") in ORDEM_ANO else 99, int(i["meta"].get("ordem", 999)), i["titulo"]))
        if t in ("escrito", "resenha"): return sorted(L, key=lambda i: (i["meta"]["data"], i["titulo"]), reverse=True)
        return sorted(L, key=lambda i: i["titulo"])
    por_tipo = {t: ordena(t) for t in TIPOS}
    por_chave = {i["chave"]: i for i in itens}
    ativo = {"aula": "aulas", "projeto": "projetos", "escrito": "escritos", "resenha": "resenhas", "livro": "biblioteca"}
    S = {}
    for i in itens:
        rel_html = secao_relacionados(i, por_chave, itens)
        S[i["url"]] = layout(i["titulo"], i["resumo"], pagina_item(i, i["html"], i["heads"], estados, rel_html), "../", i["url"], ativo[i["tipo"]])

    def valores(t, campo, rot=None):
        v = {i["meta"].get(campo) for i in por_tipo[t] if i["meta"].get(campo)}
        return sorted(v, key=lambda x: ORDEM_ANO.index(x) if x in ORDEM_ANO else x)
    est_rot = {k: v["rotulo"] for k, v in estados.items()}
    listas = {
        "projetos": dict(rotulo="Projetos", titulo="Investigações, experimentos e criações", tipo="projeto", ativo="projetos", agrupar=None,
                         intro="Cada projeto mostra em que etapa está. Ideia, planejamento e realização são coisas diferentes, e o site não as confunde.",
                         vazio="<p>Nenhum projeto publicado ainda.</p>",
                         filtros=[("estado", "Estado", valores("projeto", "estado"), est_rot),
                                  ("area", "Área", sorted({i["meta"]["area"].split("·")[0].strip() for i in por_tipo["projeto"]}), {})]),
        "aulas": dict(rotulo="Aulas e educação", titulo="Planos, atividades e materiais", tipo="aula", ativo="aulas", agrupar="ano",
                      intro="Material de ensino de Biologia (e além), organizado por ano, unidade e tipo de recurso. Tudo aqui é material planejado, em rascunho, até que se registre a aplicação em sala.",
                      vazio="<p>Nenhum material publicado ainda.</p>",
                      filtros=[("ano", "Ano", valores("aula", "ano"), {}), ("recurso", "Tipo de recurso", valores("aula", "recurso"), ROTULOS["recurso"]), ("estado", "Estado", valores("aula", "estado"), est_rot)]),
        "escritos": dict(rotulo="Escritos", titulo="Ensaios, notícias comentadas e relatos", tipo="escrito", ativo="escritos", agrupar=None,
                         intro="A produção textual autoral: ensaios, notícias comentadas, relatos de experiências, reflexões e outros textos.",
                         vazio="<p>Os textos que hoje estão nos blogs vão ser trazidos para cá, com datas, imagens e autoria preservadas. A migração está aguardando a exportação dos blogs.</p>",
                         filtros=[("categoria", "Categoria", valores("escrito", "categoria"), ROTULOS["categoria"])]),
        "resenhas": dict(rotulo="Resenhas", titulo="Livros, filmes e séries", tipo="resenha", ativo="resenhas", agrupar=None,
                         intro="Análises críticas, com atenção à interpretação filosófica, científica, social e estética, e à linguagem cinematográfica.",
                         vazio="<p>As resenhas ainda estão sendo preparadas. Quando houver, aparecem aqui com aviso de spoilers quando necessário.</p>",
                         filtros=[("tipo", "Tipo de obra", valores("resenha", "tipo"), ROTULOS["tipo"])]),
        "biblioteca": dict(rotulo="Biblioteca", titulo="Leituras, fichamentos e anotações", tipo="livro", ativo="biblioteca", agrupar=None,
                           intro="Mais que uma lista de livros: o registro da leitura, com resumo, anotações, citações com página e edição, perguntas e conceitos.",
                           vazio="<p>A biblioteca comentada ainda está sendo montada. Cada livro terá ficha, estado de leitura, anotações e passagens marcadas, sem nada inventado.</p>",
                           filtros=[("leitura", "Estado de leitura", valores("livro", "leitura"), ROTULOS["leitura"])]),
    }
    for nome, cfg in listas.items():
        cfg = dict(cfg, caminho=f"{nome}.html")
        S[f"{nome}.html"] = layout(cfg["rotulo"], re.sub(r"<[^>]+>", "", cfg["intro"]), pagina_lista(cfg, por_tipo[cfg["tipo"]], estados), "", f"{nome}.html", cfg["ativo"], dados_js=False)
    S["index.html"] = layout(NOME, "Arquivo vivo de investigação, ensino e criação: projetos, aulas, ensaios, resenhas e leituras entre ciência, tecnologia, filosofia e arte.", pagina_index(dados, itens, por_tipo, estados, frases), "", "index.html", "inicio", dados_js=bool(frases))
    S["mapa.html"] = layout("Mapa de interesses", "Áreas de interesse ligadas aos conteúdos reais do site.", pagina_mapa(dados, itens), "", "mapa.html", "mapa")
    S["estudos.html"] = layout("Estudos e fórum", "Central de estudos: aulas, ensaios, resenhas, biblioteca e fórum de discussões.", pagina_estudos(dados, por_tipo), "", "estudos.html", "estudos")
    S["busca.html"] = layout("Busca", "Buscar no site.", pagina_busca(), "", "busca.html", "", dados_js=True, indexar=False)
    S["404.html"] = layout("Página não encontrada", "Página não encontrada.", '<div class="pagina"><h1>Página não encontrada</h1><p class="lead">O endereço não existe ou mudou de lugar. Volte ao <a href="/index.html">início</a> ou use a <a href="/busca.html">busca</a>.</p></div>', "/", "404.html", indexar=False)
    S["favicon.svg"] = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32" rx="6" fill="#1f4d41"/><g fill="none" stroke="#f6f4ee"><circle cx="16" cy="16" r="8" stroke-width="2"/><ellipse cx="16" cy="16" rx="14" ry="5" transform="rotate(-25 16 16)"/></g><circle cx="27" cy="10" r="2" fill="#f6f4ee"/></svg>\n'
    indice = [{"u": i["url"], "t": i["titulo"], "k": {"aula": "Aula", "projeto": "Projeto", "escrito": ROTULOS["categoria"].get(i["meta"].get("categoria"), "Escrito"),
               "resenha": "Resenha", "livro": "Biblioteca"}[i["tipo"]], "r": i["resumo"], "g": i["meta"].get("tags", []), "x": i["plain"][:2500]} for i in itens]
    S["indice.js"] = "/* GERADO por build.py. Não edite à mão. */\nwindow.NOOSFERA = " + json.dumps({"indice": indice, "frases": frases, "forum": dados.get("forum")}, ensure_ascii=False, separators=(",", ":")) + ";\n"
    urls = sorted(u for u in S if u.endswith(".html") and u not in ("404.html", "busca.html"))
    S["sitemap.xml"] = ('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                        + "".join(f"  <url><loc>{esc(SITE_URL + ('' if u == 'index.html' else u))}</loc></url>\n" for u in urls) + "</urlset>\n")
    S["robots.txt"] = f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}sitemap.xml\n"
    if e: return list(e), None
    if escrever:
        for nome, conteudo in S.items():
            alvo = RAIZ / nome; alvo.parent.mkdir(exist_ok=True); alvo.write_text(conteudo, encoding="utf-8")
    return [], S


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
