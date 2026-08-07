/* 목록 거르개 — 검색어와 참여형태. 스크립트가 없으면 **전부 보인다**(빌드가 이미 다 그렸다).
   ⚠️ 페이지 자체가 정적이라 이 파일이 실패해도 내용이 사라지지 않는다. */
(function () {
  "use strict";
  var q = document.getElementById("q");
  var count = document.getElementById("count");
  var table = document.getElementById("ptable");
  var rows = table ? Array.prototype.slice.call(table.tBodies[0].rows) : [];
  var people = Array.prototype.slice.call(document.querySelectorAll(".person"));
  var facet = "all";
  var tpl = count ? count.textContent.replace(/[0-9]+/, "{n}") : "";

  function norm(s) { return (s || "").toLowerCase().trim(); }

  function apply() {
    var needle = norm(q && q.value);
    var shown = 0;

    rows.forEach(function (tr) {
      var okFacet = facet === "all" ||
        (facet === "new" ? tr.dataset.new === "1" : tr.dataset.role === facet);
      var okText = !needle || (tr.dataset.q || "").indexOf(needle) !== -1;
      var on = okFacet && okText;
      tr.hidden = !on;
      if (on) shown++;
    });

    people.forEach(function (el) {
      var hay = norm(el.textContent);
      var on = !needle || hay.indexOf(needle) !== -1;
      el.hidden = !on;
      if (on) shown++;
    });

    if (count && tpl) count.textContent = tpl.replace("{n}", shown);
  }

  if (q) q.addEventListener("input", apply);

  Array.prototype.forEach.call(document.querySelectorAll("[data-facet]"), function (b) {
    b.addEventListener("click", function () {
      facet = b.dataset.facet;
      Array.prototype.forEach.call(document.querySelectorAll("[data-facet]"), function (o) {
        var on = o === b;
        o.classList.toggle("is-on", on);
        o.setAttribute("aria-pressed", on ? "true" : "false");
      });
      apply();
    });
  });
})();
