// Execute: node tests/app.smoke.js  (DOM simulado mínimo; não substitui teste em navegador real)
const fs = require("fs"), vm = require("vm"), assert = require("assert"), path = require("path");
const raiz = path.join(__dirname, "..");
function mkEl(tag) {
  const e = { tag, children: [], attrs: {}, listeners: {}, className: "", hidden: false, value: "", _t: "", style: {},
    appendChild(c) { this.children.push(c); return c; }, removeChild(c) { this.children.splice(this.children.indexOf(c), 1); },
    get firstChild() { return this.children[0] || null; }, setAttribute(k, v) { this.attrs[k] = String(v); },
    removeAttribute(k) { delete this.attrs[k]; }, getAttribute(k) { return this.attrs[k]; },
    addEventListener(t, f) { (this.listeners[t] = this.listeners[t] || []).push(f); }, focus() {},
    set textContent(v) { this._t = String(v); this.children = []; }, get textContent() { return this._t + this.children.map(c => c.textContent).join(""); } };
  return e;
}
function cenario(dados, comLib = true) {
  const ids = {}; ["erro-dados", "legenda", "lista-projetos", "status", "limpar", "busca", "categoria", "filtros", "lista-mapa", "lista-traj", "lista-con"].forEach(i => ids[i] = mkEl("x"));
  const erros = [];
  const doc = { readyState: "complete", getElementById: i => ids[i], createElement: mkEl, createTextNode: t => ({ textContent: t, children: [] }),
    querySelectorAll: () => [], addEventListener() {} };
  const ctx = { window: {}, document: doc, console: { error: (...a) => erros.push(a.join(" ")), warn() {} }, URL, IntersectionObserver: undefined };
  ctx.window = ctx; ctx.window.DADOS = dados;
  vm.createContext(ctx);
  if (comLib) vm.runInContext(fs.readFileSync(path.join(raiz, "lib.js"), "utf8"), ctx);
  vm.runInContext(fs.readFileSync(path.join(raiz, "app.js"), "utf8"), ctx);
  return { ids, erros, ctx };
}
// 1) dados reais
const dados = JSON.parse(fs.readFileSync(path.join(raiz, "dados.json"), "utf8"));
let c = cenario(dados);
assert.strictEqual(c.ids["lista-projetos"].children.length, dados.projetos.length, "renderiza todos os projetos");
assert.strictEqual(c.ids["legenda"].children.length, dados.estados.length, "legenda vem dos estados");
assert.ok(c.ids["legenda"].textContent.includes("concluído"), "legenda inclui 'concluído' definido nos dados");
assert.strictEqual(c.ids["erro-dados"].textContent, "", "sem mensagem de erro com dados válidos");
// 2) busca + limpar
c.ids["busca"].value = "aetherion"; c.ids["busca"].listeners.input[0]();
assert.strictEqual(c.ids["lista-projetos"].children.length, 1);
assert.strictEqual(c.ids["limpar"].hidden, false);
c.ids["busca"].value = "zzzz"; c.ids["busca"].listeners.input[0]();
assert.ok(c.ids["status"].textContent.startsWith("Nenhum projeto"), "mensagem de ausência de resultados");
c.ids["limpar"].listeners.click[0]();
assert.strictEqual(c.ids["lista-projetos"].children.length, dados.projetos.length);
// 3) DADOS ausente: mensagem visível + console.error
c = cenario(undefined);
assert.strictEqual(c.ids["erro-dados"].hidden, false); assert.ok(c.ids["erro-dados"].textContent.length > 10); assert.ok(c.erros.length >= 1);
// 4) lib ausente
c = cenario(dados, false);
assert.strictEqual(c.ids["erro-dados"].hidden, false);
// 5) dados malformados: não quebra
c = cenario({ estados: "x", projetos: 5 });
assert.strictEqual(c.ids["erro-dados"].hidden, false);
// 6) link perigoso nunca vira href
const mal = JSON.parse(JSON.stringify(dados)); mal.projetos[0].link = "javascript:alert(1)";
c = cenario(mal);
const hrefs = []; (function varre(n) { if (n.href) hrefs.push(n.href); (n.children || []).forEach(varre); })(c.ids["lista-projetos"]);
assert.ok(!hrefs.some(h => h.startsWith("javascript")), "javascript: bloqueado");
console.log("app.smoke.js: todos os testes passaram");
