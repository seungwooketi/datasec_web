#!/usr/bin/env python3
"""정본 갱신 자동화 — 매달 정본 엑셀로 `data/*.json` 을 갱신해 **PR 을 연다**(병합은 사람이 한다).

    python tools/sot_pr.py            # 실제로 돈다(LaunchAgent 가 매달 1일 10:00 에 부른다)
    python tools/sot_pr.py --dry-run  # 무엇을 할지만 찍는다 — 푸시, PR, 두레이 없음

흐름:
    ① 별도 작업 트리(origin/main)에서 `pull_from_sot.py --write --report` → ② `build.py --strict`
    ③ 바뀐 것이 있으면 가지 `sot/YYYY-MM-DD` 로 커밋, 푸시, PR → ④ 두레이 @swkum 업무로 알린다

⭐ **사람의 작업 트리를 건드리지 않는다.** `~/Library/Caches/datasec-sot-pr/wt` 에 origin/main 을 따로 꺼낸다.
⭐ **매달 1일인 이유.** 참여율이 월 단위로 갱신되고, 과제 상태(종료 예정, 종료)도 달이 바뀔 때 바뀐다 —
   데이터가 같아도 그날 다시 구운 `docs/` 가 달라지면 PR 이 열린다(예약 빌드는 커밋하지 않는다, README §7).
⛔ **PR 본문은 공개다**(공개 리포). 이미 사이트에 있는 값의 변경(slug 단위)과 건수만 싣는다. 정본에만 있는
   새 과제명, 새 사람 이름, 실패 사유의 원문은 **두레이 업무에만** 적는다 — PR 이 곧 공개 결정이 아니다.
⛔ **조용히 실패하지 않는다.** 정본을 못 읽거나 빌드가 막히면 두레이 업무를 연다. 본인 계정으로 연 PR 은
   GitHub 이 본인에게 알리지 않으므로, PR 을 열었을 때도 두레이로 알린다.
⚠️ 두레이 토큰은 keti-kb 와 같은 키체인 항목(`kb-dooray`)을 읽는다(`resolve_token`). cron 에서는 키체인을 못
   읽으므로 LaunchAgent(`ops/com.datasec.sot-pr.plist`)로 돈다.
"""
from __future__ import annotations

import argparse
import datetime as dt
import fcntl
import json
import os
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
KETI_KB = pathlib.Path(os.environ.get("KETI_KB", pathlib.Path.home() / "work" / "keti-kb"))
PY = os.environ.get("SOT_PYTHON", str(KETI_KB / ".venv" / "bin" / "python"))
"""openpyxl 이 있는 파이썬. ⭐ LaunchAgent 가 띄우는 실행 파일과 같게 둔다 — 구글드라이브 폴더 접근 권한(TCC)이
그 실행 파일의 것이다(keti-kb 의 `ops/com.keti.kb-doctor-alert.plist` 주석)."""
CACHE = pathlib.Path.home() / "Library" / "Caches" / "datasec-sot-pr"
WT = CACHE / "wt"
REPO = "seungwooketi/datasec_web"
REF = os.environ.get("SOT_PR_REF", "origin/main")
"""꺼낼 기준. ⚠️ 시험할 때만 바꾼다(예: 아직 푸시 안 한 커밋으로 `--dry-run`)."""

DOORAY_PROJECT = "3860521715044819723"     # @swkum — 할 일의 정본(사용자 규칙)
DOORAY_TAG_ETC = "4408877705372826055"      # 카테고리: 기타
DOORAY_KEYCHAIN = "kb-dooray"


def kst_today() -> dt.date:
    return dt.datetime.now(dt.timezone(dt.timedelta(hours=9))).date()


def run(cmd: list[str], *, cwd: pathlib.Path | None = None, env: dict | None = None,
        check: bool = True) -> subprocess.CompletedProcess:
    print("$", " ".join(cmd), flush=True)
    r = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True)
    if r.stdout.strip():
        print(r.stdout.rstrip(), flush=True)
    if r.stderr.strip():
        print(r.stderr.rstrip(), file=sys.stderr, flush=True)
    if check and r.returncode != 0:
        raise Failure(f"`{' '.join(cmd[:3])} …` 이 {r.returncode} 로 끝났다", r.stderr[-2000:])
    return r


class Failure(Exception):
    def __init__(self, what: str, detail: str = "") -> None:
        super().__init__(what)
        self.what, self.detail = what, detail


# ── 두레이 ──────────────────────────────────────────────────────────────
def dooray(subject: str, body: str, *, dry: bool) -> str:
    """@swkum 에 업무를 연다(담당 = 토큰 주인). 실패해도 예외를 던지지 않고 사유를 돌려준다."""
    if dry:
        print(f"[dry-run] 두레이 업무: {subject}\n{body}")
        return "dry-run"
    sys.path.insert(0, str(KETI_KB))
    try:
        from kb.adapters.notify.dooray import API_BASE, _urllib_http, resolve_token
    except Exception as e:                                     # noqa: BLE001
        return f"keti-kb 두레이 어댑터를 못 읽음: {type(e).__name__}"
    token, problem = resolve_token(DOORAY_KEYCHAIN)
    if not token:
        return f"두레이 토큰 없음: {problem or '키체인 항목 없음'}"
    head = {"Authorization": f"dooray-api {token}", "Accept": "application/json",
            "Content-Type": "application/json"}
    try:
        st, me = _urllib_http("GET", API_BASE + "/common/v1/members/me", head, None, 10)
        me_id = str(((me or {}).get("result") or {}).get("id") or "")
        if st >= 400 or not me_id:
            return f"두레이 me 조회 실패(HTTP {st})"
        st, got = _urllib_http("POST", f"{API_BASE}/project/v1/projects/{DOORAY_PROJECT}/posts", head, {
            "subject": subject[:200],
            "body": {"mimeType": "text/x-markdown", "content": body},
            "users": {"to": [{"type": "member", "member": {"organizationMemberId": me_id}}]},
            "tagIds": [DOORAY_TAG_ETC],
        }, 10)
    except Exception as e:                                     # noqa: BLE001 — 토큰은 사유에 넣지 않는다
        return f"두레이 호출 실패: {type(e).__name__}"
    ref = str(((got or {}).get("result") or {}).get("id") or "")
    return f"두레이 업무 {ref}" if st < 400 and ref else f"두레이 업무 생성 실패(HTTP {st})"


def bullets(items: list[str]) -> str:
    """두레이 마크다운은 홑 줄바꿈을 합칠 수 있다 — 줄마다 빈 줄(사용자 규칙)."""
    return "\n\n".join(f"- {x}" for x in items)


# ── 본체 ─────────────────────────────────────────────────────────────
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="푸시, PR, 두레이 없이 무엇을 할지만 찍는다")
    args = ap.parse_args()
    dry = args.dry_run
    today = kst_today()
    print(f"\n===== {dt.datetime.now().isoformat(timespec='seconds')} sot_pr{' (dry-run)' if dry else ''}",
          flush=True)

    CACHE.mkdir(parents=True, exist_ok=True)
    lock = open(CACHE / "lock", "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        print("다른 회차가 돌고 있다 — 이번 회차는 건너뛴다")
        return 0

    report_path = CACHE / "report.json"
    try:
        run(["git", "-C", str(ROOT), "fetch", "-q", "origin"])
        run(["git", "-C", str(ROOT), "worktree", "prune"])
        if WT.exists():
            run(["git", "-C", str(ROOT), "worktree", "remove", "--force", str(WT)], check=False)
        run(["git", "-C", str(ROOT), "worktree", "add", "-q", "--detach", str(WT), REF])

        report_path.unlink(missing_ok=True)
        env = {**os.environ, "KETI_KB": str(KETI_KB)}
        pull = run([PY, "tools/pull_from_sot.py", "--write", "--report", str(report_path)],
                   cwd=WT, env=env, check=False)
        rep = json.loads(report_path.read_text(encoding="utf-8")) if report_path.exists() else {}
        if pull.returncode != 0:
            raise Failure(f"정본을 못 읽었다(pull_from_sot 종료코드 {pull.returncode})",
                          "\n".join(rep.get("errors") or [pull.stderr[-2000:]]))
        run([PY, "build.py", "--strict"], cwd=WT)

        dirty = run(["git", "status", "--porcelain"], cwd=WT).stdout.strip()
        ch = rep.get("changed") or {}
        pend = rep.get("pending") or {}
        n_changed = sum(len(v) for v in ch.values())
        human = {k: v for k, v in pend.items() if v and k != "unmatched"}
        if not dirty and not human:
            print("바뀐 것 없음 — PR 도 두레이 업무도 만들지 않는다")
            return 0

        lines: list[str] = []
        pr_url = ""
        if dirty:
            branch = f"sot/{today.isoformat()}"
            data_note = (f"정본 반영 {n_changed}건" if n_changed else "데이터 변경 없음")
            title = f"정본 갱신 {today.isoformat()}: {data_note}"
            # ⛔ 공개 본문 — slug 단위의 바뀐 값과 건수만. 새 과제명, 새 이름은 싣지 않는다.
            pub = [f"매달 자동 갱신(tools/sot_pr.py). 병합 전 diff 를 본다.", ""]
            for label, key in (("과제", "projects"), ("구성원 직급, 구분", "members"),
                               ("구성원 수행 과제", "participation")):
                if ch.get(key):
                    pub += [f"### {label} ({len(ch[key])})", *[f"- {x}" for x in ch[key]], ""]
            if not n_changed:
                pub += ["데이터는 그대로이고, 오늘 날짜로 다시 구운 docs/ 가 다르다(과제 상태 전환 등).", ""]
            if human:
                pub += [f"사람이 정할 것 {sum(len(v) for v in human.values())}건은 두레이 업무에 있다(공개하지 않는다).", ""]
            pub += ["🤖 Generated with [Claude Code](https://claude.com/claude-code)"]
            msg = (f"{title}\n\n매달 정본 갱신 회차(tools/sot_pr.py). pull_from_sot.py --write 와 build.py --strict 결과.\n\n"
                   "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>")
            if dry:
                print(f"[dry-run] 가지 {branch} 로 커밋, 푸시, PR: {title}\n" + "\n".join(pub))
                pr_url = "(dry-run)"
            else:
                run(["git", "switch", "-q", "-c", branch], cwd=WT)
                run(["git", "add", "data", "docs"], cwd=WT)
                run(["git", "commit", "-q", "-m", msg], cwd=WT)
                run(["git", "push", "-q", "-u", "origin", branch], cwd=WT)
                pr_url = run(["gh", "pr", "create", "--repo", REPO, "--base", "main", "--head", branch,
                              "--title", title, "--body", "\n".join(pub)], cwd=WT).stdout.strip().splitlines()[-1]
            lines.append(f"PR: {pr_url}")
            for label, key in (("과제", "projects"), ("구성원 직급, 구분", "members"),
                               ("구성원 수행 과제", "participation")):
                if ch.get(key):
                    lines.append(f"{label} {len(ch[key])}건: " + ", ".join(ch[key]))
        for label, key in (("정본에만 있는 새 과제(slug, 영문 제목을 정해 data 에 넣어야 실린다)", "new_projects"),
                           ("정본에서 사라진 과제", "gone"),
                           ("직원명부에만 있는 사람(slug, 영문 이름을 정해야 실린다)", "new_people"),
                           ("사이트에만 있는 사람", "site_only")):
            if pend.get(key):
                lines.append(f"{label}: " + ", ".join(pend[key]))
        subject = (f"datasec.work 정본 갱신 PR 검토 ({today.isoformat()})" if dirty
                   else f"datasec.work 정본에 사람이 정할 것이 있다 ({today.isoformat()})")
        print(dooray(subject, bullets(lines) + "\n\n근거: tools/sot_pr.py 매달 회차", dry=dry))
        return 0

    except Failure as f:
        detail = (f.detail or "").strip().splitlines()[-15:]
        body = bullets([f.what, *detail, "로그: ~/Library/Logs/datasec-sot-pr.log",
                        "다시 돌리기: python tools/sot_pr.py (datasec_web 에서, keti-kb venv 파이썬)"])
        print(dooray(f"datasec.work 정본 갱신 실패 ({today.isoformat()})", body, dry=dry))
        return 1
    finally:
        if WT.exists() and not dry:
            subprocess.run(["git", "-C", str(ROOT), "worktree", "remove", "--force", str(WT)],
                           capture_output=True)
        report_path.unlink(missing_ok=True)       # 이름이 든 보고서를 남기지 않는다


if __name__ == "__main__":
    sys.exit(main())
