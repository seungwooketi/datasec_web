/* 셸 공통 동작. ⭐ 여기서 하는 일은 모두 덧붙임이다 — JS 가 없어도 쪽은 온전하다.

   채용 안내 카드 (build.py 의 hire_note)
   - HTML 에는 `hidden` 으로 구워져 있다. 마감 전이고 닫은 기록이 없을 때만 연다.
   - ⭐ 마감 시각(data-deadline)이 지나면 닫는다. 쪽을 연 채 그 시각을 넘겨도 타이머가 닫는다.
     빌드는 날짜 단위로만 보므로 마감 당일 13:00 이후의 숨김은 이 스크립트가 맡는다.
   - D-n 은 **한국 날짜** 차이다. (마감 − 지금)을 하루로 나눠 올림하면 마감 시각 전에는
     하루를 더 세어, 마감 당일 아침에 「D-1」이 뜬다.
   - 저장소 접근은 모두 try/catch — 사생활 보호 모드에서는 예외가 난다. 실패해도 카드는 정상이다. */
(function () {
  "use strict";
  var DAY = 86400000, KST = 9 * 3600000;
  function kstDay(t) { return Math.floor((t + KST) / DAY); }
  function kstDate(t) { return new Date(t + KST).toISOString().slice(0, 10); }
  function get(store, k) { try { return window[store].getItem(k); } catch (e) { return null; } }
  function put(store, k, v) { try { window[store].setItem(k, v); } catch (e) { /* 무시 */ } }

  var note = document.querySelector("aside.hire-note[data-deadline]");
  if (!note) return;
  var end = Date.parse(note.getAttribute("data-deadline"));
  var key = note.getAttribute("data-key") || "hire-note";
  if (!(end > Date.now())) return;                           // 마감이 지났다(또는 값을 못 읽었다)
  if (get("sessionStorage", key) === "closed") return;       // 이번 방문에서 닫았다
  if (get("localStorage", key) === kstDate(Date.now())) return;   // 오늘 하루 보지 않기

  var dday = note.querySelector("[data-dday]");
  var timer = null;
  function close() {
    note.hidden = true;
    document.documentElement.classList.remove("has-hire-note");
    if (timer) clearInterval(timer);
  }
  function paint() {
    var now = Date.now();
    if (now >= end) { close(); return; }
    var n = kstDay(end) - kstDay(now);
    if (dday) dday.textContent = n > 0 ? "D-" + n : "D-day";
  }

  paint();
  note.hidden = false;
  document.documentElement.classList.add("has-hire-note");
  timer = setInterval(paint, 60000);                         // 자정에 D-n, 마감에 닫힘
  var left = end - Date.now();
  if (left < 2147483647) setTimeout(close, left);            // 마감 시각에 바로 닫는다

  var x = note.querySelector("[data-hire-close]");
  if (x) x.addEventListener("click", function () { put("sessionStorage", key, "closed"); close(); });
  var today = note.querySelector("[data-hire-today]");
  if (today) today.addEventListener("click", function () {
    put("localStorage", key, kstDate(Date.now()));
    close();
  });
})();
