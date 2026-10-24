"""Execute: python3 -m unittest discover -s tests -v"""
import json, pathlib, re, sys, tempfile, unittest
RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
import build

class Dados(unittest.TestCase):
    def setUp(self): self.d = json.loads((RAIZ / "dados.json").read_text(encoding="utf-8"))
    def test_dados_reais_validos(self): self.assertEqual(list(build.validar_dados(self.d)), [])
    def test_estados_ids_sem_acento(self):
        for s in self.d["estados"]: self.assertRegex(s["id"], build.ID_RE)
    def test_concluido_existe_e_legenda_vem_dos_dados(self):
        self.assertIn("concluido", {s["id"] for s in self.d["estados"]})
        self.assertNotIn("concluído", (RAIZ / "index.html").read_text(encoding="utf-8").split('id="legenda"')[1][:200])
    def test_estado_desconhecido(self):
        self.d["projetos"][0]["estagio"] = "xyz"
        self.assertTrue(any("estado desconhecido" in x for x in build.validar_dados(self.d)))
    def test_link_perigoso(self):
        self.d["projetos"][0]["link"] = "javascript:alert(1)"
        self.assertTrue(any("link" in x for x in build.validar_dados(self.d)))
    def test_campos_ausentes_e_tipos(self):
        self.d["projetos"].append({"titulo": 5}); self.d["conexoes"][0]["url"] = 7
        e = build.validar_dados(self.d)
        self.assertTrue(any("projetos" in x and "titulo" in x for x in e)); self.assertTrue(any("url" in x for x in e))
    def test_lista_vazia_de_trajetoria_ok(self):
        self.assertEqual(list(build.validar_dados(self.d)), [])  # "Cursos complementares" tem itens []

class FrontMatter(unittest.TestCase):
    ids = {"proposta", "planejamento"}
    def meta(self, txt):
        e = build.Erros(); m, c = build.ler_meta("x.md", txt, e); build.validar_meta("x.md", m, self.ids, e); return m, c, e
    def test_valido(self):
        m, c, e = self.meta("---\ntitulo: A\nestagio: proposta\ndata: 2026-10-24\n---\ncorpo"); self.assertFalse(e); self.assertEqual(m["titulo"], "A")
    def test_bloco_aberto(self): self.assertTrue(self.meta("---\ntitulo: A\ncorpo")[2])
    def test_linha_invalida(self): self.assertTrue(any("linha" in x for x in self.meta("---\nlixo sem dois pontos\n---\nx")[2]))
    def test_data_invalida(self): self.assertTrue(any("data" in x for x in self.meta("---\ndata: 31/12/2026\n---\nx")[2]))
    def test_estado_e_campo_desconhecidos(self):
        e = self.meta("---\nestagio: nada\nfoo: 1\n---\nx")[2]
        self.assertTrue(any("estagio" in x for x in e)); self.assertTrue(any("foo" in x for x in e))
    def test_chave_duplicada(self): self.assertTrue(any("duplicada" in x for x in self.meta("---\ntitulo: A\ntitulo: B\n---\nx")[2]))

class Markdown(unittest.TestCase):
    def test_xss_escapado(self):
        h = build.markdown("<script>alert(1)</script> [x](javascript:alert(1)) [ok](https://a.org)")
        self.assertNotIn("<script>", h); self.assertNotIn("javascript:", h); self.assertIn('href="https://a.org"', h)
    def test_tabela_e_lista(self):
        h = build.markdown("| A | B |\n| --- | --- |\n| 1 | 2 |\n\n- um\n- dois"); self.assertIn("<th scope='col'>A</th>", h); self.assertIn("<li>dois</li>", h)

class Construcao(unittest.TestCase):
    def test_build_ok_e_deterministico(self):
        e, a = build.construir(escrever=False); self.assertEqual(e, [])
        e2, b = build.construir(escrever=False); self.assertEqual(a, b)
    def test_erro_nao_escreve(self):
        ruim = build.ORIGEM / "_tmp_ruim.md"
        self.addCleanup(lambda: ruim.exists() and ruim.unlink())
        ruim.write_text("---\nestagio: nada\n---\n# T\n", encoding="utf-8")
        # arquivos que começam com _ são ignorados:
        self.assertEqual(build.construir(escrever=False)[0], [])
        ruim.rename(build.ORIGEM / "tmp-ruim.md"); self.addCleanup(lambda: (build.ORIGEM / "tmp-ruim.md").exists() and (build.ORIGEM / "tmp-ruim.md").unlink())
        erros, saidas = build.construir(escrever=False)
        self.assertIsNone(saidas); self.assertTrue(any("tmp-ruim.md" in x and "estagio" in x for x in erros))

class Integridade(unittest.TestCase):
    def paginas(self): return [p for p in RAIZ.rglob("*.html") if "tests" not in p.parts]
    def test_links_e_ancoras_locais(self):
        for p in self.paginas():
            h = p.read_text(encoding="utf-8"); ids = set(re.findall(r'id="([^"]+)"', h))
            for a in re.findall(r'href="#([^"]+)"', h): self.assertIn(a, ids, f"{p.name}: âncora #{a}")
            for ref in re.findall(r'(?:href|src)=["\']([^"\'#:]+?)(?:#[^"\']*)?["\']', h):
                if ref.startswith(("http", "mailto")): continue
                self.assertTrue((p.parent / ref).exists(), f"{p.relative_to(RAIZ)}: recurso ausente {ref}")
    def test_sem_href_vazio_e_com_idioma_e_titulo(self):
        for p in self.paginas():
            h = p.read_text(encoding="utf-8")
            self.assertNotIn('href="#"', h, p.name); self.assertIn('lang="pt-BR"', h); self.assertRegex(h, r"<title>[^<]+</title>")
            self.assertEqual(len(re.findall(r"<h1[ >]", h)), 1, f"{p.name}: deve ter um h1")
    def test_sem_segredos_e_sem_codigo_de_turma(self):
        for p in RAIZ.rglob("*"):
            if p.is_file() and p.suffix in {".html", ".js", ".json", ".md", ".py"} and "tests" not in p.parts:
                t = p.read_text(encoding="utf-8")
                self.assertNotIn("bxznaujq", t); self.assertNotIn("character.ai/chat", t)
    def test_sitemap_so_aponta_para_arquivos_existentes(self):
        for loc in re.findall(r"<loc>(.*?)</loc>", (RAIZ / "sitemap.xml").read_text()):
            self.assertTrue((RAIZ / loc.replace(build.SITE_URL, "")).exists(), loc)

if __name__ == "__main__": unittest.main()
