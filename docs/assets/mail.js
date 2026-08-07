/* 메일 주소를 사람에게만 되돌린다.
   ⭐ HTML 원문에는 `mailto:` 도, `user@domain` 도, `user [at] domain` 도 **없다** —
      글자가 통째로 뒤집혀 있고 CSS(`.rev`)가 시각적으로만 되돌린다.
   ⚠️ 완전한 차단은 아니다. 스크립트를 실행하는 수집기(헤드리스 브라우저)는 이 결과를 본다 —
      목적은 **대량 정규식 수집을 막는 것**이지 결심한 상대를 막는 것이 아니다.
      주소를 아예 노출하지 않으려면 문의 폼이어야 한다.
   ⚠️ 스크립트가 없으면 뒤집힌 글자가 CSS 로 바로 보인다 — 읽고 옮겨 적을 수 있다. */
(function () {
  "use strict";
  var list = document.querySelectorAll("a.mail");
  for (var i = 0; i < list.length; i++) {
    var a = list[i];
    var span = a.querySelector(".rev");
    if (!span) continue;
    var m = span.textContent.split("").reverse().join("").replace(" [at] ", "@");
    if (m.indexOf("@") < 0) continue;
    a.setAttribute("href", "mailto:" + m);
    a.textContent = m;                 // .rev 가 사라지므로 복사도 정상으로 된다
  }
})();
