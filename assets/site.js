/* 셸 공통 동작. ⭐ 여기서 하는 일은 모두 덧붙임이다 — JS 가 없어도 쪽은 온전하다.
   날마다 바뀌는 값(D-n, 진행 %, 오늘 표시선)은 **빌드가 굽지 않고 여기서 채운다** —
   굽으면 커밋한 날과 CI 가 다시 구운 날이 달라 「docs/ 가 원본과 같은가」가 깨진다. */
(function () {
  "use strict";
  var DAY = 86400000, KST = 9 * 3600000;
  var root = document.documentElement;
  function kstDay(t) { return Math.floor((t + KST) / DAY); }
  function localDate() {
    var d = new Date();
    return d.getFullYear() + "-" + (d.getMonth() + 1) + "-" + d.getDate();
  }
  function get(store, k) { try { return window[store].getItem(k); } catch (e) { return null; } }
  function put(store, k, v) { try { window[store].setItem(k, v); } catch (e) { /* 무시 */ } }
  function each(sel, fn) { Array.prototype.forEach.call(document.querySelectorAll(sel), fn); }
  // "YYYY-MM" → 그달 1일 0시(KST) / 그달 말일 24시(KST)
  function monthStart(s) { var p = s.split("-"); return Date.UTC(+p[0], +p[1] - 1, 1) - KST; }
  function monthEnd(s) { var p = s.split("-"); return Date.UTC(+p[0], +p[1], 1) - KST; }
  function dday(end, now) { var n = kstDay(end) - kstDay(now); return n > 0 ? "D-" + n : "D-day"; }

  /* ── 머리말 높이 — 채용 카드가 메뉴 바로 아래에 붙는다 */
  var nav = document.querySelector("nav.nav");
  function navH() { if (nav) root.style.setProperty("--nav-h", nav.offsetHeight + "px"); }
  navH();
  window.addEventListener("resize", navH);

  /* ── 영문 안내 줄 (국문 홈). 브라우저 언어에 한국어가 하나도 없을 때만 연다.
     ⭐ 자동으로 영문판에 보내지 않는다 — Google 은 언어 자동 이동을 피하라고 한다. */
  var en = document.querySelector(".en-note");
  if (en) {
    var langs = (navigator.languages && navigator.languages.length ? navigator.languages : [navigator.language || "ko"]);
    var ko = Array.prototype.some.call(langs, function (l) { return /^ko/i.test(l || ""); });
    if (!ko && get("localStorage", "en-note") !== "closed") en.hidden = false;
    var ex = en.querySelector("[data-en-note-close]");
    if (ex) ex.addEventListener("click", function () { en.hidden = true; put("localStorage", "en-note", "closed"); });
  }

  /* ── 과제 목록: 타임라인의 오늘 표시선 */
  each("table[data-axis-start]", function (tb) {
    var a = monthStart(tb.getAttribute("data-axis-start")), b = monthEnd(tb.getAttribute("data-axis-end"));
    var now = Date.now();
    if (now < a || now > b) return;
    tb.style.setProperty("--today", ((now - a) / (b - a) * 100).toFixed(2) + "%");
    tb.classList.add("has-today");
    each(".lg-today-k", function (k) { k.hidden = false; });   // 범례의 「오늘」도 선이 있을 때만
  });

  /* ── 과제 상세: 진행 % 와 진행 막대 */
  each("[data-progress]", function (c) {
    var a = monthStart(c.getAttribute("data-start")), b = monthEnd(c.getAttribute("data-end"));
    var now = Date.now(), total = +c.getAttribute("data-n");
    var r = Math.max(0, Math.min(1, (now - a) / (b - a)));
    var pct = c.querySelector("[data-progress-pct]"), note = c.querySelector("[data-progress-note]");
    // 내림한다 — 반올림하면 끝나기 전(남은 기간 0.5% 미만, 41개월 과제면 마지막 엿새쯤)에 100% 가 된다.
    if (pct) pct.textContent = Math.floor(r * 100) + "%";
    // 「n개월 경과」는 **다 지난 달**만 센다(이번 달은 아직 안 끝났다). 종료 뒤에는 전체.
    var d = new Date(now + KST), s = c.getAttribute("data-start").split("-");
    var done = now >= b ? total
      : Math.max(0, Math.min(total, (d.getUTCFullYear() - +s[0]) * 12 + d.getUTCMonth() + 1 - +s[1]));
    if (note) note.textContent = (c.getAttribute("data-tpl") || "").replace("%n", total).replace("%m", done);
    c.hidden = false;
  });
  each("[data-pbar]", function (bar) {
    var a = monthStart(bar.getAttribute("data-start")), b = monthEnd(bar.getAttribute("data-end"));
    var r = Math.max(0, Math.min(1, (Date.now() - a) / (b - a)));
    bar.style.setProperty("--done", (r * 100).toFixed(2) + "%");
    bar.hidden = false;
  });

  /* ── 소식: 상단 고정 글의 D-n. 마감 시각이 지나면 「마감」 — 「진행 중」 딱지도 함께 바꾼다
        (고정 해제는 다음 예약 빌드가 한다. 그 사이 「진행 중 … 마감」이 한 액자에 같이 있으면 안 된다). */
  each("[data-dday-of]", function (el) {
    var end = Date.parse(el.getAttribute("data-dday-of"));
    var box = el.closest ? el.closest(".npin") : null;
    var state = box ? box.querySelector("[data-pin-state]") : null;
    function paint() {
      var now = Date.now(), shut = now >= end, closed = el.getAttribute("data-closed") || "";
      el.textContent = shut ? closed : dday(end, now);
      if (shut && state) state.textContent = closed;
    }
    paint();
    setInterval(paint, 15000);
  });

  /* ── 채용 안내 카드 (build.py 의 hire_note)
     - HTML 에는 `hidden` 으로 구워져 있다. 마감 전이고 닫은 기록이 없을 때만 연다.
     - ⭐ 마감 시각(data-deadline)이 지나면 닫는다. 쪽을 연 채 그 시각을 넘겨도 타이머가 닫는다.
       빌드는 날짜 단위로만 보므로 마감 당일 13:00 이후의 숨김은 이 스크립트가 맡는다.
     - ⚠️ 타이머만 믿지 않는다. 타이머는 절전 동안 멈추고, 뒤로 가기(bfcache)로 돌아온 쪽은
       스크립트를 다시 돌리지 않는다. 그래서 화면이 다시 보일 때마다 마감과 닫은 기록을 다시 본다.
     - D-n 은 **한국 날짜** 차이다. (마감 − 지금)을 하루로 나눠 올림하면 마감 시각 전에는
       하루를 더 세어, 마감 당일 아침에 「D-1」이 뜬다.
     - 「오늘 하루 보지 않기」는 **방문자의 날짜**로 기억한다 — 해외 방문자의 「오늘」이 한국
       자정에 끝나면 안 된다. 저장소 접근은 모두 try/catch(사생활 보호 모드에서는 예외가 난다). */
  var note = document.querySelector("aside.hire-note[data-deadline]");
  if (!note) return;
  var end = Date.parse(note.getAttribute("data-deadline"));
  var key = note.getAttribute("data-key") || "hire-note";
  var dd = note.querySelector("[data-dday]");
  var timer = null, closer = null;
  var shut = false;   // 저장소가 막힌 브라우저에서도 이 쪽을 보는 동안은 닫힌 채로 둔다

  function dismissed() {
    return shut ||
           get("sessionStorage", key) === "closed" ||          // 이번 방문에서 닫았다
           get("localStorage", key) === localDate();           // 오늘 하루 보지 않기
  }
  // 좁은 화면의 바닥 띠는 띠 높이만큼 쪽 아래 여백을 둔다(--hire-h).
  function pad() { root.style.setProperty("--hire-h", note.offsetHeight + "px"); }
  function close() {
    if (note.hidden) return;
    // 포커스가 카드 안에 있으면 본문으로 옮긴다. 그대로 숨기면 포커스가 body 로 떨어진다.
    if (note.contains(document.activeElement)) {
      var main = document.getElementById("main");
      if (main) {
        main.setAttribute("tabindex", "-1");
        try { main.focus({ preventScroll: true }); } catch (e) { main.focus(); }
      }
    }
    note.hidden = true;
    root.classList.remove("has-hire-note");
    root.style.removeProperty("--hire-h");
    if (timer) { clearInterval(timer); timer = null; }
    if (closer) { clearTimeout(closer); closer = null; }
  }
  function paint() {
    var now = Date.now();
    if (!(end > now) || dismissed()) { close(); return; }
    if (dd) dd.textContent = dday(end, now);
  }
  function open() {
    var now = Date.now();
    if (!(end > now) || dismissed()) return;                    // 마감이 지났거나(값을 못 읽었거나) 닫았다
    paint();
    navH();
    note.hidden = false;
    root.classList.add("has-hire-note");
    pad();
    if (!timer) timer = setInterval(paint, 15000);              // 자정에 D-n, 마감에 닫힘
    var left = end - now;
    if (!closer && left < 2147483647) closer = setTimeout(close, left);
  }

  open();
  window.addEventListener("resize", function () { if (!note.hidden) pad(); });
  // 다시 보일 때 다시 본다: 절전 해제, 탭 복귀, 뒤로 가기 복원.
  document.addEventListener("visibilitychange", function () {
    if (document.visibilityState === "visible") { if (note.hidden) open(); else paint(); }
  });
  window.addEventListener("pageshow", function (ev) {
    if (ev.persisted) { if (note.hidden) open(); else paint(); }
  });

  var x = note.querySelector("[data-hire-close]");
  if (x) x.addEventListener("click", function () { shut = true; put("sessionStorage", key, "closed"); close(); });
  var today = note.querySelector("[data-hire-today]");
  if (today) today.addEventListener("click", function () { shut = true; put("localStorage", key, localDate()); close(); });
  note.addEventListener("keydown", function (ev) {
    if (ev.key === "Escape") { shut = true; put("sessionStorage", key, "closed"); close(); }
  });
})();
