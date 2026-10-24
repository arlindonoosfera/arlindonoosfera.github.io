// Execute: node tests/lib.test.js
const assert = require("assert");
const L = require("../lib.js");
const base = { estados: [{ id: "proposta", rotulo: "Proposta", lua: "🌑" }, { id: "confirmar", rotulo: "A confirmar", lua: "◌" }],
  projetos: [{ titulo: "Árvore", area: "Botânica · Campo", resumo: "Estudo de caatinga", estagio: "proposta", link: "javascript:alert(1)" },
             { titulo: "X", area: "Arte", resumo: "y", estagio: "inexistente" }, { titulo: "", area: "a", resumo: "b" }],
  trajetoria: [{ titulo: "T", itens: "errado" }], interesses: [{ grupo: "G", itens: ["a"] }, { grupo: "vazio", itens: [] }],
  conexoes: [{ nome: "A", url: "https://x.org" }, { nome: "B", url: "ftp://x" }, { nome: "C" }] };
const r = L.validarDados(base);
assert.strictEqual(r.dados.projetos.length, 2, "descarta projeto sem título");
assert.strictEqual(r.dados.projetos[0].link, null, "bloqueia javascript:");
assert.strictEqual(r.dados.projetos[1].estagio, "confirmar", "estado desconhecido vira 'confirmar'");
assert.deepStrictEqual(r.dados.trajetoria[0].itens, [], "itens inválidos viram lista vazia");
assert.strictEqual(r.dados.interesses.length, 1, "grupo vazio é descartado");
assert.strictEqual(r.dados.conexoes[0].url, "https://x.org/");
assert.strictEqual(r.dados.conexoes[1].url, null, "protocolo ftp rejeitado");
assert.ok(r.erros.length >= 3);
assert.strictEqual(L.validarDados(undefined).dados, null);
assert.strictEqual(L.validarDados({}).dados.projetos.length, 0);
assert.strictEqual(L.urlSegura("data:text/html,x"), null);
assert.strictEqual(L.urlSegura("não é url"), null);
const ps = r.dados.projetos;
assert.strictEqual(L.filtrar(ps, { busca: "arvore" }).length, 1, "busca ignora acento");
assert.strictEqual(L.filtrar(ps, { busca: "caatinga botanica" }).length, 1, "todos os termos");
assert.strictEqual(L.filtrar(ps, { busca: "zzz" }).length, 0);
assert.strictEqual(L.filtrar(ps, { estado: "confirmar" }).length, 1);
assert.strictEqual(L.filtrar(ps, { categoria: "Botânica", estado: "proposta" }).length, 1, "filtros combinados");
assert.strictEqual(L.filtrar(ps, { categoria: "Botânica", estado: "confirmar" }).length, 0);
console.log("lib.test.js: todos os testes passaram");
