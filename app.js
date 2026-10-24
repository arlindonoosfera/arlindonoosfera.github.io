(function () {
  "use strict";
  var D = window.DADOS;
  if (!D) return;

  function el(tag, cls, texto) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (texto) e.textContent = texto;
    return e;
  }

  /* Projetos + filtros */
  var lista = document.getElementById("lista-projetos");
  var filtros = document.getElementById("filtros");
  var atual = "todos";

  function desenhaProjetos() {
    lista.textContent = "";
    D.projetos.forEach(function (p) {
      if (atual !== "todos" && p.estagio !== atual) return;
      var a = el("article", "projeto");
      var et = el("p", "etapa");
      var lua = el("span", "lua", D.luas[p.estagio] + " ");
      lua.setAttribute("aria-hidden", "true");
      et.appendChild(lua);
      et.appendChild(document.createTextNode(D.estagios[p.estagio]));
      a.appendChild(et);
      var h = el("h3");
      if (p.link) {
        var l = el("a", "", p.titulo);
        l.href = p.link; l.rel = "noopener";
        h.appendChild(l);
      } else { h.textContent = p.titulo; }
      a.appendChild(h);
      a.appendChild(el("p", "area", p.area));
      a.appendChild(el("p", "", p.resumo));
      if (p.metodo) a.appendChild(el("p", "", p.metodo));
      if (p.nota) a.appendChild(el("p", "nota", p.nota));
      lista.appendChild(a);
    });
  }

  function desenhaFiltros() {
    var opcoes = [["todos", "Todos"]].concat(Object.keys(D.estagios).map(function (k) { return [k, D.estagios[k]]; }));
    opcoes.forEach(function (o) {
      var b = el("button", "", o[1]);
      b.type = "button";
      b.setAttribute("aria-pressed", o[0] === atual ? "true" : "false");
      b.addEventListener("click", function () {
        atual = o[0];
        Array.prototype.forEach.call(filtros.children, function (x) { x.setAttribute("aria-pressed", "false"); });
        b.setAttribute("aria-pressed", "true");
        desenhaProjetos();
      });
      filtros.appendChild(b);
    });
  }

  /* Mapa de interesses */
  var mapa = document.getElementById("lista-mapa");
  D.interesses.forEach(function (g) {
    var d = el("div");
    d.appendChild(el("h3", "", g.grupo));
    var ul = el("ul");
    g.itens.forEach(function (i) { ul.appendChild(el("li", "", i)); });
    d.appendChild(ul);
    mapa.appendChild(d);
  });

  /* Trajetória */
  var traj = document.getElementById("lista-traj");
  D.trajetoria.forEach(function (g) {
    var d = el("div");
    d.appendChild(el("h3", "", g.titulo));
    if (g.itens.length) {
      var ul = el("ul");
      g.itens.forEach(function (i) { ul.appendChild(el("li", "", i)); });
      d.appendChild(ul);
    } else { d.appendChild(el("p", "vazio-t", "Nada registrado ainda.")); }
    traj.appendChild(d);
  });

  /* Conexões: sem link inventado; sem URL = pendente */
  var con = document.getElementById("lista-con");
  D.conexoes.forEach(function (c) {
    var li = el("li");
    if (c.url) {
      var a = el("a", "", c.nome);
      a.href = c.url; a.rel = "noopener";
      li.appendChild(el("strong")).appendChild(a);
    } else {
      li.appendChild(el("strong", "pendente", c.nome + " (em breve)"));
    }
    li.appendChild(el("p", "nota", c.nota));
    con.appendChild(li);
  });

  desenhaFiltros();
  desenhaProjetos();
})();
