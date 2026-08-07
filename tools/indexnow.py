#!/usr/bin/env python3
"""IndexNow — 검색엔진에 "이 주소들이 바뀌었다"고 알린다. 표준 라이브러리만 쓴다.

⭐ **계정이 없어도 되는 유일한 제출 경로다.** 키 파일을 사이트 루트에 두는 것이 소유 증명이고,
   한 곳에 보내면 참여 엔진(빙 · 네이버 · Yandex · Seznam)에 전파된다.
⛔ **구글은 IndexNow 를 쓰지 않는다.** 구글은 Search Console 로만 간다.
⚠️ 알리는 것이지 **색인을 보장하지 않는다.** 네이버도 그렇게 명시한다.

    python3 tools/indexnow.py            # 사이트맵의 모든 주소
    python3 tools/indexnow.py /ko/news/  # 특정 주소만
"""
from __future__ import annotations

import json
import pathlib
import re
import sys
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
ENDPOINTS = [
    "https://api.indexnow.org/indexnow",          # 참여 엔진 전체로 전파
    "https://searchadvisor.naver.com/indexnow",   # 네이버는 직접도 받는다
]


def key_and_host() -> tuple[str, str, str]:
    keys = [p for p in (ROOT / "content" / "verify").glob("*.txt")
            if re.fullmatch(r"[0-9a-f]{8,128}", p.stem)]
    if not keys:
        raise SystemExit("⛔ content/verify/ 에 IndexNow 키 파일(<key>.txt)이 없다")
    if len(keys) > 1:
        raise SystemExit(f"⛔ 키 파일이 여럿이다: {[p.name for p in keys]}")
    site = json.loads((ROOT / "content" / "site.json").read_text(encoding="utf-8"))["site_url"]
    host = site.split("://", 1)[-1].strip("/")
    return keys[0].stem, host, site.rstrip("/")


def urls_from_sitemap(base: str) -> list[str]:
    xml = (ROOT / "docs" / "sitemap.xml").read_text(encoding="utf-8")
    return re.findall(r"<loc>([^<]+)</loc>", xml)


def main() -> int:
    key, host, base = key_and_host()
    urls = [f"{base}{a}" if a.startswith("/") else a for a in sys.argv[1:]] \
        or urls_from_sitemap(base)

    # ⛔ 키 파일이 **실제로 열려야** 한다. 안 열리면 엔진이 소유 증명을 못 해 조용히 무시한다.
    kurl = f"{base}/{key}.txt"
    try:
        with urllib.request.urlopen(kurl, timeout=20) as r:
            got = r.read().decode().strip()
    except Exception as exc:
        raise SystemExit(f"⛔ 키 파일을 못 읽는다: {kurl}\n   {exc}\n"
                         f"   빌드·배포가 끝난 뒤에 실행하라.")
    if got != key:
        raise SystemExit(f"⛔ 키 파일 내용이 키와 다르다: {got[:20]!r} ≠ {key}")

    body = json.dumps({"host": host, "key": key, "keyLocation": kurl,
                       "urlList": urls}).encode()
    print(f"{len(urls)}개 주소 · key {key[:8]}…")
    ok = 0
    for ep in ENDPOINTS:
        req = urllib.request.Request(ep, data=body,
                                     headers={"Content-Type": "application/json; charset=utf-8"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                print(f"  ✅ {ep} → {r.status}")
                ok += 1
        except urllib.error.HTTPError as exc:
            # 202 Accepted 도 HTTPError 로 오지 않지만, 400/403 은 이유가 본문에 있다
            print(f"  ⛔ {ep} → {exc.code} {exc.read()[:200].decode(errors='replace')}")
        except Exception as exc:
            print(f"  ⛔ {ep} → {exc}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
