/* 셸 공통 동작. ⭐ 여기서 하는 일은 모두 덧붙임이다 — JS 가 없어도 쪽은 온전하다.

   채용 안내 카드 (build.py 의 hire_note)
   - HTML 에는 `hidden` 으로 구워져 있다. 마감 전이고 닫은 기록이 없을 때만 연다.
   - ⭐ 마감 시각(data-deadline)이 지나면 닫는다. 쪽을 연 채 그 시각을 넘겨도 타이머가 닫는다.
     빌드는 날짜 단위로만 보므로 마감 당일 13:00 이후의 숨김은 이 스크립트가 맡는다.
   - ⚠️ 타이머만 믿지 않는다. 브라우저 타이머는 절전 동안 멈추고, 뒤로 가기(bfcache)로 돌아온 쪽은
     스크립트를 다시 돌리지 않는다. 그래서 화면이 다시 보일 때마다 마감과 닫은 기록을 다시 본다.
   - D-n 은 **한국 날짜** 차이다(마감이 한국 시각이므로). (마감 − 지금)을 하루로 나눠 올림하면
     마감 시각 전에는 하루를 더 세어, 마감 당일 아침에 「D-1」이 뜬다.
   - 「오늘 하루 보지 않기」는 **방문자의 날짜**로 기억한다 — 해외 방문자의 「오늘」이 한국 자정에
     끝나면 안 된다.
   - 저장소 접근은 모두 try/catch — 사생활 보호 모드에서는 예외가 난다. 실패해도 카드는 정상이다. */
(function () {
  "use strict";
  var DAY = 86400000, KST = 9 * 3600000;
  function kstDay(t) { return Math.floor((t + KST) / DAY); }
  function localDate() {
    var d = new Date();
    return d.getFullYear() + "-" + (d.getMonth() + 1) + "-" + d.getDate();
  }
  function get(store, k) { try { return window[store].getItem(k); } catch (e) { return null; } }
  function put(store, k, v) { try { window[store].setItem(k, v); } catch (e) { /* 무시 */ } }

  var note = document.querySelector("aside.hire-note[data-deadline]");
  if (!note) return;
  var root = document.documentElement;
  var end = Date.parse(note.getAttribute("data-deadline"));
  var key = note.getAttribute("data-key") || "hire-note";
  var dday = note.querySelector("[data-dday]");
  var timer = null, closer = null;

  function dismissed() {
    return get("sessionStorage", key) === "closed" ||          // 이번 방문에서 닫았다
           get("localStorage", key) === localDate();           // 오늘 하루 보지 않기
  }
  // 카드 높이만큼 쪽 아래에 여백을 둔다 — 없으면 끝까지 내려도 바닥글과 마지막 행이 카드 밑에 남는다.
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
    var n = kstDay(end) - kstDay(now);
    if (dday) dday.textContent = n > 0 ? "D-" + n : "D-day";
  }
  function open() {
    var now = Date.now();
    if (!(end > now) || dismissed()) return;                    // 마감이 지났거나(값을 못 읽었거나) 닫았다
    paint();
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
  if (x) x.addEventListener("click", function () { put("sessionStorage", key, "closed"); close(); });
  var today = note.querySelector("[data-hire-today]");
  if (today) today.addEventListener("click", function () { put("localStorage", key, localDate()); close(); });
  note.addEventListener("keydown", function (ev) {
    if (ev.key === "Escape") { put("sessionStorage", key, "closed"); close(); }
  });
})();
