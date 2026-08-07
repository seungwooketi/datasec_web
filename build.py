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
        "nav_news": "소식", "nav_collab": "협력", "contact": "문의하기",
        "skip": "본문으로 건너뛰기",
        "k_latest": "01 · 새소식", "k_research": "02 · 연구 과제", "k_center": "03 · 센터 안내",
        "k_people": "03 · 구성원", "k_news": "01 · 새소식", "k_collab": "04 · 협력",
        "all_projects": "연구 과제 목록 →", "all_news": "지난 소식 →",
        "researchers": "연구인력", "active_projects": "수행중 과제",
        "lead_projects": "주관 과제", "new_projects": "26년 신규",
        "project": "과제명", "period": "수행기간", "funder": "지원기관",
        "role": "참여형태", "status": "상태", "pi": "책임자", "no": "번호",
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
        "nav_news": "News", "nav_collab": "Collaborate", "contact": "Contact",
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
        "role_lead": "Lead", "role_joint": "Joint", "role_contract": "Contract",
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
    for slug, langs in seen.items():
        missing = set(LANGS) - langs
        if missing:
            warn(f"뉴스 `{slug}` 에 {'/'.join(sorted(missing))} 판이 없다 — 그 언어에서는 안 보인다")
    for lg in LANGS:
        news[lg].sort(key=lambda x: x["date"], reverse=True)
    return news


# ════════════════════════════════════════════════════════════════════
# 껍데기
# ════════════════════════════════════════════════════════════════════

def e(s) -> str:
    return html.escape(str(s if s is not None else ""), quote=True)


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
        ("news/", "nav_news"), ("collaborate/", "nav_collab")]


def shell(lg: str, here: str, title: str, desc: str, body: str, site: dict) -> str:
    t = T[lg]
    CUR = ' aria-current="page"'
    nav = "".join(
        '<a href="/{}/{}"{}>{}</a>'.format(lg, path, CUR if path == here else "", e(t[key]))
        for path, key in NAVS)
    def opt(code: str, label: str) -> str:
        on = code == lg
        return ('<a class="seg-opt{}" hreflang="{}" href="/{}/{}"{}>{}</a>'
                .format(" is-on" if on else "", code, code, here,
                        ' aria-current="true"' if on else "", label))
    seg = ('<div class="seg langseg" role="group" aria-label="{}">{}{}</div>'
           .format(e(t["lang_switch"]), opt("en", "EN"), opt("ko", "한국어")))
    center = site["center"][lg]
    email = site.get("contact", {}).get("email", "")
    foot_mid = f'<a href="mailto:{e(email)}">{e(email)}</a>' if email else e(site["org_url_label"])
    base = site["site_url"].rstrip("/")
    canonical = f"{base}/{lg}/{here}"
    return f"""<!doctype html>
<html lang="{lg}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)} — {e(center)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{e(canonical)}">
<link rel="alternate" hreflang="ko" href="{base}/ko/{here}">
<link rel="alternate" hreflang="en" href="{base}/en/{here}">
<link rel="alternate" hreflang="x-default" href="{base}/{DEFAULT_LANG}/{here}">
<meta property="og:title" content="{e(title)} — {e(center)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{e(canonical)}">
<meta property="og:locale" content="{'ko_KR' if lg == 'ko' else 'en_US'}">
<meta property="og:image" content="{base}/assets/brand/hero.jpg">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" type="image/png" sizes="32x32" href="{stamp('/assets/brand/favicon-32.png')}">
<link rel="icon" type="image/png" sizes="512x512" href="{stamp('/assets/brand/favicon-512.png')}">
<link rel="apple-touch-icon" href="{stamp('/assets/brand/favicon-180.png')}">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow:wght@400;500;600;700&family=Barlow+Condensed:wght@400;600;700&family=IBM+Plex+Sans+KR:wght@400;500;600;700&display=swap">
<link rel="stylesheet" href="{stamp('/assets/industry.css')}">
<link rel="stylesheet" href="{stamp('/assets/site.css')}">
</head>
<body data-lang="{lg}">
<a class="skip" href="#main">{e(t['skip'])}</a>
<nav class="nav">
<a href="/{lg}/" class="nav-brand"><img src="{stamp('/assets/brand/mark.png')}"
 srcset="{stamp('/assets/brand/mark@2x.png')} 2x" alt="" width="137" height="128">AIDSRC</a>
<div class="navlinks">{nav}</div>
{seg}
<a class="btn btn-primary" href="/{lg}/collaborate/#contact">{e(t['contact'])}</a>
</nav>
<main id="main">
{body}
</main>
<footer>
<span class="footlogo"><img src="{stamp('/assets/brand/logo.png')}"
 srcset="{stamp('/assets/brand/logo@2x.png')} 2x" alt="{e(center)}" width="324" height="128"></span>
<span>{foot_mid}</span>
<span>{e(site['location'][lg])}</span>
</footer>
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


def kicker(text: str) -> str:
    return f'<span class="k">{e(text)}</span><hr class="cr">'


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

def page_home(lg, site, projects, members, news, stats):
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
        f'<a class="ht rowtitle" href="/{lg}/research/{p["slug"]}/">{e(p["title"][lg])}</a>'
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
        val = f'<a href="mailto:{e(v)}">{e(v)}</a>' if key == "email" else e(v)
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
<span>{e(site['center'][lg])}</span>
</div>
<div class="herorow">
<div>
<h1 class="ht hero">{e(site['hero'][lg])}</h1>
<p class="lede">{e(site['lede'][lg])}</p>
</div>
{blueprint('<img src="' + stamp('/assets/brand/hero.jpg') + '" alt="" width="900" height="900">',
           cls="heroart")}
</div>
<div class="figs">{figs}</div>
<div class="threeup">
<section>{kicker(t['k_latest'])}{col1}</section>
<section>{kicker(t['k_research'])}{col2}</section>
<section>{kicker(t['k_center'])}{col3}</section>
</div>
"""
    return shell(lg, "", t["nav_home"], site["lede"][lg], body, site)


def page_research(lg, site, projects):
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
        f'<td><a class="ht rowtitle" href="/{lg}/research/{p["slug"]}/">{e(p["title"][lg])}</a></td>'
        f'<td>{e(p["agency_short"][lg])}</td>'
        f'<td class="tnum">{e(p["start"])} – {e(p["end"])}</td>'
        f'<td>{e(p["pi"][lg])}</td>'
        f'<td class="tagcell">{tags(p, lg)}</td></tr>'
        for i, p in enumerate(projects, 1))
    body = f"""
<div class="page">
{kicker(t['k_research'])}
<h1 class="ht h-sec">{e(site['research_title'][lg])}</h1>
<div class="filters">
<input class="input" type="search" id="q" placeholder="{e(t['search_projects'])}"
       aria-label="{e(t['search_projects'])}">
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
    return shell(lg, "research/", T[lg]["nav_research"], site["research_desc"][lg], body, site)


def page_project(lg, site, p, members, summary):
    t = T[lg]
    who = [m for m in members if any(x["slug"] == p["slug"] for x in m["projects"])]
    reg = [
        (t["funder"], e(p["agency"][lg])),
        (t["period"], f'<span class="tnum">{e(p["start"])} – {e(p["end"])}</span>'),
        (t["role"], e(t[ROLE_KEY[p["role"]]])),
        (t["pi"], e(p["pi"][lg])),
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
    return shell(lg, "research/", p["title"][lg], p["title"][lg], body, site)


def page_people(lg, site, members, projects):
    t = T[lg]
    by_slug = {p["slug"]: p for p in projects}
    cards = []
    for m in members:
        own = [x for x in m["projects"] if x["role"] == "lead"]
        rows = "".join(
            f'<div class="pl"><span class="rl {"own" if x["role"] == "lead" else "join"}">'
            f'{e(t["own"] if x["role"] == "lead" else t["join"])}</span>'
            f'<a href="/{lg}/research/{x["slug"]}/">{e(by_slug[x["slug"]]["title"][lg])}</a></div>'
            for x in sorted(m["projects"], key=lambda y: (y["role"] != "lead",
                                                          by_slug[y["slug"]]["title"][lg])))
        if not rows:
            rows = f'<div class="pl none">{e(t["no_projects"])}</div>'
        ext = (f'<div class="extnote">{e(t["ext_n"].format(n=m["external_count"]))}</div>'
               if m.get("external_count") else "")
        role = m["org_role"][lg]
        badge = f'<div class="orgrole">{e(role)}</div>' if role else ""
        links = "".join(
            f'<a class="ext" href="{e(u)}" rel="noopener" target="_blank" '
            f'title="{e(ICON_LABEL[k][lg])}" aria-label="{e(ICON_LABEL[k][lg])}">{icon(k)}</a>'
            for k, u in (m.get("links") or {}).items() if k in ICONS)
        linkbar = f'<div class="exts">{links}</div>' if links else ""
        photo = ""
        if m.get("photo"):
            photo = blueprint(
                f'<img src="/assets/people/{e(m["photo"])}" alt="" loading="lazy">',
                cls="duotone portrait")
        unit = "건" if lg == "ko" else ""
        lead_note = " · {} {}".format(t["own"], len(own)) if own else ""
        cards.append(
            f'<article class="person" id="{e(m["slug"])}">'
            f'<div class="pid">{photo}{badge}<div class="ht nm">{e(m["name"][lg])}</div>'
            f'<div class="rk">{e(m["grade"][lg])}</div>'
            f'<div class="ct tnum">{len(m["projects"])}{unit}{e(lead_note)}</div>'
            f'{linkbar}</div>'
            f'<div class="plist">{rows}{ext}</div></article>')
    body = f"""
<div class="page">
{kicker(t['k_people'])}
<h1 class="ht h-sec">{e(site['people_title'][lg])}</h1>
<div class="filters">
<input class="input" type="search" id="q" placeholder="{e(t['search_people'])}"
       aria-label="{e(t['search_people'])}">
<span class="count" id="count">{e(t['count_people'].format(n=len(members)))}</span>
</div>
<div class="people">{"".join(cards)}</div>
</div>
<script src="{stamp('/assets/filter.js')}" defer></script>
"""
    return shell(lg, "people/", t["nav_people"], site["people_desc"][lg], body, site)


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
    return shell(lg, "news/", t["nav_news"], site["news_lede"][lg], body, site)


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
    return shell(lg, "news/", n["title"], n["summary"] or n["title"], body, site)


def page_collaborate(lg, site, stats):
    t = T[lg]
    ways = "".join(
        blueprint(f'<div class="ht cardtitle">{e(w["title"][lg])}</div>'
                  f'<p class="cardbody">{e(w["body"][lg])}</p>', cls="way")
        for w in site["collaborate"]["ways"])
    email = site.get("contact", {}).get("email", "")
    if email:
        contact = (f'<a class="btn btn-primary" href="mailto:{e(email)}">{e(email)}</a>')
    else:
        contact = f'<p class="empty">{e(site["collaborate"]["no_contact"][lg])}</p>'
    body = f"""
<div class="page narrow">
{kicker(t['k_collab'])}
<h1 class="ht h-sec">{e(site['collaborate']['title'][lg])}</h1>
<p class="lede-m">{e(site['collaborate']['lede'][lg])}</p>
<div class="ways">{ways}</div>
<section id="contact" class="contact">
{kicker(t['contact'])}
<p class="lede-m">{e(site['collaborate']['contact_lede'][lg])}</p>
{contact}
<p class="asof"><a href="{e(site['org_url'])}" rel="noopener">{e(site['org_name'][lg])}</a>
{e(site['org_division'][lg])} · {e(site['location'][lg])}</p>
</section>
</div>
"""
    return shell(lg, "collaborate/", t["nav_collab"],
                 site["collaborate"]["lede"][lg], body, site)


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
        m["projects"] = [x for x in m["projects"] if x["slug"] in published]
    for m in members:
        if not m["projects"]:
            warn(f"구성원 {m['slug']} 에게 공개할 과제가 하나도 없다 — 「없음」으로 나간다")
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
        "members": len(members),
        "active": sum(1 for p in projects if p["status"] != "closed"),
        "lead": sum(1 for p in projects if p["role"] == "lead"),
        "new": sum(1 for p in projects if p.get("new_2026")),
    }

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    missing_summary: list[str] = []
    for lg in LANGS:
        write(f"{lg}/index.html", page_home(lg, site, projects, members, news, stats))
        write(f"{lg}/research/index.html", page_research(lg, site, projects))
        write(f"{lg}/people/index.html", page_people(lg, site, members, projects))
        write(f"{lg}/news/index.html", page_news_index(lg, site, news))
        write(f"{lg}/collaborate/index.html", page_collaborate(lg, site, stats))
        for p in projects:
            f = ROOT / "content" / "projects" / f"{p['slug']}.{lg}.md"
            if f.exists():
                summary = markdown(front_matter(f.read_text(encoding="utf-8"))[1])
            else:
                summary = ""
                missing_summary.append(f"{p['slug']}.{lg}")
            write(f"{lg}/research/{p['slug']}/index.html",
                  page_project(lg, site, p, members, summary))
        for n in news[lg]:
            write(f"{lg}/news/{n['slug']}/index.html", page_news_post(lg, site, n))

    if missing_summary:
        warn(f"과제 소개가 없는 쪽 {len(missing_summary)}개 — 상세 쪽은 「준비 중」으로 나간다. "
             f"채우려면 content/projects/<slug>.<lang>.md 를 만든다 "
             f"(예: {missing_summary[0]}.md)")

    shutil.copytree(ROOT / "assets", OUT / "assets")
    # ⭐ 도메인은 `content/site.json` 의 `site_url` 하나에서 온다 — 여섯 군데에 박아 두면
    #    도메인을 바꿀 때 한 군데를 반드시 빠뜨린다(그리고 에러는 안 난다).
    base = site["site_url"].rstrip("/")
    host = base.split("://", 1)[-1].strip("/")
    write("CNAME", host + "\n")
    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    write("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {base}/sitemap.xml\n")

    urls = []
    for lg in LANGS:
        urls += [f"/{lg}/", f"/{lg}/research/", f"/{lg}/people/", f"/{lg}/news/",
                 f"/{lg}/collaborate/"]
        urls += [f"/{lg}/research/{p['slug']}/" for p in projects]
        urls += [f"/{lg}/news/{n['slug']}/" for n in news[lg]]
    write("sitemap.xml",
          '<?xml version="1.0" encoding="UTF-8"?>\n'
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
          + "".join(f"<url><loc>{base}{u}</loc></url>\n" for u in urls)
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
