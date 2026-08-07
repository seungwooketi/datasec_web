#!/usr/bin/env python3
"""정본(SoT) 엑셀 → `data/*.json`. ⭐ **사이트가 KB 를 부르지 않는 이유가 이 파일이다.**

흐름:

    01. 센터 현황/*.xlsx        (사내, 사람이 회사 시스템에서 내려받아 갱신)
        └─ tools/pull_from_sot.py   ← 여기 (사내에서만 돈다)
             └─ data/*.json          ← 커밋된다. 사이트는 이것만 읽는다
                  └─ PR              ← 리뷰가 곧 「무엇을 공개할지」의 결정이다

⭐ **덮어쓰지 않고 합친다.** 정본이 소유한 것(부처·기간·참여형태·책임자)만 갱신하고,
   사람이 정한 것(slug · 영문 제목 · 영문 이름 확인 여부 · 외부 링크)은 **건드리지 않는다.**
⛔ 새 과제가 나타나면 **자동으로 싣지 않는다.** slug 와 영문 제목이 없기 때문이다 —
   보고만 하고 사람이 채운다. 그래야 번역되지 않은 제목이 대외 페이지로 새지 않는다.
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
    / "내 드라이브/센터 업무/01. 센터 현황"))

ROLE = {"주관": "lead", "참여(공동)": "joint", "기업수탁": "contract",
        "위탁": "joint", "기업 외 수탁": "contract"}

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
    return xlsx


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true", help="실제로 data/*.json 을 고친다")
    args = ap.parse_args()

    xlsx = load_adapter()
    read = xlsx.read_all(SOT_DIR)
    warnings = [w for r in read.values() for w in r.warnings]

    running = [p for p in read["projects"].projects if p.standing == "수행"]
    people = read["people"].people
    part = read["people"].participation

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
        print("⛔ 정본 과제 전부가 사이트 목록과 안 맞는다 — 이름 정규화가 깨졌을 가능성이 크다.\n"
              "   이 상태로 --write 하지 마라. 아래 '정본에만 있는 과제' 를 먼저 눈으로 보라.",
              file=sys.stderr)

    grades = {p.name: p for p in people}
    members = json.loads((ROOT / "data" / "members.json").read_text(encoding="utf-8"))
    for m in members:
        sp = grades.get(m["name"]["ko"])
        if sp and sp.grade and not m["grade"]["ko"].startswith(sp.grade):
            changed.append(f"{m['slug']}.grade: {m['grade']['ko']} → {sp.grade}연구원")
    roster_only = sorted({p.name for p in people} - {m["name"]["ko"] for m in members})
    site_only = sorted({m["name"]["ko"] for m in members} - {p.name for p in people})

    print(f"정본: 수행 과제 {len(running)} · 부서원 {len(people)} · 참여관계 {len(part)}")
    print(f"사이트: 과제 {len(cur)} · 구성원 {len(members)}")
    for label, items in (("바뀐 값", changed), ("정본에만 있는 과제(사람이 slug·영문명을 채워야 한다)", unseen),
                         ("정본에서 사라진 과제(종료 처리 대상)", gone),
                         ("명단에만 있는 사람", roster_only), ("사이트에만 있는 사람", site_only),
                         ("어댑터 경고", warnings)):
        if items:
            print(f"\n── {label} ({len(items)})")
            for x in items:
                print(f"   {x}")

    if args.write and changed:
        (ROOT / "data" / "projects.json").write_text(
            json.dumps(cur, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print("\n✅ data/projects.json 갱신. `python3 build.py` 로 다시 그린 뒤 PR 을 연다.")
    elif changed:
        print("\n(미리보기다. 실제로 고치려면 --write)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
