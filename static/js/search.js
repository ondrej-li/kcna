/* Client-side full-text search over /index.json (no dependencies). */
(function () {
  "use strict";

  var input = document.getElementById("q");
  var status = document.getElementById("search-status");
  var list = document.getElementById("search-results");
  if (!input || !status || !list) return;

  var MAX_RESULTS = 100;
  var index = null;
  var pending = null;

  function normalize(value) {
    return (value || "")
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/[^a-z0-9]+/g, " ")
      .trim();
  }

  function escapeHtml(value) {
    return value
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function highlight(text, terms) {
    var escaped = escapeHtml(text);
    if (!terms.length) return escaped;
    var pattern = terms
      .filter(function (term) { return term.length > 1; })
      .map(function (term) { return term.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"); })
      .join("|");
    if (!pattern) return escaped;
    // Match the words as typed (with diacritics), so "Čong" highlights too.
    return escaped.replace(new RegExp("(" + pattern + ")", "gi"), "<mark>$1</mark>");
  }

  function render(items, terms) {
    if (!items.length) {
      list.innerHTML = "";
      status.textContent = "Nic nenalezeno.";
      return;
    }
    status.textContent = items.length >= MAX_RESULTS
      ? "Zobrazeno prvních " + MAX_RESULTS + " z " + items.length + " zpráv"
      : items.length + " nalezených zpráv";
    var html = "";
    for (var i = 0; i < items.length && i < MAX_RESULTS; i++) {
      var item = items[i];
      html += '<li><a class="title" href="' + item.url + '">' + highlight(item.title, terms) + "</a>";
      if (item.date) html += '<p class="meta"><span class="star">★</span>' + escapeHtml(item.date) + "</p>";
      if (item.text) html += '<p class="snippet">' + highlight(item.text, terms) + "</p>";
      html += "</li>";
    }
    list.innerHTML = html;
  }

  function search(query) {
    if (!index) return;
    var terms = normalize(query).split(" ").filter(Boolean);
    if (!terms.length) {
      list.innerHTML = "";
      status.textContent = "";
      return;
    }
    var termsNorm = terms;
    var results = [];
    for (var i = 0; i < index.length; i++) {
      var item = index[i];
      if (!item._haystack) {
        item._haystack = normalize(
          item.title + " " + item.text + " " + (item.labels || []).join(" ") + " " + item.date
        );
      }
      var haystack = item._haystack;
      var matched = true;
      for (var t = 0; t < termsNorm.length; t++) {
        if (haystack.indexOf(termsNorm[t]) === -1) {
          matched = false;
          break;
        }
      }
      if (matched) results.push(item);
    }
    var rawTerms = query.split(/\s+/).filter(Boolean);
    render(results, rawTerms);
  }

  function load() {
    if (index) return Promise.resolve(index);
    if (pending) return pending;
    pending = fetch("/index.json")
      .then(function (response) {
        if (!response.ok) throw new Error("HTTP " + response.status);
        return response.json();
      })
      .then(function (data) {
        index = data;
        return index;
      });
    return pending;
  }

  function run() {
    load()
      .then(function () { search(input.value); })
      .catch(function () {
        status.textContent = "Index se nepodařilo načíst.";
      });
  }

  var timer = null;
  input.addEventListener("input", function () {
    clearTimeout(timer);
    timer = setTimeout(run, 120);
  });

  var params = new URLSearchParams(window.location.search);
  if (params.get("q")) {
    input.value = params.get("q");
    run();
  }
})();
