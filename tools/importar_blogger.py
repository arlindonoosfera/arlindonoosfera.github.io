#!/usr/bin/env python3
"""Converte o backup XML do Blogger em RASCUNHOS de Markdown para revisão.

    python3 tools/importar_blogger.py backup-blog.xml [--saida conteudo/_rascunhos_blogger]

Como obter o XML: Blogger → Configurações → Gerenciar blog → Fazer backup do conteúdo.
- Gera um .md por postagem/página (comentários são ignorados) e um relatorio.txt.
- Os rascunhos ficam em pasta iniciada por "_" e NÃO entram no site: revise, escolha a categoria
  (ensaio, noticia, relato, reflexao, texto) ou o tipo (resenha, aula, projeto), complete os campos
  e mova para conteudo/<tipo>/.
- Mantém data original, título e categorias do Blogger (como tags quando válidas).
- Imagens continuam apontando para o endereço do Blogger: baixe-as para img/ e ajuste os links
  (o build recusa imagens que não existam no projeto). Postagens "DRAFT" são marcadas no relatório.
Nunca apaga nem sobrescreve arquivos existentes."""
import html, pathlib, re, sys, unicodedata
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

ATOM = "{http://www.w3.org/2005/Atom}"
BLOG = "{http://schemas.google.com/blogger/2018}"


class ParaMd(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True); self.o, self.listas, self.link, self.imgs, self.links = [], [], None, [], []
    def w(self, t): self.o.append(t)
    def handle_starttag(self, tag, a):
        a = dict(a)
        if tag in ("p", "div", "blockquote", "br"): self.w("\n" if tag == "br" else "\n\n" + ("> " if tag == "blockquote" else ""))
        elif re.fullmatch(r"h[1-6]", tag): self.w("\n\n## ")
        elif tag in ("strong", "b"): self.w("**")
        elif tag in ("em", "i"): self.w("*")
        elif tag in ("ul", "ol"): self.listas.append(tag); self.w("\n")
        elif tag == "li": self.w("\n" + "  " * (len(self.listas) - 1) + ("1. " if self.listas and self.listas[-1] == "ol" else "- "))
        elif tag == "a" and a.get("href", "").startswith(("http://", "https://")): self.link = a["href"]; self.w("["); self.links.append(a["href"])
        elif tag == "img" and a.get("src"): self.imgs.append(a["src"]); self.w(f"\n\n![{(a.get('alt') or '').strip()}]({a['src']})\n\n")
    def handle_endtag(self, tag):
        if tag in ("strong", "b"): self.w("**")
        elif tag in ("em", "i"): self.w("*")
        elif tag in ("ul", "ol") and self.listas: self.listas.pop(); self.w("\n")
        elif tag == "a" and self.link: self.w(f"]({self.link})"); self.link = None
        elif tag in ("p", "div", "blockquote") or re.fullmatch(r"h[1-6]", tag): self.w("\n")
    def handle_data(self, d): self.w(re.sub(r"\s+", " ", d) if not d.isspace() or self.o else "")


def converter(xml_texto):
    raiz = ET.fromstring(xml_texto); itens = []
    for e in raiz.iter(ATOM + "entry"):
        tipo = (e.findtext(BLOG + "type") or "POST").upper()
        if tipo not in ("POST", "PAGE"): continue
        titulo = (e.findtext(ATOM + "title") or "").strip() or "Sem título"
        pub = (e.findtext(ATOM + "published") or "")[:10]
        conteudo = e.findtext(ATOM + "content") or ""
        p = ParaMd(); p.feed(conteudo); corpo = re.sub(r"\n{3,}", "\n\n", "".join(p.o)).strip()
        tags = []
        for c in e.findall(ATOM + "category"):
            t = re.sub(r"[^a-z0-9]+", "-", unicodedata.normalize("NFD", c.get("term", "")).encode("ascii", "ignore").decode().lower()).strip("-")
            if t and t not in tags and not t.startswith("http"): tags.append(t)
        itens.append({"titulo": titulo, "data": pub, "corpo": corpo, "tags": tags, "imagens": p.imgs, "links": p.links,
                      "status": (e.findtext(BLOG + "status") or "LIVE").upper(), "tipo": tipo,
                      "url": next((l.get("href") for l in e.findall(ATOM + "link") if l.get("rel") == "alternate"), "")})
    return itens


def slug(t):
    t = unicodedata.normalize("NFD", t).encode("ascii", "ignore").decode().lower()
    t = re.sub(r"[^a-z0-9]+", "-", t).strip("-")
    return t if len(t) <= 60 else t[:60].rsplit("-", 1)[0]


def escrever(itens, destino):
    destino.mkdir(parents=True, exist_ok=True); rel = []
    for it in itens:
        nome = f"{it['data'] or 'sem-data'}-{slug(it['titulo'])}.md"; alvo = destino / nome
        if alvo.exists(): rel.append(f"MANTIDO (já existia): {nome}"); continue
        resumo = re.sub(r"\s+", " ", re.sub(r"[#>*\[\]!()]|https?://\S+", " ", it["corpo"])).strip()[:150]
        cab = ["---", f"titulo: {it['titulo']}", "categoria: texto"] + ([f"data: {it['data']}"] if it["data"] else []) + [f"resumo: {resumo}"]
        if it["tags"]: cab.append("tags: " + ", ".join(it["tags"]))
        alvo.write_text("\n".join(cab) + "\n---\n\n" + it["corpo"] + "\n", encoding="utf-8")
        rel.append(f"{nome} | {it['tipo']} | {it['status']} | imagens: {len(it['imagens'])} | links externos: {len(it['links'])} | original: {it['url']}")
    (destino / "relatorio.txt").write_text(f"{len(itens)} postagens/páginas lidas.\n" + "\n".join(rel) + "\n", encoding="utf-8")
    return rel


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    if not a: sys.exit(__doc__)
    saida = pathlib.Path(sys.argv[sys.argv.index("--saida") + 1]) if "--saida" in sys.argv else pathlib.Path(__file__).resolve().parent.parent / "conteudo" / "_rascunhos_blogger"
    r = escrever(converter(pathlib.Path(a[0]).read_text(encoding="utf-8")), saida)
    print(f"{len(r)} rascunhos em {saida}. Leia relatorio.txt.")
