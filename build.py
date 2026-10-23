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
        # ── 메뉴 라벨. ⚠️ <title> 은 title_* 를 쓴다 — 메뉴 라벨만 바꾸면 검색결과 제목이 조용히 바뀐다.
        "nav_topics": "연구", "nav_projects": "과제", "nav_insights": "인사이트",
        "nav_news": "소식", "nav_people": "구성원", "nav_collab": "협력",
        "title_projects": "과제", "title_insights": "인사이트", "title_news": "소식",
        "title_people": "구성원", "title_collab": "협력, 찾아오시는 길",
        "crumb_home": "홈", "crumbs": "경로",
        "contact": "문의하기", "skip": "본문으로 건너뛰기", "lang_switch": "언어",
        "range": " ~ ", "sep": ", ", "slash": " / ",
        "addr": "주소", "phone": "대표전화", "visit": "찾아오시는 길",
        # ── 절 라벨. 번호는 메뉴 위치(NAVS)에서 온다 — 홈에 없는 메뉴(구성원 05)는 건너뛴다.
        "k_research": "01 / Research", "k_projects": "02 / Projects", "k_insights": "03 / Insights",
        "k_news": "04 / News", "k_people": "05 / People", "k_collab": "06 / Collaborate",
        "k_ways": "01 / Ways to collaborate", "k_contact": "02 / Contact", "k_visit": "03 / Visit",
        "k_researchers": "Faculty", "k_staff": "Associates & Admin",
        # ── 홈
        "btn_topics": "연구 주제 보기", "btn_contact": "협력 문의",
        "map_label": "연구 지도", "map_core": "신뢰할 수 있는 AI",
        "topics_h": "핵심 연구 주제", "topics_note": "주제별 대표 과제", "featured": "대표 과제",
        "archive_h": "과제 아카이브", "archive_sub": "지원 부처, 상태, 참여형태로 찾아보기",
        "all_projects": "전체 과제 보기",
        "insights_h": "인사이트", "all_insights": "전체 인사이트 →",
        "news_h": "소식", "all_news": "전체 소식 →",
        "collab_h": "함께할 방법", "way_more": "자세히 →",
        "news_empty": "등록된 소식이 없습니다.",
        # ── 통계
        "researchers": "연구인력", "active_projects": "수행 중 과제", "lead_projects": "수행 중 주관 과제",
        "new_stat": "{yy}년 신규 과제", "tag_new": "{yy}년 신규",
        "fig_total": "과제", "fig_active": "수행 중", "fig_lead": "수행 중 주관",
        # ── 과제 목록
        "project": "과제명", "period": "수행기간", "funder": "지원 부처", "role": "참여형태",
        "status": "상태", "pi": "담당자", "no": "번호", "topic": "연구 주제", "new_row": "신규",
        "filter_all": "전체", "count_projects": "과제 {n}개", "more_detail": "연구 내용 소개",
        "role_lead": "주관", "role_joint": "참여/공동", "role_contract": "기업수탁",
        "st_upcoming": "착수 예정", "st_active": "수행 중", "st_closing": "종료 예정", "st_closed": "종료",
        "lg_today": "오늘",
        # ── 과제 상세
        "months": "총 {n}개월", "progress": "진행", "progress_of": "%n개월 중 %m개월 경과",
        "sec_overview": "개요", "sec_consortium": "추진 체계", "sec_related": "관련 소식과 글",
        "cons_lead": "주관", "cons_joint": "공동", "cons_demand": "수요기업",
        "side_topic": "연구 주제", "side_members": "참여 구성원", "side_other": "담당자의 다른 과제",
        "side_contact": "협력 문의", "back_research": "← 과제 목록", "register": "과제 요약",
        # ── 소식, 인사이트
        "back_news": "← 지난 소식", "back_insights": "← 인사이트",
        "read_source": "전체 글 읽기 ↗", "source_note": "그림, 비교표, 참고 문헌을 포함한 원문",
        "excerpt_pre": "이 글은 {who}의 개인 블로그에 올린 문서를 발췌한 것입니다. 원문은 ",
        "excerpt_post": "에서 보실 수 있습니다.",
        "read_excerpt": "발췌 읽기", "latest": "최신 글", "date_k": "날짜", "author": "저자", "origin": "원문",
        "pinned": "진행 중", "deadline_k": "접수 마감", "closed": "마감", "related": "관련 과제",
        "all_news_k": "전체 소식", "count_news": "{n}건", "day": "{d}일",
        "cat_project": "과제", "cat_hiring": "채용", "cat_people": "구성원", "cat_center": "센터",
        "sample_badge": "예시",
        "sample_note": "이 글은 디자인 확인용 예시입니다. 게시 전에 지우거나 실제 내용으로 바꾸세요.",
        # ── 구성원
        "fig_all": "전체 구성원", "fig_research": "연구진", "fig_staff": "연구원", "fig_admin": "행정",
        "researchers_h": "연구진", "staff_h": "연구원, 행정", "grade_filter": "직급",
        "grade_chief": "수석연구원", "grade_principal": "책임연구원", "grade_senior": "선임연구원",
        "own": "책임", "join": "참여", "count_pn": "과제 {n}", "count_own": ", 책임 {m}",
        "more_n": "외 {n}건 더 보기",
        # ── 협력
        "ways_h": "협력 방안", "contact_h": "문의하기", "visit_h": "찾아오시는 길",
        "copy_mail": "주소 복사", "copied": "주소를 복사했습니다", "copy_failed": "복사하지 못했습니다. 위 주소를 옮겨 적어 주십시오.",
        # ── 채용 안내 카드
        "hire_label": "채용 중", "hire_aria": "채용 안내", "hire_see": "공고 보기",
        "hire_close": "채용 안내 닫기", "hire_hide_today": "오늘 하루 보지 않기",
        "hire_closes": "마감 {m}월 {d}일({wd}) {hm}",
        # ── 영문 안내 줄(국문 홈에만, 내용은 영어)
        "en_note": "This page is also available in English", "en_note_close": "Close",
    },
    "en": {
        "nav_topics": "Research", "nav_projects": "Projects", "nav_insights": "Insights",
        "nav_news": "News", "nav_people": "People", "nav_collab": "Collaborate",
        "title_projects": "Projects", "title_insights": "Insights", "title_news": "News",
        "title_people": "People", "title_collab": "Collaborate and visit",
        "crumb_home": "Home", "crumbs": "Breadcrumb",
        "contact": "Contact", "skip": "Skip to content", "lang_switch": "Language",
        "range": " – ", "sep": ", ", "slash": " / ",
        "addr": "Address", "phone": "Phone", "visit": "Visit",
        "k_research": "01 / Research", "k_projects": "02 / Projects", "k_insights": "03 / Insights",
        "k_news": "04 / News", "k_people": "05 / People", "k_collab": "06 / Collaborate",
        "k_ways": "01 / Ways to collaborate", "k_contact": "02 / Contact", "k_visit": "03 / Visit",
        "k_researchers": "Faculty", "k_staff": "Associates & Admin",
        "btn_topics": "Explore research topics", "btn_contact": "Work with us",
        "map_label": "Research map", "map_core": "Reliable AI",
        "topics_h": "Research topics", "topics_note": "Featured projects by topic", "featured": "Featured project",
        "archive_h": "Project archive", "archive_sub": "Browse by funder, status and role",
        "all_projects": "All projects",
        "insights_h": "Insights", "all_insights": "All insights →",
        "news_h": "News", "all_news": "All news →",
        "collab_h": "Ways to work with us", "way_more": "Details →",
        "news_empty": "No news posted yet.",
        "researchers": "Research staff", "active_projects": "Active projects", "lead_projects": "Active, as lead",
        "new_stat": "Started in {y}", "tag_new": "New in {y}",
        "fig_total": "Projects", "fig_active": "Active", "fig_lead": "Active, as lead",
        "project": "Project", "period": "Period", "funder": "Funder", "role": "Role",
        "status": "Status", "pi": "PI", "no": "No.", "topic": "Topic", "new_row": "New",
        "filter_all": "All", "count_projects": "{n} projects", "count_projects_one": "{n} project", "more_detail": "About this project",
        "role_lead": "Lead", "role_joint": "Partner", "role_contract": "Contract",
        "st_upcoming": "Upcoming", "st_active": "Active", "st_closing": "Closing", "st_closed": "Closed",
        "lg_today": "Today",
        "months": "{n} months", "progress": "Progress", "progress_of": "%m of %n months",
        "sec_overview": "Overview", "sec_consortium": "Consortium", "sec_related": "Related news and articles",
        "cons_lead": "Lead", "cons_joint": "Partner", "cons_demand": "End user",
        "side_topic": "Research topic", "side_members": "Center members", "side_other": "Other projects by the PI",
        "side_contact": "Work with us", "back_research": "← All projects", "register": "Project summary",
        "back_news": "← All news", "back_insights": "← Insights",
        "read_source": "Read the full article ↗", "source_note": "The original, with figures, tables and references",
        "excerpt_pre": "This article is excerpted from a post on {who}'s personal blog. The original is available at ",
        "excerpt_post": ".",
        "read_excerpt": "Read the excerpt", "latest": "Latest", "date_k": "Date", "author": "Author", "origin": "Original",
        "pinned": "Open", "deadline_k": "Applications close", "closed": "Closed", "related": "Related project", "related_many": "Related projects",
        "all_news_k": "All news", "count_news": "{n} posts", "count_news_one": "{n} post", "day": "{d}",
        "cat_project": "Projects", "cat_hiring": "Hiring", "cat_people": "People", "cat_center": "Center",
        "sample_badge": "Sample",
        "sample_note": "This post is a sample for design review. Remove or replace it before publishing.",
        "fig_all": "All members", "fig_research": "Faculty", "fig_staff": "Research associates", "fig_admin": "Administration",
        "researchers_h": "Faculty", "staff_h": "Research associates and administration", "grade_filter": "Grade",
        "grade_chief": "Chief", "grade_principal": "Principal", "grade_senior": "Senior",
        "own": "PI", "join": "Member", "count_pn": "{n} projects", "count_pn_one": "{n} project", "count_own": ", PI on {m}",
        "more_n": "{n} more",
        "ways_h": "Ways to collaborate", "contact_h": "Contact", "visit_h": "Visit",
        "copy_mail": "Copy address", "copied": "Address copied", "copy_failed": "Could not copy. Please copy the address above.",
        "hire_label": "Hiring", "hire_aria": "Hiring notice", "hire_see": "See the posting",
        "hire_close": "Close hiring notice", "hire_hide_today": "Hide for today",
        "hire_closes": "Applications close {d} {mon}, {hm} KST",
        "en_note": "This page is also available in English", "en_note_close": "Close",
    },
}

ROLE_KEY = {"lead": "role_lead", "joint": "role_joint", "contract": "role_contract"}
STATUS_KEY = {"upcoming": "st_upcoming", "active": "st_active", "closing": "st_closing", "closed": "st_closed"}

KST = dt.timezone(dt.timedelta(hours=9))
KO_WD = "월화수목금토일"
EN_MON = ("January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December")

# ── 소식 분류. ⭐ 값은 언어 중립 키다 — 두 언어 파일에 **같은 값**을 쓴다.
#    국문 파일에 「채용」, 영문 파일에 「Hiring」을 쓰면 한쪽 언어에서만 채용 카드가 빠진다(에러 없이).
NEWS_CATEGORIES = ("project", "hiring", "people", "center")
# 마감 시각. ⛔ 오프셋을 반드시 적는다 — 없으면 보는 사람의 시간대로 해석된다.
DEADLINE_RX = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}\+09:00$")
DATE_RX = re.compile(r"^\d{4}-\d{2}-\d{2}$")
# 예약 소식(아직 공개일이 안 된 글)의 projects. 공개 글과 같은 게이트를 **지금** 통과해야 한다.
HELD_PROJECTS: list[tuple[str, list[str]]] = []
# 인사이트 = 센터장 블로그 글의 발췌. 발췌 안내와 (개편 뒤) 인사이트 목록이 같은 판정을 쓴다.
INSIGHT_SOURCE = "https://seungwoo.datasec.work/"


def is_insight(n: dict) -> bool:
    return n.get("source", "").startswith(INSIGHT_SOURCE)


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


# 그림 한 줄: `![대체 글](/assets/news/<slug>/<파일>.png "캡션")`. 한 줄에 그림 하나만.
# ⛔ 경로는 `/assets/news/` 아래만 받는다 — 밖의 그림(브랜드 등)을 본문에 끌어오지 않게.
# 뒤에 `{width=60%}` 를 붙이면 그 그림만 본문 폭보다 좁게 둔다(세로로 긴 그림용). 좁은 화면에서는 무시한다.
FIG_RE = re.compile(r'^!\[([^\]]*)\]\((/assets/news/[^)\s"]+)(?:\s+"([^"]*)")?\)(?:\{width=(\d{2,3})%\})?$')


def figure(alt: str, src: str, caption: str, width: str = "") -> str:
    """소식 본문 그림. 크기는 파일에서 읽고(img_size), 없는 파일이면 막는다.

    ⭐ 액자는 디자인 시스템의 `.blueprint`(네 귀 등록마크)다. 면을 채우지 않는다.
    ⚠️ alt 를 비워 두면 막는다 — 그림 속 글자는 검색, 번역, 화면낭독이 안 되므로
       무엇을 그린 그림인지 alt 와 캡션에 글로 남겨야 한다.
    """
    if not (ROOT / src.lstrip("/")).exists():
        block(f"소식 그림 파일이 없다: {src}")
        return ""
    if not alt.strip():
        block(f"소식 그림에 대체 글(alt)이 없다: {src}")
    w, h = img_size(src)
    cap = f"<figcaption>{_inline(caption)}</figcaption>" if caption else ""
    if width and not 20 <= int(width) <= 100:
        block(f"소식 그림 width 는 20~100% 사이여야 한다: {src}")
        width = ""
    style = f' style="--fig-w:{int(width)}%"' if width else ""
    return (f'<figure class="newsfig"{style}>' + blueprint(
        f'<img src="{stamp(src)}" alt="{e(alt)}" width="{w}" height="{h}" loading="lazy" decoding="async">')
        + cap + "</figure>")


def markdown(text: str) -> str:
    """문단 · 제목 · 목록 · 인용 · 구분선 · 그림만. 그 이상은 이 사이트에 필요 없다."""
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
        fig = FIG_RE.match(line.strip())
        if fig:
            flush()
            out.append(figure(fig.group(1), fig.group(2), fig.group(3) or "", fig.group(4) or ""))
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
    """착수 예정 / 수행 중 / 종료 예정(종료월 말일까지 183일 이하) / 종료. ⚠️ **일 단위로** 바뀐다."""
    start = project.get("start")
    if start:
        sy, sm = ym(start)
        if dt.date(sy, sm, 1) > today:
            return "upcoming"
    end = project.get("end")
    if not end:
        return "active"
    y, m = ym(end)
    last = dt.date(y + (m == 12), (m % 12) + 1, 1) - dt.timedelta(days=1)
    if last < today:
        return "closed"
    if (last - today).days <= 183:
        return "closing"
    return "active"


def ym(s: str) -> tuple[int, int]:
    y, m = s.split("-")[:2]
    return int(y), int(m)


def months_of(p: dict) -> int:
    """총 개월 수, 양끝 포함(2026-08 ~ 2029-12 = 41)."""
    sy, sm = ym(p["start"])
    ey, em = ym(p["end"])
    return (ey * 12 + em) - (sy * 12 + sm) + 1


def split_list(s: str) -> list[str]:
    """쉼표로 나눈 목록. 괄호 안의 쉼표는 나누지 않는다 — 「한국전자기술연구원 (A, B)」."""
    out, cur, depth = [], "", 0
    for ch in s or "":
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth -= 1
        if ch == "," and depth == 0:
            out.append(cur.strip())
            cur = ""
        else:
            cur += ch
    if cur.strip():
        out.append(cur.strip())
    return [x for x in out if x]


# 새 과제 기준 연도. ⭐ 빌드 날짜가 아니라 **데이터의 가장 늦은 시작 연도**다 — 빌드 날짜로 두면
#    1월 1일에 「2027년 신규 0」이 뜨고 신규 딱지 11개가 한꺼번에 사라진다. 2027 과제가 처음
#    들어오는 커밋에서 넘어간다. main() 이 정한다.
NEW_Y = 0


def new_label(lg: str, key: str = "tag_new") -> str:
    return T[lg][key].format(yy=str(NEW_Y)[2:], y=NEW_Y)

def load_news(publish_on: dt.date) -> dict[str, list[dict]]:
    """`<slug>.<lang>.md`. 같은 slug 의 두 언어가 한 글이다.

    ⭐ `date` 가 `publish_on`(한국 시각 오늘)보다 늦은 글은 **아직 싣지 않는다.** 블로그 원문이
    그날 열리는 글을 미리 올려 두면, 그날 예약 빌드(check.yml 의 schedule)가 싣는다.
    """
    news: dict[str, list[dict]] = {lg: [] for lg in LANGS}
    d = ROOT / "content" / "news"
    if not d.exists():
        return news
    seen: dict[str, set[str]] = {}
    held: set[str] = set()
    twins: dict[str, dict[str, tuple]] = {}
    for f in sorted(d.glob("*.md")):
        if f.name == "README.md":            # 쓰는 법 안내. 글이 아니다.
            continue
        parts = f.name[:-3].rsplit(".", 1)
        if len(parts) != 2 or parts[1] not in LANGS:
            warn(f"뉴스 파일 이름이 `<slug>.<lang>.md` 가 아니다: {f.name}")
            continue
        slug, lg = parts
        meta, body = front_matter(f.read_text(encoding="utf-8"))
        if not meta.get("date") or not meta.get("title"):
            block(f"뉴스에 date 나 title 이 없다: {f.name}")
            continue
        # ⚠️ 공개 여부를 문자열 비교로 정한다. `2026-10-9` 나 `2026/10/09` 는 에러 없이 예약으로 빠져
        #    몇 달씩 안 실린다 — 형식부터 막는다.
        try:
            if not DATE_RX.match(meta["date"]):
                raise ValueError
            dt.date.fromisoformat(meta["date"])
        except ValueError:
            block(f"뉴스 date 형식이 틀렸다: {f.name} 「{meta['date']}」 — YYYY-MM-DD")
            continue
        if meta.get("source") and not meta["source"].startswith("https://"):
            block(f"뉴스 source 는 https:// 주소여야 한다: {f.name}")
            continue
        # ⭐ 분류와 마감은 예약 글에도 지금 검사한다 — 그날 예약 빌드에서 처음 터지면 배포가 멈춘다.
        cat = meta.get("category", "")
        if cat and cat not in NEWS_CATEGORIES:
            block(f"뉴스 category 가 허용 값이 아니다: {f.name} 「{cat}」 — {' / '.join(NEWS_CATEGORIES)}")
        elif not cat and not is_insight(meta):
            block(f"소식에 category 가 없다: {f.name} — {' / '.join(NEWS_CATEGORIES)} 중 하나 "
                  f"(블로그 발췌 글만 생략한다)")
        deadline = None
        if meta.get("deadline"):
            if not DEADLINE_RX.match(meta["deadline"]):
                block(f"뉴스 deadline 형식이 틀렸다: {f.name} 「{meta['deadline']}」 — "
                      f"YYYY-MM-DDTHH:MM+09:00 (오프셋 필수)")
            else:
                try:
                    deadline = dt.datetime.fromisoformat(meta["deadline"])
                except ValueError:                   # 2026-11-31 같은 없는 날짜·시각
                    block(f"뉴스 deadline 이 없는 날짜나 시각이다: {f.name} 「{meta['deadline']}」")
        if cat == "hiring" and not deadline:
            warn(f"채용 소식에 deadline 이 없다: {f.name} — 채용 안내 카드가 뜨지 않는다")
        projs = [x.strip() for x in meta.get("projects", "").split(",") if x.strip()]
        # 인사이트 여부(출처가 센터장 블로그인가)도 두 언어가 같아야 한다 — 한쪽만 인사이트면
        # 언어 전환기가 다른 메뉴의 쪽을 가리킨다.
        twins.setdefault(slug, {})[lg] = (meta["date"], bool(meta.get("source")), is_insight(meta), cat,
                                          meta.get("deadline", ""), tuple(projs))
        if meta["date"] > publish_on.isoformat():
            held.add(f"{slug} ({meta['date']})")
            # ⭐ 예약 글도 그림·관련 과제를 지금 검사한다. 공개일 예약 빌드에서 처음 터지면
            #    --strict 가 그날부터 배포를 멈춘다.
            markdown(body)
            HELD_PROJECTS.append((f"{slug}.{lg}", projs))
            continue
        seen.setdefault(slug, set()).add(lg)
        news[lg].append({
            "slug": slug, "date": meta["date"], "title": meta["title"],
            "summary": meta.get("summary", ""),
            # 원문이 따로 있는 글(블로그 등)의 주소. 있으면 상세 쪽 위와 아래에 버튼으로 건다.
            "source": meta.get("source", ""),
            "category": cat, "deadline": deadline, "projects": projs,
            "sample": meta.get("sample", "").lower() in ("true", "yes", "1"),
            "body": markdown(body),
            # 본문 첫 그림을 그 쪽의 소셜 카드(og:image)로 쓴다. 없으면 사이트 기본 카드.
            "image": next((m.group(2) for m in map(FIG_RE.match, (x.strip() for x in body.splitlines())) if m), ""),
        })
    # ⛔ 한 언어만 있는 글은 **아예 싣지 않는다.** 싣으면 그 쪽의 hreflang 과 언어 전환기가
    #    없는 쪽을 가리켜 404 가 된다 — 과제 상세와 같은 규칙이다.
    for h in sorted(held):
        print(f"⏳ 예약 소식 {h} — 그날 예약 빌드에서 실린다")
    # ⛔ 두 언어 파일의 머리말이 어긋나면 언어마다 다른 글이 된다 — 날짜가 다르면 목록 순서가,
    #    분류나 마감이 다르면 한쪽 언어에서만 채용 카드가 갈린다. 에러는 나지 않는다.
    for slug, by_lang in sorted(twins.items()):
        if len(set(by_lang.values())) > 1:
            block(f"소식 `{slug}` 의 두 언어 머리말(date, source 유무, 인사이트 여부, category, deadline, projects)이 다르다: "
                  + " / ".join(f"{lg}={v}" for lg, v in sorted(by_lang.items())))
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


NAVS = [("#research", "nav_topics"), ("research/", "nav_projects"), ("insights/", "nav_insights"),
        ("news/", "nav_news"), ("people/", "nav_people"), ("collaborate/", "nav_collab")]

# 옛 주소 → 새 주소. 쪽은 남긴다(외부 링크와 기존 색인). sitemap 에서는 뺀다.
# ⚠️ canonical 게이트는 이 표의 쪽만 예외로 두고, 대신 대상과 앵커가 있는지를 검사한다.
REDIRECTS = {"visit/": ("collaborate/", "visit")}

# ── 채용 안내 카드 (셸 공통). main() 이 언어별로 고른다 — 마감이 남은 hiring 소식 중 가장 가까운 것.
HIRE: dict[str, dict | None] = {lg: None for lg in LANGS}
X_ICON = ('<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" '
          'stroke-width="1.8" stroke-linecap="round" aria-hidden="true" focusable="false">'
          '<path d="M6 6l12 12M18 6L6 18"/></svg>')


def hire_note(lg: str, path: str) -> str:
    """⭐ `<main>` **밖**에 둔다. 쪽 지문(page_sig)은 `<main>` 을 보므로, 안에 두면 카드를 붙이고
    떼는 날마다 모든 쪽의 sitemap lastmod 가 함께 움직인다.

    ⭐ `hidden` 으로 굽고 `site.js` 가 연다 — JS 가 없으면 닫을 수 없는 카드가 남기 때문이다.
    마감 시각이 지나면 JS 가 닫고, 다음 날 예약 빌드가 HTML 에서도 뺀다(빌드는 **날짜** 단위로만 본다).
    ⛔ class 이름에 ad/banner/popup/modal/promo 같은 토큰을 쓰지 않는다 — 광고 차단 목록에 걸린다.
    """
    n = HIRE.get(lg)
    if not n or path == f"news/{n['slug']}/":       # 공고 글 자체에는 띄우지 않는다
        return ""
    t = T[lg]
    dl = n["deadline"].astimezone(KST)
    when = t["hire_closes"].format(m=dl.month, d=dl.day, wd=KO_WD[dl.weekday()],
                                   mon=EN_MON[dl.month - 1], hm=dl.strftime("%H:%M"))
    href = f"/{lg}/news/{n['slug']}/"
    inner = (f'<div class="hire-top"><span class="k">{e(t["hire_label"])}</span>'
             f'<b class="ht hire-dday tnum" data-dday></b>'
             f'<button type="button" class="hire-x" data-hire-close aria-label="{e(t["hire_close"])}">'
             f'{X_ICON}</button></div>'
             f'<a class="ht hire-title" href="{href}">{e(n["title"])}</a>'
             f'<p class="hire-when">{e(when)}</p>'
             f'<div class="hire-acts"><a class="btn btn-primary" href="{href}">{e(t["hire_see"])}</a>'
             f'<button type="button" class="hire-today" data-hire-today>{e(t["hire_hide_today"])}</button>'
             f'</div>')
    return (f'\n<aside class="hire-note" aria-label="{e(t["hire_aria"])}" hidden '
            f'data-deadline="{dl.isoformat()}" data-key="hire-note:{e(n["slug"])}">'
            f'{blueprint(inner, cls="hire-card")}</aside>')


def crumbs_html(lg: str, items: list) -> str:
    """경로 표시. ⭐ `<main>` 밖(메뉴와 본문 사이)에 둔다 — 쪽 지문이 흔들리지 않게.
    JSON-LD(BreadcrumbList)는 넣지 않는다(CLAUDE.md §9)."""
    lis = "".join(
        f'<li><a href="{e(h)}">{e(label)}</a></li>' if h else f'<li aria-current="page">{e(label)}</li>'
        for label, h in items)
    return f'\n<nav class="crumbs" aria-label="{e(T[lg]["crumbs"])}"><ol>{lis}</ol></nav>'


# 도메인 표기 - "datasec work" 같은 도메인 검색어가 이 사이트와 맞물리게 한다.
# 화면(바닥글)에 보이게 두고, JSON-LD alternateName 도 같은 값을 쓴다(§9).
DOMAIN_LABEL = "datasec.work"


def shell(lg: str, nav_key: str, path: str, title: str | None, desc: str, body: str, site: dict,
          og_type: str = "website", jsonld: str = "", head_extra: str = "",
          og_image: str = "", og_alt: str = "", crumbs: list | None = None) -> str:
    """⛔ `nav_key` 와 `path` 는 **다른 것**이다.

    `nav_key` = 내비게이션에서 어느 항목을 현재로 표시할지 (상세 쪽도 목록 항목을 밝힌다).
    `path`    = 이 쪽의 **실제 주소** — canonical · hreflang · og:url · 언어 전환기가 쓴다.

    ⛔ 둘을 하나로 합쳐 두었더니 소식 상세 4쪽이 **자기를 목록 쪽으로 canonical** 시켰다.
       색인이 불가능해지고(구글은 canonical 을 따른다) 언어 전환 버튼도 목록으로 갔다.
       에러는 나지 않았다.
    ⭐ `title` 이 None 이면 홈이다 — 「센터명 | datasec.work」.
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
    og_title = f"{title} — {center}" if title else center
    doc_title = og_title + (f" | {DOMAIN_LABEL}" if path == "" else "")
    if crumbs is None and path:
        label = next((t[k] for p, k in NAVS if p == nav_key), title or "")
        crumbs = [(t["crumb_home"], f"/{lg}/")]
        crumbs += [(label, None)] if path == nav_key else [(label, f"/{lg}/{nav_key}"), (title, None)]
    bc = crumbs_html(lg, crumbs) if crumbs else ""
    en_note = ""
    if lg == "ko" and path == "":
        en_note = ('\n<div class="en-note" lang="en" hidden><a href="/en/" hreflang="en">'
                   f'{e(t["en_note"])} →</a><button type="button" class="en-note-x" data-en-note-close '
                   f'aria-label="{e(t["en_note_close"])}">{X_ICON}</button></div>')
    return f"""<!doctype html>
<html lang="{lg}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(doc_title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{e(canonical)}">
<link rel="alternate" hreflang="ko" href="{base}/ko/{path}">
<link rel="alternate" hreflang="en" href="{base}/en/{path}">
<link rel="alternate" hreflang="x-default" href="{base}/{DEFAULT_LANG}/{path}">
<meta property="og:title" content="{e(og_title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:type" content="{og_type}">
<meta property="og:url" content="{e(canonical)}">
<meta property="og:site_name" content="{e(center)}">
<meta property="og:locale" content="{'ko_KR' if lg == 'ko' else 'en_US'}">
<meta property="og:image" content="{base}{og_image or '/assets/brand/og-image.png'}">
<meta property="og:image:width" content="{img_size(og_image)[0] if og_image else OG_W}">
<meta property="og:image:height" content="{img_size(og_image)[1] if og_image else OG_H}">
<meta property="og:image:alt" content="{e(og_alt) if og_image else 'ADSRC — ' + e(center)}">
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
<a class="btn btn-primary nav-cta" href="/{lg}/collaborate/#contact">{e(t['contact'])}</a>
</nav>{bc}{en_note}
<main id="main">
{body}
</main>{hire_note(lg, path)}
<footer>
<span>{e(site['center_full'][lg])}</span>
<span>{foot_mid}</span>
<span class="foot-domain"><a href="/{lg}/collaborate/#visit">{e(t['visit'])}</a><a href="/{lg}/">{DOMAIN_LABEL}</a></span>
</footer>
<script src="{stamp('/assets/mail.js')}" defer></script>
<script src="{stamp('/assets/site.js')}" defer></script>
</body>
</html>
"""


def redirect_page(lg: str, site: dict, src: str) -> str:
    """옛 주소의 자리. ⭐ `shell()` 을 쓰지 않는다 — 메뉴와 hreflang 을 단 채 이동시키지 않는다.
    canonical 은 대상(조각 없이), meta refresh 0 은 대상의 앵커로. 구글은 0초 refresh 를 영구 이동으로 본다."""
    dst, frag = REDIRECTS[src]
    base = site["site_url"].rstrip("/")
    label = T[lg]["visit"]
    return f"""<!doctype html>
<html lang="{lg}">
<head><meta charset="utf-8">
<title>{e(label)} — {e(site['center'][lg])}</title>
<link rel="canonical" href="{base}/{lg}/{dst}">
<meta http-equiv="refresh" content="0; url=/{lg}/{dst}#{frag}">
</head>
<body><p><a href="/{lg}/{dst}#{frag}">{e(label)}</a></p></body></html>
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
                          site["center_full"]["ko"], site["center_full"]["en"], "ADSRC",
                          DOMAIN_LABEL],
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


def blueprint(inner: str, cls: str = "", style: str = "", tag: str = "div", attrs: str = "") -> str:
    attr = ' style="{}"'.format(style) if style else ""
    return ('<{tag} class="blueprint {cls}"{attr}{attrs}>'
            '<i class="corner tl"></i><i class="corner tr"></i>'
            '<i class="corner bl"></i><i class="corner br"></i>'
            '{inner}</{tag}>').format(tag=tag, cls=cls, attr=attr, attrs=attrs, inner=inner)


def klabel(text: str) -> str:
    """절 머리의 눈금 라벨(「01 / Research」)과 가는 선. ⭐ 장식이다 — 절 제목은 따로 h2 로 둔다.
    ⚠️ 라벨을 h2 로 쓰면 `h2.k` 리셋이 라벨 모양(12px, 대문자)을 덮는다."""
    return f'<div class="klabel"><span class="k">{e(text)}</span></div>'


def period(p: dict, lg: str) -> str:
    return f'<span class="tnum">{e(p["start"])}{T[lg]["range"]}{e(p["end"])}</span>'


def tags(p: dict, lg: str) -> str:
    t = T[lg]
    cls = "tag-accent" if p["role"] == "lead" else "tag-neutral"
    return f'<span class="tag {cls}">{e(t[ROLE_KEY[p["role"]]])}</span>'


def proj_meta(p: dict, lg: str) -> str:
    """부처 / 참여형태 / 기간 — 카드와 옆단의 한 줄."""
    t = T[lg]
    return t["slash"].join([p["agency_short"][lg], t[ROLE_KEY[p["role"]]],
                            f'{p["start"]}{t["range"]}{p["end"]}'])


def load_topics(all_slugs: set, published: set) -> list[dict]:
    """`content/topics.json`. ⭐ 정본에 없는 **편집 분류**다(README §5). 게이트가 형식을 지킨다."""
    p = ROOT / "content" / "topics.json"
    if not p.exists():
        return []
    topics = json.loads(p.read_text(encoding="utf-8")).get("topics", [])
    seen: set[str] = set()
    for tp in topics:
        tid = tp.get("id") if isinstance(tp.get("id"), str) else ""
        tp["id"] = tid
        if not re.fullmatch(r"[a-z][a-z0-9-]*", tid) or tid in seen:
            block(f"content/topics.json: id 가 비었거나 겹친다 「{tid}」")
        seen.add(tid)
        if tp.get("axis") not in ("data", "security"):
            block(f"content/topics.json {tid}: axis 는 data 나 security 여야 한다")
        for key in ("name", "line", "desc"):
            v = tp.get(key) or {}
            if not isinstance(v, dict):
                block(f"content/topics.json {tid}.{key}: {{\"ko\": …, \"en\": …}} 꼴이어야 한다")
                v = {}
            filled = [bool((v.get(x) or "").strip()) for x in LANGS]
            if key == "name" and not all(filled):
                block(f"content/topics.json {tid}.name: 두 언어가 모두 있어야 한다")
            elif any(filled) and not all(filled):
                block(f"content/topics.json {tid}.{key}: 한 언어만 있다 — 두 언어 모두 쓰거나 둘 다 비운다")
            tp[key] = {x: (v.get(x) or "").strip() for x in LANGS}
        projs, feat = tp.get("projects") or [], tp.get("featured") or ""
        if not isinstance(projs, list):
            block(f"content/topics.json {tid}.projects: 과제 slug 의 목록([…])이어야 한다")
            projs = []
        if not isinstance(feat, str):
            block(f"content/topics.json {tid}.featured: 과제 slug 하나(문자열)여야 한다")
            feat = ""
        tp["projects"] = [x for x in projs if isinstance(x, str)]
        tp["featured"] = feat
        for s in tp["projects"]:
            if s not in all_slugs:
                block(f"content/topics.json {tid}: 없는 과제 「{s}」")
            elif s not in published:
                block(f"content/topics.json {tid}: 공개하지 않는 과제 「{s}」")
        f = tp["featured"]
        if f and f not in tp["projects"]:
            block(f"content/topics.json {tid}: featured 「{f}」가 이 주제의 projects 에 없다")
    # 연구 지도의 칩 자리는 축마다 셋이다(site.css .rm-<axis>-0~2). 넷째는 자리가 없어 지도 위에 겹친다.
    for axis in ("data", "security"):
        if sum(1 for tp in topics if tp.get("axis") == axis) > 3:
            block(f"content/topics.json: {axis} 축의 주제가 셋을 넘는다 — 연구 지도에 자리가 없다(site.css .rm-chip)")
    # 축이 틀린 주제는 위에서 막았다. 쪽을 그리다 KeyError 로 죽으면 막은 이유가 안 보이므로 빼고 넘긴다.
    return [tp for tp in topics if tp.get("axis") in ("data", "security") and tp.get("id")]


def md_sections(body: str, lg: str) -> list[tuple[str, str]]:
    """과제 소개 md 를 `# ` 절로 나눈다. 첫 `# ` 앞 문단은 「개요」다."""
    chunks: list[list] = [[None, []]]
    for line in body.splitlines():
        if line.startswith("# "):
            chunks.append([line[2:].strip(), []])
        else:
            chunks[-1][1].append(line)
    out = []
    for title, lines in chunks:
        text = "\n".join(lines).strip()
        if title is None and not text:
            continue
        out.append((title or T[lg]["sec_overview"], text))
    return out


FEAT_RX = re.compile(r"^- \*\*(.+?)\*\*\s*[:：]\s*(.+)$")


def feature_grid(text: str) -> str:
    """「- **제목**: 설명」 네 줄이면 2x2 액자로. 아니면 빈 문자열(본문 그대로 렌더)."""
    lines = [x.strip() for x in text.splitlines() if x.strip()]
    ms = [FEAT_RX.match(x) for x in lines]
    if len(lines) != 4 or not all(ms):
        return ""
    cells = "".join(
        blueprint(f'<span class="ht fnum tnum">{i:02d}</span><b class="ftitle">{_inline(m.group(1))}</b>'
                  f'<span class="fdesc">{_inline(m.group(2))}</span>', cls="fcell")
        for i, m in enumerate(ms, 1))
    return f'<div class="fgrid">{cells}</div>'


CONSORTIUM_KEYS = ("consortium_lead", "consortium_joint", "consortium_demand", "consortium_note")


def consortium(meta: dict, lg: str) -> str:
    """추진 체계 도식. ⭐ **사람이 쓴 소개문 머리말**(`consortium_*`)에서만 그린다 — 정본의
    공동연구기관 칸은 옛 기관명과 자리표시자가 섞여 있어 옮기지 않는다(README §3)."""
    t = T[lg]
    lead = (meta.get("consortium_lead") or "").strip()
    joint = split_list(meta.get("consortium_joint", ""))
    demand = split_list(meta.get("consortium_demand", ""))
    if not (lead or joint or demand):
        return ""
    out = []
    if lead:
        out.append(blueprint(f'<span class="k">{e(t["cons_lead"])}</span><b class="ht">{e(lead)}</b>',
                             cls="cons-lead"))
    for label, items, cls in ((t["cons_joint"], joint, ""), (t["cons_demand"], demand, " is-demand")):
        if items:
            out.append('<div class="cons-row">' + "".join(
                f'<div class="cons-box{cls}"><span class="k">{e(label)}</span><b class="ht">{e(x)}</b></div>'
                for x in items) + '</div>')
    note = (meta.get("consortium_note") or "").strip()
    if note:
        out.append(f'<p class="cons-note">{e(note)}</p>')
    return '<div class="cons">' + "".join(out) + '</div>'

# ════════════════════════════════════════════════════════════════════
# 페이지
# ════════════════════════════════════════════════════════════════════

def research_map(lg: str, topics: list[dict]) -> str:
    """연구 지도. ⛔ **그림이 아니라 HTML 이다** — 주제명이 글자로 있어야 색인되고, 번역되고,
    선택된다(그림 속 글자는 크기를 줄이면 제일 먼저 죽는다, CLAUDE.md §5).
    좁은 화면에서는 같은 DOM 을 미디어쿼리가 목록으로 바꾼다."""
    t = T[lg]
    at = {"data": 0, "security": 0}
    chips = []
    for tp in topics:
        i = at[tp["axis"]]
        at[tp["axis"]] += 1
        chips.append(f'<a class="rm-chip rm-{tp["axis"]}-{i}" href="#topic-{e(tp["id"])}">'
                     f'{e(tp["name"][lg])}</a>')
    return (f'<div class="rmap" role="group" aria-label="{e(t["map_label"])}">'
            '<div class="rm-sq rm-sq-data" aria-hidden="true"></div>'
            '<div class="rm-sq rm-sq-sec" aria-hidden="true"></div>'
            f'<div class="rm-core"><span class="ht">{e(t["map_core"])}</span></div>'
            '<span class="ht rm-axis rm-axis-data">DATA</span>'
            '<span class="ht rm-axis rm-axis-sec">SECURITY</span>'
            + "".join(chips) + '</div>')


def topic_card(lg: str, tp: dict, by_slug: dict, detailed: set) -> str:
    t = T[lg]
    o = other(lg)
    parts = [f'<span class="k">{"DATA" if tp["axis"] == "data" else "SECURITY"}</span>',
             f'<div><h3 class="ht tname">{e(tp["name"][lg])}</h3>'
             f'<span class="tname-o" lang="{o}">{e(tp["name"][o])}</span></div>']
    if tp["line"][lg]:
        parts.append(f'<p class="tline">{e(tp["line"][lg])}</p>')
    if tp["desc"][lg]:
        parts.append(f'<p class="tdesc">{e(tp["desc"][lg])}</p>')
    fp = by_slug.get(tp.get("featured", ""))
    # 대표 과제가 끝나면 그 줄을 싣지 않는다(차단하지 않는다 — 날짜로 바뀌는 조건이라 예약 빌드가 멈춘다).
    if fp and fp["status"] != "closed":
        parts.append(f'<div class="tfeat"><span class="tfeat-k">{e(t["featured"])}</span>'
                     f'{project_link(lg, fp, detailed, e(fp["title"][lg]), "tfeat-t")}'
                     f'<span class="ht tfeat-m tnum">{e(proj_meta(fp, lg))}</span></div>')
    return blueprint("".join(parts), cls="tcard", tag="article", attrs=f' id="topic-{e(tp["id"])}"')


def hlist(lg: str, items: list[dict]) -> str:
    if not items:
        return f'<p class="empty">{e(T[lg]["news_empty"])}</p>'
    return "".join(
        f'<a class="hitem" href="/{lg}/news/{n["slug"]}/"><span class="num">{e(n["date"])}</span>'
        f'<span class="hitem-t">{e(n["title"])}</span></a>' for n in items)


def fig(v, label: str, cls: str = "") -> str:
    return (f'<div class="fig{cls}"><div class="ht v tnum">{v}</div>'
            f'<div class="figk">{e(label)}</div></div>')


def page_home(lg, site, projects, members, news, stats, detailed, topics):
    t = T[lg]
    by_slug = {p["slug"]: p for p in projects}
    figs = (fig(stats["members"], t["researchers"]) + fig(stats["active"], t["active_projects"])
            + fig(stats["lead"], t["lead_projects"])
            + (fig(stats["new"], new_label(lg, "new_stat"), " is-accent") if stats["new"] else ""))
    cards = "".join(topic_card(lg, tp, by_slug, detailed) for tp in topics)
    any_feat = any(by_slug.get(tp.get("featured", ""), {}).get("status") not in (None, "closed")
                   for tp in topics)
    note = f'<span class="hsec-note">{e(t["topics_note"])}</span>' if any_feat else ""
    insights = [n for n in news[lg] if is_insight(n)][:3]
    plain = [n for n in news[lg] if not is_insight(n)][:3]
    ways = "".join(
        f'<div class="hway"><b class="ht">{e(w["title"][lg])}</b><p>{e(w["body"][lg])}</p>'
        f'<a href="/{lg}/collaborate/#way-{e(w["id"])}">{e(t["way_more"])}</a></div>'
        for w in site["collaborate"]["ways"])
    body = f"""
<div class="masthead"><h1>{e(site['center_full'][lg])}</h1><span>{e(site['org_division'][lg])}</span></div>
<div class="herorow">
<div class="herotext">
<p class="ht hero">{e(site['hero'][lg])}</p>
<p class="lede">{e(site['lede'][lg])}</p>
<div class="herobtns"><a class="btn btn-primary" href="/{lg}/#research">{e(t['btn_topics'])}</a>
<a class="btn btn-secondary" href="/{lg}/collaborate/#contact">{e(t['btn_contact'])}</a></div>
</div>
{research_map(lg, topics)}
</div>
<div class="figs">{figs}</div>
<section id="research" class="hsec">{klabel(t['k_research'])}
<div class="hsec-head"><h2 class="ht h-2">{e(t['topics_h'])}</h2>{note}</div>
<div class="tcards">{cards}</div>
</section>
<section id="projects" class="hsec">{klabel(t['k_projects'])}
<a class="archive" href="/{lg}/research/">
<span class="arch-l"><b class="ht">{e(t['archive_h'])}</b><span>{e(t['archive_sub'])}</span></span>
<span class="arch-r"><span class="arch-n"><b class="ht tnum">{stats['active']}</b><span>{e(t['fig_active'])}</span></span>
<span class="arch-n"><b class="ht tnum">{stats['lead']}</b><span>{e(t['fig_lead'])}</span></span>
<span class="btn btn-primary">{e(t['all_projects'])}</span></span>
</a>
</section>
<div class="twocol">
<section id="insights" class="hsec">{klabel(t['k_insights'])}
<div class="hsec-head"><h2 class="ht h-2">{e(t['insights_h'])}</h2><a class="more" href="/{lg}/insights/">{e(t['all_insights'])}</a></div>
{hlist(lg, insights)}
</section>
<section id="news" class="hsec">{klabel(t['k_news'])}
<div class="hsec-head"><h2 class="ht h-2">{e(t['news_h'])}</h2><a class="more" href="/{lg}/news/">{e(t['all_news'])}</a></div>
{hlist(lg, plain)}
</section>
</div>
<section id="collab" class="hsec">{klabel(t['k_collab'])}
<h2 class="ht h-2">{e(t['collab_h'])}</h2>
<div class="hways">{ways}</div>
</section>
"""
    return shell(lg, "", "", None, site["lede"][lg], body, site,
                 jsonld=org_jsonld(lg, site, stats))


def load_summaries() -> dict[str, dict[str, dict]]:
    """`content/projects/<slug>.<lang>.md`. ⭐ **두 언어가 다 있어야** 상세 쪽을 만든다 —
    한쪽만 있으면 언어 전환이 404 로 간다. 머리말(약칭 short, 추진 체계 consortium_*)도 돌려준다."""
    out: dict[str, dict[str, dict]] = {}
    d = ROOT / "content" / "projects"
    if not d.exists():
        return out
    for f in sorted(d.glob("*.md")):
        parts = f.name[:-3].rsplit(".", 1)
        if len(parts) != 2 or parts[1] not in LANGS:
            warn(f"과제 소개 파일 이름이 `<slug>.<lang>.md` 가 아니다: {f.name}")
            continue
        slug, lg = parts
        meta, body = front_matter(f.read_text(encoding="utf-8"))
        out.setdefault(slug, {})[lg] = {"meta": meta, "body": body}
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


def fbuttons(f: str, opts: list[tuple[str, str]]) -> str:
    return "".join(
        f'<button type="button" class="seg-opt{" is-on" if v == "all" else ""}" data-f="{f}" '
        f'data-v="{e(v)}" aria-pressed="{"true" if v == "all" else "false"}">{e(txt)}</button>'
        for v, txt in opts)


def nfmt(t: dict, key: str, n: int) -> str:
    """수 낱말. 영문은 1 일 때 단수(`<key>_one`)를 쓴다 — 「1 projects」 방지. 국문은 같은 꼴."""
    return t.get(f"{key}_one" if n == 1 else key, t[key]).format(n=n)


def frow(f: str, label: str, opts: list[tuple[str, str]]) -> str:
    return (f'<div class="frow"><span class="flabel">{e(label)}</span>'
            f'<div class="seg" role="group" aria-label="{e(label)}">{fbuttons(f, opts)}</div></div>')


def page_research(lg, site, projects, members, detailed, topics, stats):
    t = T[lg]
    # ── 타임라인 축: 수행 중인 과제의 처음 시작 연도 ~ 가장 늦은 종료 연도.
    #    끝난 지 오래된 과제까지 넣으면 10년 축이 되어 막대가 읽히지 않는다 — 축 밖은 잘라 그린다.
    live = [p for p in projects if p["status"] != "closed"] or projects
    y0 = min(int(p["start"][:4]) for p in live)
    y1 = max(int(p["end"][:4]) for p in projects)
    a0, span = y0 * 12, (y1 - y0 + 1) * 12

    def bar(p: dict) -> str:
        sy, sm = ym(p["start"])
        ey, em = ym(p["end"])
        lo = max(0.0, (sy * 12 + sm - 1 - a0) / span * 100)
        hi = min(100.0, (ey * 12 + em - a0) / span * 100)
        if hi <= lo:
            return ""
        closed = " is-closed" if p["status"] == "closed" else ""
        return (f'<span class="tl-bar r-{p["role"]}{closed}" '
                f'style="left:{lo:.2f}%;width:{hi - lo:.2f}%"></span>')

    topic_of = {p["slug"]: [tp["id"] for tp in topics if p["slug"] in tp["projects"]] for p in projects}
    cnt = lambda pred: sum(1 for p in projects if pred(p))
    role_opts = [("all", f'{t["filter_all"]} {len(projects)}')]
    for r in ("lead", "joint", "contract"):
        n = cnt(lambda p, r=r: p["role"] == r)
        if n:
            role_opts.append((r, f'{t[ROLE_KEY[r]]} {n}'))
    # 「민간」은 참여형태 「기업수탁」과 1:1로 겹친다 — 부처 거르개에서 뺀다.
    agencies: dict[str, int] = {}
    for p in projects:
        if p["role"] != "contract":
            agencies[p["agency_short"][lg]] = agencies.get(p["agency_short"][lg], 0) + 1
    ag_opts = [("all", t["filter_all"])] + [(a, f"{a} {n}") for a, n in
                                             sorted(agencies.items(), key=lambda x: (-x[1], x[0]))]
    # ⭐ 상태 「수행 중」은 종료 예정을 포함한다(통계 띠의 「수행 중」과 같은 모집단). 그래서 종료 예정
    #    과제의 data-status 는 「active closing」 두 낱말이고, 거르개는 낱말 단위로 맞춘다(filter.js).
    st_tokens = lambda p: {"closing": "active closing"}.get(p["status"], p["status"])
    st_opts = [("all", t["filter_all"])] + [
        (s, f'{t[STATUS_KEY[s]]} {cnt(lambda p, s=s: s in st_tokens(p).split())}')
        for s in ("upcoming", "active", "closing", "closed") if cnt(lambda p, s=s: s in st_tokens(p).split())]
    rows_f = frow("role", t["role"], role_opts) + frow("agency", t["funder"], ag_opts) \
        + frow("status", t["status"], st_opts)
    # 신규는 참여형태가 아니다 — 따로 한 줄. 「주관이면서 신규」를 고를 수 있다.
    if stats["new"]:
        rows_f += frow("new", t["new_row"], [("all", t["filter_all"]), ("1", f'{new_label(lg)} {stats["new"]}')])
    # ⭐ 주제 거르개는 **모든 주제에 과제가 붙은 뒤에만** 싣는다 — 분류가 덜 된 채로 띄우면
    #    「이 주제의 과제는 이것뿐」으로 읽힌다.
    if topics and all(tp["projects"] for tp in topics):
        rows_f += frow("topics", t["topic"], [("all", t["filter_all"])] + [
            (tp["id"], f'{tp["name"][lg]} {len(tp["projects"])}') for tp in topics])

    rows = []
    for i, p in enumerate(projects, 1):
        marks = ""
        if p["new"]:
            marks += f'<span class="mtag is-new">{e(new_label(lg))}</span>'
        if p["status"] in ("closed", "upcoming"):
            marks += f'<span class="mtag">{e(t[STATUS_KEY[p["status"]]])}</span>'
        more = (f'<a class="moreline" href="/{lg}/research/{p["slug"]}/">{e(t["more_detail"])}'
                f'<span aria-hidden="true"> →</span></a>' if p["slug"] in detailed else "")
        tr_cls = ' class="has-detail"' if p["slug"] in detailed else ""
        marks_html = f'<span class="mtags">{marks}</span>' if marks else ""
        rows.append(
            f'<tr{tr_cls} '
            f'data-role="{p["role"]}" data-agency="{e(p["agency_short"][lg])}" data-status="{st_tokens(p)}" '
            f'data-topics="{" ".join(topic_of[p["slug"]])}" data-new="{"1" if p["new"] else "0"}">'
            f'<td class="num">{i:02d}</td>'
            # ⭐ 소개가 있는 과제는 적다. 제목은 글로 두고 아랫줄에 「연구 내용 소개 →」를 따로 단다.
            f'<td><span class="ht rowtitle">{e(p["title"][lg])}</span>'
            f'{marks_html}{more}</td>'
            f'<td>{e(p["agency_short"][lg])}</td>'
            f'<td class="c-tl"><div class="tl" aria-hidden="true">{bar(p)}</div>'
            f'<span class="tnum tl-text">{e(p["start"])}{t["range"]}{e(p["end"])}</span></td>'
            f'<td>{person_link(lg, p["pi"], members)}</td>'
            f'<td class="tagcell">{tags(p, lg)}</td></tr>')
    years = "".join(f"<span>{str(y)[2:]}</span>" for y in range(y0, y1 + 1))
    legend = (f'<div class="legend" aria-hidden="true">'
              f'<span><i class="lg r-lead"></i>{e(t["role_lead"])}</span>'
              f'<span><i class="lg r-joint"></i>{e(t["role_joint"])}</span>'
              f'<span><i class="lg r-contract"></i>{e(t["role_contract"])}</span>'
              f'<span><i class="lg is-closed"></i>{e(t["st_closed"])}</span>'
              f'<span class="lg-today-k" hidden><i class="lg lg-today"></i>{e(t["lg_today"])}</span></div>')
    figs = (fig(len(projects), t["fig_total"]) + fig(stats["active"], t["fig_active"])
            + fig(stats["lead"], t["fig_lead"])
            + (fig(stats["new"], new_label(lg, "new_stat"), " is-accent") if stats["new"] else ""))
    body = f"""
<div class="page">
{klabel(t['k_projects'])}
<h1 class="ht h-sec">{e(site['research_title'][lg])}</h1>
<div class="figs pfigs">{figs}</div>
<div class="pfilters" data-filters hidden>{rows_f}</div>
<div class="listhead"><span class="count" id="count" data-one="{e(nfmt(t, 'count_projects', 1).replace('1', '%n', 1))}" data-many="{e(t['count_projects'].format(n='%n'))}">{e(nfmt(t, 'count_projects', len(projects)))}</span>{legend}</div>
<div class="tablewrap">
<table class="table fixed listing" id="ptable" data-axis-start="{y0}-01" data-axis-end="{y1}-12">
<thead><tr>
<th scope="col" class="c-no">{e(t['no'])}</th>
<th scope="col">{e(t['project'])}</th>
<th scope="col" class="c-fund">{e(t['funder'])}</th>
<th scope="col" class="c-tl"><span class="tl-head"><span>{e(t['period'])}</span><span class="tnum">{y0}{t['range']}{y1}</span></span><span class="tl-years tnum">{years}</span></th>
<th scope="col" class="c-pi">{e(t['pi'])}</th>
<th scope="col" class="c-role">{e(t['role'])}</th>
</tr></thead>
<tbody>{"".join(rows)}</tbody>
</table>
</div>
</div>
<script src="{stamp('/assets/filter.js')}" defer></script>
"""
    return shell(lg, "research/", "research/", t["title_projects"],
                 site["research_desc"][lg], body, site)

def page_project(lg, site, p, members, summary, topics, projects, news, detailed):
    t = T[lg]
    o = other(lg)
    meta = summary["meta"]
    short = (meta.get("short") or "").strip()
    sy, sm = ym(p["start"])
    ey, em = ym(p["end"])
    total = months_of(p)
    ptopics = [tp for tp in topics if p["slug"] in tp["projects"]]
    pi_m = next((m for m in members if m["name"]["ko"] == p["pi"]["ko"]), None)
    pi_sub = ", ".join(x for x in ((pi_m["grade"][lg], pi_m["org_role"][lg]) if pi_m else ()) if x)

    st_cls = "tag-neutral" if p["status"] == "closed" else "tag-accent"
    tagrow = [f'<span class="tag {st_cls}">{e(t[STATUS_KEY[p["status"]]])}</span>', tags(p, lg)]
    if p["new"]:
        tagrow.append(f'<span class="tag tag-outline">{e(new_label(lg))}</span>')
    tagrow += [f'<a class="tag tag-outline" href="/{lg}/#topic-{e(tp["id"])}">{e(tp["name"][lg])}</a>'
               for tp in ptopics]

    def cell(k: str, v: str, sub: str = "") -> str:
        s = f'<span class="pcell-s">{sub}</span>' if sub else ""
        return f'<div class="pcell"><span class="dt">{e(k)}</span><b class="ht pcell-v">{v}</b>{s}</div>'
    cells = (cell(t["funder"], e(p["agency"][lg]))
             + cell(t["period"], period(p, lg), e(t["months"].format(n=total)))
             + cell(t["role"], e(t[ROLE_KEY[p["role"]]]),
                    e(site["org_name"][lg]) if p["role"] == "lead" else "")
             + cell(t["pi"], person_link(lg, p["pi"], members), e(pi_sub))
             # 진행 %는 날마다 바뀐다 — 굽지 않고 site.js 가 채운다(굽으면 CI 의 docs 비교가 깨진다).
             + f'<div class="pcell" data-progress data-start="{p["start"]}" data-end="{p["end"]}" '
               f'data-tpl="{e(t["progress_of"])}" data-n="{total}" hidden>'
               f'<span class="dt">{e(t["progress"])}</span><b class="ht pcell-v tnum" data-progress-pct></b>'
               f'<span class="pcell-s" data-progress-note></span></div>')
    ticks = [f'<span style="left:0%">{sy}</span>']
    for y in range(sy + 1, ey + 1):
        left = (y * 12 - (sy * 12 + sm - 1)) / total * 100
        if left < 100:
            ticks.append(f'<span style="left:{left:.2f}%">{y}</span>')
    pbar = (f'<div class="pbar" data-pbar data-start="{p["start"]}" data-end="{p["end"]}" hidden>'
            '<div class="pbar-track"><span class="pbar-fill"></span><span class="pbar-today"></span></div>'
            f'<div class="pbar-years tnum">{"".join(ticks)}</div></div>')

    secs, n = [], 0
    def sec(title: str, content: str) -> str:
        return (f'<section class="psec"><div class="psec-h"><span class="ht psec-n tnum">{n:02d}</span>'
                f'<h2 class="ht">{e(title)}</h2></div>{content}</section>')
    for title, text in md_sections(summary["body"], lg):
        n += 1
        secs.append(sec(title, feature_grid(text) or f'<div class="prose">{markdown(text)}</div>'))
    cons = consortium(meta, lg)
    if cons:
        n += 1
        secs.append(sec(t["sec_consortium"], cons))
    rel = [x for x in news[lg] if p["slug"] in x["projects"]]
    if rel:
        n += 1
        secs.append(sec(t["sec_related"], "".join(
            f'<a class="rel" href="/{lg}/news/{x["slug"]}/">'
            f'<span class="tag {"tag-outline" if is_insight(x) else "tag-accent"}">'
            f'{e(t["nav_insights"] if is_insight(x) else t["nav_news"])}</span>'
            f'<span class="rel-t">{e(x["title"])}</span><span class="num">{e(x["date"])}</span></a>'
            for x in rel)))

    side = []
    if ptopics:
        side.append(blueprint(f'<span class="k">{e(t["side_topic"])}</span>' + "".join(
            f'<a class="ht side-topic" href="/{lg}/#topic-{e(tp["id"])}">{e(tp["name"][lg])}</a>'
            f'<span class="side-sub" lang="{o}">{e(tp["name"][o])}</span>' for tp in ptopics),
            cls="side-box"))
    # 참여 구성원 = 참여율에서 온 연결 ∪ 담당자(정본 「책임자 이름」).
    who = [m for m in members
           if any(x["slug"] == p["slug"] for x in m["projects"]) or m["name"]["ko"] == p["pi"]["ko"]]
    if who:
        side.append(f'<div class="side-sec"><span class="k">{e(t["side_members"])}</span><div class="chips">'
                    + "".join(f'<a class="chip" href="/{lg}/people/#{e(m["slug"])}">{e(m["name"][lg])}</a>'
                              for m in who) + '</div></div>')
    others = [q for q in projects if q["pi"]["ko"] == p["pi"]["ko"] and q["slug"] != p["slug"]
              and q["status"] != "closed"]
    if others:
        side.append(f'<div class="side-sec"><span class="k">{e(t["side_other"])}</span>' + "".join(
            f'<div class="side-proj">{project_link(lg, q, detailed, e(q["title"][lg]))}'
            f'<span class="side-sub tnum">{e(proj_meta(q, lg))}</span></div>' for q in others) + '</div>')
    side.append(f'<a class="btn btn-secondary btn-block" href="/{lg}/collaborate/#contact">'
                f'{e(t["side_contact"])}</a>')

    short_html = f'<span class="ht pshort">{e(short)}</span>' if short else ""
    body = f"""
<div class="page">
<a class="back" href="/{lg}/research/">{e(t['back_research'])}</a>
<div class="phead">{short_html}
<h1 class="ht h-proj">{e(p['title'][lg])}</h1>
<p class="psub" lang="{o}">{e(p['title'][o])}</p>
<div class="ptags">{"".join(tagrow)}</div>
</div>
<section class="psum" aria-label="{e(t['register'])}">
<div class="pcells">{cells}</div>
{pbar}
</section>
<div class="pbody">
<article class="pmain">{"".join(secs)}</article>
<aside class="pside">{"".join(side)}</aside>
</div>
</div>
"""
    crumbs = [(t["crumb_home"], f"/{lg}/"), (t["nav_projects"], f"/{lg}/research/"),
              (short or p["title"][lg], None)]
    return shell(lg, "research/", f'research/{p["slug"]}/', p["title"][lg],
                 p["title"][lg], body, site, crumbs=crumbs)


GRADE_KEY = {"수석연구원": "chief", "책임연구원": "principal", "선임연구원": "senior"}
GRADES = {"수석연구원", "책임연구원", "선임연구원", "연구원", "행정원"}


def page_people(lg, site, members, projects, detailed):
    t = T[lg]
    o = other(lg)
    by_slug = {p["slug"]: p for p in projects}

    def plist(m: dict) -> list[tuple[dict, str]]:
        """참여율에서 온 연결 ∪ 담당자로 걸린 과제(정본 「책임자 이름」)."""
        d = {x["slug"]: x["role"] for x in m["projects"]}
        for p in projects:
            if p["pi"]["ko"] == m["name"]["ko"]:
                d[p["slug"]] = "lead"
        items = [(by_slug[s], r) for s, r in d.items() if s in by_slug]
        items.sort(key=lambda x: (x[1] != "lead", x[0]["status"] == "closed", x[0]["title"][lg]))
        return items

    def count_label(items) -> str:
        live = [x for x in items if x[0]["status"] != "closed"]
        if not live:
            return ""
        own = sum(1 for x in live if x[1] == "lead")
        return nfmt(t, "count_pn", len(live)) + (t["count_own"].format(m=own) if own else "")

    def prow(p: dict, r: str) -> str:
        closed = (f'<span class="mtag">{e(t["st_closed"])}</span>' if p["status"] == "closed" else "")
        return (f'<div class="pl"><span class="rl {"own" if r == "lead" else "join"}">'
                f'{e(t["own"] if r == "lead" else t["join"])}</span>'
                f'<span class="pl-t" title="{e(p["title"][lg])}">'
                f'{project_link(lg, p, detailed, e(p["title"][lg]))}{closed}</span></div>')

    def projects_html(items) -> str:
        # ⚠️ 과제가 없으면 아무것도 싣지 않는다. 「수행 중인 과제가 없습니다」는 참여율이 아직
        #    반영되지 않은 사람에게 거짓 문장이 된다(정본에는 과제가 있는데 data 가 늦은 경우).
        if not items:
            return ""
        rows = "".join(prow(p, r) for p, r in items[:3])
        if len(items) > 3:
            rows += (f'<details class="pmore"><summary>{e(t["more_n"].format(n=len(items) - 3))}</summary>'
                     + "".join(prow(p, r) for p, r in items[3:]) + '</details>')
        return f'<div class="plist">{rows}</div>'

    for m in members:
        if m["grade"]["ko"] not in GRADES:
            block(f"구성원 {m['slug']} 의 직급이 허용 값이 아니다: {m['grade']['ko']} "
                  f"(직위 원값을 쓰지 않는다 — 고용 구분 낱말이 공개된다)")
        if m.get("admin") and m["grade"]["ko"] != "행정원":
            block(f"구성원 {m['slug']}: admin 인데 직급이 행정원이 아니다")
    directors = [m for m in members if m["org_role"]["ko"] == "센터장"]
    if len(directors) != 1:
        block(f"센터장이 정확히 한 명이어야 한다(지금 {len(directors)}명) — data/members.json org_role")
    director = directors[0] if len(directors) == 1 else None

    n_all = len(members)
    n_res = sum(1 for m in members if m.get("research"))
    n_admin = sum(1 for m in members if m.get("admin"))
    n_staff = n_all - n_res - n_admin
    figs = (fig(n_all, t["fig_all"]) + fig(n_res, t["fig_research"])
            + fig(n_staff, t["fig_staff"]) + fig(n_admin, t["fig_admin"]))

    # ⭐ 센터장이 연구진(research:true)이면 「연구진」 절 **안의 첫 사람**이다 — 밖에 두면 띠와 소개문은
    #    연구진 13 인데 절의 거르개는 「전체 12」가 되어 같은 낱말이 두 수를 낸다.
    dir_in = bool(director and director.get("research"))
    dblock = ""
    if director:
        m = director
        items = plist(m)
        links = "".join(
            f'<a class="ext" href="{e(u)}" rel="noopener" target="_blank" '
            f'title="{e(ICON_LABEL[k][lg])}" aria-label="{e(ICON_LABEL[k][lg])}">{icon(k)}</a>'
            for k, u in (m.get("links") or {}).items() if k in ICONS)
        photo = ""
        if m.get("photo"):
            pw, ph = img_size(f"assets/people/{m['photo']}")
            photo = blueprint(f'<img src="{stamp("/assets/people/" + m["photo"])}" alt="" '
                              f'width="{pw}" height="{ph}">', cls="portrait")   # 원색 — 단색 덧칠 금지(아래 게이트)
        sub = t["slash"].join(x for x in (m["grade"][lg], count_label(items)) if x)
        hx = "h3" if dir_in else "h2"
        grade = f' data-grade="{GRADE_KEY.get(m["grade"]["ko"], "other")}"' if dir_in else ""
        dblock = (f'<article class="dir" id="{e(m["slug"])}"{grade} aria-labelledby="dir-nm">{photo}'
                  f'<div class="dir-text"><div class="orgrole">{e(m["org_role"][lg])}</div>'
                  f'<{hx} class="ht dir-nm" id="dir-nm">{e(m["name"][lg])} '
                  f'<span class="dir-o" lang="{o}">{e(m["name"][o])}</span></{hx}>'
                  f'<div class="rk">{e(sub)}</div>'
                  + (f'<div class="exts">{links}</div>' if links else "")
                  + projects_html(items) + '</div></article>')

    # ⭐ 「연구진」 절 = research:true 인 사람(센터장 포함, 통계 띠의 「연구진」과 같은 모집단).
    #    과제가 있다는 이유로 넣으면 정본 갱신 뒤 띠의 수와 절의 사람 수가 조용히 갈린다.
    profiled = [m for m in members if m.get("research") and m is not director]
    listed = [m for m in members if not m.get("research") and m is not director]
    cards = []
    for m in profiled:
        items = plist(m)
        role = m["org_role"][lg]
        badge = f'<div class="orgrole">{e(role)}</div>' if role else ""
        ct = count_label(items)
        cards.append(
            f'<article class="pcard" id="{e(m["slug"])}" data-grade="{GRADE_KEY.get(m["grade"]["ko"], "other")}">'
            f'{badge}<h3 class="ht nm">{e(m["name"][lg])}</h3><div class="rk">{e(m["grade"][lg])}</div>'
            + (f'<div class="ct tnum">{e(ct)}</div>' if ct else "")
            + projects_html(items) + '</article>')
    pool = ([director] if dir_in else []) + profiled
    g_opts = [("all", f'{t["filter_all"]} {len(pool)}')]
    for ko, key in GRADE_KEY.items():
        n = sum(1 for m in pool if m["grade"]["ko"] == ko)
        if n:
            g_opts.append((key, f'{t["grade_" + key]} {n}'))
    staff = "".join(
        f'<div class="sl" id="{e(m["slug"])}"><b class="ht nm-s">{e(m["name"][lg])}</b>'
        f'<span class="rk-s">{e(m["grade"][lg])}</span></div>' for m in listed)
    body = f"""
<div class="page">
{klabel(t['k_people'])}
<h1 class="ht h-sec">{e(site['people_title'][lg])}</h1>
<p class="lede-m">{e(site['about'][lg])}</p>
<div class="figs">{figs}</div>
{"" if dir_in else dblock}
<section class="rsec" aria-labelledby="h-res">{klabel(t['k_researchers'])}
<div class="rsec-head"><h2 class="ht h-2" id="h-res">{e(t['researchers_h'])}</h2>
<div class="pfilters" data-filters hidden><div class="seg" role="group" aria-label="{e(t['grade_filter'])}">{fbuttons("grade", g_opts)}</div></div></div>
{dblock if dir_in else ""}
<div class="pcards">{"".join(cards)}</div>
</section>
<section class="ssec" aria-labelledby="h-staff">{klabel(t['k_staff'])}
<h2 class="ht h-2" id="h-staff">{e(t['staff_h'])}</h2>
<div class="stafflist">{staff}</div>
</section>
</div>
<script src="{stamp('/assets/filter.js')}" defer></script>
"""
    return shell(lg, "people/", "people/", t["title_people"], site["people_desc"][lg], body, site)

def blog_owner(members: list[dict]) -> dict | None:
    """인사이트 출처(INSIGHT_SOURCE)를 자기 홈페이지로 둔 구성원.
    ⭐ 저자는 **출처로** 정한다. 「지금 센터장」으로 정하면 센터장이 바뀌는 날 남의 블로그 글이
    새 센터장 이름으로 나간다 — 에러 없이."""
    host = host_of(INSIGHT_SOURCE)
    return next((m for m in members if host_of((m.get("links") or {}).get("homepage", "")) == host), None)


def author_of(n: dict, lg: str, members: list[dict], *, lead: bool = False) -> str:
    """인사이트의 저자 「이름 직함」. lead=True 면 영문을 「직함 이름」 순서로(문장 속에 넣을 때)."""
    d = blog_owner(members)
    if not (is_insight(n) and d):
        return ""
    role = d["org_role"][lg] or d["grade"][lg]
    if lg == "ko":
        return f'{d["name"][lg]} {role}'
    return f'{role} {d["name"][lg]}' if lead else f'{d["name"][lg]}, {role}'


def host_of(u: str) -> str:
    return u.split("://", 1)[-1].split("/", 1)[0]


def page_insights(lg, site, news, members):
    t = T[lg]
    items = [n for n in news[lg] if is_insight(n)]
    feat, rest = (items[0], items[1:]) if items else (None, [])
    fhtml = ""
    if feat:
        fhtml = blueprint(
            f'<div class="ifeat-main"><span class="k">{e(t["latest"])}</span>'
            f'<h2 class="ht ifeat-t"><a href="/{lg}/news/{feat["slug"]}/">{e(feat["title"])}</a></h2>'
            f'<p class="ifeat-s">{e(feat["summary"])}</p>'
            f'<div class="ifeat-btns"><a class="btn btn-primary" href="/{lg}/news/{feat["slug"]}/">'
            f'{e(t["read_excerpt"])}</a><a class="btn btn-secondary" href="{e(feat["source"])}" rel="noopener">'
            f'{e(t["read_source"])}</a></div></div>'
            f'<dl class="ifeat-meta"><div><dt>{e(t["date_k"])}</dt><dd class="tnum">{e(feat["date"])}</dd></div>'
            f'<div><dt>{e(t["author"])}</dt><dd>{e(author_of(feat, lg, members))}</dd></div>'
            f'<div><dt>{e(t["origin"])}</dt><dd>{e(host_of(feat["source"]))}</dd></div></dl>',
            cls="ifeat", tag="article")
    rhtml = "".join(
        f'<article class="iitem"><span class="num">{e(n["date"])}</span>'
        f'<div class="iitem-b"><h2 class="ht iitem-t"><a href="/{lg}/news/{n["slug"]}/">{e(n["title"])}</a></h2>'
        f'<p>{e(n["summary"])}</p><span class="meta">{e(author_of(n, lg, members))}{t["slash"]}'
        f'{e(host_of(n["source"]))}</span></div>'
        f'<a class="btn btn-secondary" href="{e(n["source"])}" rel="noopener">{e(t["read_source"])}</a></article>'
        for n in rest)
    if not items:
        rhtml = f'<p class="empty">{e(t["news_empty"])}</p>'
    body = f"""
<div class="page">
{klabel(t['k_insights'])}
<h1 class="ht h-sec">{e(site['insights_title'][lg])}</h1>
<p class="lede-m">{e(site['insights_lede'][lg])}</p>
<p class="disclaimer">{e(site['insights_disclaimer'][lg])}</p>
{fhtml}
<div class="ilist">{rhtml}</div>
</div>
"""
    return shell(lg, "insights/", "insights/", t["title_insights"], site["insights_desc"][lg], body, site)


def deadline_label(dl: dt.datetime) -> str:
    dl = dl.astimezone(KST)
    return f"{dl.year}.{dl.month:02d}.{dl.day:02d} {dl:%H:%M}"


def page_news_index(lg, site, news, shorts, projects, detailed, today):
    t = T[lg]
    by_slug = {p["slug"]: p for p in projects}
    items = [n for n in news[lg] if not is_insight(n)]
    open_ = [n for n in items if n["deadline"] and n["deadline"].astimezone(KST).date() >= today]
    pin = min(open_, key=lambda n: n["deadline"]) if open_ else None
    # 고정 글도 목록에 그대로 둔다 — 목록은 빠짐없는 연대기이고, 「전체 소식 n건」이 목록과 맞는다.
    rest = items

    def cat(n: dict) -> str:
        return (f'<span class="tag tag-neutral">{e(t["cat_" + n["category"]])}</span>'
                if n["category"] else "")

    def rel(n: dict) -> str:
        links = [project_link(lg, by_slug[s], detailed, e(shorts[lg].get(s) or by_slug[s]["title"][lg]))
                 for s in n["projects"] if s in by_slug]
        lab = t.get("related_many", t["related"]) if len(links) > 1 else t["related"]
        return (f'<p class="nrel"><span>{e(lab)}</span> {t["sep"].join(links)}</p>' if links else "")

    phtml = ""
    if pin:
        # 고정 액자는 JS 가 숨기지 않는다. 마감 시각이 지나면 D-n 자리만 「마감」이 되고,
        # 고정 해제는 다음 빌드가 한다(빌드는 날짜 단위로만 본다).
        phtml = blueprint(
            f'<span class="npin-l"><span class="npin-k">{cat(pin)}<span class="k" data-pin-state>{e(t["pinned"])}</span></span>'
            f'<b class="ht npin-t">{e(pin["title"])}</b><span class="npin-s">{e(pin["summary"])}</span></span>'
            f'<span class="npin-r"><span class="k">{e(t["deadline_k"])}</span>'
            f'<b class="ht npin-d tnum" data-dday-of="{pin["deadline"].astimezone(KST).isoformat()}" '
            f'data-closed="{e(t["closed"])}"></b>'
            f'<span class="tnum npin-w">{e(deadline_label(pin["deadline"]))}</span></span>',
            cls="npin", tag="a", attrs=f' href="/{lg}/news/{pin["slug"]}/"')
    groups: list[tuple[str, list[dict]]] = []
    for n in rest:
        key = n["date"][:7].replace("-", ".")
        if not groups or groups[-1][0] != key:
            groups.append((key, []))
        groups[-1][1].append(n)
    ghtml = "".join(
        f'<section class="nmonth"><h2 class="ht nm-h tnum">{e(key)}</h2>' + "".join(
            f'<article class="nitem"><div class="nday"><b class="ht tnum">'
            f'{e(t["day"].format(d=int(n["date"][8:10])))}</b>{cat(n)}</div>'
            f'<div class="nbody"><h3 class="ht ntitle"><a href="/{lg}/news/{n["slug"]}/">{e(n["title"])}</a>'
            + (f' <span class="tag tag-outline">{e(t["sample_badge"])}</span>' if n["sample"] else "")
            + f'</h3>'
            + (f'<p class="newssum">{e(n["summary"])}</p>' if n["summary"] else "")
            + rel(n) + '</div></article>' for n in ns) + '</section>'
        for key, ns in groups)
    if not items:
        ghtml = f'<p class="empty">{e(t["news_empty"])}</p>'
    body = f"""
<div class="page">
{klabel(t['k_news'])}
<h1 class="ht h-sec">{e(site['news_title'][lg])}</h1>
<p class="lede-m">{e(site['news_lede'][lg])}</p>
{phtml}
<div class="nlist-head"><span class="k">{e(t['all_news_k'])}</span><span class="count tnum">{e(nfmt(t, 'count_news', len(items)))}</span></div>
<div class="nlist">{ghtml}</div>
</div>
"""
    return shell(lg, "news/", "news/", t["title_news"], site["news_lede"][lg], body, site)


def page_news_post(lg, site, n, members):
    t = T[lg]
    ins = is_insight(n)
    note = (f'<p class="samplenote">{e(t["sample_note"])}</p>' if n["sample"] else "")
    src = (f'<p class="srcbox"><a class="btn btn-primary" href="{e(n["source"])}" rel="noopener">'
           f'{e(t["read_source"])}</a><span>{e(t["source_note"])}</span></p>' if n["source"] else "")
    # ⭐ 개인 블로그 글을 줄여 실은 소식은 본문 맨 위에 발췌 안내를 눈에 띄게 둔다(원문 주소 포함).
    #    출처가 블로그(seungwoo.datasec.work)일 때만 붙는다 — 다른 출처의 글에 센터장 이름이 붙지 않게.
    excerpt = ""
    if ins:
        shown = n["source"].removeprefix("https://").rstrip("/")
        excerpt = (f'<p class="excerpt">{e(t["excerpt_pre"].format(who=author_of(n, lg, members, lead=True)))}'
                   f'<a href="{e(n["source"])}" rel="noopener">'
                   f'{e(shown)}</a>{e(t["excerpt_post"])}</p>')
    author = (f'<span class="postby">{e(author_of(n, lg, members))}</span>' if ins else "")
    disclaimer = (f'<p class="disclaimer">{e(site["insights_disclaimer"][lg])}</p>' if ins else "")
    back = (f'<a class="back" href="/{lg}/insights/">{e(t["back_insights"])}</a>' if ins
            else f'<a class="back" href="/{lg}/news/">{e(t["back_news"])}</a>')
    body = f"""
<div class="page narrow">
{back}
<div class="num postdate">{e(n['date'])}{author}</div>
<h1 class="ht h-proj">{e(n['title'])}</h1>
{note}
{src}
{excerpt}
<div class="prose">{n['body']}</div>
{src}
{disclaimer}
</div>
"""
    # ⛔ nav_key 와 path 를 합치지 않는다 — 인사이트 글은 메뉴는 「인사이트」, 주소는 /news/<slug>/ 그대로다.
    return shell(lg, "insights/" if ins else "news/", f'news/{n["slug"]}/', n["title"],
                 n["summary"] or n["title"], body, site, og_type="article",
                 head_extra=f'\n<meta property="article:published_time" content="{e(n["date"])}">',
                 og_image=n["image"], og_alt=n["title"])


def page_collaborate(lg, site):
    t = T[lg]
    c = site["collaborate"]
    ways = []
    for i, w in enumerate(c["ways"], 1):
        link = w.get("link")
        btn = (f'<a class="btn btn-secondary" href="{e(link["url"])}" rel="noopener" target="_blank">'
               f'{e(link["label"][lg])}</a>' if link else "")
        ways.append(blueprint(
            f'<span class="ht wnum tnum">{i:02d}</span><h3 class="ht cardtitle">{e(w["title"][lg])}</h3>'
            f'<p class="cardbody">{e(w["body"][lg])}</p>{btn}',
            cls="way", tag="article", attrs=f' id="way-{e(w["id"])}"'))
    email = site.get("contact", {}).get("email", "")
    if email:
        rev = email.replace("@", " [at] ")[::-1]
        # ⭐ 복사 버튼은 hidden 으로 굽고 mail.js 가 연다 — JS 가 없으면 죽은 버튼이 보이지 않게.
        #    담는 값은 mail() 과 같은 **뒤집힌** 글자뿐이다(평문 주소 게이트).
        contact = (f'<div class="cbtns">{mail(email, cls="btn btn-primary")}'
                   f'<button type="button" class="btn btn-secondary" data-copy-mail="{e(rev)}" '
                   f'data-ok="{e(t["copied"])}" data-fail="{e(t["copy_failed"])}" hidden>{e(t["copy_mail"])}</button>'
                   f'<span class="copy-msg" aria-live="polite"></span></div>')
    else:
        contact = f'<p class="empty">{e(c["no_contact"][lg])}</p>'
    v = site["visit"]
    maplink = (f'<a class="maplink" href="{e(v["map_url"])}" rel="noopener" target="_blank">'
               f'{e(v["map_label"][lg])} ↗</a>')
    rows = [(t["addr"], f'{e(v["org_line"][lg])}<br>{e(v["address"][lg])}<br>{maplink}')]
    if v.get("phone"):
        tel = "+82" + re.sub(r"\D", "", v["phone"].split(")", 1)[-1])
        rows.append((t["phone"], f'<a class="tnum" href="tel:{e(tel)}">{e(v["phone"])}</a>'))
    dl = "".join(f'<div class="dl reg"><span class="dt">{e(k)}</span><span>{val}</span></div>'
                 for k, val in rows)
    notes = "".join(
        blueprint(f'<h3 class="ht cardtitle">{e(nn["title"][lg])}</h3>'
                  f'<p class="cardbody">{e(nn["body"][lg])}</p>', cls="way")
        for nn in v.get("notes", []) if nn["body"][lg].strip())
    body = f"""
<div class="page narrow">
{klabel(t['k_collab'])}
<h1 class="ht h-sec">{e(c['title'][lg])}</h1>
<section id="ways" class="csec">{klabel(t['k_ways'])}
<h2 class="ht h-2">{e(t['ways_h'])}</h2>
<div class="ways4">{"".join(ways)}</div>
</section>
<section id="contact" class="csec">{klabel(t['k_contact'])}
<h2 class="ht h-2">{e(t['contact_h'])}</h2>
<p class="lede-m">{e(c['contact_lede'][lg])}</p>
{contact}
</section>
<section id="visit" class="csec">{klabel(t['k_visit'])}
<h2 class="ht h-2">{e(t['visit_h'])}</h2>
<div class="visitbox">{blueprint(f'<div class="reg-inner">{dl}</div>', style="padding:18px")}</div>
{f'<div class="ways">{notes}</div>' if notes else ''}
</section>
</div>
"""
    return shell(lg, "collaborate/", "collaborate/", t["title_collab"], c["lede"][lg], body, site)

# ════════════════════════════════════════════════════════════════════
# 조립
# ════════════════════════════════════════════════════════════════════

# 이번 빌드가 쓴 파일. sitemap lastmod 를 정할 때 쪽 지문을 여기서 다시 읽는다.
WRITTEN: dict[str, str] = {}


def write(path: str, text: str) -> None:
    p = OUT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    WRITTEN[path] = text


# ── sitemap lastmod 용 쪽 지문
#    제목, 설명, JSON-LD, 본문(<main>)만 본다. 머리말 띠, 바닥글, 자산 주소의 내용 해시(?v=),
#    공백과 줄바꿈의 차이는 뺀다 - CSS 하나만 고치거나 빈 줄 하나가 늘어도 모든 쪽의 날짜가
#    바뀌면 lastmod 가 신호 구실을 못 한다. (원문 링크 버튼을 넣을 때 source 가 없는 소식에도
#    빈 줄이 생겨, 공백을 그대로 비교하면 내용이 같은 소식들이 바뀐 것으로 잡혔다.)
SIG_PARTS = (
    re.compile(r"<title>.*?</title>", re.S),
    re.compile(r'<meta name="description" content="[^"]*">'),
    re.compile(r'<script type="application/ld\+json">.*?</script>', re.S),
    re.compile(r'<main id="main">.*?</main>', re.S),
)
STAMP_QS = re.compile(r"\?v=[0-9a-f]+")
SPACES = re.compile(r"\s+")


def page_sig(text: str) -> str:
    parts = [m for rx in SIG_PARTS for m in rx.findall(text)]
    norm = SPACES.sub(" ", STAMP_QS.sub("", " ".join(parts))).strip()
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()


def previous_build() -> tuple[dict[str, str], dict[str, str]]:
    """직전 산출물(커밋된 docs/)의 쪽 지문과 sitemap lastmod. 키는 사이트 경로(`/ko/news/`).

    ⚠️ `shutil.rmtree(OUT)` **전에** 불러야 한다. 지운 뒤에는 비교할 대상이 없다.
    """
    sig: dict[str, str] = {}
    mod: dict[str, str] = {}
    if not OUT.exists():
        return sig, mod
    for f in OUT.rglob("index.html"):
        rel = f.relative_to(OUT).as_posix()
        sig["/" + rel[: -len("index.html")]] = page_sig(f.read_text(encoding="utf-8"))
    sm = OUT / "sitemap.xml"
    if sm.exists():
        for loc, d in re.findall(r"<loc>https?://[^/<]+(/[^<]*)</loc><lastmod>([^<]+)</lastmod>",
                                 sm.read_text(encoding="utf-8")):
            mod[loc] = d
    return sig, mod


# ── 문장에 박힌 수치
#    상시 문구(소개, 협력 안내)에 「연구진 12명」, 「수탁 과제 1건을 수행」처럼 숫자를 적어 두면
#    인원이 바뀌거나 과제가 끝나도 문장은 그대로 남는다. 에러는 나지 않는다 — 실제로 둘 다 그랬다.
#    ⭐ 수치는 data/ 에서 세어 자리표(`{researchers}`)로 넣는다.
# ⭐ 화면에 나가는 문구는 전부 본다(빼는 쪽을 적는다). 「검사할 키」를 나열하면 새로 싣는 키가 빠진다.
#    주소·전화·지도 주소처럼 숫자가 본래 들어가는 칸만 뺀다(찾아오는 길의 안내 글 visit.notes 는 본다).
FIXED_NUM_SKIP = ("site_url", "org_url", "contact", "visit.address", "visit.phone", "visit.map_url")
FIXED_NUM_KO = re.compile(r"\d+\s*(명|건|개)")
FIXED_NUM_EN = re.compile(
    r"\b(\d+|one(?!\s+of\b)|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|"
    r"thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|"
    r"twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|a\s+dozen|dozens\s+of)\b"
    r"(?:\s+[\w-]+){0,2}?\s+(researchers?|contracts?|projects?|programmes?|members?|people|staff)\b",
    re.I)
PLACEHOLDERS = {"{researchers}"}


def check_fixed_numbers(site: dict) -> None:
    def leaves(node, path):
        if isinstance(node, dict):
            if set(node) >= {"ko", "en"} and all(isinstance(node[x], str) for x in LANGS):
                yield path, node
                return
            for k, v in node.items():
                yield from leaves(v, f"{path}.{k}")
        elif isinstance(node, list):
            for i, v in enumerate(node):
                yield from leaves(v, f"{path}[{i}]")
    for key in (k for k in site if not k.startswith("_") and k not in FIXED_NUM_SKIP):
        for path, node in leaves(site.get(key, {}), key):
            if path in FIXED_NUM_SKIP or path.startswith(tuple(x + "." for x in FIXED_NUM_SKIP)):
                continue
            for lg, rx in (("ko", FIXED_NUM_KO), ("en", FIXED_NUM_EN)):
                m = rx.search(node[lg])
                if m:
                    block(f"content/site.json {path}.{lg} 에 수치가 박혀 있다: 「{m.group(0)}」 — "
                          f"인원·건수는 data/ 에서 세어 자리표로 넣는다")
                for ph in re.findall(r"\{[^}]*\}", node[lg]):
                    if ph not in PLACEHOLDERS:
                        block(f"content/site.json {path}.{lg} 에 모르는 자리표가 있다: {ph}")


# ── 센터명 변형. 정식 표기 하나만 통과시킨다.
#    ⚠️ 「인공지능데이터보안」만 찾으면 띄어 쓴 「인공지능데이터 보안연구센터」를 놓친다 —
#    실제로 소식 그림의 alt 에 실려 공개됐다.
CENTER_NAME = "인공지능데이터·보안연구센터"
CENTER_RX = re.compile(r"인공지능\s*\S?\s*데이터\s*\S?\s*보안\s*(?:연구\s*)?센터")
TAG_RX = re.compile(r"<[^>]+>")
# 자리표가 치환되지 않은 채 산출물에 남았는가. ⚠️ HTML 만 본다 — assets/filter.js 의 `{n}` 은 코드다.
LEFT_PLACEHOLDER_RX = re.compile(r"\{[a-z_]+\}")


def fill_placeholders(site: dict, stats: dict) -> dict:
    """⭐ 자리표(`{researchers}`)는 **여기 한 곳에서** 바꾼다. 쪽 함수마다 바꾸면, 게이트가
    받아 주는 다른 키(lede, 협력 문구)에 쓴 자리표가 글자 그대로 공개된다.
    ⚠️ `check_fixed_numbers` 는 바꾸기 **전** 원본에 돌린다 — 바꾼 뒤에는 「13명」이 걸린다."""
    values = {"{researchers}": str(stats["researchers"])}
    def walk(node):
        if isinstance(node, dict):
            return {k: (v if k.startswith("_") else walk(v)) for k, v in node.items()}
        if isinstance(node, list):
            return [walk(v) for v in node]
        if isinstance(node, str):
            for ph, v in values.items():
                node = node.replace(ph, v)
        return node
    return walk(site)


def main() -> int:
    global NEW_Y
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true",
                    help="공개 차단 사유가 하나라도 있으면 실패한다 (배포 전 필수)")
    ap.add_argument("--today", default=None, help="YYYY-MM-DD — 상태 판정 기준일")
    args = ap.parse_args()
    # ⭐ 날짜 판정은 **한국 날짜 하나**로 한다. 시스템 날짜를 쓰면 CI(UTC)와 로컬(KST)이
    #    00~09시 KST 에 하루 갈라져, 상태가 바뀌는 날(과제 종료 다음 달 1일) 새벽 push 가
    #    「docs/ 가 원본과 다르다」로 막힌다.
    kst_today = dt.datetime.now(KST).date()
    today = dt.date.fromisoformat(args.today) if args.today else kst_today

    site = load_json("content/site.json")
    projects = load_json("data/projects.json")
    members = load_json("data/members.json")
    # 소식 공개일은 한국 시각으로 판단한다(CI 는 UTC). --today 를 주면 그 날짜로 본다.
    publish_on = today
    news = load_news(publish_on)
    if BLOCKERS:
        for b in BLOCKERS:
            print(f"⛔ {b}", file=sys.stderr)
        return 1
    # ⭐ 채용 카드는 **날짜**로 판정한다(마감 날짜 ≥ 한국 시각 오늘). 시각까지 보면 마감 전에 커밋한
    #    docs/ 와 마감 뒤 CI 재빌드가 갈라져 push 검사가 실패한다. 13:00 이후 숨김은 JS 가 맡는다.
    # ⚠️ 한 건만 굽는다. 공고가 여럿 열려 있으면, 가까운 공고가 마감 시각에 닫힌 뒤 다음 예약
    #    빌드까지(약 하루) 다른 공고의 카드가 없다. 지금은 공고가 하나라 그대로 둔다.
    for lg in LANGS:
        open_ = [n for n in news[lg] if n["category"] == "hiring" and n["deadline"]
                 and n["deadline"].astimezone(KST).date() >= publish_on]
        HIRE[lg] = min(open_, key=lambda n: n["deadline"]) if open_ else None
        if HIRE[lg]:
            print(f"📌 채용 안내 카드({lg}): {HIRE[lg]['slug']} — 마감 {HIRE[lg]['deadline'].isoformat()}")

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
    # 소식이 가리키는 과제. ⛔ 없는 과제나 공개하지 않는 과제를 가리키면 막는다.
    refs = [(f"{n['slug']}.{lg}", n["projects"]) for lg in LANGS for n in news[lg]] + HELD_PROJECTS
    for where, projs in refs:
        for s in projs:
            if s not in all_slugs:
                block(f"소식 {where} 의 projects 에 없는 과제가 있다: {s}")
            elif s not in published:
                block(f"소식 {where} 이 공개하지 않는 과제를 가리킨다: {s}")
    topics = load_topics(all_slugs, published)

    NEW_Y = max((int(p["start"][:4]) for p in projects), default=today.year)
    for p in projects:
        p["status"] = status_of(p, today)
        p["new"] = p["start"][:4] == str(NEW_Y)
    order = {"lead": 0, "joint": 1, "contract": 2}
    projects.sort(key=lambda p: (p["status"] == "closed", not p["new"], order[p["role"]], p["start"]))
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
    for k in ("insights_title", "insights_lede", "insights_desc", "insights_disclaimer"):
        if not all((site.get(k) or {}).get(x, "").strip() for x in LANGS):
            block(f"content/site.json {k}: 두 언어가 모두 있어야 한다")
            site[k] = {x: (site.get(k) or {}).get(x, "") for x in LANGS}   # 막은 이유가 보이게 끝까지 굽는다
    if any(is_insight(n) for lg in LANGS for n in news[lg]) and not blog_owner(members):
        block(f"인사이트 글의 저자를 못 찾았다 — {INSIGHT_SOURCE} 를 links.homepage 로 둔 구성원이 없다")

    # ⭐ 수치는 여기 한 곳에서 센다. 쪽마다 다시 세면 같은 낱말이 다른 값을 낸다.
    stats = {
        # ⚠️ 「연구인력」이라 적히는 숫자다 — 행정 인력은 빼야 라벨이 참이 된다.
        "members": sum(1 for m in members if not m.get("admin")),
        # 수행 중 = 시작했고 끝나지 않은 과제(종료 예정 포함). ⚠️ 착수 예정은 넣지 않는다 —
        #    시작 안 한 과제를 「수행 중」이라 적으면 대외 허위다. 과제 목록의 상태 거르개도 같은 모집단이다.
        "active": sum(1 for p in projects if p["status"] in ("active", "closing")),
        # 「수행 중 주관」. 라벨에 「수행 중」을 붙여 참여형태 거르개의 「주관 N」(누적)과 구별한다.
        "lead": sum(1 for p in projects if p["role"] == "lead" and p["status"] in ("active", "closing")),
        "new": sum(1 for p in projects if p["new"]),
        # 「연구진」= 정규직 연구원(직원명부 구분 연구직). 소개문 {researchers} 에 들어간다.
        "researchers": sum(1 for m in members if m.get("research")),
    }
    check_fixed_numbers(site)          # 바꾸기 전 원본에
    site = fill_placeholders(site, stats)

    summaries = load_summaries()
    # ⭐ 소개가 **두 언어 다** 있는 과제만 상세 쪽을 갖는다. 나머지는 링크도 걸지 않는다 —
    #    빈 쪽으로 보내지 않고, sitemap 에도 넣지 않는다.
    detailed = {p["slug"] for p in projects
                if all((summaries.get(p["slug"], {}).get(x) or {}).get("body", "").strip() for x in LANGS)}
    partial = [s for s in summaries if s not in detailed]
    for s in partial:
        warn(f"과제 소개가 한 언어에만 있다(또는 공개 과제가 아니다): {s} — 두 언어가 다 있어야 상세 쪽이 생긴다")
    if len(detailed) < len(projects):
        warn(f"상세 쪽이 없는 과제 {len(projects) - len(detailed)}건 — 목록에서 링크가 걸리지 않는다. "
             f"content/projects/<slug>.ko.md 와 .en.md 를 만들면 생긴다")
    for s in detailed:
        n_items = {}
        for lg in LANGS:
            meta, body = summaries[s][lg]["meta"], summaries[s][lg]["body"]
            heads = {x[2:].strip() for x in body.splitlines() if x.startswith("# ")}
            if any(k.startswith("consortium_") for k in meta) and T[lg]["sec_consortium"] in heads:
                block(f"content/projects/{s}.{lg}.md: 추진 체계가 머리말(consortium_*)과 본문 "
                      f"「# {T[lg]['sec_consortium']}」 두 곳에 있다 — 한 곳만 둔다")
            unknown = sorted(k for k in meta if k.startswith("consortium_") and k not in CONSORTIUM_KEYS)
            if unknown:
                block(f"content/projects/{s}.{lg}.md: 모르는 추진 체계 키 {unknown} — "
                      f"{' / '.join(CONSORTIUM_KEYS)} 만 읽는다(나머지는 조용히 버려진다)")
            # 주관·비고는 있고 없음, 공동·수요는 기관 수. 한쪽 언어에만 있으면 그 언어에서만 절이 빠진다.
            n_items[lg] = (bool(meta.get("consortium_lead", "").strip()),
                           len(split_list(meta.get("consortium_joint", ""))),
                           len(split_list(meta.get("consortium_demand", ""))),
                           bool(meta.get("consortium_note", "").strip()))
        if len(set(n_items.values())) > 1:
            block(f"content/projects/{s}: 두 언어의 추진 체계가 다르다(주관 유무, 공동 수, 수요 수, 비고 유무) {n_items}")
    # 약칭은 언어마다 그 언어 파일의 `short:` 다(상세 쪽 머리와 같은 값).
    shorts = {lg: {s: (summaries[s][lg]["meta"].get("short") or "").strip() for s in detailed} for lg in LANGS}

    # 지우기 전에 직전 산출물을 읽어 둔다 - sitemap lastmod 를 이어 쓰는 데 필요하다.
    prev_sig, prev_mod = previous_build()
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    for lg in LANGS:
        write(f"{lg}/index.html", page_home(lg, site, projects, members, news, stats, detailed, topics))
        write(f"{lg}/research/index.html",
              page_research(lg, site, projects, members, detailed, topics, stats))
        write(f"{lg}/people/index.html", page_people(lg, site, members, projects, detailed))
        write(f"{lg}/news/index.html",
              page_news_index(lg, site, news, shorts, projects, detailed, today))
        write(f"{lg}/insights/index.html", page_insights(lg, site, news, members))
        write(f"{lg}/collaborate/index.html", page_collaborate(lg, site))
        for src in REDIRECTS:
            write(f"{lg}/{src}index.html", redirect_page(lg, site, src))
        for p in projects:
            if p["slug"] not in detailed:
                continue
            write(f"{lg}/research/{p['slug']}/index.html",
                  page_project(lg, site, p, members, summaries[p["slug"]][lg], topics, projects, news,
                               detailed))
        for n in news[lg]:
            write(f"{lg}/news/{n['slug']}/index.html", page_news_post(lg, site, n, members))

    shutil.copytree(ROOT / "assets", OUT / "assets")
    # ⛔ 검색엔진 소유확인 파일은 **여기** 둔다. `docs/` 루트에 직접 두면 다음 빌드의
    #    `shutil.rmtree(OUT)` 가 조용히 지우고, 소유확인이 에러 없이 끊긴다.
    #    ⚠️ 네이버 소유확인은 만료가 있다(1년, 30일 전 알림) — 파일을 지우면 안 된다.
    verify_files: set[str] = set()
    vdir = ROOT / "content" / "verify"
    if vdir.exists():
        for f in sorted(vdir.iterdir()):
            if f.is_file() and not f.name.startswith(".") and f.name != "README.md":
                shutil.copy2(f, OUT / f.name)
                verify_files.add(f.name)
    # ⭐ 도메인은 `content/site.json` 의 `site_url` 하나에서 온다 — 여섯 군데에 박아 두면
    #    도메인을 바꿀 때 한 군데를 반드시 빠뜨린다(그리고 에러는 안 난다).
    base = site["site_url"].rstrip("/")
    host = base.split("://", 1)[-1].strip("/")
    write("CNAME", host + "\n")
    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    write("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {base}/sitemap.xml\n")

    # ⭐ `lastmod` 는 **그 쪽 내용이 마지막으로 바뀐 날**이다. 쪽마다 지문(page_sig)을 직전
    #    산출물과 비교해, 같으면 직전 docs/sitemap.xml 의 날짜를 잇고 바뀐 쪽만 빌드한 날로 둔다.
    #    날짜의 정본은 **커밋된 docs/sitemap.xml** 이다. CI 는 같은 원본을 다시 구우므로 지문이
    #    같고 날짜도 같다 - 「docs/ 가 원본과 같은가」 검사와 어긋나지 않는다.
    # ⛔ 예전에는 홈, 목록, 소개 쪽 전부에 `data/meta.json` 의 asof 하나를 썼다. 새 소식이 홈과
    #    소식 목록에 올라가고 히어로 문구가 바뀌어도 lastmod 가 8월 7일에 머물렀다. 구글은
    #    lastmod 가 일관되게 정확할 때만 쓰므로, 틀린 날짜가 이어지면 이 신호를 쓰지 않게 된다.
    # ⚠️ 바뀐 쪽에는 `--today` 가 아니라 **실제 오늘**을 쓴다. `--today` 는 상태 판정 실험용이라
    #    미래 날짜가 sitemap 에 박힐 수 있다.
    built_on = kst_today.isoformat()
    urls: list[tuple[str, str]] = []
    for lg in LANGS:
        paths = [f"/{lg}/{s}" for s in
                 ("", "research/", "insights/", "news/", "people/", "collaborate/")]
        paths += [f"/{lg}/research/{p['slug']}/" for p in projects if p["slug"] in detailed]
        paths += [f"/{lg}/news/{n['slug']}/" for n in news[lg]]
        for u in paths:
            same = prev_sig.get(u) == page_sig(WRITTEN[u.lstrip("/") + "index.html"])
            urls.append((u, prev_mod[u] if same and prev_mod.get(u) else built_on))
    write("sitemap.xml",
          '<?xml version="1.0" encoding="UTF-8"?>\n'
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
          + "".join(f"<url><loc>{base}{u}</loc>"
                    + (f"<lastmod>{d}</lastmod>" if d else "") + "</url>\n"
                    for u, d in urls)
          + "</urlset>\n")

    # ⭐ 루트는 meta refresh 와 canonical 만 둔다. ⛔ 브라우저 언어로 /en/ 에 보내던 JS 를 지웠다 —
    #    Google 은 자동 언어 리디렉션을 피하라고 하고, canonical·refresh(/ko/)와 JS 대상(/en/)이 어긋났다.
    #    영어 사용자에게는 국문 홈의 안내 줄(en-note)이 영문판을 알린다.
    write("index.html", f"""<!doctype html>
<html lang="{DEFAULT_LANG}">
<head><meta charset="utf-8">
<title>{e(site['center'][DEFAULT_LANG])}</title>
<link rel="canonical" href="{base}/{DEFAULT_LANG}/">
<meta http-equiv="refresh" content="0; url=/{DEFAULT_LANG}/">
</head>
<body><p><a href="/{DEFAULT_LANG}/">{e(site['center'][DEFAULT_LANG])}</a> · <a href="/en/">English</a></p></body></html>
""")
    write("404.html", f"""<!doctype html>
<html lang="{DEFAULT_LANG}"><head><meta charset="utf-8"><title>404</title>
<link rel="stylesheet" href="{stamp('/assets/industry.css')}"><link rel="stylesheet" href="{stamp('/assets/site.css')}">
</head><body data-lang="ko"><main id="main"><div class="page narrow">
<h1 class="ht h-sec">404</h1>
<p class="lede-m">요청하신 페이지를 찾을 수 없습니다. / The page you asked for is not here.</p>
<p><a href="/ko/">한국어</a> · <a href="/en/">English</a></p>
</div></main></body></html>
""")

    pages = {f.relative_to(OUT).as_posix(): f.read_text(encoding="utf-8") for f in OUT.rglob("*.html")}
    redirect_files = {f"{lg}/{src}index.html": (lg, dst, frag)
                      for lg in LANGS for src, (dst, frag) in REDIRECTS.items()}

    # ⛔ **메일 주소가 평문으로 새어 나갔는지 산출물에서 확인한다.** `mail()` 을 한 군데라도
    #    안 거치면 그 쪽만 조용히 수집 대상이 된다 — 실제로 홈의 「이메일」 줄을 놓쳤었다.
    # ⛔ **센터명의 가운뎃점.** 정식 표기는 `인공지능데이터·보안연구센터` 다.
    #    점 없는 표기가 섞이면 같은 조직이 두 이름으로 검색엔진에 잡히고, 문서마다 달라진다.
    #    ⚠️ 사람이 지킬 규약으로 두면 반드시 다시 섞인다 — 산출물에서 직접 막는다.
    for rel, text in pages.items():
        if "인공지능데이터보안" in text:
            block(f"센터명에 가운뎃점이 빠졌다: {rel} — 「{CENTER_NAME}」가 정식 표기다")
        plain = TAG_RX.sub("", text)        # <b>인공지능데이터</b>·보안… 처럼 태그로 끊긴 경우
        found = {m.group(0) for rx_text in (text, plain) for m in CENTER_RX.finditer(rx_text)}
        for ph in sorted(set(LEFT_PLACEHOLDER_RX.findall(text))):
            block(f"자리표가 바뀌지 않은 채 실렸다: {rel} {ph} — fill_placeholders 에 값을 더한다")
        for bad in sorted(found - {CENTER_NAME}):
            block(f"센터명이 정식 표기와 다르다: {rel} 「{bad}」 — 「{CENTER_NAME}」가 정식 표기다")

    # ⚠️ 일반 정규식으로 훑으면 `logo@2x.png` 같은 srcset 이 걸린다 — **지키려는 주소**만 본다.
    #    「adsrc [at] keti.re.kr」 같은 형태도 막는다(뒤집지 않은 로컬부·구분자·도메인 조합).
    addr = site.get("contact", {}).get("email", "")
    if addr:
        local, _, domain = addr.partition("@")
        addr_rx = re.compile(re.escape(local) + r"\s*(?:@|\[at\]|\(at\)|\s)\s*" + re.escape(domain), re.I)
    for rel, text in pages.items():
        if "mailto:" in text:
            block(f"평문 mailto: 가 남았다: {rel} — mail() 을 거쳐라")
        if addr and addr_rx.search(text):
            block(f"평문 메일 주소가 남았다: {rel} — mail() 을 거쳐라")

    # ⛔ **광고 차단 목록에 걸리는 이름.** 차단 필터는 class/id 의 토큰(「-」, 「_」로 나눈 낱말)을
    #    본다. 채용 카드 같은 셸 요소가 `banner`, `popup` 같은 이름을 달면 방문자 화면에서 조용히 사라진다.
    #    부분 문자열은 상관없다(`masthead` 의 「ad」는 토큰이 아니다).
    BANNED = {"ad", "ads", "banner", "popup", "pop", "modal", "overlay", "interstitial",
              "newsletter", "subscribe"}
    BANNED_PREFIX = ("advert", "promo", "sponsor")
    for rel, text in pages.items():
        for attr in re.findall(r'\s(?:class|id)="([^"]*)"', text):
            for tok in re.split(r"[\s_-]+", attr.lower()):
                if tok in BANNED or tok.startswith(BANNED_PREFIX):
                    block(f"광고 차단에 걸리는 이름: {rel} 「{attr}」 — 토큰 「{tok}」")
            # ⛔ 사진을 강철색 한 가지로 덮지 않는다(.duotone) — 얼굴이 창백한 파랑이 된다.
            if "duotone" in attr.split():
                block(f"사진에 단색 덧칠(.duotone)이 걸렸다: {rel} 「{attr}」 — 사진은 원색으로 싣는다")

    # ⛔ **미공개 과제가 새어 나갔는지 산출물에서 직접 확인한다.** 걸러 냈다고 믿지 않는다 —
    #    뉴스 글이나 과제 소개문이 제목·slug 를 그대로 적어 두면 거르기를 통과한다.
    if withheld:
        needles = {n for p in withheld
                   for n in (p["slug"], p["title"]["ko"], p["title"]["en"]) if n}
        for rel, text in pages.items():
            for n in needles:
                if n in text:
                    block(f"미공개 과제가 산출물에 실렸다: {rel} ← \"{n[:40]}…\"")

    # ⛔ **canonical 이 자기 주소를 가리키는지 확인한다.** 목록 쪽 주소를 넘기면 그 쪽은
    #    색인이 불가능해진다 — 구글은 canonical 을 따른다. 실제로 소식 상세 4쪽이 그랬다.
    #    ⚠️ 예외: 루트(`/`)는 기본 언어를, 404 는 canonical 이 없고, 검색엔진 소유확인 파일은
    #    그쪽이 정한 형식이다. 옮긴 주소(REDIRECTS)는 끄지 않고 **대상**을 가리키는지 본다.
    for rel, text in pages.items():
        if rel in ("index.html", "404.html") or rel in verify_files:
            continue
        m = re.search(r'<link rel="canonical" href="([^"]+)"', text)
        if rel in redirect_files:
            lg, dst, frag = redirect_files[rel]
            want = f"{base}/{lg}/{dst}"
        else:
            want = f"{base}/{rel.rsplit('/', 1)[0]}/" if "/" in rel else f"{base}/"
        if not m:
            block(f"canonical 이 없다: {rel}")
        elif m.group(1) != want:
            block(f"canonical 이 자기 주소가 아니다: {rel}\n"
                  f"      있는 값 {m.group(1)}\n      있어야 할 값 {want}")
    if "<script" in pages.get("index.html", ""):
        block("루트 index.html 에 스크립트가 있다 — 언어 자동 이동을 다시 넣지 않는다")

    # ⛔ **내부 링크와 앵커.** CI 의 링크 검사는 `#` 뒤와 meta refresh 를 보지 않았다 —
    #    `/collaborate/#contact`, `/people/#<slug>` 의 앵커가 사라져도 초록이었다. 여기서 모두 본다.
    ids: dict[str, dict[str, int]] = {}
    def ids_of(rel: str) -> dict[str, int]:
        if rel not in ids:
            c: dict[str, int] = {}
            for i in re.findall(r'\sid="([^"]+)"', pages.get(rel, "")):
                c[i] = c.get(i, 0) + 1
            ids[rel] = c
        return ids[rel]
    for rel, text in pages.items():
        targets = re.findall(r'\s(?:href|src)="([^"]+)"', text)
        targets += re.findall(r'http-equiv="refresh" content="0; url=([^"]+)"', text)
        for u in targets:
            if u.startswith(("http://", "https://", "mailto:", "tel:", "data:", "//")) or u == "#":
                continue
            path, _, frag = u.partition("#")
            path = path.split("?", 1)[0]
            if not path:
                target = rel
            elif path.startswith("/"):
                fp = OUT / path.lstrip("/")
                if path.endswith("/") or fp.is_dir():
                    fp = fp / "index.html"
                if not fp.exists():
                    block(f"깨진 내부 링크: {rel} → {u}")
                    continue
                target = fp.relative_to(OUT).as_posix()
            else:
                continue
            if frag and target.endswith(".html"):
                k = ids_of(target).get(frag, 0)
                if k != 1:
                    block(f"앵커가 {'없다' if k == 0 else '겹친다'}: {rel} → {u}")
    # ⛔ 쪽마다 <h1> 하나(셸로 쓴 쪽). 홈의 h1 은 센터 정식명이다(CLAUDE.md §9).
    shell_pages = {rel for rel, text in pages.items() if '<main id="main">' in text and rel != "404.html"}
    for rel in sorted(shell_pages):
        k = len(re.findall(r"<h1[\s>]", pages[rel]))
        if k != 1:
            block(f"<h1> 이 {k}개다: {rel} — 쪽마다 하나")
    for lg in LANGS:
        if f'"@id":"{base}/#center"' not in pages.get(f"{lg}/index.html", ""):
            block(f"홈({lg})에 Organization JSON-LD 가 없다")
    # ⛔ sitemap 은 셸로 쓴 쪽 전부여야 한다 — 손으로 쓴 경로 목록이라, 쪽을 새로 만들고
    #    목록에 안 넣으면 그 쪽이 sitemap 에서 조용히 빠진다.
    want_urls = {"/" + rel[: -len("index.html")] for rel in shell_pages}
    have_urls = {u for u, _ in urls}
    for u in sorted(want_urls - have_urls):
        block(f"sitemap 에 없는 쪽: {u}")
    for u in sorted(have_urls - want_urls):
        block(f"sitemap 에 있는데 쪽이 없다: {u}")
    # ⛔ 인사이트 고지문: 인사이트 목록과 인사이트 글에는 반드시, 다른 소식에는 싣지 않는다.
    for lg in LANGS:
        disc = e(site["insights_disclaimer"][lg])
        if not disc:
            continue                     # 비었으면 위에서 이미 막았다 — 빈 문자열은 어디에나 「있다」
        main_of = lambda rel: (re.search(r'<main id="main">(.*?)</main>', pages.get(rel, ""), re.S) or [None, ""])[1]
        if disc not in main_of(f"{lg}/insights/index.html"):
            block(f"인사이트 쪽({lg})에 고지문이 없다")
        for n in news[lg]:
            has = disc in main_of(f"{lg}/news/{n['slug']}/index.html")
            if is_insight(n) and not has:
                block(f"인사이트 글에 고지문이 없다: {lg}/news/{n['slug']}/")
            if not is_insight(n) and has:
                block(f"소식 글에 인사이트 고지문이 실렸다: {lg}/news/{n['slug']}/")

    n_pages = len(pages)
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
