#!/usr/bin/env python3
"""정적 사이트 생성기 — 표준 라이브러리만 쓴다.

⭐ **이 사이트는 KB 에 질의하지 않는다.** `data/*.json` 은 빌드 시점에 이미 확정된 값이고,
   그 값은 정본(`01. 센터 현황` 엑셀)에서 `tools/pull_from_sot.py` 가 옮겨 온다.
   갱신은 PR 로 온다 — 리뷰가 곧 「무엇을 공개할지」의 결정이다.

⛔ **대외 공개물이다.** 틀린 값이 나가면 되돌려도 이미 나간 것이다. 그래서:
   - 사람 영문명이 확인되지 않은 채로는 `--strict` 가 빌드를 **실패시킨다**
   - 예시(sample) 뉴스가 남아 있으면 `--strict` 가 실패시킨다
   - 비어 있는 연락처 같은 것은 경고로 남고, 페이지에는 **빈 자리로도 나가지 않는다**

의존성 0. `python3 build.py` 로 끝난다.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import html
import json
import pathlib
import re
import shutil
import sys

ROOT = pathlib.Path(__file__).parent
OUT = ROOT / "docs"
LANGS = ("ko", "en")
DEFAULT_LANG = "ko"

WARNINGS: list[str] = []
BLOCKERS: list[str] = []


def warn(msg: str) -> None:
    WARNINGS.append(msg)


def block(msg: str) -> None:
    BLOCKERS.append(msg)


# ════════════════════════════════════════════════════════════════════
# UI 문자열 — 페이지 껍데기의 말. 내용은 content/ 와 data/ 에서 온다.
# ════════════════════════════════════════════════════════════════════

T = {
    "ko": {
        "nav_home": "센터 소개", "nav_research": "연구", "nav_people": "구성원",
        "nav_news": "소식", "nav_collab": "협력", "nav_visit": "찾아오시는 길",
        "contact": "문의하기", "k_visit": "05 · 찾아오시는 길",
        "addr": "주소", "phone": "대표전화", "k_roster": "연구원 · 행정",
        "funders": "지원 부처", "k_lead": "저희가 이끄는 과제",
        "skip": "본문으로 건너뛰기",
        "k_latest": "01 · 새소식", "k_research": "02 · 연구 과제", "k_center": "03 · 센터 안내",
        "k_people": "03 · 구성원", "k_news": "01 · 새소식", "k_collab": "04 · 협력",
        "all_projects": "연구 과제 목록 →", "all_news": "지난 소식 →",
        "researchers": "연구인력", "active_projects": "수행중 과제",
        "lead_projects": "주관 과제", "new_projects": "26년 신규",
        "project": "과제명", "period": "수행기간", "funder": "지원기관",
        "role": "참여형태", "status": "상태", "pi": "담당자", "no": "번호",
        "members_n": "참여 구성원",
        "role_lead": "주관", "role_joint": "참여·공동", "role_contract": "기업수탁",
        "st_active": "수행중", "st_closing": "종료예정", "st_closed": "종료",
        "tag_new": "26년 신규",
        "filter_all": "전체", "count_projects": "과제 {n}개",
        "count_people": "구성원 {n}명",
        "search_projects": "과제명, 부처, 책임자 검색", "search_people": "이름 또는 직급 검색",
        "back_research": "← 연구 과제 목록", "back_news": "← 지난 소식",
        "register": "과제 정보", "summary_missing": "과제 소개는 준비 중입니다.",
        "own": "책임", "join": "참여",
        "in_dept": "부서 과제", "ext_n": "부서 외 과제 {n}건 참여",
        "no_projects": "수행 중인 과제가 없습니다.",
        "news_empty": "아직 올린 소식이 없습니다.",
        "lang_switch": "언어", "sample_badge": "예시",
        "sample_note": "이 글은 디자인 확인용 예시입니다. 게시 전에 지우거나 실제 내용으로 바꾸세요.",
    },
    "en": {
        "nav_home": "Overview", "nav_research": "Research", "nav_people": "People",
        "nav_news": "News", "nav_collab": "Collaborate", "nav_visit": "Visit",
        "contact": "Contact", "k_visit": "05 · Visit",
        "addr": "Address", "phone": "Phone", "k_roster": "Researchers · Administration",
        "funders": "Funding ministries", "k_lead": "Programmes we lead",
        "skip": "Skip to content",
        "k_latest": "01 · Latest", "k_research": "02 · Research programmes",
        "k_center": "03 · The center", "k_people": "03 · People",
        "k_news": "01 · Latest", "k_collab": "04 · Collaborate",
        "all_projects": "Research programmes →", "all_news": "Past news →",
        "researchers": "Researchers", "active_projects": "Active projects",
        "lead_projects": "As lead institute", "new_projects": "Started in 2026",
        "project": "Project", "period": "Period", "funder": "Funder",
        "role": "Role", "status": "Status", "pi": "PI", "no": "No.",
        "members_n": "Members",
        "role_lead": "Lead", "role_joint": "Partner", "role_contract": "Contract",
        "st_active": "Active", "st_closing": "Closing", "st_closed": "Closed",
        "tag_new": "New in 2026",
        "filter_all": "All", "count_projects": "{n} projects",
        "count_people": "{n} members",
        "search_projects": "Search projects, funders, PIs", "search_people": "Search by name or grade",
        "back_research": "← Research programmes", "back_news": "← All news",
        "register": "Register", "summary_missing": "A project summary is not published yet.",
        "own": "PI", "join": "Member",
        "in_dept": "Center projects", "ext_n": "Also on {n} projects led by other KETI centers",
        "no_projects": "No active projects.",
        "news_empty": "No news posted yet.",
        "lang_switch": "Language", "sample_badge": "Sample",
        "sample_note": "This post is a sample for design review. Remove or replace it before publishing.",
    },
}

ROLE_KEY = {"lead": "role_lead", "joint": "role_joint", "contract": "role_contract"}
STATUS_KEY = {"active": "st_active", "closing": "st_closing", "closed": "st_closed"}


# ════════════════════════════════════════════════════════════════════
# 아주 작은 마크다운 — 뉴스 글에 필요한 것만
# ════════════════════════════════════════════════════════════════════

def _inline(s: str) -> str:
    s = html.escape(s, quote=False)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", r'<a href="\2">\1</a>', s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\w*])\*([^*\n]+)\*(?![\w*])", r"<em>\1</em>", s)
    return s


def markdown(text: str) -> str:
    """문단 · 제목 · 목록 · 인용 · 구분선만. 그 이상은 이 사이트에 필요 없다."""
    out: list[str] = []
    buf: list[str] = []
    mode: str | None = None

    def flush() -> None:
        nonlocal mode
        if not buf:
            mode = None
            return
        if mode == "p":
            out.append("<p>" + "<br>".join(_inline(x) for x in buf) + "</p>")
        elif mode in ("ul", "ol"):
            items = "".join(f"<li>{_inline(x)}</li>" for x in buf)
            out.append(f"<{mode}>{items}</{mode}>")
        elif mode == "quote":
            out.append("<blockquote>" + " ".join(_inline(x) for x in buf) + "</blockquote>")
        buf.clear()
        mode = None

    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.strip():
            flush()
            continue
        if line.startswith("#"):
            flush()
            n = len(line) - len(line.lstrip("#"))
            out.append(f"<h{min(n + 1, 6)}>{_inline(line.lstrip('#').strip())}</h{min(n + 1, 6)}>")
        elif re.match(r"^(-{3,}|\*{3,})$", line.strip()):
            flush()
            out.append('<hr class="cr">')
        elif line.lstrip().startswith(("- ", "* ")):
            if mode != "ul":
                flush()
                mode = "ul"
            buf.append(line.lstrip()[2:])
        elif re.match(r"^\s*\d+\.\s", line):
            if mode != "ol":
                flush()
                mode = "ol"
            buf.append(re.sub(r"^\s*\d+\.\s", "", line))
        elif line.lstrip().startswith("> "):
            if mode != "quote":
                flush()
                mode = "quote"
            buf.append(line.lstrip()[2:])
        else:
            if mode != "p":
                flush()
                mode = "p"
            buf.append(line)
    flush()
    return "\n".join(out)


def front_matter(raw: str) -> tuple[dict, str]:
    """`---` 로 감싼 `키: 값` 머리말. YAML 이 아니다 — 그만큼만 쓴다."""
    if not raw.startswith("---"):
        return {}, raw
    _, fm, body = raw.split("---", 2)
    meta: dict[str, str] = {}
    for line in fm.strip().splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip().strip('"')
    return meta, body.strip()


# ════════════════════════════════════════════════════════════════════
# 자료 읽기
# ════════════════════════════════════════════════════════════════════

def load_json(name: str):
    p = ROOT / name
    if not p.exists():
        block(f"자료 파일이 없다: {name}")
        return [] if name.endswith("s.json") else {}
    return json.loads(p.read_text(encoding="utf-8"))


def status_of(project: dict, today: dt.date) -> str:
    end = project.get("end")
    if not end:
        return "active"
    y, m = (int(x) for x in end.split("-"))
    last = dt.date(y + (m == 12), (m % 12) + 1, 1) - dt.timedelta(days=1)
    if last < today:
        return "closed"
    if (last - today).days <= 183:
        return "closing"
    return "active"


def load_news() -> dict[str, list[dict]]:
    """`<slug>.<lang>.md`. 같은 slug 의 두 언어가 한 글이다."""
    news: dict[str, list[dict]] = {lg: [] for lg in LANGS}
    d = ROOT / "content" / "news"
    if not d.exists():
        return news
    seen: dict[str, set[str]] = {}
    for f in sorted(d.glob("*.md")):
        parts = f.name[:-3].rsplit(".", 1)
        if len(parts) != 2 or parts[1] not in LANGS:
            warn(f"뉴스 파일 이름이 `<slug>.<lang>.md` 가 아니다: {f.name}")
            continue
        slug, lg = parts
        meta, body = front_matter(f.read_text(encoding="utf-8"))
        if not meta.get("date") or not meta.get("title"):
            block(f"뉴스에 date 나 title 이 없다: {f.name}")
            continue
        seen.setdefault(slug, set()).add(lg)
        news[lg].append({
            "slug": slug, "date": meta["date"], "title": meta["title"],
            "summary": meta.get("summary", ""),
            "sample": meta.get("sample", "").lower() in ("true", "yes", "1"),
            "body": markdown(body),
        })
    # ⛔ 한 언어만 있는 글은 **아예 싣지 않는다.** 싣으면 그 쪽의 hreflang 과 언어 전환기가
    #    없는 쪽을 가리켜 404 가 된다 — 과제 상세와 같은 규칙이다.
    only_one = {s for s, langs in seen.items() if set(LANGS) - langs}
    for slug in sorted(only_one):
        warn(f"소식 `{slug}` 이 한 언어에만 있다 — 두 언어가 다 있어야 실린다")
    for lg in LANGS:
        news[lg] = sorted((n for n in news[lg] if n["slug"] not in only_one),
                          key=lambda x: x["date"], reverse=True)
    return news


# ════════════════════════════════════════════════════════════════════
# 껍데기
# ════════════════════════════════════════════════════════════════════

def e(s) -> str:
    return html.escape(str(s if s is not None else ""), quote=True)


def img_size(rel: str) -> tuple[int, int]:
    """이미지의 **실제** 픽셀 크기. ⛔ `width`/`height` 를 손으로 적지 않는다.

    실측: 히어로를 1100×1100 이라 적어 두었는데 파일은 1200×896 이었고, 로고는 414×128 로
    적었는데 450×128 이었다. CSS 가 `width:100%; height:auto` 라 브라우저가 **틀린 비율로
    자리를 예약**해 레이아웃이 밀린다(CLS). 그림을 바꿀 때마다 숫자를 고쳐야 하는 구조가
    문제였다 — 파일에서 읽는다.
    """
    b = (ROOT / rel.lstrip("/")).read_bytes()
    if b[:8] == b"\x89PNG\r\n\x1a\n":
        return int.from_bytes(b[16:20], "big"), int.from_bytes(b[20:24], "big")
    if b[:2] == b"\xff\xd8":                                   # JPEG — SOF 마커를 찾는다
        i = 2
        while i < len(b) - 9:
            if b[i] != 0xFF:
                i += 1
                continue
            mk = b[i + 1]
            if mk in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
                      0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                return (int.from_bytes(b[i + 7:i + 9], "big"),
                        int.from_bytes(b[i + 5:i + 7], "big"))
            i += 2 + int.from_bytes(b[i + 2:i + 4], "big")
    raise ValueError(f"크기를 못 읽는 이미지: {rel}")


HERO_W, HERO_H = img_size("assets/brand/hero.png")
OG_W, OG_H = img_size("assets/brand/og-image.png")

# ⭐ CI 의 심볼은 **인라인 SVG** 다 — 요청 0회이고 어느 배율에서도 또렷하다.
#    ⚠️ 세 굵기는 축소본이 아니라 **다른 그림**이다(2.5 / 4 / 5). 놓을 크기에 맞는 것을 쓴다.
SYMBOL = ('<svg viewBox="0 0 48 48" width="32" height="32" aria-hidden="true" focusable="false">'
          '<g fill="none" stroke="#5980A6" stroke-width="2.5">'
          '<rect x="6" y="6" width="24" height="24"/><rect x="18" y="18" width="24" height="24"/>'
          '</g><rect x="18" y="18" width="12" height="12" fill="#5980A6"/></svg>')


def stamp(rel: str) -> str:
    """`/assets/site.css?v=<내용 해시>`.

    ⛔ 이게 없으면 **배포해도 방문자는 옛 CSS 를 본다** — 브라우저가 같은 주소를 캐시하고,
       내용이 바뀐 걸 알 방법이 없다. 에러는 안 나고 화면만 틀어진다.
    """
    p = ROOT / rel.lstrip("/")
    if not p.exists():
        return rel
    return f"{rel}?v={hashlib.sha256(p.read_bytes()).hexdigest()[:10]}"


def other(lg: str) -> str:
    return "en" if lg == "ko" else "ko"


NAVS = [("", "nav_home"), ("research/", "nav_research"), ("people/", "nav_people"),
        ("news/", "nav_news"), ("collaborate/", "nav_collab"), ("visit/", "nav_visit")]


def shell(lg: str, nav_key: str, path: str, title: str, desc: str, body: str, site: dict,
          og_type: str = "website", jsonld: str = "", head_extra: str = "") -> str:
    """⛔ `nav_key` 와 `path` 는 **다른 것**이다.

    `nav_key` = 내비게이션에서 어느 항목을 현재로 표시할지 (상세 쪽도 목록 항목을 밝힌다).
    `path`    = 이 쪽의 **실제 주소** — canonical · hreflang · og:url · 언어 전환기가 쓴다.

    ⛔ 둘을 하나로 합쳐 두었더니 소식 상세 4쪽이 **자기를 목록 쪽으로 canonical** 시켰다.
       색인이 불가능해지고(구글은 canonical 을 따른다) 언어 전환 버튼도 목록으로 갔다.
       에러는 나지 않았다.
    """
    t = T[lg]
    CUR = ' aria-current="page"'
    nav = "".join(
        '<a href="/{}/{}"{}>{}</a>'.format(lg, p, CUR if p == nav_key else "", e(t[key]))
        for p, key in NAVS)
    def opt(code: str, label: str) -> str:
        on = code == lg
        return ('<a class="seg-opt{}" hreflang="{}" href="/{}/{}"{}>{}</a>'
                .format(" is-on" if on else "", code, code, path,
                        ' aria-current="true"' if on else "", label))
    seg = ('<div class="seg langseg" role="group" aria-label="{}">{}{}</div>'
           .format(e(t["lang_switch"]), opt("en", "EN"), opt("ko", "한국어")))
    center = site["center"][lg]
    email = site.get("contact", {}).get("email", "")
    foot_mid = mail(email) if email else e(site["org_url_label"])
    base = site["site_url"].rstrip("/")
    canonical = f"{base}/{lg}/{path}"
    return f"""<!doctype html>
<html lang="{lg}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)} — {e(center)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{e(canonical)}">
<link rel="alternate" hreflang="ko" href="{base}/ko/{path}">
<link rel="alternate" hreflang="en" href="{base}/en/{path}">
<link rel="alternate" hreflang="x-default" href="{base}/{DEFAULT_LANG}/{path}">
<meta property="og:title" content="{e(title)} — {e(center)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:type" content="{og_type}">
<meta property="og:url" content="{e(canonical)}">
<meta property="og:site_name" content="{e(center)}">
<meta property="og:locale" content="{'ko_KR' if lg == 'ko' else 'en_US'}">
<meta property="og:image" content="{base}/assets/brand/og-image.png">
<meta property="og:image:width" content="{OG_W}">
<meta property="og:image:height" content="{OG_H}">
<meta property="og:image:alt" content="ADSRC — {e(center)}">
<meta name="twitter:card" content="summary_large_image">{head_extra}{jsonld}
<link rel="icon" type="image/svg+xml" href="{stamp('/assets/brand/adsrc-symbol-16.svg')}">
<link rel="icon" type="image/png" sizes="32x32" href="{stamp('/assets/brand/favicon-32.png')}">
<link rel="icon" type="image/png" sizes="64x64" href="{stamp('/assets/brand/favicon-64.png')}">
<link rel="apple-touch-icon" href="{stamp('/assets/brand/apple-touch-icon-180.png')}">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow:wght@400;500;600;700&family=Barlow+Condensed:wght@400;600;700&family=IBM+Plex+Sans+KR:wght@400;500;600;700&display=swap">
<link rel="stylesheet" href="{stamp('/assets/industry.css')}">
<link rel="stylesheet" href="{stamp('/assets/site.css')}">
</head>
<body data-lang="{lg}">
<a class="skip" href="#main">{e(t['skip'])}</a>
<nav class="nav">
<a href="/{lg}/" class="nav-brand" aria-label="ADSRC — {e(center)}">{SYMBOL}
<span class="brand-text"><b>ADSRC</b><em>AI Data and Security Research Center</em></span></a>
<div class="navlinks">{nav}</div>
{seg}
<a class="btn btn-primary" href="/{lg}/collaborate/#contact">{e(t['contact'])}</a>
</nav>
<main id="main">
{body}
</main>
<footer>
<span>{e(site['center_full'][lg])}</span>
<span>{foot_mid}</span>
</footer>
<script src="{stamp('/assets/mail.js')}" defer></script>
</body>
</html>
"""


# ── 아이콘 — Lucide, stroke 1.5 (디자인 시스템이 정한 굵기). 인라인이라 요청이 0회다.
ICONS = {
    "homepage": ('<circle cx="12" cy="12" r="10"/>'
                 '<path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/><path d="M2 12h20"/>'),
    "github": ('<path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5'
               '.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 '
               '2.35 0 3.5A5.4 5.4 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 '
               '1.23-.15 1.85v4"/><path d="M9 18c-4.51 2-5-2-7-2"/>'),
    "linkedin": ('<path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-4 0v7h-4v-7a6 6 0 0 1 6-6z"/>'
                 '<rect width="4" height="12" x="2" y="9"/><circle cx="4" cy="4" r="2"/>'),
    "scholar": ('<path d="M22 10v6"/><path d="M2 10l10-5 10 5-10 5z"/>'
                '<path d="M6 12v5c3 2.5 9 2.5 12 0v-5"/>'),
}
ICON_LABEL = {"homepage": {"ko": "개인 홈페이지", "en": "Homepage"},
              "github": {"ko": "GitHub", "en": "GitHub"},
              "linkedin": {"ko": "LinkedIn", "en": "LinkedIn"},
              "scholar": {"ko": "Google Scholar", "en": "Google Scholar"}}


def icon(kind: str) -> str:
    return ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" '
            'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
            f'{ICONS[kind]}</svg>')


def mail(email: str, cls: str = "") -> str:
    """메일 주소를 **뒤집어서** 심는다 — `assets/mail.js` 가 사람에게만 되돌린다.

    ⛔ `mailto:` 나 `user@domain` 문자열을 HTML 에 두면 수집 봇의 정규식에 그대로 걸린다.
    ⚠️ 스크립트가 없으면 `aidsrc [at] keti.re.kr` 로 남는다 — 사람은 읽고 쓸 수 있다.
    """
    # ⭐ **화면에 보이는 글자마저 뒤집혀 있다.** CSS 가 시각적으로만 되돌리므로
    #    사람은 `aidsrc [at] keti.re.kr` 로 읽지만, HTML 원문에는 그 문자열이 없다.
    #    앞 판은 `[at]` 폼을 평문으로 두어서 `[at]`→`@` 로 바꾸는 수집기에 뚫렸다.
    shown = email.replace("@", " [at] ")[::-1]
    return (f'<a class="mail {cls}" href="#" rel="nofollow">'
            f'<span class="rev">{e(shown)}</span></a>')


def org_jsonld(lg: str, site: dict, stats: dict) -> str:
    """조직 구조화 데이터 — **홈 한 쪽에만** 넣는다.

    ⚠️ 기대를 낮춰 둔다. 구글의 Organization 지원 속성에 `parentOrganization` 은 **없고**
       `ResearchOrganization` 은 리치결과 타입이 아니다. 이건 순위 요인이 아니라
       *이 이름들이 같은 조직이고 KETI 산하다* 를 밝히는 **디스앰비규에이션**이다 —
       갓 만든 `.work` 도메인이 무관한 datasec 업체들과 섞이지 않게 하는 것이 목적이다.
    ⛔ 주소는 여기 한 곳에만 둔다. 네이버가 사이트 공통 주소를 여러 쪽에 뿌리지 말라고 한다.
    ⛔ 화면에 없는 사실을 넣지 않는다 — 본문과 어긋나는 마크업은 무시되거나 감점이다.
    """
    base = site["site_url"].rstrip("/")
    v = site["visit"]
    d = {
        "@context": "https://schema.org",
        "@type": ["Organization", "ResearchOrganization"],
        "@id": f"{base}/#center",
        "name": site["center_full"][lg],
        "alternateName": [site["center"]["ko"], site["center"]["en"],
                          site["center_full"]["ko"], site["center_full"]["en"], "ADSRC"],
        "url": f"{base}/{lg}/",
        "logo": f"{base}/assets/brand/symbol-1024.png",
        "image": f"{base}/assets/brand/og-image.png",
        "description": site["lede"][lg],
        "telephone": v["phone"],
        "address": {"@type": "PostalAddress", "streetAddress": v["address"][lg],
                    "addressCountry": "KR"},
        "parentOrganization": {
            "@type": "Organization", "name": site["org_name"][lg], "url": site["org_url"],
            "sameAs": ["https://ror.org/039k6f508", "https://www.wikidata.org/wiki/Q30281929"]},
    }
    body = json.dumps(d, ensure_ascii=False, separators=(",", ":"))
    return f'\n<script type="application/ld+json">{body}</script>'


def kicker(text: str, tag: str = "span") -> str:
    """눈금 라벨. ⭐ 절의 제목 노릇을 할 때는 `tag="h2"` 로 — 모양은 `.k` 가 그대로 정한다."""
    return f'<{tag} class="k">{e(text)}</{tag}><hr class="cr">'


def blueprint(inner: str, cls: str = "", style: str = "") -> str:
    attr = ' style="{}"'.format(style) if style else ""
    return ('<div class="blueprint {}"{}>'
            '<i class="corner tl"></i><i class="corner tr"></i>'
            '<i class="corner bl"></i><i class="corner br"></i>'
            '{}</div>').format(cls, attr, inner)


def period(p: dict) -> str:
    return f'<span class="tnum">{e(p["start"])} – {e(p["end"])}</span>'


def tags(p: dict, lg: str) -> str:
    t = T[lg]
    cls = "tag-accent" if p["role"] == "lead" else "tag-neutral"
    out = f'<span class="tag {cls}">{e(t[ROLE_KEY[p["role"]]])}</span>'
    if p.get("new_2026"):
        out += f'<span class="tag tag-outline">{e(t["tag_new"])}</span>'
    return out


# ════════════════════════════════════════════════════════════════════
# 페이지
# ════════════════════════════════════════════════════════════════════

def page_home(lg, site, projects, members, news, stats, detailed):
    t = T[lg]
    active = [p for p in projects if p["status"] != "closed"]
    latest = news[lg][:4]

    if latest:
        items = []
        for i, n in enumerate(latest):
            cls = "" if i == 0 else " ruled"
            badge = f' <span class="tag tag-outline">{e(t["sample_badge"])}</span>' if n["sample"] else ""
            summ = (f'<p class="newssum">{e(n["summary"])}</p>' if n["summary"] else "")
            items.append(
                f'<a class="newsitem{cls}" href="/{lg}/news/{n["slug"]}/">'
                f'<span class="num">{e(n["date"])}</span>'
                f'<span class="newstitle">{e(n["title"])}{badge}</span>{summ}</a>')
        col1 = "".join(items) + (
            f'<a class="btn btn-ghost flush" href="/{lg}/news/">{e(t["all_news"])}</a>')
    else:
        col1 = f'<p class="empty">{e(t["news_empty"])}</p>'

    rows = "".join(
        f'<tr><td class="num">{i:02d}</td><td>'
        f'{project_link(lg, p, detailed, e(p["title"][lg]), "ht rowtitle")}'
        f'<div class="meta">{period(p)} · {e(p["agency_short"][lg])}</div></td></tr>'
        for i, p in enumerate(active[:5], 1))
    col2 = (f'<table class="table fixed"><tbody>{rows}</tbody></table>'
            f'<a class="btn btn-ghost flush" href="/{lg}/research/">'
            f'{e(t["all_projects"])}</a>')

    dl = []
    for key, label in (("address", "주소" if lg == "ko" else "Address"),
                       ("email", "이메일" if lg == "ko" else "Email"),
                       ("phone", "전화" if lg == "ko" else "Phone")):
        v = site.get("contact", {}).get(key)
        if isinstance(v, dict):
            v = v.get(lg)
        if not v:
            continue
        val = mail(v) if key == "email" else e(v)
        dl.append(f'<div class="dl"><span class="dt">{e(label)}</span><span>{val}</span></div>')
    org_link = (f'<div class="dl"><span class="dt">{"소속" if lg == "ko" else "Institute"}</span>'
                f'<span><a href="{e(site["org_url"])}" rel="noopener">{e(site["org_name"][lg])}</a>'
                f' {e(site["org_division"][lg])}</span></div>')
    col3 = (f'<p class="lede-s">{e(site["about"][lg])}</p>'
            f'<div class="dlist">{"".join(dl)}{org_link}</div>'
            + blueprint(
                f'<div class="ht cardtitle">{e(site["cta"]["title"][lg])}</div>'
                f'<p class="cardbody">{e(site["cta"]["body"][lg])}</p>'
                f'<a class="btn btn-secondary btn-block" href="/{lg}/collaborate/">'
                f'{e(site["cta"]["action"][lg])}</a>', style="margin-top:26px;padding:16px"))

    figs = "".join(
        f'<div class="fig"><div class="ht v tnum">{v}</div><div class="figk">{e(t[k])}</div></div>'
        for k, v in (("researchers", stats["members"]), ("active_projects", stats["active"]),
                     ("lead_projects", stats["lead"]), ("new_projects", stats["new"])))

    body = f"""
<div class="masthead">
<h1>{e(site['center_full'][lg])}</h1>
</div>
<div class="herorow">
<div>
<p class="ht hero">{e(site['hero'][lg])}</p>
<p class="lede">{e(site['lede'][lg])}</p>
</div>
<figure class="heroart"><img src="{stamp('/assets/brand/hero.png')}"
 alt="{e(site['hero_alt'][lg])}" width="{HERO_W}" height="{HERO_H}"></figure>
</div>
<div class="figs">{figs}</div>
<div class="threeup">
<section>{kicker(t['k_latest'], 'h2')}{col1}</section>
<section>{kicker(t['k_research'], 'h2')}{col2}</section>
<section>{kicker(t['k_center'], 'h2')}{col3}</section>
</div>
"""
    return shell(lg, "", "", t["nav_home"], site["lede"][lg], body, site,
                 jsonld=org_jsonld(lg, site, stats))


def load_summaries() -> dict[str, dict[str, str]]:
    """`content/projects/<slug>.<lang>.md`. ⭐ **두 언어가 다 있어야** 상세 쪽을 만든다 —
    한쪽만 있으면 언어 전환이 404 로 간다."""
    out: dict[str, dict[str, str]] = {}
    d = ROOT / "content" / "projects"
    if not d.exists():
        return out
    for f in sorted(d.glob("*.md")):
        parts = f.name[:-3].rsplit(".", 1)
        if len(parts) != 2 or parts[1] not in LANGS:
            warn(f"과제 소개 파일 이름이 `<slug>.<lang>.md` 가 아니다: {f.name}")
            continue
        slug, lg = parts
        out.setdefault(slug, {})[lg] = markdown(front_matter(f.read_text(encoding="utf-8"))[1])
    return out


def project_link(lg, p, detailed: set, inner: str, cls: str = "") -> str:
    """소개가 있는 과제만 링크한다. ⚠️ 없으면 **빈 상세 쪽으로 보내지 않는다.**"""
    c = f' class="{cls}"' if cls else ""
    if p["slug"] in detailed:
        return f'<a{c} href="/{lg}/research/{p["slug"]}/">{inner}</a>'
    return f'<span{c}>{inner}</span>'


def person_link(lg, pi, members):
    """담당자 이름 → 구성원 쪽의 그 사람. ⚠️ 명단에 없으면 **이름만** 남긴다 — 링크가 404 가 되느니."""
    m = next((x for x in members if x["name"]["ko"] == pi["ko"]), None)
    if not m:
        return e(pi[lg])
    return f'<a href="/{lg}/people/#{e(m["slug"])}">{e(pi[lg])}</a>'


def page_research(lg, site, projects, members, detailed):
    t = T[lg]
    facets = [("all", t["filter_all"]), ("lead", t[ROLE_KEY["lead"]]),
              ("joint", t[ROLE_KEY["joint"]]), ("contract", t[ROLE_KEY["contract"]]),
              ("new", t["tag_new"])]
    seg = "".join(
        f'<button class="seg-opt{" is-on" if k == "all" else ""}" data-facet="{k}" '
        f'aria-pressed="{"true" if k == "all" else "false"}">{e(v)}</button>' for k, v in facets)
    def haystack(p: dict) -> str:
        # ⚠️ **화면에 보이는 말로 찾을 수 있어야 한다.** 표는 약칭(`해수부`)을 보여 주는데
        #    전체명(`해양수산부`)만 넣어 두면 보이는 대로 쳐도 0건이 나온다. 둘 다 넣는다.
        return " ".join((p["title"][lg], p["agency"][lg], p["agency_short"][lg],
                         p["pi"][lg], T[lg][ROLE_KEY[p["role"]]])).lower()

    rows = "".join(
        f'<tr data-role="{p["role"]}" data-new="{"1" if p.get("new_2026") else "0"}" '
        f'data-q="{e(haystack(p))}">'
        f'<td class="num">{i:02d}</td>'
        f'<td>{project_link(lg, p, detailed, e(p["title"][lg]), "ht rowtitle")}</td>'
        f'<td>{e(p["agency_short"][lg])}</td>'
        f'<td class="tnum">{e(p["start"])} – {e(p["end"])}</td>'
        f'<td>{person_link(lg, p["pi"], members)}</td>'
        f'<td class="tagcell">{tags(p, lg)}</td></tr>'
        for i, p in enumerate(projects, 1))
    body = f"""
<div class="page">
{kicker(t['k_research'])}
<h1 class="ht h-sec">{e(site['research_title'][lg])}</h1>
<div class="filters">
<div class="seg">{seg}</div>
<span class="count" id="count">{e(t['count_projects'].format(n=len(projects)))}</span>
</div>
<div class="tablewrap">
<table class="table fixed listing" id="ptable">
<thead><tr>
<th scope="col" class="c-no">{e(t['no'])}</th>
<th scope="col">{e(t['project'])}</th>
<th scope="col" class="c-fund">{e(t['funder'])}</th>
<th scope="col" class="c-per">{e(t['period'])}</th>
<th scope="col" class="c-pi">{e(t['pi'])}</th>
<th scope="col" class="c-role">{e(t['role'])}</th>
</tr></thead>
<tbody>{rows}</tbody>
</table>
</div>
</div>
<script src="{stamp('/assets/filter.js')}" defer></script>
"""
    return shell(lg, "research/", "research/", T[lg]["nav_research"],
                 site["research_desc"][lg], body, site)


def page_project(lg, site, p, members, summary):
    t = T[lg]
    who = [m for m in members if any(x["slug"] == p["slug"] for x in m["projects"])]
    reg = [
        (t["funder"], e(p["agency"][lg])),
        (t["period"], f'<span class="tnum">{e(p["start"])} – {e(p["end"])}</span>'),
        (t["role"], e(t[ROLE_KEY[p["role"]]])),
        (t["pi"], person_link(lg, p["pi"], members)),
        (t["members_n"], f'<span class="tnum">{len(who)}</span>' if who else "—"),
        (t["status"], f'<span class="tag {"tag-accent" if p["status"] == "active" else "tag-neutral"}">'
                      f'{e(t[STATUS_KEY[p["status"]]])}</span>'),
    ]
    regrows = "".join(f'<div class="dl reg"><span class="dt">{e(k)}</span><span>{v}</span></div>'
                      for k, v in reg)
    people = "".join(
        f'<a class="chip" href="/{lg}/people/#{m["slug"]}">{e(m["name"][lg])}</a>' for m in who)
    left = (f'<h1 class="ht h-proj">{e(p["title"][lg])}</h1>'
            + (f'<div class="prose">{summary}</div>' if summary
               else f'<p class="lede-m muted">{e(t["summary_missing"])}</p>'))
    right = (blueprint(f'<div class="reg-inner">{kicker(t["register"])}{regrows}</div>',
                       style="padding:16px")
             + (f'<div class="chips">{people}</div>' if people else ""))
    body = f"""
<div class="page">
<a class="back" href="/{lg}/research/">{e(t['back_research'])}</a>
{blueprint(
    f'<span class="tb tb-title">{e(p["title"][lg])}</span>'
    f'<span class="tb">{e(p["agency_short"][lg])}</span>'
    f'<span class="tb">{e(t[ROLE_KEY[p["role"]]])}</span>'
    f'<span class="tb tnum">{e(p["start"])} – {e(p["end"])}</span>',
    cls="titleblock", style="margin-top:22px")}
<div class="twoup">
<div>{left}</div>
<div>{right}</div>
</div>
</div>
"""
    return shell(lg, "research/", f'research/{p["slug"]}/', p["title"][lg],
                 p["title"][lg], body, site)


def page_people(lg, site, members, projects, detailed):
    t = T[lg]
    by_slug = {p["slug"]: p for p in projects}
    # ⭐ 과제가 붙은 사람과 명단만 있는 사람을 나눈다 — 한 형식에 다 넣으면 빈 행만 길게 남는다.
    detailed = [m for m in members if m["projects"]]
    listed = [m for m in members if not m["projects"]]
    cards = []
    for m in detailed:
        own = [x for x in m["projects"] if x["role"] == "lead"]
        rows = "".join(
            f'<div class="pl"><span class="rl {"own" if x["role"] == "lead" else "join"}">'
            f'{e(t["own"] if x["role"] == "lead" else t["join"])}</span>'
            f'{project_link(lg, by_slug[x["slug"]], detailed, e(by_slug[x["slug"]]["title"][lg]))}</div>'
            for x in sorted(m["projects"], key=lambda y: (y["role"] != "lead",
                                                          by_slug[y["slug"]]["title"][lg])))
        if not rows:
            rows = f'<div class="pl none">{e(t["no_projects"])}</div>'
        ext = ""     # 「부서 외 과제 N건 참여」는 싣지 않는다
        role = m["org_role"][lg]
        badge = f'<div class="orgrole">{e(role)}</div>' if role else ""
        links = "".join(
            f'<a class="ext" href="{e(u)}" rel="noopener" target="_blank" '
            f'title="{e(ICON_LABEL[k][lg])}" aria-label="{e(ICON_LABEL[k][lg])}">{icon(k)}</a>'
            for k, u in (m.get("links") or {}).items() if k in ICONS)
        linkbar = f'<div class="exts">{links}</div>' if links else ""
        photo = ""
        if m.get("photo"):
            pw, ph = img_size(f"assets/people/{m['photo']}")
            photo = blueprint(
                f'<img src="/assets/people/{e(m["photo"])}" alt="" loading="lazy" '
                f'width="{pw}" height="{ph}">', cls="duotone portrait")
        unit = "건" if lg == "ko" else ""
        lead_note = " · {} {}".format(t["own"], len(own)) if own else ""
        cards.append(
            f'<article class="person" id="{e(m["slug"])}">'
            f'<div class="pid">'
            f'<div class="pidtext">{badge}<h2 class="ht nm">{e(m["name"][lg])}</h2>'
            f'<div class="rk">{e(m["grade"][lg])}</div>'
            f'<div class="ct tnum">{len(m["projects"])}{unit}{e(lead_note)}</div>'
            f'{linkbar}</div>{photo}</div>'
            f'<div class="plist">{rows}{ext}</div></article>')
    roster = ""
    if listed:
        items = "".join(
            f'<div class="sl" id="{e(m["slug"])}">'
            f'<h2 class="ht nm-s">{e(m["name"][lg])}</h2>'
            f'<span class="rk-s">{e(m["grade"][lg])}</span></div>' for m in listed)
        roster = (f'<div class="rosterhead">{kicker(t["k_roster"])}</div>'
                  f'<div class="stafflist">{items}</div>')

    body = f"""
<div class="page">
{kicker(t['k_people'])}
<h1 class="ht h-sec">{e(site['people_title'][lg])}</h1>
<div class="filters">
<span class="count">{e(t['count_people'].format(n=len(members)))}</span>
</div>
<div class="people">{"".join(cards)}</div>
{roster}
</div>
"""
    return shell(lg, "people/", "people/", t["nav_people"], site["people_desc"][lg], body, site)


def page_news_index(lg, site, news):
    t = T[lg]
    items = news[lg]
    if items:
        parts = []
        for n in items:
            badge = (f' <span class="tag tag-outline">{e(t["sample_badge"])}</span>'
                     if n["sample"] else "")
            summ = f'<p class="newssum">{e(n["summary"])}</p>' if n["summary"] else ""
            parts.append(
                f'<a class="newsitem ruled" href="/{lg}/news/{n["slug"]}/">'
                f'<span class="num">{e(n["date"])}</span>'
                f'<span class="newstitle">{e(n["title"])}{badge}</span>{summ}</a>')
        inner = "".join(parts)
    else:
        inner = f'<p class="empty">{e(t["news_empty"])}</p>'
    body = f"""
<div class="page">
{kicker(t['k_news'])}
<h1 class="ht h-sec">{e(site['news_title'][lg])}</h1>
<p class="lede-m">{e(site['news_lede'][lg])}</p>
<div class="newslist">{inner}</div>
</div>
"""
    return shell(lg, "news/", "news/", t["nav_news"], site["news_lede"][lg], body, site)


def page_news_post(lg, site, n):
    t = T[lg]
    note = (f'<p class="samplenote">{e(t["sample_note"])}</p>' if n["sample"] else "")
    body = f"""
<div class="page narrow">
<a class="back" href="/{lg}/news/">{e(t['back_news'])}</a>
<div class="num postdate">{e(n['date'])}</div>
<h1 class="ht h-proj">{e(n['title'])}</h1>
{note}
<div class="prose">{n['body']}</div>
</div>
"""
    return shell(lg, "news/", f'news/{n["slug"]}/', n["title"],
                 n["summary"] or n["title"], body, site, og_type="article",
                 head_extra=f'\n<meta property="article:published_time" content="{e(n["date"])}">')


def page_collaborate(lg, site):
    t = T[lg]
    ways = "".join(
        blueprint(f'<h2 class="ht cardtitle">{e(w["title"][lg])}</h2>'
                  f'<p class="cardbody">{e(w["body"][lg])}</p>', cls="way")
        for w in site["collaborate"]["ways"])
    email = site.get("contact", {}).get("email", "")
    if email:
        contact = mail(email, cls="btn btn-primary")
    else:
        contact = f'<p class="empty">{e(site["collaborate"]["no_contact"][lg])}</p>'
    body = f"""
<div class="page narrow">
{kicker(t['k_collab'])}
<h1 class="ht h-sec">{e(site['collaborate']['title'][lg])}</h1>
<div class="ways">{ways}</div>
<section id="contact" class="contact">
{kicker(t['contact'])}
<p class="lede-m">{e(site['collaborate']['contact_lede'][lg])}</p>
{contact}
<p class="asof"><a href="{e(site['org_url'])}" rel="noopener">{e(site['org_name'][lg])}</a>
{e(site['org_division'][lg])}</p>
</section>
</div>
"""
    return shell(lg, "collaborate/", "collaborate/", t["nav_collab"],
                 site["collaborate"]["lede"][lg], body, site)


def page_visit(lg, site):
    t = T[lg]
    v = site["visit"]
    # 지도는 주소 바로 아래의 **작은 링크**다 — 큰 버튼을 하나 더 두면 문의 버튼과 경쟁한다.
    maplink = (f'<a class="maplink" href="{e(v["map_url"])}" rel="noopener" target="_blank">'
               f'{e(v["map_label"][lg])} ↗</a>')
    rows = [(t["addr"], f'{e(v["org_line"][lg])}<br>{e(v["address"][lg])}<br>{maplink}')]
    if v.get("phone"):
        tel = "+82" + re.sub(r"\D", "", v["phone"].split(")", 1)[-1])
        rows.append((t["phone"],
                     f'<a class="tnum" href="tel:{e(tel)}">{e(v["phone"])}</a>'))
    dl = "".join(f'<div class="dl reg"><span class="dt">{e(k)}</span><span>{val}</span></div>'
                 for k, val in rows)
    cards = "".join(
        blueprint(f'<h2 class="ht cardtitle">{e(n["title"][lg])}</h2>'
                  f'<p class="cardbody">{e(n["body"][lg])}</p>', cls="way")
        for n in v.get("notes", []) if n["body"][lg].strip())
    body = f"""
<div class="page narrow">
{kicker(t['k_visit'])}
<h1 class="ht h-sec">{e(v['title'][lg])}</h1>
<div class="visitbox">
{blueprint(f'<div class="reg-inner">{dl}</div>', style="padding:18px")}
</div>
{f'<div class="ways">{cards}</div>' if cards else ''}
</div>
"""
    return shell(lg, "visit/", "visit/", v["title"][lg], v["address"][lg], body, site)


# ════════════════════════════════════════════════════════════════════
# 조립
# ════════════════════════════════════════════════════════════════════

def write(path: str, text: str) -> None:
    p = OUT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true",
                    help="공개 차단 사유가 하나라도 있으면 실패한다 (배포 전 필수)")
    ap.add_argument("--today", default=None, help="YYYY-MM-DD — 상태 판정 기준일")
    args = ap.parse_args()
    today = dt.date.fromisoformat(args.today) if args.today else dt.date.today()

    site = load_json("content/site.json")
    projects = load_json("data/projects.json")
    members = load_json("data/members.json")
    news = load_news()
    if BLOCKERS:
        for b in BLOCKERS:
            print(f"⛔ {b}", file=sys.stderr)
        return 1

    # ⚠️ 오타 검사는 **거르기 전에** 한다 — 거른 뒤에 하면 미공개 과제를 가리키는 참조가
    #    "없는 과제"로 잘못 잡힌다.
    all_slugs = {p["slug"] for p in projects}
    for m in members:
        for x in m["projects"]:
            if x["slug"] not in all_slugs:
                block(f"구성원 {m['slug']} 이 없는 과제를 가리킨다: {x['slug']}")
        if not m.get("name_en_confirmed"):
            block(f"영문 이름이 확인되지 않았다: {m['name']['ko']} → \"{m['name']['en']}\" "
                  f"(data/members.json 의 name_en_confirmed 를 true 로 바꾸기 전에는 공개 금지)")

    # ⭐ `publish: false` 는 **지우는 것이 아니라 표시하는 것**이다. 지우면 정본 대조
    #    (`tools/pull_from_sot.py`)가 매번 "새 과제"로 다시 올린다 — 결정이 기록으로 남아야 한다.
    withheld = [p for p in projects if not p.get("publish", True)]
    projects = [p for p in projects if p.get("publish", True)]
    published = {p["slug"] for p in projects}
    for m in members:
        had = len(m["projects"])
        m["projects"] = [x for x in m["projects"] if x["slug"] in published]
        # ⚠️ 애초에 과제가 없는 사람(명단만 있는 구성원)은 정상이다.
        #    **있던 것이 전부 미공개로 걸러진 경우**만 알린다.
        if had and not m["projects"]:
            warn(f"구성원 {m['slug']} 의 과제가 전부 미공개로 걸러졌다 — 이름만 나간다")
    if withheld:
        warn(f"공개하지 않는 과제 {len(withheld)}건: "
             + " · ".join(f"{p['slug']}({p.get('withheld', '사유 없음')})" for p in withheld))

    for p in projects:
        p["status"] = status_of(p, today)
    order = {"lead": 0, "joint": 1, "contract": 2}
    projects.sort(key=lambda p: (p["status"] == "closed", not p.get("new_2026"),
                                 order[p["role"]], p["start"]))
    pis = {p["pi"]["ko"] for p in projects}
    known = {m["name"]["ko"] for m in members}
    for x in sorted(pis - known):
        warn(f"책임자 `{x}` 가 구성원 명단에 없다 — 이름만 표시된다")
    for lg in LANGS:
        for n in news[lg]:
            if n["sample"]:
                block(f"예시 뉴스가 남아 있다: content/news/{n['slug']}.{lg}.md")
    if not site.get("contact", {}).get("email"):
        warn("연락처 이메일이 비어 있다 — 협력 페이지에 문의 수단이 안 나간다 "
             "(content/site.json 의 contact.email)")

    stats = {
        # ⚠️ 「연구인력」이라 적히는 숫자다 — 행정 인력은 빼야 라벨이 참이 된다.
        "members": sum(1 for m in members if not m.get("admin")),
        "active": sum(1 for p in projects if p["status"] != "closed"),
        "lead": sum(1 for p in projects if p["role"] == "lead"),
        "new": sum(1 for p in projects if p.get("new_2026")),
    }

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    summaries = load_summaries()
    # ⭐ 소개가 **두 언어 다** 있는 과제만 상세 쪽을 갖는다. 나머지는 링크도 걸지 않는다 —
    #    빈 쪽으로 보내지 않고, sitemap 에도 넣지 않는다.
    detailed = {p["slug"] for p in projects
                if all(summaries.get(p["slug"], {}).get(x) for x in LANGS)}
    partial = [s for s in summaries if s not in detailed and any(summaries[s].values())]
    for s in partial:
        warn(f"과제 소개가 한 언어에만 있다: {s} — 두 언어가 다 있어야 상세 쪽이 생긴다")
    if len(detailed) < len(projects):
        warn(f"상세 쪽이 없는 과제 {len(projects) - len(detailed)}건 — 목록에서 링크가 걸리지 않는다. "
             f"content/projects/<slug>.ko.md 와 .en.md 를 만들면 생긴다")

    for lg in LANGS:
        write(f"{lg}/index.html", page_home(lg, site, projects, members, news, stats, detailed))
        write(f"{lg}/research/index.html", page_research(lg, site, projects, members, detailed))
        write(f"{lg}/people/index.html", page_people(lg, site, members, projects, detailed))
        write(f"{lg}/news/index.html", page_news_index(lg, site, news))
        write(f"{lg}/collaborate/index.html", page_collaborate(lg, site))
        write(f"{lg}/visit/index.html", page_visit(lg, site))
        for p in projects:
            if p["slug"] not in detailed:
                continue
            write(f"{lg}/research/{p['slug']}/index.html",
                  page_project(lg, site, p, members, summaries[p["slug"]][lg]))
        for n in news[lg]:
            write(f"{lg}/news/{n['slug']}/index.html", page_news_post(lg, site, n))

    shutil.copytree(ROOT / "assets", OUT / "assets")
    # ⛔ 검색엔진 소유확인 파일은 **여기** 둔다. `docs/` 루트에 직접 두면 다음 빌드의
    #    `shutil.rmtree(OUT)` 가 조용히 지우고, 소유확인이 에러 없이 끊긴다.
    #    ⚠️ 네이버 소유확인은 만료가 있다(1년, 30일 전 알림) — 파일을 지우면 안 된다.
    vdir = ROOT / "content" / "verify"
    if vdir.exists():
        for f in sorted(vdir.iterdir()):
            if f.is_file() and not f.name.startswith(".") and f.name != "README.md":
                shutil.copy2(f, OUT / f.name)
    # ⭐ 도메인은 `content/site.json` 의 `site_url` 하나에서 온다 — 여섯 군데에 박아 두면
    #    도메인을 바꿀 때 한 군데를 반드시 빠뜨린다(그리고 에러는 안 난다).
    base = site["site_url"].rstrip("/")
    host = base.split("://", 1)[-1].strip("/")
    write("CNAME", host + "\n")
    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    write("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {base}/sitemap.xml\n")

    # ⚠️ `lastmod` 는 **결정적인 값**이어야 한다. `datetime.now()` 나 파일 mtime 을 쓰면
    #    실행마다 결과가 달라져 CI 의 「docs/ 가 원본과 같은가」 검사가 즉시 깨진다.
    #    커밋된 값만 쓴다 — 데이터 파생 쪽은 `data/meta.json` 의 asof, 소식은 그 글의 date.
    asof = json.loads((ROOT / "data" / "meta.json").read_text(encoding="utf-8")).get("asof", "")
    urls: list[tuple[str, str]] = []
    for lg in LANGS:
        urls += [(f"/{lg}/{s}", asof) for s in
                 ("", "research/", "people/", "news/", "collaborate/", "visit/")]
        urls += [(f"/{lg}/research/{p['slug']}/", asof)
                 for p in projects if p["slug"] in detailed]
        urls += [(f"/{lg}/news/{n['slug']}/", n["date"]) for n in news[lg]]
    write("sitemap.xml",
          '<?xml version="1.0" encoding="UTF-8"?>\n'
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
          + "".join(f"<url><loc>{base}{u}</loc>"
                    + (f"<lastmod>{d}</lastmod>" if d else "") + "</url>\n"
                    for u, d in urls)
          + "</urlset>\n")

    write("index.html", f"""<!doctype html>
<html lang="{DEFAULT_LANG}">
<head><meta charset="utf-8">
<title>{e(site['center'][DEFAULT_LANG])}</title>
<link rel="canonical" href="{base}/{DEFAULT_LANG}/">
<meta http-equiv="refresh" content="0; url=/{DEFAULT_LANG}/">
<script>
// 브라우저 언어가 한국어가 아니면 영문판으로 보낸다. 스크립트가 없으면 위 refresh 가 받는다.
location.replace((navigator.language||"ko").toLowerCase().startsWith("ko") ? "/ko/" : "/en/");
</script></head>
<body><p><a href="/{DEFAULT_LANG}/">{e(site['center'][DEFAULT_LANG])}</a></p></body></html>
""")
    write("404.html", f"""<!doctype html>
<html lang="{DEFAULT_LANG}"><head><meta charset="utf-8"><title>404</title>
<link rel="stylesheet" href="/assets/industry.css"><link rel="stylesheet" href="/assets/site.css">
</head><body data-lang="ko"><main id="main"><div class="page narrow">
<h1 class="ht h-sec">404</h1>
<p class="lede-m">요청하신 쪽을 찾을 수 없습니다. / The page you asked for is not here.</p>
<p><a href="/ko/">한국어</a> · <a href="/en/">English</a></p>
</div></main></body></html>
""")

    # ⛔ **메일 주소가 평문으로 새어 나갔는지 산출물에서 확인한다.** `mail()` 을 한 군데라도
    #    안 거치면 그 쪽만 조용히 수집 대상이 된다 — 실제로 홈의 「이메일」 줄을 놓쳤었다.
    # ⛔ **센터명의 가운뎃점.** 정식 표기는 `인공지능데이터·보안연구센터` 다.
    #    점 없는 표기가 섞이면 같은 조직이 두 이름으로 검색엔진에 잡히고, 문서마다 달라진다.
    #    ⚠️ 사람이 지킬 규약으로 두면 반드시 다시 섞인다 — 산출물에서 직접 막는다.
    for f in OUT.rglob("*.html"):
        if "인공지능데이터보안" in f.read_text(encoding="utf-8"):
            block(f"센터명에 가운뎃점이 빠졌다: {f.relative_to(OUT)} — "
                  f"「인공지능데이터·보안연구센터」가 정식 표기다")

    # ⚠️ 일반 정규식으로 훑으면 `logo@2x.png` 같은 srcset 이 걸린다 — **지키려는 주소**만 본다.
    addr = site.get("contact", {}).get("email", "")
    for f in OUT.rglob("*.html"):
        text = f.read_text(encoding="utf-8")
        if "mailto:" in text:
            block(f"평문 mailto: 가 남았다: {f.relative_to(OUT)} — mail() 을 거쳐라")
        if addr and addr in text:
            block(f"평문 메일 주소가 남았다: {f.relative_to(OUT)} — mail() 을 거쳐라")

    # ⛔ **미공개 과제가 새어 나갔는지 산출물에서 직접 확인한다.** 걸러 냈다고 믿지 않는다 —
    #    뉴스 글이나 과제 소개문이 제목·slug 를 그대로 적어 두면 거르기를 통과한다.
    if withheld:
        needles = {n for p in withheld
                   for n in (p["slug"], p["title"]["ko"], p["title"]["en"]) if n}
        for f in OUT.rglob("*.html"):
            text = f.read_text(encoding="utf-8")
            for n in needles:
                if n in text:
                    block(f"미공개 과제가 산출물에 실렸다: {f.relative_to(OUT)} ← \"{n[:40]}…\"")

    # ⛔ **canonical 이 자기 주소를 가리키는지 확인한다.** 목록 쪽 주소를 넘기면 그 쪽은
    #    색인이 불가능해진다 — 구글은 canonical 을 따른다. 실제로 소식 상세 4쪽이 그랬다.
    #    ⚠️ 예외 둘: 루트(`/`)는 기본 언어를 가리키고, 404 는 canonical 이 없다.
    for f in OUT.rglob("*.html"):
        rel = f.relative_to(OUT)
        if rel.as_posix() in ("index.html", "404.html"):
            continue
        want = f"{base}/{rel.parent.as_posix()}/".replace("/./", "/")
        m = re.search(r'<link rel="canonical" href="([^"]+)"', f.read_text(encoding="utf-8"))
        if not m:
            block(f"canonical 이 없다: {rel}")
        elif m.group(1) != want:
            block(f"canonical 이 자기 주소가 아니다: {rel}\n"
                  f"      있는 값 {m.group(1)}\n      있어야 할 값 {want}")

    n_pages = sum(1 for _ in OUT.rglob("*.html"))
    print(f"✅ {n_pages}쪽 · 과제 {len(projects)} · 구성원 {len(members)} · "
          f"소식 {len(news['ko'])}/{len(news['en'])} → {OUT.relative_to(ROOT)}/")
    for w in WARNINGS:
        print(f"⚠️  {w}")
    for b in BLOCKERS:
        print(f"⛔ {b}")
    if BLOCKERS and args.strict:
        print("\n⛔ --strict: 위 사유가 남아 있는 동안 공개하지 않는다.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
