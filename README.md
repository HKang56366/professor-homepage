# professor-homepage

강희조(Kang, Hijo) · 전남대학교 영어영문학과 부교수 — 개인 사이트.
음성학 · 음운론 · 형태론.

**https://hijokang.duckdns.org**

## 구성

| 경로 | 내용 |
|---|---|
| `index.html` | 첫 화면 — 연구 분야, 이 달의 글, 최근 글, 대표 논문 |
| `about.html` | 소개 · 경력 · 학력 · 연락처 |
| `research.html` | 연구 분야, 논문과 글·강의를 주제별로 묶은 정리 |
| `teaching.html` | 담당 과목 |
| `blog.html` | 글 목록 (전체 + 주제별) |
| `post1.html` … `post13.html` | 글 본문 |
| `en/` | 영문 페이지 (About · Research · Teaching · Writing) |
| `sitemap.xml` `robots.txt` `feed.xml` | 검색·구독용 |
| `_build/` | 사이트를 다시 찍는 스크립트 (게시되지 않음) |

## 다시 찍기

작업 사본은 서버의 `~/Workspace/kang/professor-homepage` 에 둔다.

```bash
cd ~/Workspace/kang/professor-homepage
python3 _build/build.py . .        # 제자리에서 다시 찍는다
git diff --stat                    # 무엇이 바뀌었는지 본다
```

`_build/build.py` 는 `post*.html` 에서 본문을 그대로 꺼내 새 템플릿으로 다시 찍는다.
**본문 문장은 건드리지 않는다** — 하드랩된 줄만 문단으로 합친다. 자기가 찍어낸
결과도 다시 읽을 수 있어(멱등) 몇 번을 돌려도 같은 결과가 나온다. 아무것도 안 고치고
돌리면 `git status` 가 비어 있어야 정상이다.

프로필 사진을 바꿀 때는 원본 한 장을 주고 아래를 돌리면 세 크기가 함께 나온다.
잘라내는 자리는 `_build/make_images.py` 위쪽 `PORTRAIT_BOX`·`FACE_BOX` 두 줄이다.

```bash
python3 _build/make_images.py <원본사진> images/
```

글을 새로 올릴 때는 `_build/build.py` 의 `POSTS` 목록에 한 줄
(번호, 제목, 영문 제목, 연-월, 일, 주제, 한 줄 요약, 영문 요약)을 더하고
다시 돌리면 목록·주제 묶음·사이트맵·RSS 가 함께 갱신된다.

## 사실관계

소개·직위·연구분야·논문 목록은 전남대학교 영어영문학과 교수 소개 페이지를
정본으로 삼는다. 그쪽이 바뀌면 이 사이트도 함께 고친다.
