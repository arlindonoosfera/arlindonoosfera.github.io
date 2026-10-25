#!/usr/bin/env python3
"""Importa uma exportação do Notion ("Markdown & CSV", com subpáginas) para conteudo/aulas/.

    python3 tools/importar_notion.py caminho/Export.zip [--sobrescrever]

- Converte cada página em conteudo/aulas/<slug>.md com cabeçalho validado pelo build.py.
- Reescreve links entre páginas importadas; links do Notion para páginas não importadas viram texto.
- Remove links de acesso privado (Google Sala de Aula, Character.ai), URLs desses serviços e códigos de turma ("código: xxxx").
- Só inclui imagens dos caminhos em IMAGENS_PROPRIAS; as demais são omitidas com um aviso visível.
- Otimiza imagens (WebP, até 1280 px) se a biblioteca Pillow estiver instalada; senão copia o original.
- Copia PDFs para downloads/aulas/ e os liga à página.
Nunca apaga arquivos; sem --sobrescrever, não altera páginas já existentes.
"""
import pathlib, re, shutil, sys, tempfile, unicodedata, zipfile
from urllib.parse import unquote

RAIZ = pathlib.Path(__file__).resolve().parent.parent
HEX = re.compile(r"[0-9a-f]{32}")
IMAGENS_PROPRIAS = ("RPG Educacional",)          # imagens de terceiros ou de autoria incerta ficam de fora
BLOQUEADOS = ("classroom.google", "character.ai")  # acessos privados
# (trecho do título, ano, unidade, tipo, tags). Quando a posição no plano não é clara: ano "A organizar".
META = [
 ("AVALIAÇÃO GERAL", "Todos os anos", "", "avaliacao", ""),
 ("Teoria Endossimbiótica", "1º ano", "Unidade 4 · Biologia Celular", "aula", "biologia-celular, evolucao"),
 ("Extinções em massa", "1º ano", "Unidade 2 · História da Vida na Terra", "aula", "evolucao"),
 ("Método científico", "1º ano", "Unidade 3 · Natureza da Ciência", "material", "filosofia-da-ciencia, educacao-em-ciencias"),
 ("Desafio opcional", "1º ano", "Unidade 3 · Natureza da Ciência", "atividade", "educacao-em-ciencias"),
 ("Metabolismo energético", "1º ano", "Unidade 4 · Biologia Celular", "atividade", "biologia-celular"),
 ("VIDA (BIO)", "1º ano", "", "atividade", "evolucao"),
 ("Genética Familiar", "2º ano", "Unidade 1 · Genética", "atividade", ""),
 ("Botânica", "2º ano", "Unidade 2 · Botânica", "aula", "botanica"),
 ("Polinizadores", "2º ano", "Unidade 2 · Botânica", "aula", "botanica, ecologia"),
 ("Apple Hunter", "2º ano", "Unidade 2 · Botânica", "aula", "botanica"),
 ("Analisar plantas", "2º ano", "Unidade 2 · Botânica", "atividade", "botanica"),
 ("Histologia", "2º ano", "Unidade 4 · Fisiologia Humana e Saúde", "aula", ""),
 ("Proibida a entrada", "3º ano", "Unidade 1 · Ecologia", "aula", "ecologia"),
 ("Conhecendo, investigando", "3º ano", "Unidade 1 · Ecologia", "atividade", "ecologia, biodiversidade"),
 ("CAATINGA", "3º ano", "Unidade 1 · Ecologia", "aula", "ecologia, caatinga"),
 ("Ciência Nazista", "3º ano", "Unidade 3 · Biotecnologia e Ciência Aplicada", "aula", "filosofia-da-ciencia"),
 ("Neurobiologia", "3º ano", "Unidade 3 · Biotecnologia e Ciência Aplicada", "aula", "neurobiologia"),
 ("Neurotecnologia", "3º ano", "Unidade 3 · Biotecnologia e Ciência Aplicada", "aula", "neurobiologia, tecnologia-educacional"),
 ("CSI", "3º ano", "Unidade 3 · Biotecnologia e Ciência Aplicada", "atividade", ""),
 ("VESTIBULARES", "3º ano", "Unidade 4 · Revisão ENEM", "guia", ""),
 ("Ferramentas", "Todos os anos", "", "material", "tecnologia-educacional"),
 ("RPG Educacional", "Extensão", "", "material", "educacao-em-ciencias, construcao-de-mundos"),
 ("Região", "Extensão", "RPG Educacional", "material", "construcao-de-mundos"),
 ("Lúmen", "Extensão", "RPG Educacional", "material", "construcao-de-mundos"),
 ("Plano de Ensino de Biologia", "Visão geral", "", "plano", "educacao-em-ciencias"),
]


def sem_acento_slug(t):
    t = unicodedata.normalize("NFD", t).encode("ascii", "ignore").decode().lower()
    t = re.sub(r"[^a-z0-9]+", "-", t).strip("-")
    return t if len(t) <= 60 else t[:60].rsplit("-", 1)[0]


def limpa_nome(stem):
    return re.sub(r"\s[0-9a-f]{32}$", "", stem).strip()


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    sobrescrever = "--sobrescrever" in sys.argv
    if not args: sys.exit(__doc__)
    tmp = pathlib.Path(tempfile.mkdtemp())
    with zipfile.ZipFile(args[0]) as z: z.extractall(tmp)
    mds = sorted(p for p in tmp.rglob("*.md") if p.stat().st_size > 60)
    pulados = [p.name for p in tmp.rglob("*.md") if p.stat().st_size <= 60]
    # 1) slug e título de cada página
    info, slugs = {}, set()
    for p in mds:
        txt = p.read_text(encoding="utf-8")
        h = re.search(r"^#\s+(.*)", txt, re.M)
        titulo = (h.group(1).strip() if h else limpa_nome(p.stem)).replace("**", "")
        slug, n = sem_acento_slug(titulo), 2
        base = slug
        while slug in slugs: slug, n = f"{base}-{n}", n + 1
        slugs.add(slug)
        m = HEX.search(p.name)
        info[p] = {"slug": slug, "titulo": titulo, "id": m.group(0) if m else None}
    por_id = {i["id"]: i["slug"] for i in info.values() if i["id"]}
    pend = []
    for p in mds:
        i = info[p]
        txt = p.read_text(encoding="utf-8")
        txt = re.sub(r"^#\s+.*\n+", "", txt, count=1, flags=re.M)
        omitidas = []

        def imagem(m):
            alt, src = m.group(1), unquote(m.group(2))
            if src.startswith("http"): return "*Imagem externa omitida (direitos de uso a confirmar).*"
            origem = (p.parent / src)
            if not any(k in str(origem) for k in IMAGENS_PROPRIAS) or not origem.exists():
                omitidas.append(origem.name)
                return "*Imagem omitida até a confirmação dos direitos de uso.*"
            n = len(list((RAIZ / "img" / "aulas" / i["slug"]).glob("*"))) + 1 if (RAIZ / "img" / "aulas" / i["slug"]).exists() else 1
            destino_dir = RAIZ / "img" / "aulas" / i["slug"]; destino_dir.mkdir(parents=True, exist_ok=True)
            try:
                from PIL import Image
                im = Image.open(origem); im.thumbnail((1280, 1280)); destino = destino_dir / f"{n:02d}.webp"
                im.convert("RGB").save(destino, "WEBP", quality=80)
            except ImportError:
                destino = destino_dir / f"{n:02d}{origem.suffix.lower()}"; shutil.copy(origem, destino)
            rel = destino.relative_to(RAIZ).as_posix()
            return f'![Ilustração do cenário do RPG educacional, imagem {n}]({rel} "Ilustração do RPG. Autoria e ferramenta de criação a confirmar.")'
        txt = re.sub(r"!\[(.*?)\]\(([^\n]*?\.(?:jpe?g|png|webp|gif))\)", imagem, txt, flags=re.I)

        def link_md(m):
            rotulo, alvo = m.group(1), m.group(3)
            return f"[{rotulo}](aulas/{por_id[alvo]})" if alvo in por_id else rotulo
        txt = re.sub(r"(?<!!)\[((?:(?!\]\().)*?)\]\(((?:(?!\]\()[^\n])*?([0-9a-f]{32})\.md)\)", link_md, txt, flags=re.S)

        def link(m):
            rotulo, href = m.group(1), unquote(m.group(2))
            if any(b in href for b in BLOQUEADOS):
                return "" if re.match(r"^\s*(https?://|www\.)", rotulo) else rotulo
            alvo = HEX.search(href.replace("-", ""))
            if "notion" in href and alvo and alvo.group(0) in por_id:
                return f"[{rotulo}](aulas/{por_id[alvo.group(0)]})"
            if "notion" in href or not href.startswith(("http://", "https://", "#")):
                return rotulo                       # página privada ou não importada: só o texto
            return m.group(0)
        txt = re.sub(r"(?<!!)\[((?:(?!\]\().)*?)\]\(((?:[^()\n]|\([^()\n]*\))*)\)", link, txt)
        txt = re.sub(r"https?://(?:www\.)?(?:classroom\.google|character\.ai)\S*", "", txt)
        txt = re.sub(r"\s*[-–—:]?\s*c[óo]digo(?: da turma)?\s*:\s*[A-Za-z0-9]{5,12}\b", "", txt, flags=re.I)  # código de entrada de turma
        txt = re.sub(r"\n{3,}", "\n\n", txt).strip() + "\n"
        if not re.sub(r"\*Imagem[^*]*\*", "", txt).strip():
            print(f"  ignorada (só continha imagem omitida): {i['titulo']}"); continue
        meta = next((x for x in META if x[0].lower() in i["titulo"].lower()), None)
        ano, unidade, tipo, tags = (meta[1:] if meta else ("A organizar", "", "material", ""))
        nivel = "Extensão" if ano == "Extensão" else "Ensino Médio"
        cab = ["---", f"titulo: {i['titulo']}", "estado: planejamento", f"ano: {ano}"]
        if unidade: cab.append(f"unidade: {unidade}")
        cab += [f"recurso: {tipo}", "disciplina: Biologia", f"nivel: {nivel}"]
        if tags: cab.append(f"tags: {tags}")
        pasta_pdf = p.parent / limpa_nome(p.stem)
        for pdf in sorted(pasta_pdf.glob("*.pdf")) if pasta_pdf.is_dir() else []:
            (RAIZ / "downloads" / "aulas").mkdir(parents=True, exist_ok=True)
            nome = sem_acento_slug(pdf.stem) + ".pdf"; shutil.copy(pdf, RAIZ / "downloads" / "aulas" / nome)
            cab.append(f"arquivo: downloads/aulas/{nome} | Apresentação em PDF")
        cab.append("---")
        pend.append((i["slug"], cab, txt, ano, tipo, len(omitidas)))
    escritas = {x[0] for x in pend}
    for slug, cab, txt, ano, tipo, n_omit in pend:
        txt = re.sub(r"\[([^\]]*)\]\(aulas/([a-z0-9-]+)\)", lambda m: m.group(0) if m.group(2) in escritas else m.group(1), txt)
        saida = RAIZ / "conteudo" / "aulas" / f"{slug}.md"
        if saida.exists() and not sobrescrever:
            print(f"  já existe, mantido: {saida.name}"); continue
        saida.parent.mkdir(parents=True, exist_ok=True)
        saida.write_text("\n".join(cab) + "\n\n" + txt, encoding="utf-8")
        print(f"  {saida.name:62} {ano} | {tipo}" + (f"  [imagens omitidas: {n_omit}]" if n_omit else ""))
    print(f"\n{len(mds)} páginas processadas; {len(pulados)} vazias ignoradas: {pulados}")


if __name__ == "__main__":
    main()
