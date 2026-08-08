# 소식 쓰는 법

한 편에 **파일 두 개**다. 같은 이름(slug) + 언어 꼬리표.

```
content/news/2026-09-iso-contribution.ko.md      ← 한국어
content/news/2026-09-iso-contribution.en.md      ← 영어
```

⛔ **두 언어가 다 있어야 실린다.** 한쪽만 두면 빌드가 경고하고 **양쪽 다 안 보인다** —
없는 쪽을 가리키는 언어 전환 버튼과 `hreflang` 이 404 가 되기 때문이다.

주소는 slug 에서 나온다: `https://www.datasec.work/ko/news/2026-09-iso-contribution/`
⚠️ **한 번 게시한 뒤에는 slug 를 바꾸지 않는다.** 주소가 바뀌면 밖에서 걸린 링크가 죽는다.

---

## 그대로 복사해 쓰는 틀

`content/news/2026-09-iso-contribution.ko.md`

```markdown
---
title: ISO/IEC SC 27 회의에 기고 3건 제출
date: 2026-09-14
summary: 목록과 검색 결과에 실리는 한 문장. 제목을 되풀이하지 말고 무슨 일인지 적는다.
---

첫 문단이 본문이다. 무슨 일이 있었고 왜 중요한지 두세 문장.

두 번째 문단. 필요하면 [연구](/ko/research/) 나 [협력](/ko/collaborate/) 로 링크한다.
```

`content/news/2026-09-iso-contribution.en.md` — **같은 slug, 같은 date**, 내용만 영어로.

```markdown
---
title: Three contributions submitted to ISO/IEC SC 27
date: 2026-09-14
summary: One sentence for the list and for search results.
---

The English text. Not a machine translation of the Korean — write it for a reader
who does not read Korean and does not know the Korean funding landscape.
```

## 머리말(frontmatter) 네 줄

| 키 | 필수 | 쓰임 |
|---|---|---|
| `title` | ⭐ | 목록·상세의 제목, `<title>`, 소셜 카드 |
| `date` | ⭐ | `YYYY-MM-DD`. **정렬 기준**(최신이 위) · sitemap 의 `lastmod` |
| `summary` | | 목록의 한 줄 · `<meta name="description">`. 없으면 제목이 대신 들어간다 |
| `sample` | | `true` 면 「예시」 딱지가 붙고 **`--strict` 가 배포를 막는다** |

⚠️ `date` 는 두 언어가 같아야 한다. 다르면 목록 순서가 언어마다 달라진다.

## 본문에 쓸 수 있는 것

문단 · `## 소제목` · `- 목록` · `1. 번호 목록` · `> 인용` · `---` 구분선 ·
`**굵게**` · `*기울임*` · `` `코드` `` · `[링크](/ko/…)`

그게 전부다. 표·이미지·HTML 은 안 된다 — 필요하면 말해 달라.

⛔ **과제 상세로 링크할 때 주의.** `/ko/research/<slug>/` 는 그 과제에 소개문이 있을 때만
존재한다. 없는 과제로 링크하면 CI 의 링크 검사가 막는다(그래서 조용히 404 가 되지 않는다).
과제 목록 `/ko/research/` 는 언제나 있다.

## 올리기

```bash
python3 build.py            # docs/ 를 다시 굽는다
python3 build.py --strict   # 배포 전 확인 — 0 이어야 한다
git add -A && git commit -m "소식: ISO/IEC SC 27 기고" && git push
```

⚠️ **`docs/` 를 같이 커밋해야 한다.** 원본만 올리면 CI 가 「docs/ 가 원본과 다르다」로 막는다
(그 검사가 없으면 옛 내용이 계속 서빙된다).

배포되면 검색엔진에 알린다:

```bash
python3 tools/indexnow.py https://www.datasec.work/ko/news/2026-09-iso-contribution/
```

## ⛔ 쓰지 말아야 할 것

- **지어낸 사실.** 대외 공개물이라 틀린 한 문장이 곧 허위다. 성과·수치·수상은 근거가 있을 때만
- **예산·계정번호·공동연구기관 목록** — `data/meta.json` 의 `excluded` 가 정한 비공개 항목이다
- **개인 연락처·사진** — 본인이 동의한 것만
