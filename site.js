/* Noosfera: menu, filtros, busca, frase do dia e fórum. Sem dependências.
   As funções puras são exportadas para teste em Node (tests/site.test.js). */
(function (raiz) {
  "use strict";

  function normaliza(t) { return String(t == null ? "" : t).normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase(); }
  function termos(q) { return normaliza(q).split(/\s+/).filter(Boolean); }

  /* item: {texto, campos:{campo:valor}}; filtro: {busca, campos:{campo:valor}} */
  function casa(item, filtro) {
    var campos = filtro.campos || {};
    for (var c in campos) if (campos[c] && item.campos[c] !== campos[c]) return false;
    var palheiro = normaliza(item.texto);
    return termos(filtro.busca).every(function (t) { return palheiro.indexOf(t) >= 0; });
  }

  /* Busca global: todos os termos precisam aparecer; título pesa mais que resumo, tags e texto. */
  function buscar(indice, q) {
    var ts = termos(q);
    if (!ts.length) return [];
    return indice.map(function (e) {
      var t = normaliza(e.t), r = normaliza(e.r), g = normaliza((e.g || []).join(" ")), x = normaliza(e.x), pontos = 0;
      for (var i = 0; i < ts.length; i++) {
        var p = (t.indexOf(ts[i]) >= 0 ? 6 : 0) + (g.indexOf(ts[i]) >= 0 ? 3 : 0) + (r.indexOf(ts[i]) >= 0 ? 2 : 0) + (x.indexOf(ts[i]) >= 0 ? 1 : 0);
        if (!p) return null;
        pontos += p;
      }
      return { e: e, pontos: pontos };
    }).filter(Boolean).sort(function (a, b) { return b.pontos - a.pontos || a.e.t.localeCompare(b.e.t, "pt-BR"); }).map(function (x) { return x.e; });
  }

  function trecho(texto, ts, tam) {
    var plano = String(texto || ""), n = normaliza(plano), pos = -1;
    for (var i = 0; i < ts.length && pos < 0; i++) pos = n.indexOf(ts[i]);
    if (pos < 0) return plano.slice(0, tam);
    var ini = Math.max(0, pos - Math.min(60, Math.floor(tam / 3)));
    return (ini > 0 ? "…" : "") + plano.slice(ini, ini + tam) + (ini + tam < plano.length ? "…" : "");
  }

  /* Determinística: a mesma frase o dia inteiro, para qualquer visitante. */
  function fraseDoDia(frases, data) {
    if (!Array.isArray(frases) || !frases.length) return null;
    var dia = Math.floor(Date.UTC(data.getFullYear(), data.getMonth(), data.getDate()) / 86400000);
    return frases[((dia % frases.length) + frases.length) % frases.length];
  }

  var api = { normaliza: normaliza, casa: casa, buscar: buscar, trecho: trecho, fraseDoDia: fraseDoDia };
  if (typeof module !== "undefined" && module.exports) { module.exports = api; return; }
  raiz.NoosferaSite = api;
  if (typeof document === "undefined") return;

  function iniciar() {
    var D = raiz.NOOSFERA || {};
    var params = new URLSearchParams(raiz.location.search);

    /* Menu em telas pequenas (sem JS, o menu fica sempre visível) */
    var btn = document.querySelector(".menu-btn"), menu = document.getElementById("menu");
    if (btn && menu) {
      btn.addEventListener("click", function () {
        var aberto = menu.classList.toggle("aberto");
        btn.setAttribute("aria-expanded", String(aberto));
      });
      document.addEventListener("keydown", function (ev) {
        if (ev.key === "Escape" && menu.classList.contains("aberto")) { menu.classList.remove("aberto"); btn.setAttribute("aria-expanded", "false"); btn.focus(); }
      });
    }

    /* Filtros das listas */
    var ctrl = document.querySelector("[data-controles]");
    if (ctrl) {
      var itens = Array.prototype.map.call(document.querySelectorAll("[data-item]"), function (el) {
        var campos = {};
        Array.prototype.forEach.call(ctrl.querySelectorAll("select[data-campo]"), function (s) { campos[s.dataset.campo] = el.dataset[s.dataset.campo] || ""; });
        return { el: el, texto: el.dataset.texto || "", campos: campos };
      });
      var busca = document.getElementById("f-busca"), limpar = ctrl.querySelector("[data-limpar]");
      var status = document.querySelector("[data-status]"), semRes = document.querySelector("[data-sem-resultado]");
      var selects = ctrl.querySelectorAll("select[data-campo]");
      var aplica = function () {
        var f = { busca: busca.value, campos: {} };
        Array.prototype.forEach.call(selects, function (s) { f.campos[s.dataset.campo] = s.value; });
        var n = 0;
        itens.forEach(function (i) { var ok = casa(i, f); i.el.hidden = !ok; if (ok) n++; });
        Array.prototype.forEach.call(document.querySelectorAll("[data-grupo]"), function (g) { g.hidden = !g.querySelector("[data-item]:not([hidden])"); });
        var ativo = !!busca.value || Array.prototype.some.call(selects, function (s) { return s.value; });
        limpar.hidden = !ativo; semRes.hidden = n > 0;
        status.textContent = ativo ? n + (n === 1 ? " resultado de " : " resultados de ") + itens.length : "";
      };
      busca.addEventListener("input", aplica);
      Array.prototype.forEach.call(selects, function (s) {
        var v = params.get(s.dataset.campo);
        if (v && Array.prototype.some.call(s.options, function (o) { return o.value === v; })) s.value = v;
        s.addEventListener("change", aplica);
      });
      limpar.addEventListener("click", function () { busca.value = ""; Array.prototype.forEach.call(selects, function (s) { s.value = ""; }); aplica(); busca.focus(); });
      aplica();
    }

    /* Página de busca */
    var lista = document.querySelector("[data-busca-resultados]");
    if (lista) {
      var q = params.get("q") || "", campo = document.getElementById("q-busca"), st = document.querySelector("[data-busca-status]");
      campo.value = q;
      if (q.trim()) {
        var res = buscar(D.indice || [], q), ts = termos(q);
        st.textContent = res.length ? res.length + (res.length === 1 ? " resultado" : " resultados") + " para “" + q + "”" : "Nenhum resultado para “" + q + "”. Tente outros termos.";
        res.slice(0, 50).forEach(function (e) {
          var li = document.createElement("li"), a = document.createElement("a"), k = document.createElement("p"), r = document.createElement("p");
          a.href = e.u; a.textContent = e.t; k.className = "meta"; k.textContent = e.k; r.textContent = trecho(e.x || e.r, ts, 180);
          li.appendChild(a); li.appendChild(k); li.appendChild(r); lista.appendChild(li);
        });
      }
    }

    /* Frase do dia: só aparece se existir frase com autoria e fonte */
    var bloco = document.querySelector("[data-frase]");
    if (bloco) {
      var f = fraseDoDia(D.frases, new Date());
      if (!f) { bloco.hidden = true; }
      else {
        bloco.querySelector("[data-frase-texto]").textContent = f.texto;
        var fonte = bloco.querySelector("[data-frase-fonte]");
        fonte.textContent = "— " + f.autor + ", " + f.fonte + (f.ano ? " (" + f.ano + ")" : "");
      }
    }

    /* Fórum: o script de terceiros só é carregado quando a pessoa pede */
    var forum = document.getElementById("forum"), botao = document.querySelector("[data-forum-carregar]");
    if (forum && botao) {
      botao.addEventListener("click", function () {
        var s = document.createElement("script");
        s.src = "https://giscus.app/client.js"; s.async = true; s.crossOrigin = "anonymous";
        var d = forum.dataset;
        [["repo", d.repo], ["repo-id", d.repoId], ["category", d.categoria], ["category-id", d.categoriaId], ["mapping", "pathname"], ["strict", "1"],
         ["reactions-enabled", "1"], ["input-position", "top"], ["theme", "preferred_color_scheme"], ["lang", "pt"]].forEach(function (p) { s.setAttribute("data-" + p[0], p[1]); });
        botao.hidden = true; forum.appendChild(s);
      });
    }
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", iniciar); else iniciar();
})(typeof window !== "undefined" ? window : this);
