#!/usr/bin/env python3
"""히어로 그림을 사이트용으로 굽는다. ⚠️ Pillow 가 필요하다(사이트 빌드에는 불필요).

    python3 tools/build_hero.py ~/Downloads/hero.png
    python3 tools/build_hero.py <파일> --check     # 쓰지 않고 진단만

⭐ **진단이 본체다.** 그림 안의 라벨이 실제 표시 폭에서 몇 px 로 그려지는지 잰다 —
   이걸 안 재고 넣었다가 8.4px 짜리 라벨을 두 번 실었다.
⛔ 12px 미만이면 막는다. 그 그림은 그 자리에 못 넣는다는 뜻이다.
⚠️ 선과 글자가 많은 도해는 **PNG 로 둔다.** JPEG 는 가는 선을 뭉갠다.
"""
from __future__ import annotations

import argparse
import pathlib
import sys

try:
    from PIL import Image
except ImportError:                                        # pragma: no cover
    raise SystemExit("⛔ Pillow 가 필요하다:  python3 -m pip install --user Pillow")

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "brand" / "hero.png"
DISPLAY_PX = 938       # 실제 표시 폭(.heroband 의 max-height 700px 기준)
TARGET_W = 1800        # 고밀도 화면용으로 1.5×
MIN_LABEL_PX = 12


def label_cap_px(im: Image.Image) -> int:
    """왼쪽 라벨 열에서 어두운 글자 행의 중앙값 높이 = 대문자 높이."""
    g = im.convert("L")
    sub = g.crop((int(im.width * 0.23), 0, int(im.width * 0.36), im.height))
    on = [sub.crop((0, y, sub.width, y + 1)).point(lambda p: 255 if p < 120 else 0).getbbox()
          is not None for y in range(sub.height)]
    runs, s = [], None
    for y, v in enumerate(on + [False]):
        if v and s is None:
            s = y
        elif not v and s is not None:
            if y - s > 6:
                runs.append(y - s)
            s = None
    return sorted(runs)[len(runs) // 2] if runs else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("src", type=pathlib.Path)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--display", type=int, default=DISPLAY_PX, help="실제로 그려질 CSS 폭")
    args = ap.parse_args()

    im = Image.open(args.src).convert("RGB")
    cap = label_cap_px(im)
    at = cap * args.display / im.width
    print(f"{im.width}x{im.height} ({im.width/im.height:.2f}:1) · 라벨 대문자 {cap}px")
    for d in (560, 700, 930, args.display):
        mark = "  ⛔" if cap * d / im.width < MIN_LABEL_PX else "  ✅"
        print(f"  {d:4d}px 로 그리면 {cap*d/im.width:5.1f}px{mark}")
    if cap and at < MIN_LABEL_PX:
        print(f"\n⛔ {args.display}px 에서 라벨이 {at:.1f}px 다 — 읽히지 않는다.\n"
              f"   더 넓게 놓거나, 라벨을 키워 다시 그려라.")
        return 1
    if args.check:
        return 0

    w = min(TARGET_W, im.width)
    im.resize((w, round(im.height * w / im.width)), Image.LANCZOS).save(OUT, optimize=True)
    print(f"\n  → {OUT.relative_to(ROOT)}  {Image.open(OUT).size}  {OUT.stat().st_size//1024}KB")
    print("⭐ `python3 build.py` 를 돌려야 반영된다(자산 주소의 내용 해시가 바뀐다).")
    print("⚠️ 그림이 바뀌었으면 `content/site.json` 의 `hero_alt` 도 고쳐라 — 라벨 목록이다.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
