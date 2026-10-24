(function () {
  "use strict";
  var N = window.Noosfera;

  function el(tag, cls, texto) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (texto) e.textContent = texto;
    return e;
  }
  function limpa(e) { while (e.firstChild) e.removeChild(e.firstChild); }
  function porId(id) { return document.getElementById(id); }

  function mostraErro(msg, detalhe) {
    console.error("[Noosfera] " + msg, detalhe || "");
    var caixa = porId("erro-dados");
    if (caixa) { caixa.textContent = msg; caixa.hidden = false; }
  }

  function link(texto, url) {
    var a = el("a", "", texto);
    a.href = url; a.rel = "noopener noreferrer";
    return a;
  }

  function iniciar() {
    if (!N) return mostraErro("Não foi possível carregar o site (lib.js). Recarregue a página.");
    if (!window.DADOS) return mostraErro("Não foi possível carregar o conteúdo (data.js). Recarregue a página ou tente mais tarde.");
    var r = N.validarDados(window.DADOS);
    r.erros.forEach(function (x) { console.warn("[Noosfera] dados: " + x); });
    if (!r.dados || !r.dados.estados.length) return mostraErro("O conteúdo do site está incompleto. Tente novamente mais tarde.", r.erros);
    var D = r.dados;
    var estado = {}; D.estados.forEach(function (s) { estado[s.id] = s; });
    var filtro = { busca: "", estado: "", categoria: "" };

    /* Legenda: gerada a partir da definição única de estados */
    var leg = porId("legenda");
    D.estados.forEach(function (s) {
      var item = el("span");
      var lua = el("span", "lua", s.lua + " "); lua.setAttribute("aria-hidden", "true");
      item.appendChild(lua); item.appendChild(document.createTextNode(s.rotulo.toLowerCase()));
      leg.appendChild(item);
    });

    /* Projetos */
    var lista = porId("lista-projetos"), status = porId("status");
    function desenha() {
      var achados = N.filtrar(D.projetos, filtro).sort(function (a, b) { return a.titulo.localeCompare(b.titulo, "pt-BR"); });
      limpa(lista);
      achados.forEach(function (p) {
        var a = el("article", "projeto");
        var et = el("p", "etapa");
        var lua = el("span", "lua", estado[p.estagio].lua + " "); lua.setAttribute("aria-hidden", "true");
        et.appendChild(lua); et.appendChild(document.createTextNode(estado[p.estagio].rotulo));
        a.appendChild(et);
        var h = el("h3");
        if (p.link) h.appendChild(link(p.titulo, p.link)); else h.textContent = p.titulo;
        a.appendChild(h);
        a.appendChild(el("p", "area", p.area));
        a.appendChild(el("p", "", p.resumo));
        if (p.metodo) a.appendChild(el("p", "", p.metodo));
        if (p.nota) a.appendChild(el("p", "nota", p.nota));
        lista.appendChild(a);
      });
      var ativo = filtro.busca || filtro.estado || filtro.categoria;
      porId("limpar").hidden = !ativo;
      status.textContent = achados.length === 0
        ? "Nenhum projeto encontrado. Tente outros termos ou limpe os filtros."
        : achados.length + (achados.length === 1 ? " projeto" : " projetos") + (ativo ? " encontrados" : "");
    }

    var busca = porId("busca"), cat = porId("categoria"), grupo = porId("filtros"), botoes = {};
    function marca() { Object.keys(botoes).forEach(function (k) { botoes[k].setAttribute("aria-pressed", String(k === filtro.estado)); }); }
    [["", "Todos"]].concat(D.estados.filter(function (s) {
      return D.projetos.some(function (p) { return p.estagio === s.id; });
    }).map(function (s) { return [s.id, s.rotulo]; })).forEach(function (o) {
      var b = el("button", "", o[1]); b.type = "button"; botoes[o[0]] = b;
      b.addEventListener("click", function () { filtro.estado = o[0]; marca(); desenha(); });
      grupo.appendChild(b);
    });
    var cats = []; D.projetos.forEach(function (p) { var c = N.categoriaDe(p); if (cats.indexOf(c) < 0) cats.push(c); });
    cats.sort(function (a, b) { return a.localeCompare(b, "pt-BR"); }).forEach(function (c) {
      var o = el("option", "", c); o.value = c; cat.appendChild(o);
    });
    busca.addEventListener("input", function () { filtro.busca = busca.value; desenha(); });
    cat.addEventListener("change", function () { filtro.categoria = cat.value; desenha(); });
    porId("limpar").addEventListener("click", function () {
      filtro = { busca: "", estado: "", categoria: "" }; busca.value = ""; cat.value = ""; marca(); desenha(); busca.focus();
    });
    marca(); desenha();

    /* Mapa, trajetória, conexões */
    var mapa = porId("lista-mapa");
    D.interesses.forEach(function (g) {
      var d = el("div"); d.appendChild(el("h3", "", g.grupo));
      var ul = el("ul"); g.itens.forEach(function (i) { ul.appendChild(el("li", "", i)); });
      d.appendChild(ul); mapa.appendChild(d);
    });
    var traj = porId("lista-traj");
    D.trajetoria.forEach(function (g) {
      var d = el("div"); d.appendChild(el("h3", "", g.titulo));
      if (g.itens.length) { var ul = el("ul"); g.itens.forEach(function (i) { ul.appendChild(el("li", "", i)); }); d.appendChild(ul); }
      else d.appendChild(el("p", "vazio-t", "Nada registrado ainda."));
      traj.appendChild(d);
    });
    var con = porId("lista-con");
    D.conexoes.forEach(function (c) {
      var li = el("li"), forte = el("strong");
      if (c.url) forte.appendChild(link(c.nome, c.url));
      else { forte.className = "pendente"; forte.textContent = c.nome + " (em breve)"; }
      li.appendChild(forte);
      if (c.nota) li.appendChild(el("p", "nota", c.nota));
      con.appendChild(li);
    });

    /* Seção atual no menu */
    var links = document.querySelectorAll('.topo nav a[href^="#"]');
    if ("IntersectionObserver" in window && links.length) {
      var obs = new IntersectionObserver(function (es) {
        es.forEach(function (x) {
          if (!x.isIntersecting) return;
          links.forEach(function (a) {
            if (a.getAttribute("href") === "#" + x.target.id) a.setAttribute("aria-current", "true");
            else a.removeAttribute("aria-current");
          });
        });
      }, { rootMargin: "-30% 0px -60% 0px" });
      document.querySelectorAll("main section[id]").forEach(function (s) { obs.observe(s); });
    }
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", iniciar); else iniciar();
})();
