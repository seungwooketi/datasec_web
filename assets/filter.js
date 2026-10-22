/* 목록 거르개 — 과제 목록(참여형태, 지원 부처, 상태, 연구 주제)과 구성원(직급).
   ⭐ 스크립트가 없으면 **전부 보인다**(빌드가 이미 다 그렸다). 거르개 막대도 hidden 으로 구워져
      있다가 여기서 열린다 — JS 없이 눌러도 아무 일 없는 버튼을 보이지 않으려고.
   묶음 사이는 AND, 묶음 안은 하나만 고른다. 주소의 ?topic=<id> 를 읽어 미리 고른다.
   상태와 주제는 낱말 목록이다(종료 예정 과제의 상태는 「active closing」 — 「수행 중」에도 걸린다). */
(function () {
  "use strict";
  var bars = document.querySelectorAll("[data-filters]");
  if (!bars.length) return;
  var table = document.getElementById("ptable");
  var items = table ? Array.prototype.slice.call(table.tBodies[0].rows)
                    : Array.prototype.slice.call(document.querySelectorAll(".pcard[data-grade], .dir[data-grade]"));
  var count = document.getElementById("count");
  // 영문은 1 일 때 단수다(data-one). 없으면 지금 글에서 숫자 자리를 찾는다.
  var many = count ? (count.getAttribute("data-many") || count.textContent.replace(/[0-9]+/, "%n")) : "";
  var one = count ? (count.getAttribute("data-one") || many) : "";
  var WORDS = { status: 1, topics: 1 };
  var state = {};

  function match(el) {
    for (var f in state) {
      var v = state[f];
      if (v === "all") continue;
      var have = el.getAttribute("data-" + f) || "";
      if (WORDS[f]) { if ((" " + have + " ").indexOf(" " + v + " ") < 0) return false; continue; }
      if (have !== v) return false;
    }
    return true;
  }
  function apply() {
    var n = 0;
    items.forEach(function (el) { var on = match(el); el.hidden = !on; if (on) n++; });
    if (count && many) count.textContent = (n === 1 ? one : many).replace("%n", n);
  }
  function pick(btn) {
    var f = btn.getAttribute("data-f");
    state[f] = btn.getAttribute("data-v");
    var group = btn.parentNode.querySelectorAll("[data-f]");
    Array.prototype.forEach.call(group, function (o) {
      var on = o === btn;
      o.classList.toggle("is-on", on);
      o.setAttribute("aria-pressed", on ? "true" : "false");
    });
    apply();
  }
  Array.prototype.forEach.call(document.querySelectorAll("[data-f][data-v]"), function (b) {
    b.addEventListener("click", function () { pick(b); });
  });
  Array.prototype.forEach.call(bars, function (b) { b.hidden = false; });

  var topic = null;
  try { topic = new URLSearchParams(location.search).get("topic"); } catch (e) { /* 무시 */ }
  if (topic) {
    var btn = document.querySelector('[data-f="topics"][data-v="' + topic.replace(/[^a-z0-9-]/g, "") + '"]');
    if (btn) pick(btn);
  }
})();
