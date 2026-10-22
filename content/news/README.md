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
category: project
summary: 목록과 검색 결과에 실리는 한 문장. 제목을 되풀이하지 말고 무슨 일인지 적는다.
---

첫 문단이 본문이다. 무슨 일이 있었고 왜 중요한지 두세 문장.

두 번째 문단. 필요하면 [과제](/ko/research/) 나 [협력](/ko/collaborate/) 로 링크한다.
```

`content/news/2026-09-iso-contribution.en.md` — **같은 slug, 같은 date, 같은 category**, 내용만 영어로.

```markdown
---
title: Three contributions submitted to ISO/IEC SC 27
date: 2026-09-14
category: project
summary: One sentence for the list and for search results.
---

The English text. Not a machine translation of the Korean — write it for a reader
who does not read Korean and does not know the Korean funding landscape.
```

## 머리말(frontmatter)

| 키 | 필수 | 쓰임 |
|---|---|---|
| `title` | ⭐ | 목록·상세의 제목, `<title>`, 소셜 카드 |
| `date` | ⭐ | `YYYY-MM-DD`. **정렬 기준**(최신이 위)이자 **공개일**. 한국 시각 오늘보다 늦으면 빌드가 싣지 않고, 그날 예약 빌드가 싣는다. sitemap 의 `lastmod` 는 이 값이 아니라 빌드가 정한다(쪽 내용이 바뀐 날) |
| `category` | ⭐ | `project` / `hiring` / `people` / `center` 중 하나(과제 / 채용 / 구성원 / 센터). **두 언어 파일에 같은 영문 키**를 쓴다 — 국문 파일에 「채용」을 쓰면 빌드가 막는다. 블로그 발췌 글(`source` 가 `https://seungwoo.datasec.work/…`)만 생략한다 |
| `deadline` | | 채용처럼 마감이 있는 글. `2026-11-05T13:00+09:00` 형식(**+09:00 필수**). `category: hiring` 이고 마감이 남았으면 쪽마다 왼쪽 위(메뉴 바로 아래)에 채용 안내 카드가 뜨고(좁은 화면에서는 바닥 띠, 공고 글 자체에는 없음, 열린 공고가 여럿이면 마감이 가장 가까운 한 건), 마감 시각이 지나면 스스로 닫힌다. 값은 공고의 접수 마감을 그대로 옮긴다. 예: `category: hiring` + `deadline: 2026-11-05T13:00+09:00` |
| `projects` | | 관련 과제 slug, 쉼표로(`aegis-rm, on-device-ai-chip-software`). 소식 목록에 「관련 과제」로 붙고 과제 상세 쪽의 「관련 소식과 글」에 이 글이 실린다. 없는·미공개 과제면 빌드가 막는다 |
| `summary` | | 목록의 한 줄 · `<meta name="description">`. 없으면 제목이 대신 들어간다 |
| `source` | | 원문이 따로 있는 글(블로그 등)의 `https://` 주소. 있으면 상세 쪽 제목 아래와 본문 끝에 「전체 글 읽기」 버튼이 붙는다. https 가 아니면 빌드가 막는다. ⭐ 센터장 블로그(`https://seungwoo.datasec.work/…`)를 가리키면 그 글은 **소식이 아니라 인사이트**다 — 인사이트 쪽에 실리고 고지문이 붙는다 |
| `sample` | | `true` 면 「예시」 딱지가 붙고 **`--strict` 가 배포를 막는다** |

⛔ `date`, `category`, `deadline`, `source` 유무, `projects` 는 **두 언어가 같아야 한다.** 다르면 빌드가 막는다 —
날짜가 다르면 목록 순서가, 분류나 마감이 다르면 한쪽 언어에서만 채용 카드가 갈린다.

## 본문에 쓸 수 있는 것

문단 · `## 소제목` · `- 목록` · `1. 번호 목록` · `> 인용` · `---` 구분선 ·
`**굵게**` · `*기울임*` · `` `코드` `` · `[링크](/ko/…)`

그림은 한 줄에 하나, `content` 가 아니라 `assets/news/<slug>/` 에 파일을 두고 이렇게 쓴다:

```markdown
![무엇을 그린 그림인지 글로 (alt, 비우면 빌드가 막는다)](/assets/news/<slug>/figure.png "캡션")
```

- 경로는 `/assets/news/` 아래만 받는다. 파일이 없으면 빌드가 막는다
- 크기(`width`/`height`)는 빌드가 파일에서 읽는다. 가로 1400px 정도면 충분하다
- 세로로 긴 그림은 줄 끝에 `{width=60%}` 를 붙여 본문 폭보다 좁게 둔다(20~100%, 좁은 화면에서는 전체 폭)
- 본문 **첫 그림이 그 쪽의 소셜 카드(og:image)** 가 된다. 1.91:1 에 가까운 그림을 맨 앞에 둔다
- ⚠️ 그림 속 글자는 언어 전환, 검색, 화면낭독이 안 된다. alt 와 캡션에 내용을 글로 남긴다

표·HTML 은 안 된다 — 필요하면 말해 달라.

⛔ **과제 상세로 링크할 때 주의.** `/ko/research/<slug>/` 는 그 과제에 소개문이 있을 때만
존재한다. 없는 과제로 링크하면 CI 의 링크 검사가 막는다(그래서 조용히 404 가 되지 않는다).
과제 목록 `/ko/research/` 는 언제나 있다.

## 올리기

⭐ **예약 게시:** 블로그처럼 공개일이 미래인 글은 `date` 를 그날로 두고 미리 push 해 두면 된다.
그 전까지는 목록, 상세, sitemap 어디에도 나오지 않고(빌드가 `⏳ 예약 소식` 으로 알린다), 그날
예약 빌드(`check.yml` 의 schedule)가 싣는다. ⚠️ cron 은 10:13 KST 지만 GitHub 가 늦게 돌려
실제로는 오후 2시 반~3시 무렵에 실린다. 바로 보이게 하려면 Actions 에서 Run workflow.

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
- **예산·계정번호, 정본의 공동연구기관 칸** — `data/meta.json` 의 `excluded` 가 정한 비공개 항목이다.
  정본 칸을 옮겨 적지 않는다는 뜻이다. 기관명은 협약이나 공식 발표로 확인된 것만 쓴다
- **개인 연락처·사진** — 본인이 동의한 것만
