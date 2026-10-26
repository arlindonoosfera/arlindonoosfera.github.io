"""Execute: python3 -m unittest discover -s tests -v
Os testes de recursos ainda sem conteúdo real (notícias, resenhas, livros, frases, fórum)
usam um projeto de exemplo isolado em pasta temporária; nada disso vai para o site."""
import json, pathlib, re, shutil, sys, tempfile, unittest
REAL = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REAL))
import build

PNG = bytes.fromhex("89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000d49444154789c6360000002000001e221bc330000000049454e44ae426082")
COM = {"escritos/ensaio-um.md": "---\ntitulo: Ensaio um\ncategoria: ensaio\ndata: 2026-05-10\nresumo: Resumo do ensaio.\ntags: ecologia\nrelacionados: projetos/proj\nsubtitulo: Um subtítulo\n---\n# Ensaio um\n\n## Parte A\n\ntexto\n\n## Parte B\n\n- a\n    - b\n\n## Parte C\n\n![Alt da imagem](img/x.png \"Legenda real\")\n",
       "escritos/noticia-um.md": "---\ntitulo: Notícia um\ncategoria: noticia\ndata: 2026-06-01\nresumo: Contexto.\nfonte_titulo: Título original\nfonte_url: https://exemplo.org/materia\nfonte_data: 2026-05-30\n---\nMeu comentário crítico.\n",
       "resenhas/filme-um.md": "---\ntitulo: Filme um\ntipo: filme\nautoria: Fulana\nano: 2020\ndata: 2026-07-01\nresumo: Análise.\nspoilers: sim\nnota: 4\n---\nTexto.\n",
       "biblioteca/livro-um.md": "---\ntitulo: Livro um\nautor: Beltrano\nleitura: lendo\nresenha: filme-um\nano: 1999\n---\n## Citações\n\n> Trecho literal.\n> — p. 12, 3ª ed.\n",
       "projetos/proj.md": "---\ntitulo: Proj\nestado: ideia\narea: Natureza · Teste\nresumo: Resumo.\ntags: ecologia\ndestaque: sim\n---\ncorpo\n",
       "aulas/aula-um.md": "---\ntitulo: Aula um\nano: 1º ano\nrecurso: aula\ntags: ecologia\n---\nTexto da aula com [outra](aulas/aula-um) e [proj](projetos/proj).\n"}


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp()); self.old = build.RAIZ; build.RAIZ = self.tmp
        shutil.copy(REAL / "dados.json", self.tmp / "dados.json")
        (self.tmp / "img").mkdir(); (self.tmp / "img" / "x.png").write_bytes(PNG)
        for rel, txt in COM.items():
            p = self.tmp / "conteudo" / rel; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(txt, encoding="utf-8")
    def tearDown(self): build.RAIZ = self.old; shutil.rmtree(self.tmp, ignore_errors=True)
    def escreve(self, rel, txt):
        p = self.tmp / "conteudo" / rel; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(txt, encoding="utf-8")
    def ok(self):
        e, s = build.construir(escrever=False); self.assertEqual(e, []); return s


class Recursos(Base):
    def test_constroi_tudo(self): self.assertIn("escritos/ensaio-um.html", self.ok())
    def test_ensaio_tem_sumario_data_imagem_legenda(self):
        h = self.ok()["escritos/ensaio-um.html"]
        self.assertIn("Neste texto", h); self.assertIn('<time datetime="2026-05-10">', h); self.assertIn("<figcaption>Legenda real</figcaption>", h); self.assertIn('alt="Alt da imagem"', h)
        self.assertIn("<ul><li>a", h.replace("\n", "")); self.assertIn("<ul><li>b", h.replace("\n", ""))
    def test_noticia_separa_fonte_e_comentario(self):
        h = self.ok()["escritos/noticia-um.html"]
        self.assertIn("Notícia original", h); self.assertIn('href="https://exemplo.org/materia" rel="noopener noreferrer"', h); self.assertIn("<h2>Comentário</h2>", h)
    def test_resenha_spoiler_e_nota(self):
        h = self.ok()["resenhas/filme-um.html"]; self.assertIn("contém spoilers", h); self.assertIn("nota 4/5", h)
    def test_livro_liga_resenha_e_citacao(self):
        h = self.ok()["biblioteca/livro-um.html"]; self.assertIn("resenhas/filme-um.html", h); self.assertIn("<blockquote>", h); self.assertIn("p. 12", h)
    def test_relacionados_por_tag_e_explicitos(self):
        s = self.ok(); self.assertIn("projetos/proj.html", s["escritos/ensaio-um.html"]); self.assertIn("aulas/aula-um.html", s["projetos/proj.html"])
    def test_home_mostra_apenas_o_que_existe(self):
        h = self.ok()["index.html"]; self.assertIn("Notícias comentadas", h); self.assertIn("Resenhas recentes", h); self.assertNotIn("Frase do dia", h)
    def test_frase_do_dia_so_com_fonte(self):
        self.escreve("frases.json", json.dumps([{"texto": "x", "autor": "Y", "fonte": "Livro Z", "ano": "2000"}]))
        self.assertIn("Frase do dia", self.ok()["index.html"])
        self.escreve("frases.json", json.dumps([{"texto": "x", "autor": "Y"}]))
        e, s = build.construir(escrever=False); self.assertIsNone(s); self.assertTrue(any("fonte" in x for x in e))
    def test_forum_desativado_e_ativado(self):
        self.assertIn("ainda não foi aberto", self.ok()["estudos.html"])
        d = json.loads((self.tmp / "dados.json").read_text()); d["forum"] = {"repo": "u/r", "repo_id": "R_1", "categoria": "Geral", "categoria_id": "DIC_1"}
        (self.tmp / "dados.json").write_text(json.dumps(d))
        h = self.ok()["estudos.html"]; self.assertIn('data-repo="u/r"', h); self.assertIn("Carregar discussão", h); self.assertNotIn("<script src=\"https://giscus", h)  # o script de terceiros só é carregado pelo JS, após o clique
    def test_mapa_liga_so_o_que_existe(self):
        h = self.ok()["mapa.html"]; self.assertIn("Ecologia: 3 conteúdos", h); self.assertIn("Interesse em desenvolvimento", h)
    def test_indice_de_busca(self):
        js = self.ok()["indice.js"]; self.assertIn("Ensaio um", js); self.assertIn("Notícia comentada", js)


class Erros(Base):
    def falha(self, rel, txt, trecho):
        self.escreve(rel, txt); e, s = build.construir(escrever=False)
        self.assertIsNone(s, "não deve gerar nada"); self.assertTrue(any(trecho in x and rel.split("/")[-1] in x for x in e), e)
    def test_noticia_sem_fonte(self): self.falha("escritos/n.md", "---\ntitulo: N\ncategoria: noticia\ndata: 2026-01-01\nresumo: r\n---\nx", "fonte_url")
    def test_categoria_invalida(self): self.falha("escritos/n.md", "---\ntitulo: N\ncategoria: poema\ndata: 2026-01-01\nresumo: r\n---\nx", "categoria")
    def test_data_invalida(self): self.falha("escritos/n.md", "---\ntitulo: N\ncategoria: ensaio\ndata: 31/12/2026\nresumo: r\n---\nx", "AAAA-MM-DD")
    def test_data_inexistente(self): self.falha("escritos/n.md", "---\ntitulo: N\ncategoria: ensaio\ndata: 2026-02-30\nresumo: r\n---\nx", "inexistente")
    def test_campo_desconhecido(self): self.falha("escritos/n.md", "---\ntitulo: N\ncategoria: ensaio\ndata: 2026-01-01\nresumo: r\nfoo: 1\n---\nx", "desconhecido")
    def test_obrigatorio_ausente(self): self.falha("projetos/p2.md", "---\ntitulo: P\nestado: ideia\n---\nx", "obrigatório")
    def test_estado_desconhecido(self): self.falha("projetos/p2.md", "---\ntitulo: P\nestado: nada\narea: A\nresumo: r\n---\nx", "estado desconhecido")
    def test_leitura_invalida(self): self.falha("biblioteca/l2.md", "---\ntitulo: L\nautor: A\nleitura: talvez\n---\nx", "leitura")
    def test_nota_fora_da_faixa(self): self.falha("resenhas/r2.md", "---\ntitulo: R\ntipo: livro\nautoria: A\nano: 2000\ndata: 2026-01-01\nresumo: r\nnota: 9\n---\nx", "nota")
    def test_tag_invalida(self): self.falha("aulas/a2.md", "---\ntitulo: A\ntags: Meu Tag\n---\nx", "tag inválida")
    def test_relacionado_inexistente(self): self.falha("aulas/a2.md", "---\ntitulo: A\nrelacionados: aulas/nao-existe\n---\nx", "inexistente")
    def test_link_interno_quebrado(self): self.falha("aulas/a2.md", "---\ntitulo: A\n---\nveja [x](aulas/nao-existe)", "inexistente")
    def test_link_perigoso(self): self.falha("aulas/a2.md", "---\ntitulo: A\n---\n[x](javascript:alert(1))", "inválido")
    def test_imagem_inexistente(self): self.falha("aulas/a2.md", "---\ntitulo: A\n---\n![a](img/nao.png)", "inexistente")
    def test_cabecalho_aberto(self): self.falha("aulas/a2.md", "---\ntitulo: A\nx", "não fechado")
    def test_chave_duplicada(self): self.falha("aulas/a2.md", "---\ntitulo: A\ntitulo: B\n---\nx", "duplicada")
    def test_json_invalido(self):
        (self.tmp / "dados.json").write_text("{ruim"); e, s = build.construir(escrever=False); self.assertIsNone(s); self.assertTrue(any("JSON inválido" in x for x in e))
    def test_forum_incompleto(self):
        d = json.loads((self.tmp / "dados.json").read_text()); d["forum"] = {"repo": "u/r"}; (self.tmp / "dados.json").write_text(json.dumps(d))
        e, s = build.construir(escrever=False); self.assertTrue(any("forum" in x for x in e))
    def test_erro_nao_escreve_nada(self):
        self.escreve("aulas/a2.md", "---\ntitulo: A\nestado: nada\n---\nx"); self.assertEqual(build.main([]), 1)
        self.assertFalse((self.tmp / "index.html").exists())


class TemasPautaDatas(Base):
    def test_escrito_sem_data_aparece_depois_dos_datados(self):
        self.escreve("escritos/sem-data.md", "---\ntitulo: Sem data\ncategoria: reflexao\nresumo: r\n---\ntexto")
        s = self.ok(); self.assertIn("data original a confirmar", s["escritos/sem-data.html"])
        h = s["escritos.html"]; self.assertLess(h.index("Ensaio um"), h.index("Sem data"))
    def test_tema_derivado_e_sobreposto(self):
        s = self.ok(); self.assertIn("tema-cinema", s["resenhas/filme-um.html"]); self.assertIn("tema-ensaio", s["escritos/ensaio-um.html"]); self.assertIn("tema-livro", s["biblioteca/livro-um.html"])
        self.escreve("escritos/ensaio-um.md", COM["escritos/ensaio-um.md"].replace("subtitulo:", "tema: musica\nsubtitulo:"))
        self.assertIn("tema-musica", self.ok()["escritos/ensaio-um.html"])
    def test_tema_invalido(self):
        self.escreve("escritos/x.md", "---\ntitulo: X\ncategoria: texto\nresumo: r\ntema: neon\n---\nx")
        e, s = build.construir(escrever=False); self.assertIsNone(s); self.assertTrue(any("tema" in x and "x.md" in x for x in e))
    def test_novos_tipos_de_resenha(self):
        self.escreve("resenhas/disco.md", "---\ntitulo: Disco\ntipo: musica\nautoria: Banda\nano: 1973\nresumo: r\n---\nx")
        s = self.ok(); self.assertIn("tema-musica", s["resenhas/disco.html"]); self.assertIn("Música", s["resenhas/disco.html"])
        self.escreve("resenhas/pod.md", "---\ntitulo: Pod\ntipo: podcast\nautoria: A\nano: 2020\nresumo: r\n---\nx")
        e, s2 = build.construir(escrever=False); self.assertIsNone(s2); self.assertTrue(any("tipo" in x for x in e))
    def test_pauta_gera_pagina_busca_e_home(self):
        self.escreve("pauta.json", json.dumps({"textos": [{"titulo": "Tema X", "formato": ["resenha"], "nota": "n"}], "cadernos": [{"titulo": "Ideias", "ideias": ["a", "b"]}]}))
        s = self.ok(); self.assertIn("Tema X", s["pauta.html"]); self.assertIn("Ideias", s["pauta.html"]); self.assertIn("Na fila de escrita", s["index.html"])
        self.assertIn("pauta.html#p-tema-x", s["indice.js"]); self.assertIn("pauta.html", s["sitemap.xml"]); self.assertIn("pauta.html", s["escritos.html"])
    def test_sem_pauta_nao_ha_pagina(self): self.assertNotIn("pauta.html", self.ok())
    def test_pauta_invalida(self):
        for conteudo, trecho in (({"textos": [{"titulo": "T", "formato": ["poema"]}]}, "formato"), ({"textos": [{"formato": []}]}, "titulo"),
                                 ({"cadernos": [{"titulo": "C", "ideias": []}]}, "ideias"), ([], "objeto")):
            self.escreve("pauta.json", json.dumps(conteudo)); e, s = build.construir(escrever=False)
            self.assertIsNone(s); self.assertTrue(any("pauta.json" in x and trecho in x for x in e), (conteudo, e))


class Markdown(unittest.TestCase):
    def md(self, t):
        e = build.Erros(); h, hs = build.markdown(t, build.Ctx("x.md", "../", {"aulas/a"}, e)); return h, hs, e
    def test_xss(self):
        h, _, e = self.md("<script>alert(1)</script> <img src=x onerror=alert(1)>")
        self.assertNotIn("<script", h); self.assertNotIn("<img", h)
    def test_links(self):
        h, _, e = self.md("[ok](https://a.org) [int](aulas/a#x)")
        self.assertIn('href="https://a.org" rel="noopener noreferrer"', h); self.assertIn('href="../aulas/a.html#x"', h); self.assertEqual(e, [])
    def test_rotulo_vazio_e_negrito_solto(self):
        h, _, _ = self.md("[](https://a.org) texto**"); self.assertIn(">https://a.org</a>", h); self.assertNotIn("**", h)
    def test_titulos_ids_unicos_e_nivel_minimo_h2(self):
        h, hs, _ = self.md("### A\n\n### A\n\n#### B"); self.assertEqual([x[1] for x in hs], ["a", "a-2", "b"]); self.assertIn("<h2 id=\"a\">", h); self.assertIn("<h3 id=\"b\">", h)
    def test_tabela_e_lista_ordenada(self):
        h, _, _ = self.md("| A | B |\n| --- | --- |\n| 1 | 2 |\n\n1. um\n2. dois"); self.assertIn("<th scope='col'>A</th>", h); self.assertIn("<ol>", h)


class Real(unittest.TestCase):
    def paginas(self): return [p for p in REAL.rglob("*.html") if "tests" not in p.parts and "_conteudo" not in str(p)]
    def test_conteudo_real_valido_e_site_atualizado(self):
        e, s = build.construir(escrever=False); self.assertEqual(e, [], e)
        for nome, conteudo in s.items():
            if nome.endswith(".svg"): continue
            self.assertEqual((REAL / nome).read_text(encoding="utf-8"), conteudo, f"{nome} está desatualizado: rode python3 build.py")
    def test_estados_sem_acento(self):
        for st in json.loads((REAL / "dados.json").read_text(encoding="utf-8"))["estados"]: self.assertRegex(st["id"], build.ID_RE)
    def test_links_ancoras_e_recursos_locais(self):
        for p in self.paginas():
            h = p.read_text(encoding="utf-8"); ids = set(re.findall(r'id="([^"]+)"', h))
            for a in re.findall(r'href="#([^"]+)"', h): self.assertIn(a, ids, f"{p.name}: âncora #{a}")
            for ref in re.findall(r'(?:href|src)="([^"#:?]+?)(?:[#?][^"]*)?"', h):
                if ref.startswith(("http", "mailto", "/")): continue
                self.assertTrue((p.parent / ref).exists(), f"{p.relative_to(REAL)}: recurso ausente {ref}")
    def test_estrutura_acessivel_de_cada_pagina(self):
        for p in self.paginas():
            h = p.read_text(encoding="utf-8"); n = p.name
            self.assertIn('lang="pt-BR"', h); self.assertRegex(h, r"<title>[^<]+</title>"); self.assertIn('name="description"', h)
            self.assertEqual(len(re.findall(r"<h1[ >]", h)), 1, f"{n}: um h1"); self.assertIn('class="pular"', h)
            self.assertNotIn('href="#"', h); self.assertEqual(len(re.findall(r"<main[ >]", h)), 1)
            for img in re.findall(r"<img [^>]*>", h): self.assertIn("alt=", img, f"{n}: img sem alt")
            if n != "404.html": self.assertIn('rel="canonical"', h)
            niveis = [int(x) for x in re.findall(r"<h([1-6])[ >]", h)]
            for a, b in zip(niveis, niveis[1:]): self.assertLessEqual(b - a, 1, f"{n}: salto de título h{a}→h{b}")
    def test_secoes_removidas_nao_voltam(self):
        for p in self.paginas():
            nav = re.search(r'<nav id="menu".*?</nav>', p.read_text(encoding="utf-8"), re.S).group(0)
            for proibido in ("Trajetória", "Conexões", "Blogger", "Lattes", "LinkedIn", "Sala de aula"): self.assertNotIn(proibido, nav, p.name)
    def test_sem_segredos_nem_acessos_privados(self):
        for p in REAL.rglob("*"):
            if p.is_file() and p.suffix in {".html", ".js", ".json", ".md", ".py", ".xml", ".txt"} and "tests" not in p.parts and "tools" not in p.parts:
                t = p.read_text(encoding="utf-8")
                for ruim in ("bxznaujq", "character.ai/chat", "classroom.google.com/c/", "app.notion.com", "notion.so/"): self.assertNotIn(ruim, t, f"{p.relative_to(REAL)}: {ruim}")
    def test_sitemap_so_com_arquivos_existentes(self):
        for loc in re.findall(r"<loc>(.*?)</loc>", (REAL / "sitemap.xml").read_text()):
            alvo = loc.replace(build.SITE_URL, "") or "index.html"; self.assertTrue((REAL / alvo).exists(), loc)
    def test_imagens_do_site_existem_e_sao_leves(self):
        for img in (REAL / "img").rglob("*"):
            if img.is_file(): self.assertLess(img.stat().st_size, 400_000, f"{img.name} pesada")



class Blogger(unittest.TestCase):
    XML = """<?xml version='1.0' encoding='UTF-8'?><feed xmlns='http://www.w3.org/2005/Atom' xmlns:blogger='http://schemas.google.com/blogger/2018'>
<entry><blogger:type>POST</blogger:type><blogger:status>LIVE</blogger:status><published>2024-03-05T10:00:00.000-03:00</published><title>Sobre o Tempo</title>
<category term='Filosofia da Ciência'/><link rel='alternate' href='https://x.blogspot.com/2024/03/tempo.html'/>
<content type='html'>&lt;p&gt;Primeiro &lt;b&gt;parágrafo&lt;/b&gt; com &lt;a href="https://a.org"&gt;link&lt;/a&gt;.&lt;/p&gt;&lt;h2&gt;Seção&lt;/h2&gt;&lt;ul&gt;&lt;li&gt;um&lt;/li&gt;&lt;li&gt;dois&lt;/li&gt;&lt;/ul&gt;&lt;img src="https://img/x.jpg" alt="foto"/&gt;&lt;script&gt;alert(1)&lt;/script&gt;</content></entry>
<entry><blogger:type>COMMENT</blogger:type><title>comentário</title><content type='html'>oi</content></entry></feed>"""
    def test_converte_posts_e_ignora_comentarios(self):
        sys.path.insert(0, str(REAL / "tools")); import importar_blogger as ib
        it = ib.converter(self.XML); self.assertEqual(len(it), 1)
        p = it[0]; self.assertEqual((p["titulo"], p["data"], p["tags"]), ("Sobre o Tempo", "2024-03-05", ["filosofia-da-ciencia"]))
        self.assertIn("**parágrafo**", p["corpo"]); self.assertIn("[link](https://a.org)", p["corpo"]); self.assertIn("## Seção", p["corpo"]); self.assertIn("- um", p["corpo"])
        self.assertEqual(p["imagens"], ["https://img/x.jpg"])
    def test_rascunho_nao_sobrescreve_e_nao_entra_no_site(self):
        import importar_blogger as ib
        d = pathlib.Path(tempfile.mkdtemp()); it = ib.converter(self.XML)
        ib.escrever(it, d); arq = next(d.glob("2024-*.md")); arq.write_text("EDITADO"); r = ib.escrever(it, d)
        self.assertEqual(arq.read_text(), "EDITADO"); self.assertTrue(any("MANTIDO" in x for x in r)); shutil.rmtree(d)
        self.assertFalse((REAL / "conteudo" / "_rascunhos_blogger").exists() and any((REAL / "conteudo" / "escritos").glob("2024-*")))


if __name__ == "__main__": unittest.main()
