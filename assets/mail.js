/* 메일 주소를 사람에게만 보여 준다.
   ⭐ HTML 에는 `mailto:` 도, `user@domain` 형태의 문자열도 **없다** — 뒤집힌 문자열만 있다.
      수집 봇은 보통 `mailto:` 와 `\S+@\S+\.\S+` 를 찾으므로 둘 다 걸리지 않는다.
   ⚠️ 완전한 차단은 아니다. 스크립트를 도는 수집기는 이것도 푼다 —
      목적은 **대량 정규식 수집을 막는 것**이지 결심한 상대를 막는 것이 아니다.
   ⚠️ 스크립트가 없으면 `aidsrc [at] keti.re.kr` 그대로 남는다. 사람은 읽을 수 있다. */
(function () {
  "use strict";
  var list = document.querySelectorAll("a.mail[data-m]");
  for (var i = 0; i < list.length; i++) {
    var a = list[i];
    var m = (a.getAttribute("data-m") || "").split("").reverse().join("");
    if (m.indexOf("@") < 0) continue;
    a.setAttribute("href", "mailto:" + m);
    a.textContent = m;
    a.removeAttribute("data-m");
  }
})();
