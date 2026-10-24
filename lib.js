/* Funções puras (sem DOM): validação, URL segura e filtro. Testáveis com Node. */
(function (raiz) {
  "use strict";

  function urlSegura(valor) {
    if (typeof valor !== "string" || !valor.trim()) return null;
    try {
      var u = new URL(valor);
      return (u.protocol === "https:" || u.protocol === "http:") && u.hostname ? u.href : null;
    } catch (e) { return null; }
  }

  function textoValido(v) { return typeof v === "string" && v.trim() !== ""; }
  function listaDeTextos(v) { return Array.isArray(v) && v.every(textoValido); }

  /* Devolve dados saneados e a lista de problemas; nunca lança exceção. */
  function validarDados(d) {
    var erros = [];
    if (!d || typeof d !== "object") return { dados: null, erros: ["DADOS ausente ou não é objeto"] };
    var estados = Array.isArray(d.estados) ? d.estados.filter(function (s) {
      return s && textoValido(s.id) && textoValido(s.rotulo) && textoValido(s.lua);
    }) : [];
    if (!estados.length) erros.push("estados: lista ausente ou vazia");
    var ids = estados.map(function (s) { return s.id; });

    var projetos = (Array.isArray(d.projetos) ? d.projetos : []).filter(function (p, i) {
      var ok = p && textoValido(p.titulo) && textoValido(p.area) && textoValido(p.resumo);
      if (!ok) erros.push("projetos[" + i + "]: campos obrigatórios ausentes");
      return ok;
    }).map(function (p) {
      var estagio = ids.indexOf(p.estagio) >= 0 ? p.estagio : "confirmar";
      if (estagio !== p.estagio) erros.push("projeto '" + p.titulo + "': estado desconhecido '" + p.estagio + "'");
      var link = urlSegura(p.link);
      if (p.link != null && !link) erros.push("projeto '" + p.titulo + "': link inválido ou com protocolo não permitido");
      return { titulo: p.titulo, area: p.area, resumo: p.resumo, estagio: estagio,
               metodo: textoValido(p.metodo) ? p.metodo : "", nota: textoValido(p.nota) ? p.nota : "",
               link: link };
    });
    var trajetoria = (Array.isArray(d.trajetoria) ? d.trajetoria : []).filter(function (g, i) {
      var ok = g && textoValido(g.titulo);
      if (!ok) erros.push("trajetoria[" + i + "]: título ausente");
      return ok;
    }).map(function (g) {
      if (!listaDeTextos(g.itens)) erros.push("trajetoria '" + g.titulo + "': itens inválidos (esperada lista de textos)");
      return { titulo: g.titulo, itens: listaDeTextos(g.itens) ? g.itens : [] };
    });
    var interesses = (Array.isArray(d.interesses) ? d.interesses : []).filter(function (g, i) {
      var ok = g && textoValido(g.grupo) && listaDeTextos(g.itens) && g.itens.length;
      if (!ok) erros.push("interesses[" + i + "]: grupo ou itens inválidos");
      return ok;
    });
    var conexoes = (Array.isArray(d.conexoes) ? d.conexoes : []).filter(function (c, i) {
      var ok = c && textoValido(c.nome);
      if (!ok) erros.push("conexoes[" + i + "]: nome ausente");
      return ok;
    }).map(function (c) {
      var url = urlSegura(c.url);
      if (textoValido(c.url) && !url) erros.push("conexão '" + c.nome + "': URL inválida ou com protocolo não permitido");
      return { nome: c.nome, nota: textoValido(c.nota) ? c.nota : "", url: url };
    });
    return { dados: { estados: estados, projetos: projetos, trajetoria: trajetoria, interesses: interesses, conexoes: conexoes }, erros: erros };
  }

  function normaliza(t) {
    return String(t || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
  }
  function categoriaDe(p) { return p.area.split("·")[0].trim(); }

  /* Filtros combinados: busca textual (todos os termos), estado e categoria. */
  function filtrar(projetos, f) {
    var termos = normaliza(f.busca).split(/\s+/).filter(Boolean);
    return projetos.filter(function (p) {
      if (f.estado && p.estagio !== f.estado) return false;
      if (f.categoria && categoriaDe(p) !== f.categoria) return false;
      var palheiro = normaliza([p.titulo, p.area, p.resumo, p.metodo, p.nota].join(" "));
      return termos.every(function (t) { return palheiro.indexOf(t) >= 0; });
    });
  }

  var api = { urlSegura: urlSegura, validarDados: validarDados, filtrar: filtrar, categoriaDe: categoriaDe, normaliza: normaliza };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else raiz.Noosfera = api;
})(typeof window !== "undefined" ? window : this);
