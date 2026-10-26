// Execute: node tests/site.test.js
const assert = require("assert");
const S = require("../site.js");
assert.strictEqual(S.normaliza("Ação, Evolução!"), "acao, evolucao!");
assert.strictEqual(S.normaliza(null), "");
const item = { texto: "Árvore da Caatinga: germinação", campos: { ano: "1º ano", recurso: "aula" } };
assert.ok(S.casa(item, { busca: "arvore caatinga", campos: {} }), "todos os termos, sem acento");
assert.ok(!S.casa(item, { busca: "arvore oceano", campos: {} }), "termo ausente reprova");
assert.ok(S.casa(item, { busca: "", campos: { ano: "1º ano" } }));
assert.ok(!S.casa(item, { busca: "", campos: { ano: "2º ano" } }), "filtro de campo");
assert.ok(S.casa(item, { busca: "germinacao", campos: { ano: "", recurso: "aula" } }), "campo vazio = sem filtro; filtros combinados");
const ind = [
  { u: "a.html", t: "Botânica", k: "Aula", r: "plantas", g: ["botanica"], x: "fotossíntese e transporte" },
  { u: "b.html", t: "Ecologia", k: "Aula", r: "botânica e ambiente", g: ["ecologia"], x: "cadeias alimentares" },
  { u: "c.html", t: "Cinema", k: "Resenha", r: "filme", g: [], x: "sem relação" }];
const r = S.buscar(ind, "botanica");
assert.deepStrictEqual(r.map(e => e.u), ["a.html", "b.html"], "título pesa mais; acentos ignorados");
assert.deepStrictEqual(S.buscar(ind, "   "), [], "busca vazia não retorna nada");
assert.deepStrictEqual(S.buscar(ind, "botanica cinema"), [], "todos os termos precisam existir no mesmo item");
assert.ok(S.trecho("um texto longo sobre fotossíntese nas plantas", ["fotossintese"], 20).includes("fotossíntese"));
assert.strictEqual(S.fraseDoDia([], new Date()), null);
assert.strictEqual(S.fraseDoDia(undefined, new Date()), null);
const fr = [{ texto: "a" }, { texto: "b" }, { texto: "c" }];
const d1 = new Date(2026, 9, 24, 8), d2 = new Date(2026, 9, 24, 23);
assert.strictEqual(S.fraseDoDia(fr, d1), S.fraseDoDia(fr, d2), "mesma frase o dia todo");
assert.notStrictEqual(S.fraseDoDia(fr, d1), S.fraseDoDia(fr, new Date(2026, 9, 25)), "muda no dia seguinte");
console.log("site.test.js: todos os testes passaram");
