# Noosfera · arlindonoosfera.github.io

Arquivo vivo de investigação, ensino e criação de Arlindo Noosfera. Site **estático** (HTML, CSS e JavaScript puro), gerado por um script Python, compatível com GitHub Pages. Sem servidor, sem banco de dados, sem dependências além do Python 3.9+ (e Node 18+ só para testes).

## Estrutura

| Caminho | Função |
| --- | --- |
| `conteudo/aulas`, `projetos`, `escritos`, `resenhas`, `biblioteca` | **Fonte do conteúdo**: um `.md` por item, com cabeçalho `chave: valor`. |
| `conteudo/frases.json` | Frases do dia (opcional; só aparecem com autoria e fonte). |
| `conteudo/_modelos/` | Modelos para copiar. Ignorada pelo build. |
| `dados.json` | Estados, áreas de interesse, relações entre áreas e configuração do fórum. |
| `build.py` | Valida tudo e gera as páginas, `indice.js`, `sitemap.xml`, `robots.txt`, `404.html`. |
| `style.css`, `site.js` | Estilo (claro/escuro automático) e comportamento (menu, filtros, busca, frase, fórum). |
| `img/`, `downloads/` | Imagens otimizadas e arquivos para baixar. |
| `tools/` | Importadores (Notion e Blogger). Não fazem parte do site. |
| `tests/` | Testes automatizados. |

Os arquivos `.html`, `indice.js`, `sitemap.xml` e `robots.txt` na raiz são **gerados**: não edite à mão. Faça commit deles junto com o conteúdo.

## Estados

Definidos em `dados.json` → `estados` (identificador sem acento, rótulo, fase da Lua): `ideia` 🌑, `planejamento` 🌒, `desenvolvimento` 🌓, `aplicado` 🌔, `concluido` 🌕, `arquivado` 🌘, `confirmar` ◌ (provisório: estado ainda a definir). Estado desconhecido é erro de build.

## Tipos de conteúdo e campos

Cabeçalho entre `---`, uma linha `chave: valor` por campo; listas separadas por vírgula; datas `AAAA-MM-DD`; `sim`/`nao` para booleanos. Campo desconhecido, ausente ou inválido interrompe o build com o arquivo e o campo.

| Tipo | Obrigatórios | Opcionais |
| --- | --- | --- |
| aula | `titulo` | `estado`, `ano`, `unidade`, `recurso` (aula, atividade, guia, avaliacao, material, roteiro, plano), `disciplina`, `nivel`, `duracao`, `tags`, `resumo`, `arquivo` (`caminho \| rótulo`), `relacionados`, `ordem`, `data`, `atualizado` |
| projeto | `titulo`, `estado`, `area`, `resumo` | `tags`, `inicio`, `atualizado`, `destaque`, `link`, `relacionados` |
| escrito | `titulo`, `categoria` (ensaio, noticia, reflexao, relato, texto), `resumo` | `data` (original; se desconhecida, omita e a página mostra “data original a confirmar”), `tema`, `subtitulo`, `tags`, `atualizado`, `imagem`, `relacionados`; **notícia comentada exige** `fonte_titulo`, `fonte_url`, `fonte_data` |
| resenha | `titulo`, `tipo` (livro, filme, serie, documentario, musica, jogo, arte), `autoria`, `ano`, `resumo` | `data`, `tema`, `subtitulo`, `spoilers`, `nota` (0 a 5), `capa`, `tags`, `relacionados`, `atualizado` |
| livro (biblioteca) | `titulo`, `autor`, `leitura` (por-ler, a-ler, lendo, concluido, abandonado) | `edicao`, `editora`, `ano`, `isbn`, `inicio`, `fim`, `resenha` (slug), `tags`, `relacionados`, `resumo`, `capa`, `atualizado` |

- `area` de projeto: `Categoria · Subárea` (a categoria vira filtro).
- `tags`: identificadores de `dados.json` → `areas` alimentam o **mapa de interesses**. Outras tags valem para busca, mas não aparecem no mapa.
- `relacionados`: `tipo/slug` (ex.: `aulas/botanica`). Páginas também mostram itens que compartilham tags.
- Links internos no texto: `[texto](aulas/slug)`. Imagens: `![texto alternativo](img/pasta/arquivo.webp "legenda")`; o arquivo precisa existir.
- Livros: use `## Citações` com `>` e a página e a edição (`— p. 12, 3ª ed.`). Nada de citação sem fonte.
- Notícias: escreva só o seu comentário; o site mostra a fonte e o link antes dele.

## Temas visuais

Cada tipo de conteúdo tem um tema (cor de destaque, ornamento e ritmo de leitura): `cinema` (moldura perfurada), `serie`, `livro` (capitular), `musica`, `jogo`, `arte`, `reflexao` (texto centrado, mais arejado), `ensaio`, `noticia`, `relato`, `texto`, `ciencia` (aulas e projetos). O tema é derivado do tipo ou da categoria; para trocar, use `tema: nome` no cabeçalho de escritos e resenhas. Os temas respeitam o modo escuro e passam no contraste mínimo.

## Pauta (temas ainda sem texto)

`conteudo/pauta.json` lista o que ainda **não** foi escrito, para o site tratar como intenção e não como texto publicado. Formato (modelo em `conteudo/_modelos/pauta.exemplo.json`): `textos` (cada um com `titulo`, `formato` opcional como lista de resenha, reflexao, ensaio, biografia, guia, relato, outro, e `nota` opcional) e `cadernos` (`titulo`, `nota` opcional, `ideias` não vazia). Gera `pauta.html`, o bloco "Na fila de escrita" da página inicial e entradas na busca. Quando um tema for escrito, crie o arquivo em `conteudo/escritos/` ou `conteudo/resenhas/` e remova-o da pauta.

## Dia a dia

```
python3 build.py --check   # só valida
python3 build.py           # valida e gera (se houver erro, não escreve nada; nunca apaga arquivos)
sh tests/run.sh            # validação + testes JS + testes Python
python3 -m http.server 8000   # ver em http://localhost:8000
```

Remover ou renomear um item: apague à mão o `.html` antigo da pasta correspondente.

## Importar do Notion

Exporte a página (Markdown & CSV, com subpáginas) e rode `python3 tools/importar_notion.py Export.zip` (acrescente `--sobrescrever` para refazer). O script remove links privados (Sala de Aula, Character.ai, páginas do Notion não importadas) e códigos de turma, otimiza imagens (com Pillow, se instalado) e **omite imagens de terceiros ou de autoria incerta** (edite `IMAGENS_PROPRIAS` no script para liberar pastas suas). Revise o resultado antes de publicar: o plano de ensino contém anotações de rascunho.

## Migrar o Blogger

1. No Blogger: Configurações → Gerenciar blog → **Fazer backup do conteúdo** (um XML por blog).
2. `python3 tools/importar_blogger.py backup.xml` cria rascunhos em `conteudo/_rascunhos_blogger/` (fora do site) e um `relatorio.txt`.
3. Para cada texto: escolha categoria/tipo, complete os campos, baixe as imagens para `img/` e ajuste os links, e mova para `conteudo/<tipo>/`.
4. Só depois de validado, apague o conteúdo original no Blogger, se quiser. O build não redireciona endereços do Blogger (não estão sob seu controle); mantenha o blog ativo ou publique links do novo endereço.

## Frase do dia

Crie `conteudo/frases.json` (modelo em `conteudo/_modelos/frases.exemplo.json`). Cada frase exige `texto`, `autor` e `fonte` verificável. Sem arquivo ou sem frases, o bloco não aparece. A frase é a mesma o dia inteiro para qualquer visitante.

## Fórum

Um site estático não guarda comentários. A arquitetura escolhida é o **giscus** (comentários no GitHub Discussions): autenticação pelo GitHub, anti-spam e moderação pelo próprio GitHub, sem servidor nem chave secreta. Para ativar:

1. No repositório, habilite **Discussions** e crie uma categoria (tipo "Announcement" ou "Q&A").
2. Instale o app **giscus** no repositório e gere os valores em https://giscus.app (os identificadores são públicos por projeto, não são segredos).
3. Preencha `dados.json` → `forum` com `repo`, `repo_id`, `categoria`, `categoria_id` e rode `python3 build.py`.

Enquanto `forum` for `null`, a página mostra apenas um aviso de que o fórum não foi aberto. Com o fórum ativo, o script do giscus **só é carregado quando a pessoa clica** em "Carregar discussão", e a página informa que isso conecta a um serviço externo.

## Publicar no GitHub Pages

1. `sh tests/run.sh` passando.
2. Commit de **tudo**, inclusive os arquivos gerados (`*.html`, `aulas/`, `projetos/`, `indice.js`, `sitemap.xml`, `robots.txt`).
3. Push na branch publicada; em Settings → Pages confirme a fonte (branch, pasta raiz). Os caminhos das páginas são relativos; só `404.html` e as URLs canônicas assumem o domínio `https://arlindonoosfera.github.io/` (constante `SITE_URL` em `build.py`).

## Acessibilidade e privacidade

HTML semântico, link para pular ao conteúdo, foco visível, contraste ≥ 4,5:1 nos dois modos (verificado no CSS), `prefers-reduced-motion`, imagens com texto alternativo, mapa com alternativa em texto. Sem cookies, sem analytics, sem fontes externas. O único serviço de terceiros possível é o giscus, e só após clique.

## Regras do projeto

Nada de dados, links, créditos, imagens ou resultados inventados; o estado de cada item reflete o real. Não publicar códigos de turma, dados de estudantes nem links privados (os testes barram os já removidos). Imagens ilustrativas são identificadas como tais.
