#!/usr/bin/env python3
"""생성된 로고 PNG → `assets/brand/` 의 로고·마크. ⚠️ Pillow 가 필요하다(사이트 빌드에는 불필요).

    python3 tools/build_logo.py ~/Downloads/Gemini_Generated_Image_xxxx.png
    python3 tools/build_logo.py <파일> --check     # 쓰지 않고 진단만

⛔ **생성 이미지는 알파가 없다.** 투명해 보이는 회색/흰색 체커보드가 **픽셀로 그려져** 온다
   (실측: 알파 전부 255). 그대로 쓰면 밝은 바탕에 체커가 비친다.
   로고색(감청·청록)은 어둡거나 채도가 높으므로 **밝고 중성인 픽셀만** 알파로 뺀다.

⚠️ 우하단 생성 워터마크(✦)도 같은 규칙에 걸리지 않는다(밝은 회색이라 빠지기도 한다) —
   남으면 잘라야 하므로 진단에 위치를 찍어 준다.
"""
from __future__ import annotations

import argparse
import pathlib
import sys

try:
    from PIL import Image, ImageChops
except ImportError:                                        # pragma: no cover
    raise SystemExit("⛔ Pillow 가 필요하다:  python3 -m pip install --user Pillow")

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "brand"
NAV_PX = 52          # 머리말에서 그려지는 높이. 부제 크기 판정의 기준이다.


def keyed(src: Image.Image) -> Image.Image:
    """밝고 중성인 배경을 알파로. 가장자리에 부분 알파가 남아 계단이 생기지 않는다."""
    rgb = src.convert("RGB")
    r, g, b = rgb.split()
    lum = rgb.convert("L")
    a = lum.point(lambda p: 0 if p >= 218 else (255 if p <= 150 else int((218 - p) * 255 / 68)))
    mx = ImageChops.lighter(ImageChops.lighter(r, g), b)
    mn = ImageChops.darker(ImageChops.darker(r, g), b)
    a = ImageChops.lighter(a, ImageChops.difference(mx, mn).point(lambda p: 255 if p > 18 else 0))
    out = rgb.copy()
    out.putalpha(a)
    return out.crop(a.getbbox())


def rows(mask: Image.Image, x0: int) -> list[tuple[int, int, int]]:
    strip = mask.crop((x0, 0, mask.width, mask.height))
    on = [strip.crop((0, y, strip.width, y + 1)).getbbox() is not None for y in range(strip.height)]
    out, s = [], None
    for y, v in enumerate(on + [False]):
        if v and s is None:
            s = y
        elif not v and s is not None:
            if y - s > 5:
                out.append((s, y, y - s))
            s = None
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("src", type=pathlib.Path)
    ap.add_argument("--check", action="store_true", help="쓰지 않고 진단만")
    args = ap.parse_args()

    raw = Image.open(args.src)
    alphas = {p[3] for p in list(raw.convert("RGBA").getdata())[::4001]}
    if alphas == {255}:
        print("⚠️ 알파가 전부 255 — 배경(체커보드)이 픽셀로 그려져 있다. 키아웃한다.")

    logo = keyed(raw)
    W, H = logo.size
    m = logo.split()[3].point(lambda p: 255 if p > 40 else 0)

    cols = [m.crop((x, 0, x + 1, H)).getbbox() is not None for x in range(W)]
    gaps, s = [], None
    for x, v in enumerate(cols + [True]):
        if not v and s is None:
            s = x
        elif v and s is not None:
            if x - s >= 30:
                gaps.append((s, x))
            s = None
    if not gaps:
        raise SystemExit("⛔ 마크와 글자 사이의 빈 열을 못 찾았다 — 이 로고는 손으로 봐야 한다")

    lines = rows(m, gaps[0][1])
    print(f"크기 {W}x{H} ({W/H:.2f}:1) · 마크|글자 경계 x={gaps[0][0]}~{gaps[0][1]}")
    for i, (a, b, h) in enumerate(lines, 1):
        print(f"  글자 {i}행 높이 {h:4d}  = 로고 높이의 {h/H*100:4.1f}%  "
              f"→ {NAV_PX}px 머리말에서 {h/H*NAV_PX:4.1f}px")
    if len(lines) >= 2 and lines[1][2] / H * NAV_PX < 8:
        print("  ⛔ 부제가 8px 미만이다 — 읽히지 않는다. 부제를 두 줄로 나눠 다시 생성하라.")

    # 워터마크 흔적: 오른쪽 아래 구석에 글자와 떨어진 덩어리가 있나
    corner = m.crop((int(W * 0.82), int(H * 0.72), W, H))
    if corner.getbbox():
        print(f"  ⚠️ 우하단에 잉크가 있다 {corner.getbbox()} — 워터마크일 수 있다. 눈으로 확인하라.")

    if args.check:
        return 0

    mark = logo.crop((0, 0, gaps[0][0] + 6, H))
    mark = mark.crop(mark.split()[3].getbbox())
    for h_, sfx in ((128, ""), (256, "@2x")):
        logo.resize((round(W * h_ / H), h_), Image.LANCZOS).save(OUT / f"logo{sfx}.png", optimize=True)
        mark.resize((round(mark.width * h_ / mark.height), h_), Image.LANCZOS).save(
            OUT / f"mark{sfx}.png", optimize=True)
    for n in ("logo.png", "logo@2x.png", "mark.png", "mark@2x.png"):
        p = OUT / n
        print(f"  → {n:14} {Image.open(p).size}  {p.stat().st_size // 1024}KB")
    print("\n⭐ `python3 build.py` 를 돌려야 산출물에 반영된다(자산 주소의 내용 해시가 바뀐다).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
