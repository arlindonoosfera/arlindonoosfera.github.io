# arlindonoosfera.github.io

Site pessoal de Arlindo Noosfera: portfólio, arquivo intelectual e laboratório. Estático (HTML, CSS e JavaScript puro), compatível com GitHub Pages, sem servidor e sem dependências externas.

## Estrutura

| Arquivo | Função |
| --- | --- |
| `dados.json` | **Fonte única** de estados, projetos, trajetória, interesses e conexões. Edite este arquivo. |
| `data.js` | Gerado por `build.py` a partir de `dados.json` (define `window.DADOS`). Não edite à mão. |
| `lib.js` | Funções puras: validação, URLs seguras, busca e filtros. |
| `app.js` | Renderização e eventos (DOM seguro: nada de `innerHTML`). |
| `conteudo/aulas/*.md` | Páginas de aula em Markdown. |
| `build.py` | Valida tudo e gera `data.js`, `aulas.html`, `aulas/*.html`, `sitemap.xml`, `robots.txt`. |
| `index.html`, `plano-biologia.html`, `style.css` | Páginas e estilo escritos à mão. |
| `tests/` | Testes automatizados. |

## Estados válidos

Definidos em `dados.json` → `estados` (identificador sem acento, rótulo, fase da Lua). A legenda, os filtros, os rótulos das aulas e a validação usam essa mesma lista.

| id | rótulo | |
| --- | --- | --- |
| `proposta` | Proposta | 🌑 |
| `planejamento` | Em planejamento | 🌒 |
| `desenvolvimento` | Em desenvolvimento | 🌓 |
| `aplicado` | Aplicado | 🌔 |
| `concluido` | Concluído | 🌕 |
| `confirmar` | Estágio a confirmar | ◌ |

Estado desconhecido: o `build.py` recusa (erro com caminho e campo); se chegar ao navegador, o item vira `confirmar` e o problema é registrado no console.

## Como adicionar conteúdo

- **Projeto, trajetória, interesse ou link:** edite `dados.json` e rode `python3 build.py`. Campos de projeto: `titulo`, `area` ("Categoria · Subárea"; a categoria alimenta o filtro), `resumo`, `estagio` (obrigatórios); `metodo`, `nota`, `link` (opcionais; `link` deve ser http/https, ou omita o campo). Em `conexoes`, deixe `url` vazia enquanto o endereço não existir.
- **Aula:** crie `conteudo/aulas/nome-da-aula.md` e rode `python3 build.py`. Cabeçalho opcional:

```
---
titulo: Extinções em massa
ano: 1º ano · Unidade 2
estagio: planejamento
data: 2026-10-24
---
# Extinções em massa
Texto em Markdown...
```

Chaves aceitas: `titulo`, `ano`, `estagio`, `data` (AAAA-MM-DD). Qualquer outra chave, chave repetida ou linha fora do formato `chave: valor` é erro. Sem `titulo`, vale o primeiro `# Título`. Arquivos começando com `_` são ignorados. Exportações do Notion ("Markdown & CSV") servem; revise antes de publicar (códigos de turma, links privados, dados de estudantes).

## Validar, construir e testar

```
python3 build.py --check   # só valida, não escreve
python3 build.py           # valida e gera; se houver erro, não escreve nada
sh tests/run.sh            # validação + testes JS + testes Python
```

O build nunca apaga arquivos: se renomear ou remover uma aula, apague à mão o `.html` antigo em `aulas/`. Requisitos: Python 3.9+ e Node 18+ (apenas para os testes). Sem pacotes externos.

## Ver localmente

```
python3 -m http.server 8000   # abra http://localhost:8000
```

## Publicar no GitHub Pages

1. Rode `sh tests/run.sh` e confirme que passa.
2. Faça commit de **todos** os arquivos, inclusive os gerados (`data.js`, `aulas.html`, `aulas/`, `sitemap.xml`, `robots.txt`).
3. `git push` na branch publicada; em *Settings → Pages*, confirme a fonte (branch `main`, pasta `/root`).

Todos os caminhos são relativos, então o site funciona na raiz do domínio e em subcaminhos. `SITE_URL` em `build.py` define as URLs canônicas e o sitemap; altere se o domínio mudar.

## Regras

Nada de dados, links, créditos ou resultados inventados; o estágio deve refletir o estado real. Não publicar códigos de turma, dados de estudantes nem links privados. Os testes barram o código de turma e links de chat já removidos.

## Decisões de arquitetura

- **Uma fonte de dados (`dados.json`) gerando `data.js`:** elimina o desencontro entre legenda, rótulos e filtros, e permite validar antes de publicar. `window.DADOS` continua existindo.
- **Sem framework nem bibliotecas:** o site tem poucas páginas e pouca interação.
- **Markdown próprio e mínimo:** tudo é escapado e só links http/https viram `<a>`, para evitar XSS. Se o conteúdo crescer muito, troque por uma biblioteca revisada e documente.
- **Sem `localStorage`:** os filtros são rápidos de refazer; persistir não compensa.
