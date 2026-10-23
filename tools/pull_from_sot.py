#!/usr/bin/env python3
"""정본(SoT) 엑셀 → `data/*.json`. ⭐ **사이트가 KB 를 부르지 않는 이유가 이 파일이다.**

흐름:

    01. 센터 현황/*.xlsx        (사내, 사람이 회사 시스템에서 내려받아 갱신)
        └─ tools/pull_from_sot.py   ← 여기 (사내에서만 돈다)
             └─ data/*.json          ← 커밋된다. 사이트는 이것만 읽는다
                  └─ PR              ← 리뷰가 곧 「무엇을 공개할지」의 결정이다

⭐ **덮어쓰지 않고 합친다.** 정본이 소유한 것만 갱신하고, 사람이 정한 것(slug · 영문 제목 ·
   영문 이름 확인 여부 · 외부 링크 · 사진 · 보직)은 **건드리지 않는다.**
   - 과제(`projects.json`): 기간, 참여형태, 책임자 ← `{YY}년 수행과제 현황.xlsx`
   - 구성원(`members.json`): 직급, 연구진/행정 구분 ← `{YY}년 부서 현황.xlsx` 의 `직원명부`
   - 구성원의 수행 과제 ← `{YY}년 부서 참여율.xlsx` (월 참여율이 0보다 큰 행만)
⛔ 새 과제·새 사람이 나타나면 **자동으로 싣지 않는다.** slug 와 영문 이름이 없기 때문이다 —
   보고만 하고 사람이 채운다. 그래야 번역되지 않은 제목이 대외 페이지로 새지 않는다.
⛔ **못 읽었으면 실패다**(종료코드 1). 정본 서식이 바뀌어 0건을 읽고도 「바뀐 값 없음」으로
   끝난 적이 있다. 오류가 있으면 `--write` 도 하지 않는다.
⚠️ 이 스크립트는 openpyxl 이 필요하고 정본 폴더에 닿아야 한다. **사이트 빌드에는 필요 없다.**
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
KETI_KB = pathlib.Path(os.environ.get("KETI_KB", pathlib.Path.home() / "work" / "keti-kb"))
SOT_DIR = pathlib.Path(os.environ.get(
    "KETI_SOT",
    pathlib.Path.home() / "Library/CloudStorage/GoogleDrive-seungwoo.kum@gmail.com"
    / "내 드라이브/인공지능데이터보안연구센터 공유폴더/01. 센터 현황"))

ROLE = {"주관": "lead", "참여(공동)": "joint", "기업수탁": "contract",
        "위탁": "joint", "기업 외 수탁": "contract"}

# 직원명부 `직위` → 사이트 직급. ⛔ 표에 없는 값이면 **실패**다 — 짐작하지 않는다.
# ⛔ 고용 구분 낱말(`전문계약직원`, `파견직원`, `비정규직`)은 `data/` 에 쓰지 않는다. 대응표로 바꾼 직급만 쓴다.
GRADE = {"수석": "수석연구원", "책임": "책임연구원", "선임": "선임연구원",
         "전문계약직원": "연구원", "파견직원": "행정원"}
GRADE_EN = {"수석연구원": "Chief Researcher", "책임연구원": "Principal Researcher",
            "선임연구원": "Senior Researcher", "연구원": "Researcher", "행정원": "Administrative Staff"}
RESEARCH_KIND = "연구직"
"""직원명부 `구분` 이 이것이면 `research: true` — 구성원 쪽 「연구진」과 소개문 `{researchers}` 의 모집단."""

# ⛔ 정본 과제명은 `(R)`·`(C)`·`(N)` 접두를 달고 다니고, 이중 공백이 섞여 있다
#    (실측: `…기술기반  실시간…`, `…플랫폼  구축…`, `(R) 해양…`).
#    이름을 **있는 그대로** 맞추면 18건이 전부 매칭에 실패한다 — 그러면 이 도구는
#    "바뀐 값 0건, 새 과제 18건"이라고 조용히 거짓말한다.
_PREFIX = re.compile(r"^\(\s*[A-Z]\s*\)\s*")


def norm(name: str) -> str:
    """비교용 이름. ⚠️ 표시용이 아니다 — 화면에 나가는 것은 `data/*.json` 의 제목이다."""
    return re.sub(r"\s+", " ", _PREFIX.sub("", name or "")).strip()


def load_adapter():
    """정본 어댑터는 keti-kb 가 갖는다 — 여기서 파서를 두 벌 만들지 않는다."""
    sys.path.insert(0, str(KETI_KB))
    try:
        from kb.adapters.sot import xlsx  # noqa: E402
    except Exception as exc:                     # pragma: no cover
        print(f"⛔ 정본 어댑터를 못 읽었다: {exc}\n"
              f"   KETI_KB={KETI_KB} 가 맞는지, openpyxl 이 있는지 보라.", file=sys.stderr)
        raise SystemExit(2)
    if not hasattr(xlsx, "read_staff"):          # pragma: no cover
        print("⛔ keti-kb 의 정본 어댑터가 옛 판이다(read_staff 없음) — keti-kb 를 최신으로 받아라.",
              file=sys.stderr)
        raise SystemExit(2)
    return xlsx


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true", help="실제로 data/*.json 을 고친다")
    args = ap.parse_args()

    xlsx = load_adapter()
    read = xlsx.read_all(SOT_DIR)
    errors = [f"{r.name}: {e}" for r in read.values() for e in r.errors]
    warnings = [w for r in read.values() for w in r.warnings]

    # ── ① 과제 ─────────────────────────────────────────────────────────
    running = [p for p in read["projects"].projects if p.standing == "수행"]
    cur = json.loads((ROOT / "data" / "projects.json").read_text(encoding="utf-8"))
    by_title = {norm(p["title"]["ko"]): p for p in cur}

    changed: list[str] = []
    unseen: list[str] = []
    for sp in running:
        p = by_title.get(norm(sp.name))
        if p is None:
            unseen.append(sp.name)
            continue
        for field, value in (("start", sp.start), ("end", sp.end)):
            v = value[:7] if value else None          # YYYY-MM
            if v and p.get(field) != v:
                changed.append(f"{p['slug']}.{field}: {p.get(field)} → {v}")
                p[field] = v
        role = ROLE.get(sp.role or "")
        if role and p.get("role") != role:
            changed.append(f"{p['slug']}.role: {p.get('role')} → {role}  ⚠️ 대외 표기가 바뀐다")
            p["role"] = role
        if sp.pi and p["pi"]["ko"] != sp.pi:
            changed.append(f"{p['slug']}.pi: {p['pi']['ko']} → {sp.pi}")
            p["pi"]["ko"] = sp.pi
            p["pi"]["en"] = ""                        # 영문은 사람이 채운다
    live = {norm(s.name) for s in running}
    gone = [p["slug"] for p in cur if norm(p["title"]["ko"]) not in live]
    if running and len(unseen) == len(running):
        errors.append("정본 과제 전부가 사이트 목록과 안 맞는다 — 이름 정규화가 깨졌을 가능성이 크다. "
                      "아래 '정본에만 있는 과제' 를 먼저 눈으로 보라")

    # ── ② 구성원: 직급과 구분은 직원명부(전원)에서 ───────────────────────
    members = json.loads((ROOT / "data" / "members.json").read_text(encoding="utf-8"))
    by_name = {m["name"]["ko"]: m for m in members}
    files, _ = xlsx.resolve_files(SOT_DIR)
    if files["proposals"]:
        staff, staff_err = xlsx.read_staff(SOT_DIR / files["proposals"])
    else:
        staff, staff_err = [], ["직원명부를 담은 부서 현황 파일이 없다"]
    errors += [f"직원명부: {e}" for e in staff_err]
    m_changed: list[str] = []
    for s in staff:
        grade = GRADE.get(s.rank or "")
        if grade is None:
            # ⚠️ 원값은 화면(이 도구의 출력)에만 찍는다 — data/ 에는 쓰지 않는다.
            errors.append(f"직원명부 {s.name}: 직위 「{s.rank}」 가 대응표(GRADE)에 없다")
            continue
        m = by_name.get(s.name)
        if m is None:
            continue
        research = s.kind == RESEARCH_KIND
        admin = grade == "행정원"
        if m["grade"]["ko"] != grade:
            m_changed.append(f"{m['slug']}.grade: {m['grade']['ko']} → {grade}")
            m["grade"] = {"ko": grade, "en": GRADE_EN[grade]}
        if bool(m.get("research")) != research:
            m_changed.append(f"{m['slug']}.research: {bool(m.get('research'))} → {research}")
            m["research"] = research
        if bool(m.get("admin")) != admin:
            m_changed.append(f"{m['slug']}.admin: {bool(m.get('admin'))} → {admin}")
            if admin:
                m["admin"] = True
            else:
                m.pop("admin", None)
    roster_only = sorted({s.name for s in staff} - set(by_name))
    site_only = sorted(set(by_name) - {s.name for s in staff}) if staff else []

    # ── ③ 구성원의 수행 과제: 참여율(명단에 있는 사람)에서 ───────────────────
    #    ⭐ 계정으로 잇는다(참여율 시트의 계정번호 = 수행과제 현황의 `계정`). 이름은 마지막 수단이다.
    #    ⛔ 부서 외 과제(외부과제 시트)는 사이트 과제가 아니다 — 세지 않는다.
    #    ⚠️ 기업수탁 과제는 참여율에 잡히지 않는다 — 그 과제의 기존 연결은 지우지 않는다.
    slug_of = {norm(p["title"]["ko"]): p["slug"] for p in cur}
    role_of = {p["slug"]: p.get("role") for p in cur}
    title_of_code = {c: norm(sp.name) for sp in running for c in (sp.account_no, sp.project_no) if c}
    listed = {p.name for p in read["people"].people}
    want: dict[str, dict[str, str]] = {n: {} for n in listed}
    unmatched: list[str] = []
    for row in read["people"].participation:
        if row.external:
            continue
        title = (title_of_code.get(row.account_no) if row.account_no else None) or norm(row.project_name)
        slug = slug_of.get(title)
        if slug is None:
            unmatched.append(f"{row.person} · {row.account_no or '번호 없음'} · {norm(row.project_name)[:40]}")
            continue
        got = want.setdefault(row.person, {})
        got[slug] = "lead" if row.role == "책임자" or got.get(slug) == "lead" else "member"
    if unmatched:
        errors.append(f"사이트 과제에 못 붙인 참여 {len(unmatched)}건 — 아래 '미매칭' 을 보라")
    p_changed: list[str] = []
    not_listed = 0
    for m in members:
        if m["name"]["ko"] not in listed:
            not_listed += 1                     # 참여율 명단 밖 — 이 도구는 그 사람의 과제를 모른다
            continue
        old = {x["slug"]: x["role"] for x in m["projects"]}
        new = dict(want.get(m["name"]["ko"], {}))
        for s, r in old.items():                # 기업수탁 연결은 참여율이 모르므로 그대로 둔다
            if role_of.get(s) == "contract" and s not in new:
                new[s] = r
        if new != old:
            add = sorted(set(new) - set(old))
            rm = sorted(set(old) - set(new))
            rc = sorted(s for s in set(new) & set(old) if new[s] != old[s])
            p_changed.append(f"{m['slug']}: " + " ".join(
                [f"+{s}" for s in add] + [f"-{s}" for s in rm] + [f"~{s}({old[s]}→{new[s]})" for s in rc]))
            order = [x["slug"] for x in m["projects"] if x["slug"] in new] + [s for s in new if s not in old]
            m["projects"] = [{"slug": s, "role": new[s]} for s in order]

    print(f"정본: 수행 과제 {len(running)} · 직원명부 {len(staff)} · 참여율 명단 {len(listed)} · "
          f"참여관계 {len(read['people'].participation)}")
    print(f"사이트: 과제 {len(cur)} · 구성원 {len(members)} (참여율 명단 밖 {not_listed}명은 수행 과제를 손대지 않는다)")
    for label, items in (("바뀐 값: 과제", changed), ("바뀐 값: 구성원 직급, 구분", m_changed),
                         ("바뀐 값: 구성원 수행 과제", p_changed),
                         ("정본에만 있는 과제(사람이 slug, 영문명을 채워야 한다)", unseen),
                         ("정본에서 사라진 과제(종료 처리 대상)", gone),
                         ("직원명부에만 있는 사람(사람이 slug, 영문 이름을 채워야 한다)", roster_only),
                         ("사이트에만 있는 사람", site_only),
                         ("미매칭(사이트 과제에 못 붙인 참여)", unmatched),
                         ("어댑터 경고", warnings)):
        if items:
            print(f"\n── {label} ({len(items)})")
            for x in items:
                print(f"   {x}")
    if errors:
        print("", file=sys.stderr)
        for e in errors:
            print(f"⛔ {e}", file=sys.stderr)
        print("\n⛔ 정본을 제대로 못 읽었다 — data/ 를 고치지 않는다.", file=sys.stderr)
        return 1

    if args.write and (changed or m_changed or p_changed):
        if changed:
            (ROOT / "data" / "projects.json").write_text(
                json.dumps(cur, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        if m_changed or p_changed:
            (ROOT / "data" / "members.json").write_text(
                json.dumps(members, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print("\n✅ data/*.json 갱신. `python3 build.py` 로 다시 그린 뒤 PR 을 연다.")
    elif changed or m_changed or p_changed:
        print("\n(미리보기다. 실제로 고치려면 --write)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
