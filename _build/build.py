#!/usr/bin/env python3
"""강희조 교수 사이트 빌드.

원본 post*.html 에서 본문을 그대로 꺼내 새 템플릿으로 다시 찍는다.
본문 문장은 한 글자도 고치지 않는다 — 하드랩된 줄만 문단으로 합친다.

  python3 _build/build.py <원본디렉토리> <출력디렉토리>

사실관계는 전남대 영어영문학과 교수 소개 페이지를 정본으로 삼는다.
(강희조 / Kang, Hijo · 부교수 · 음성학, 음운론, 형태론)
"""
import html
import os
import re
import shutil
import sys

SITE = "https://hijokang.duckdns.org"
BUILD_DATE = "2026-09-05"

# ── 정본 사실관계 (전남대 교수 소개 페이지) ──────────────────────────────
F = {
    "name_ko": "강희조",
    "name_en": "Hijo Kang",          # 학과 공식 표기 Kang, Hijo
    "rank_ko": "부교수",
    "rank_en": "Associate Professor",
    "dept_ko": "전남대학교 영어영문학과",
    "dept_en": "Department of English Language and Literature,\nChonnam National University",
    "office": "인문대 2호관 404호",
    "office_en": "Humanities Bldg. 2, Room 404",
    "tel": "062-530-3165",
    "email_univ": "hijokang@jnu.ac.kr",
    "email_alt": "hijo.kang@gmail.com",
    "jnu_url": ("https://ell.jnu.ac.kr/ell/14378/subview.do?enc="
                "Zm5jdDF8QEB8JTJGcHJvZiUyRmVsbCUyRjI2MyUyRjI2OTUlMkZ2aWV3LmRvJTNG"),
    "tagline_ko": "말소리의 변화를 관찰하고, 그 안의 규칙을 찾습니다.",
    "tagline_en": "Observing how speech sounds change — and finding the patterns behind them.",
}

FIELDS = [
    ("음성학", "Phonetics",
     "말소리가 실제로 어떻게 만들어지고 들리는지를 측정한다. 한국어 폐쇄음의 길이 조절, "
     "한국인 학습자의 영어 강세 지각과 발화가 최근의 주제다.",
     "Measuring how speech sounds are actually produced and perceived — duration in Korean "
     "oral stops, and English stress in Korean learners."),
    ("음운론", "Phonology",
     "표면의 소리 아래에서 움직이는 규칙을 다룬다. 영어와 한국어를 함께 놓고 보면 "
     "달라 보이는 현상들이 같은 원리로 설명되는 경우가 많다.",
     "The rules that operate beneath the surface. Placing English and Korean side by side "
     "often reveals one principle behind two seemingly different phenomena."),
    ("형태론", "Morphology",
     "단어가 꼴을 바꾸는 방식, 특히 규칙에서 벗어난 활용이 어떻게 생기고 유지되는지를 "
     "빈도와 유추로 설명한다.",
     "How words change shape — and how irregular forms arise and survive, explained through "
     "frequency and analogy."),
]

# 연구업적 (학과 페이지 게재 순, 중복 1건 제외)
PUBS = [
    ("2024", "The Effect of L2 Immersion on English Stress Perception and Production by "
             "Korean Learners.", "Studies in Phonetics, Phonology and Morphology", "30-2, 145-170."),
    ("2024", "A phonetic study of bidirectional duration modulation in Korean oral stops.",
     "Korean Journal of Linguistics", "49-1, 1-20."),
    ("2023", "한국어 용언 활용에 나타나는 선택적 /ㄹ/ 삽입에 대한 유추 기반 분석.",
     "언어학 연구", "69, 1-19."),
    ("2023", "한국어 ‘ㄹ’ 말음 어간의 활용에서 나타나는 변이의 양상: 구어 말뭉치 및 "
             "설문을 통한 연구.", "언어", "48-2, 399-416."),
]

CAREER = [("전남대학교 영어영문학과 부교수", "2025.03 – 현재"),
          ("조선대학교 영어교육과 교수", "2014.03 – 2025.02")]
CAREER_EN = [("Associate Professor, Chonnam National University", "Mar 2025 – present"),
             ("Professor, Chosun University", "Mar 2014 – Feb 2025")]
EDU = [("Ph.D. in Linguistics", "Stony Brook University"),
       ("문학석사 (언어학)", "서울대학교"), ("문학사 (언어학)", "서울대학교")]
EDU_EN = [("Ph.D. in Linguistics", "Stony Brook University"),
          ("M.A. in Linguistics", "Seoul National University"),
          ("B.A. in Linguistics", "Seoul National University")]

COURSES = [("학부", [("영어음성학", "Phonetics of English"), ("영어음운론", "Phonology of English"),
                    ("영어학개론", "Introduction to English Linguistics"),
                    ("영어학개관", "Survey of English Linguistics")]),
           ("대학원", [("영어음운론", "English Phonology"),
                     ("영어음운론심화", "Advanced English Phonology")])]

TOPICS = {
    "change":     ("언어 변화", "Language Change"),
    "phonetics":  ("음성학", "Phonetics"),
    "phonology":  ("음운론", "Phonology"),
    "morphology": ("형태론", "Morphology"),
    "acquisition": ("외국어 습득", "Language Acquisition"),
    "society":    ("언어와 사회", "Language & Society"),
    "universals": ("언어의 보편성", "Language Universals"),
    "korean":     ("한국어", "Korean"),
    "english":    ("영어", "English"),
}

# n, 제목, 영문 제목, 연·월, 일, 주제, 한 줄 요약, 영문 요약
POSTS = [
    (1, "한국어의 미래", "The Future of Korean", "2026-03", "01",
     ["korean", "change", "english"],
     "영어의 관계대명사처럼 한국어에 없는 문법 범주에서 출발해, 한국어가 앞으로 어느 쪽으로 "
     "움직일지를 짚는다.",
     "Starting from grammatical categories Korean lacks, such as English relative pronouns, "
     "and asking where Korean is heading."),
    (2, "발음에 대한 집착으로부터의 해방", "Letting Go of the Obsession with Pronunciation",
     "2026-03", "15", ["phonetics", "acquisition"],
     "아이의 언어 습득을 다룬 다큐멘터리를 실마리로, 성인 외국어 학습자가 발음에 매달릴 "
     "때 무엇을 놓치는지를 이야기한다.",
     "Using a documentary on child language development to ask what adult learners lose "
     "when they fixate on pronunciation."),
    (3, "집단지성에 의한 언어의 진화", "Language Evolves by Collective Intelligence",
     "2026-04", "01", ["change", "society", "korean"],
     "‘요즘 젊은 사람들이 한국어를 망친다’는 한글날 단골 기사를 뒤집어, 언어 변화가 어떻게 "
     "집단의 선택으로 일어나는지 설명한다.",
     "Turning around the yearly complaint that young people are ruining Korean, and showing "
     "how change happens by collective choice."),
    (4, "다르면서도 같은 언어 I", "Different Yet the Same I", "2026-04", "15",
     ["universals", "korean"],
     "‘나는 그 사람이 아프다’라는 노래 제목의 이중주어 구문에서 시작해, 문법에 어긋난 문장이 "
     "왜 자연스럽게 읽히는지를 본다.",
     "A song title with a double-subject construction opens a look at why an ungrammatical "
     "sentence can still read naturally."),
    (5, "다르면서도 같은 언어 II", "Different Yet the Same II", "2026-05", "01",
     ["universals", "acquisition"],
     "언어의 자의성 때문에 개별 언어가 서로 멀어 보이지만, 그 차이가 어디에서 오는지를 "
     "학습자의 경험과 함께 정리한다.",
     "Arbitrariness makes languages look far apart; this essay traces where that distance "
     "actually comes from."),
    (6, "다르면서도 같은 언어 III", "Different Yet the Same III", "2026-05", "15",
     ["phonology", "universals", "korean"],
     "한국어의 구개음화와 영어의 flap 실현을 나란히 놓으면, 표면의 차이를 걷어낸 아래에서 "
     "같은 음운 현상이 움직이고 있음이 드러난다.",
     "Placing Korean palatalization beside English flapping reveals the same phonological "
     "process working under different surfaces."),
    (7, "의사소통 수단 그 이상", "More Than a Means of Communication", "2026-06", "01",
     ["society", "change", "korean"],
     "드라마 속 ‘아가씨’라는 호칭에서 출발해, 사전적 정의가 그대로인 단어가 30년 만에 "
     "어떻게 다른 말이 되었는지를 본다.",
     "How a word whose dictionary definition never changed became a different word in "
     "thirty years."),
    (8, "영어는 우리에게 무엇일까", "What English Means to Us", "2026-06", "15",
     ["society", "english", "phonetics"],
     "박찬호 선수의 ‘um’ 발음을 둘러싼 옛 논란을 통해, 한국 사회가 영어에 부여해 온 의미를 "
     "짚는다.",
     "An old controversy over a baseball player's English filler sound, and what it says "
     "about how Korean society reads English."),
    (9, "반복의 중요성", "Why Repetition Matters", "2026-07", "01",
     ["morphology", "change", "english"],
     "영어 불규칙 동사는 왜 생겼고 왜 아직 살아남았는가. 사용 빈도가 형태를 지킨다는 "
     "설명을 따라간다.",
     "Why English irregular verbs arose and why they survive — frequency as the force that "
     "preserves form."),
    (10, "빈도와 유추", "Frequency and Analogy", "2026-07", "15",
     ["morphology", "change", "korean"],
     "한국어를 배우는 외국인의 ‘이게지’라는 실수에서, 유추가 어떻게 새로운 형태를 만들어 "
     "내는지를 읽어낸다.",
     "A learner's slip in Korean opens a view of how analogy generates new forms."),
    (11, "외래어 표기를 통해 알 수 있는 한국어의 특징", "What Loanword Spelling Reveals "
     "About Korean", "2026-08", "01", ["phonology", "korean", "change"],
     "‘쵸코렡’이 ‘초콜릿’이 되기까지. 외래어 표기의 변화가 한국어 음운 체계의 무엇을 "
     "드러내는지 살핀다.",
     "From ‘쵸코렡’ to ‘초콜릿’ — what shifting loanword orthography reveals about the "
     "Korean sound system."),
    (12, "현재 진행중인 한국어의 변화", "Changes Underway in Korean Right Now",
     "2026-08", "15", ["change", "korean", "phonology"],
     "언어 변화는 오래 지나야 보인다는 통념과 달리, 지금 우리 세대 안에서 진행 중인 "
     "한국어의 변화를 짚어낸다.",
     "Change is said to be visible only in hindsight; this essay points to shifts happening "
     "within our own generation."),
    (13, "영어의 철자는 왜 이렇게 엉망인가", "Why Is English Spelling Such a Mess?",
     "2026-09", "01", ["phonology", "english", "change"],
     "‘ghoti’로 fish를 쓸 수 있다는 유명한 농담에서 시작해, 영어 철자가 어긋나게 된 여러 "
     "역사적 요인을 정리한다.",
     "Starting from the famous claim that ‘ghoti’ could spell fish, and tracing the "
     "historical forces that pulled English spelling apart."),
]

# 연구 주제 ↔ 논문 ↔ 글 ↔ 강의를 잇는 실제 갈래
THREADS = [
    ("한국어 활용의 변이와 유추", "Variation and Analogy in Korean Inflection",
     "‘ㄹ’ 말음 어간의 활용에서 관찰되는 변이를 말뭉치와 설문으로 기술하고, 선택적 /ㄹ/ "
     "삽입을 유추 기반으로 설명한 두 편의 논문이 이 갈래에 있다.",
     "Two papers describe variation in the inflection of ㄹ-final stems and account for "
     "optional /ㄹ/ insertion through analogy.",
     [2, 3], [9, 10, 12], ["영어음운론", "영어음운론심화"]),
    ("제2언어의 강세 습득", "Acquiring Stress in a Second Language",
     "몰입 환경이 한국인 학습자의 영어 강세 지각과 발화에 어떤 차이를 만드는지를 다룬다. "
     "발음과 학습을 주제로 한 글들이 여기에 이어진다.",
     "How immersion changes English stress perception and production in Korean learners.",
     [0], [2, 5, 8], ["영어음성학", "영어학개론"]),
    ("조음과 음향의 미세한 조절", "Fine-Grained Articulatory and Acoustic Control",
     "한국어 폐쇄음에서 나타나는 양방향 길이 조절을 음성학적으로 측정한 연구다. 소리의 "
     "실현과 표기를 다룬 글들과 맞닿아 있다.",
     "A phonetic study of bidirectional duration modulation in Korean oral stops.",
     [1], [6, 11, 13], ["영어음성학", "영어학개관"]),
]

# ── 원본에서 꺼내기 ──────────────────────────────────────────────────────


def div_block(src, marker):
    """<div class="..."> 부터 짝이 맞는 </div> 까지 통째로."""
    i = src.find(marker)
    if i < 0:
        return ""
    depth = 0
    for m in re.finditer(r"<(/?)div\b[^>]*>", src[i:], re.I):
        depth += 1 if m.group(1) == "" else -1
        if depth == 0:
            return src[i:i + m.end()]
    return ""


def read_source(path):
    src = open(path, encoding="utf-8").read()
    a = src.find('<div class="content">')
    b = src.find("</div>", a)
    body = src[a + len('<div class="content">'):b]
    comments = div_block(src, '<div class="comments-section">')
    scripts = re.findall(r"<script\b.*?</script>", src, re.S)
    return body, comments, scripts


def paragraphs(text):
    """하드랩된 줄만 이어 붙인다. 낱말은 건드리지 않는다."""
    out = []
    for block in re.split(r"\n\s*\n", text.strip("\n")):
        lines = [ln.strip() for ln in block.split("\n") if ln.strip()]
        if lines:
            out.append(" ".join(lines))
    return out


def plain(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


# ── 템플릿 ──────────────────────────────────────────────────────────────

def head(title, desc, canon, *, lang="ko", alt=None, extra="", og_type="website"):
    t = [
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width,initial-scale=1">',
        f"<title>{title}</title>",
        f'<meta name="description" content="{desc}">',
        f'<link rel="canonical" href="{SITE}{canon}">',
        f'<meta property="og:site_name" content="{F["name_ko"]} | {F["name_en"]}">',
        f'<meta property="og:type" content="{og_type}">',
        f'<meta property="og:title" content="{title}">',
        f'<meta property="og:description" content="{desc}">',
        f'<meta property="og:url" content="{SITE}{canon}">',
        f'<meta property="og:image" content="{SITE}/images/profile.jpg">',
        f'<meta property="og:locale" content="{"ko_KR" if lang == "ko" else "en_US"}">',
        '<meta name="twitter:card" content="summary_large_image">',
    ]
    if alt:
        ko, en = alt
        t += [f'<link rel="alternate" hreflang="ko" href="{SITE}{ko}">',
              f'<link rel="alternate" hreflang="en" href="{SITE}{en}">',
              f'<link rel="alternate" hreflang="x-default" href="{SITE}{ko}">']
    t += [f'<link rel="alternate" type="application/rss+xml" title="{F["name_ko"]}" '
          f'href="{SITE}/feed.xml">',
          f'<link rel="stylesheet" href="{"../" if lang == "en" else ""}style.css">']
    return "\n".join(t) + extra


def nav(active, lang="ko"):
    p = "" if lang == "ko" else "../"
    items = ([("about.html", "소개"), ("research.html", "연구"),
              ("teaching.html", "강의"), ("blog.html", "글")] if lang == "ko" else
             [("about.html", "About"), ("research.html", "Research"),
              ("teaching.html", "Teaching"), ("writing.html", "Writing")])
    base = "" if lang == "ko" else "en/"
    home = f"{p}index.html" if lang == "ko" else "index.html"
    links = "".join(
        f'<a href="{href}"{" class=\'on\'" if href == active else ""}>{label}</a>'
        for href, label in items)
    switch = ('<a class="lang" href="en/index.html" hreflang="en">EN</a>' if lang == "ko"
              else '<a class="lang" href="../index.html" hreflang="ko">KO</a>')
    sub = (f'{F["rank_ko"]} · {F["dept_ko"]}' if lang == "ko"
           else f'{F["rank_en"]} · Chonnam National University')
    return f"""<header class="masthead">
  <div class="wrap masthead-in">
    <a class="brand" href="{home}">
      <span class="brand-en">{F["name_en"].upper()}</span>
      <span class="brand-ko">{F["name_ko"] if lang == "ko" else F["name_en"]}</span>
      <span class="brand-sub">{sub}</span>
    </a>
    <nav class="gnb">{links}{switch}</nav>
  </div>
</header>"""


def foot(lang="ko"):
    if lang == "ko":
        return f"""<footer class="foot">
  <div class="wrap foot-in">
    <div>
      <p class="foot-name">{F["name_ko"]} · {F["name_en"]}</p>
      <p class="foot-line">{F["dept_ko"]} {F["rank_ko"]}</p>
      <p class="foot-line">{F["office"]} · {F["tel"]}</p>
      <p class="foot-line"><a href="mailto:{F["email_univ"]}">{F["email_univ"]}</a></p>
    </div>
    <div>
      <p class="foot-line"><a href="{F["jnu_url"]}" rel="noopener">학과 교수 소개</a></p>
      <p class="foot-line"><a href="feed.xml">RSS</a></p>
      <p class="foot-line"><a href="en/index.html" hreflang="en">English</a></p>
    </div>
  </div>
  <div class="wrap foot-copy">© 2026 {F["name_ko"]}. 이 사이트는 GitHub Pages로 운영됩니다.</div>
</footer>"""
    return f"""<footer class="foot">
  <div class="wrap foot-in">
    <div>
      <p class="foot-name">{F["name_en"]}</p>
      <p class="foot-line">{F["rank_en"]}, Department of English Language and Literature</p>
      <p class="foot-line">Chonnam National University</p>
      <p class="foot-line"><a href="mailto:{F["email_univ"]}">{F["email_univ"]}</a></p>
    </div>
    <div>
      <p class="foot-line"><a href="{F["jnu_url"]}" rel="noopener">Department profile</a></p>
      <p class="foot-line"><a href="../feed.xml">RSS</a></p>
      <p class="foot-line"><a href="../index.html" hreflang="ko">한국어</a></p>
    </div>
  </div>
  <div class="wrap foot-copy">© 2026 {F["name_en"]}. Hosted on GitHub Pages.</div>
</footer>"""


def page(title, desc, canon, body, *, lang="ko", alt=None, extra="", og_type="website"):
    return (f"<!doctype html>\n<html lang=\"{lang}\">\n<head>\n"
            f"{head(title, desc, canon, lang=lang, alt=alt, extra=extra, og_type=og_type)}\n"
            f"</head>\n<body>\n{body}\n</body>\n</html>\n")


def jsonld(obj):
    return f'\n<script type="application/ld+json">{obj}</script>'


def person_ld():
    return ("""{"@context":"https://schema.org","@type":"Person",
"name":"Hijo Kang","alternateName":"강희조",
"jobTitle":"Associate Professor",
"url":"%s/about.html",
"image":"%s/images/profile.jpg",
"email":"mailto:%s",
"telephone":"+82-62-530-3165",
"affiliation":{"@type":"CollegeOrUniversity","name":"Chonnam National University",
"department":{"@type":"Organization","name":"Department of English Language and Literature"}},
"alumniOf":[{"@type":"CollegeOrUniversity","name":"Stony Brook University"},
{"@type":"CollegeOrUniversity","name":"Seoul National University"}],
"knowsAbout":["Phonetics","Phonology","Morphology","Korean language","English linguistics"],
"knowsLanguage":["ko","en"],
"sameAs":["%s"]}""" % (SITE, SITE, F["email_univ"], F["jnu_url"])).replace("\n", "")


def crumbs_ld(items):
    els = ",".join(
        '{"@type":"ListItem","position":%d,"name":"%s","item":"%s%s"}' % (i + 1, n, SITE, u)
        for i, (n, u) in enumerate(items))
    return ('{"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[%s]}'
            % els)


# ── 페이지 ──────────────────────────────────────────────────────────────

def build_home():
    feat = POSTS[-1]
    latest = list(reversed(POSTS))[1:4]
    fields = "".join(f"""
      <article class="field">
        <p class="field-en">{en}</p>
        <h3 class="field-ko">{ko}</h3>
        <p class="field-desc">{d}</p>
      </article>""" for ko, en, d, _ in FIELDS)
    latest_html = "".join(f"""
      <li class="row">
        <a class="row-link" href="post{n}.html">
          <span class="row-kicker">{" · ".join(TOPICS[t][0] for t in tp[:2])}</span>
          <span class="row-title">{t_ko}</span>
          <span class="row-sum">{summ}</span>
        </a>
        <span class="row-date">{ym.replace("-", ". ")}</span>
      </li>""" for n, t_ko, _, ym, _, tp, summ, _ in latest)
    pubs = "".join(f"""
      <li class="pub"><span class="pub-year">{y}</span>
        <span class="pub-body"><span class="pub-title">{t}</span>
        <span class="pub-src">{j} {v}</span></span></li>""" for y, t, j, v in PUBS[:3])
    ld = ('{"@context":"https://schema.org","@type":"WebSite","name":"강희조 | Hijo Kang",'
          '"url":"%s","inLanguage":["ko","en"],"about":["Phonetics","Phonology","Morphology"],'
          '"author":%s}' % (SITE, person_ld()))
    body = f"""{nav("index.html")}
<main>
  <section class="hero">
    <div class="wrap">
      <p class="hero-en">{F["name_en"].upper()}</p>
      <h1 class="hero-ko">{F["name_ko"]}</h1>
      <p class="hero-tag">{F["tagline_ko"]}</p>
      <p class="hero-role">{F["dept_ko"]} {F["rank_ko"]}<br>
        음성학 · 음운론 · 형태론</p>
      <p class="hero-cta"><a class="btn" href="research.html">연구 보기</a>
        <a class="btn btn-ghost" href="blog.html">글 읽기</a></p>
    </div>
  </section>

  <section class="band">
    <div class="wrap">
      <h2 class="sec-title">연구 분야</h2>
      <div class="fields">{fields}</div>
    </div>
  </section>

  <section class="band">
    <div class="wrap">
      <h2 class="sec-title">이 달의 글</h2>
      <a class="feature" href="post{feat[0]}.html">
        <p class="feature-kicker">{" · ".join(TOPICS[t][0] for t in feat[5])}</p>
        <h3 class="feature-title">{feat[1]}</h3>
        <p class="feature-sum">{feat[6]}</p>
        <p class="feature-meta">글 {feat[0]} · {feat[3].split("-")[0]}년 {int(feat[3].split("-")[1])}월</p>
      </a>
    </div>
  </section>

  <section class="band">
    <div class="wrap">
      <h2 class="sec-title">최근 글</h2>
      <ul class="rows">{latest_html}</ul>
      <p class="more"><a href="blog.html">글 전체 보기 →</a></p>
    </div>
  </section>

  <section class="band">
    <div class="wrap">
      <h2 class="sec-title">대표 논문</h2>
      <ul class="pubs">{pubs}</ul>
      <p class="more"><a href="research.html">연구 전체 보기 →</a></p>
    </div>
  </section>

  <section class="band">
    <div class="wrap">
      <h2 class="sec-title">강의</h2>
      <p class="band-lede">학부에서 영어음성학, 영어음운론, 영어학개론, 영어학개관을,
        대학원에서 영어음운론과 영어음운론심화를 맡고 있습니다.</p>
      <p class="more"><a href="teaching.html">강의 전체 보기 →</a></p>
    </div>
  </section>

  <section class="band">
    <div class="wrap about-strip">
      <h2 class="sec-title">소개</h2>
      <p class="band-lede">영어와 관련된 언어학개론, 음성학, 음운론을 가르치고 있으며,
        영어 및 한국어를 포함한 다양한 언어를 음운론적 관점에서 분석하는 연구를 수행하고
        있습니다.</p>
      <p class="more"><a href="about.html">소개 자세히 보기 →</a></p>
    </div>
  </section>
</main>
{foot()}"""
    return page(f'{F["name_ko"]} | {F["dept_ko"]} {F["rank_ko"]}',
                f'{F["dept_ko"]} {F["rank_ko"]} {F["name_ko"]}. 음성학·음운론·형태론을 연구하고 '
                '가르칩니다. 말소리의 변화와 그 규칙에 관한 글을 씁니다.',
                "/", body, alt=("/", "/en/index.html"), extra=jsonld(ld))


def build_about():
    career = "".join(f'<li class="cv"><span class="cv-what">{w}</span>'
                     f'<span class="cv-when">{t}</span></li>' for w, t in CAREER)
    edu = "".join(f'<li class="cv"><span class="cv-what">{d}</span>'
                  f'<span class="cv-when">{s}</span></li>' for d, s in EDU)
    ld = ('{"@context":"https://schema.org","@type":"ProfilePage",'
          '"mainEntity":%s,"dateModified":"%s"}' % (person_ld(), BUILD_DATE))
    body = f"""{nav("about.html")}
<main class="wrap doc">
  <p class="crumb"><a href="index.html">홈</a> <span>›</span> 소개</p>
  <h1 class="doc-title">소개</h1>
  <p class="doc-lede">{F["tagline_ko"]}</p>

  <div class="profile">
    <div class="profile-img"><img src="images/profile.jpg" alt="{F["name_ko"]} 교수"
      width="240" height="300" loading="lazy"></div>
    <div class="profile-body">
      <p class="p-name">{F["name_ko"]} <span class="p-en">Kang, Hijo</span></p>
      <p class="p-role">{F["dept_ko"]} {F["rank_ko"]}</p>
      <p>영어와 관련된 언어학개론, 음성학, 음운론을 가르치고 있으며, 영어 및 한국어를 포함한
        다양한 언어를 음운론적 관점에서 분석하는 연구를 수행하고 있습니다.</p>
      <p>표면으로 드러나는 언어들의 차이를 걷어내면 그 아래에서 비슷한 일이 일어나고 있다는
        것, 그리고 그 변화가 오랜 시간이 아니라 지금 우리 세대 안에서도 진행되고 있다는 것.
        연구와 글이 함께 향하는 곳입니다.</p>
      <ul class="chips">{"".join(f'<li>{ko}</li>' for ko, _, _, _ in FIELDS)}</ul>
    </div>
  </div>

  <h2 class="doc-h2">경력</h2>
  <ul class="cvlist">{career}</ul>

  <h2 class="doc-h2">학력</h2>
  <ul class="cvlist">{edu}</ul>

  <h2 class="doc-h2">연락처</h2>
  <table class="kv">
    <tr><th>이메일</th><td><a href="mailto:{F["email_univ"]}">{F["email_univ"]}</a></td></tr>
    <tr><th>연구실</th><td>{F["office"]}</td></tr>
    <tr><th>전화</th><td>{F["tel"]}</td></tr>
    <tr><th>학과 소개</th><td><a href="{F["jnu_url"]}" rel="noopener">전남대학교 영어영문학과
      교수 소개</a></td></tr>
  </table>

  <div class="note">
    <p>연구 갈래와 논문 목록은 <a href="research.html">연구</a>에, 담당 과목은
      <a href="teaching.html">강의</a>에 정리해 두었습니다.</p>
  </div>
</main>
{foot()}"""
    return page(f'소개 | {F["name_ko"]}',
                f'{F["name_ko"]}({F["name_en"]}) — {F["dept_ko"]} {F["rank_ko"]}. '
                'Stony Brook University 언어학 박사. 음성학·음운론·형태론.',
                "/about.html", body, alt=("/about.html", "/en/about.html"),
                extra=jsonld(ld) + jsonld(crumbs_ld([("홈", "/"), ("소개", "/about.html")])),
                og_type="profile")


def build_research():
    fields = "".join(f"""
    <article class="field-long">
      <p class="field-en">{en}</p>
      <h3 class="field-ko">{ko}</h3>
      <p>{d}</p>
    </article>""" for ko, en, d, _ in FIELDS)
    threads = ""
    for i, (ko, en, desc, _, pi, po, cs) in enumerate(THREADS, 1):
        pl = "".join(f'<li><span class="pub-year">{PUBS[k][0]}</span>'
                     f'<span class="pub-body"><span class="pub-title">{PUBS[k][1]}</span>'
                     f'<span class="pub-src">{PUBS[k][2]} {PUBS[k][3]}</span></span></li>'
                     for k in pi)
        el = "".join(f'<li><a href="post{n}.html">{dict((p[0], p[1]) for p in POSTS)[n]}</a></li>'
                     for n in po)
        cl = "".join(f"<li>{c}</li>" for c in cs)
        threads += f"""
    <section class="thread">
      <p class="thread-no">갈래 {i}</p>
      <h3 class="thread-title">{ko}</h3>
      <p class="thread-en">{en}</p>
      <p class="thread-desc">{desc}</p>
      <div class="thread-grid">
        <div><h4 class="thread-h">논문</h4><ul class="pubs tight">{pl}</ul></div>
        <div><h4 class="thread-h">이어지는 글</h4><ul class="linklist">{el}</ul></div>
        <div><h4 class="thread-h">관련 강의</h4><ul class="linklist plain">{cl}</ul></div>
      </div>
    </section>"""
    allpubs = "".join(f"""
      <li class="pub"><span class="pub-year">{y}</span>
        <span class="pub-body"><span class="pub-title">{t}</span>
        <span class="pub-src">{j} {v}</span></span></li>""" for y, t, j, v in PUBS)
    body = f"""{nav("research.html")}
<main class="wrap doc">
  <p class="crumb"><a href="index.html">홈</a> <span>›</span> 연구</p>
  <h1 class="doc-title">연구</h1>
  <p class="doc-lede">음성학, 음운론, 형태론. 영어와 한국어를 함께 놓고 말소리의 실현과
    변화를 관찰합니다.</p>

  <h2 class="doc-h2">연구 분야</h2>
  <div class="fields-long">{fields}</div>

  <h2 class="doc-h2">연구 갈래</h2>
  <p class="doc-note">논문과 글, 강의가 어떻게 이어지는지를 갈래별로 묶었습니다.</p>
  {threads}

  <h2 class="doc-h2">논문</h2>
  <ul class="pubs">{allpubs}</ul>
  <p class="doc-note">전체 목록은 <a href="{F["jnu_url"]}" rel="noopener">학과 교수 소개
    페이지</a>에서도 확인할 수 있습니다.</p>
</main>
{foot()}"""
    return page(f'연구 | {F["name_ko"]}',
                '음성학·음운론·형태론 연구. 한국어 활용의 변이와 유추, 제2언어 강세 습득, '
                '조음과 음향의 미세한 조절을 다룹니다.',
                "/research.html", body, alt=("/research.html", "/en/research.html"),
                extra=jsonld(crumbs_ld([("홈", "/"), ("연구", "/research.html")])))


def build_teaching():
    secs = ""
    for level, courses in COURSES:
        rows = "".join(f'<li class="course"><span class="course-ko">{ko}</span>'
                       f'<span class="course-en">{en}</span></li>' for ko, en in courses)
        secs += f'<h2 class="doc-h2">{level}</h2><ul class="courses">{rows}</ul>'
    body = f"""{nav("teaching.html")}
<main class="wrap doc">
  <p class="crumb"><a href="index.html">홈</a> <span>›</span> 강의</p>
  <h1 class="doc-title">강의</h1>
  <p class="doc-lede">영어와 관련된 언어학개론, 음성학, 음운론을 가르치고 있습니다.</p>
  {secs}
  <h2 class="doc-h2">수강생에게</h2>
  <div class="note">
    <p>강의계획서와 과제 안내는 학교 LMS를 통해 공지합니다. 수업 관련 문의는
      <a href="mailto:{F["email_univ"]}">{F["email_univ"]}</a>로 편하게 연락 주세요.
      연구실은 {F["office"]}입니다.</p>
    <p>수업에서 다루는 개념 가운데 몇 가지는 <a href="blog.html">글</a>에서 더 편한 말로
      풀어 두었습니다. 음운 변화는 <a href="post6.html">다르면서도 같은 언어 III</a>,
      형태의 불규칙은 <a href="post9.html">반복의 중요성</a>에서 시작하면 좋습니다.</p>
  </div>
</main>
{foot()}"""
    return page(f'강의 | {F["name_ko"]}',
                '학부 영어음성학·영어음운론·영어학개론·영어학개관, 대학원 영어음운론·'
                '영어음운론심화를 담당합니다.',
                "/teaching.html", body, alt=("/teaching.html", "/en/teaching.html"),
                extra=jsonld(crumbs_ld([("홈", "/"), ("강의", "/teaching.html")])))


def build_index_of_posts():
    used = []
    for _, _, _, _, _, tp, _, _ in POSTS:
        for t in tp:
            if t not in used:
                used.append(t)
    chips = "".join(f'<li><a href="#t-{t}">{TOPICS[t][0]}</a></li>' for t in used)
    rows = "".join(f"""
      <li class="row">
        <a class="row-link" href="post{n}.html">
          <span class="row-kicker">{" · ".join(TOPICS[t][0] for t in tp)}</span>
          <span class="row-title"><span class="row-no">{n}</span>{t_ko}</span>
          <span class="row-sum">{summ}</span>
        </a>
        <span class="row-date">{ym.replace("-", ". ")}</span>
      </li>""" for n, t_ko, _, ym, _, tp, summ, _ in reversed(POSTS))
    groups = ""
    for t in used:
        ps = [p for p in POSTS if t in p[5]]
        items = "".join(f'<li><a href="post{p[0]}.html">{p[1]}</a>'
                        f'<span class="g-date">{p[3].replace("-", ". ")}</span></li>'
                        for p in reversed(ps))
        groups += (f'<section class="group" id="t-{t}"><h3 class="group-title">'
                   f'{TOPICS[t][0]} <span class="group-en">{TOPICS[t][1]}</span>'
                   f'<span class="group-n">{len(ps)}편</span></h3>'
                   f'<ul class="linklist">{items}</ul></section>')
    ld = ('{"@context":"https://schema.org","@type":"CollectionPage",'
          '"name":"글","url":"%s/blog.html","inLanguage":"ko","author":%s,'
          '"hasPart":[%s]}' % (SITE, person_ld(), ",".join(
              '{"@type":"BlogPosting","headline":"%s","url":"%s/post%d.html",'
              '"datePublished":"%s-%s"}' % (p[1], SITE, p[0], p[3], p[4]) for p in POSTS)))
    body = f"""{nav("blog.html")}
<main class="wrap doc">
  <p class="crumb"><a href="index.html">홈</a> <span>›</span> 글</p>
  <h1 class="doc-title">글</h1>
  <p class="doc-lede">언어의 변화와 그 규칙에 관한 글. 강의실에서 다 하지 못한 이야기를
    한 달에 두 편 정도 적어 둡니다.</p>
  <ul class="chips chips-link">{chips}</ul>

  <h2 class="doc-h2">전체 <span class="count">{len(POSTS)}편</span></h2>
  <ul class="rows">{rows}</ul>

  <h2 class="doc-h2">주제로 찾기</h2>
  <div class="groups">{groups}</div>
</main>
{foot()}"""
    return page(f'글 | {F["name_ko"]}',
                '언어의 변화, 말소리, 외국어 습득에 관한 글 13편. 전남대 영어영문학과 '
                f'{F["name_ko"]} 교수가 씁니다.',
                "/blog.html", body, alt=("/blog.html", "/en/writing.html"),
                extra=jsonld(ld) + jsonld(crumbs_ld([("홈", "/"), ("글", "/blog.html")])))


def build_post(meta, src_dir):
    n, t_ko, t_en, ym, day, tp, summ, summ_en = meta
    body_raw, comments, scripts = read_source(os.path.join(src_dir, f"post{n}.html"))
    paras = "\n".join(f"<p>{p}</p>" for p in paragraphs(body_raw))
    date_iso = f"{ym}-{day}"
    y, mo = ym.split("-")
    disp = f"{y}년 {int(mo)}월"

    prev_p = next((p for p in POSTS if p[0] == n - 1), None)
    next_p = next((p for p in POSTS if p[0] == n + 1), None)
    pager = ""
    if prev_p:
        pager += (f'<a class="pg pg-prev" href="post{prev_p[0]}.html">'
                  f'<span class="pg-l">이전 글</span>'
                  f'<span class="pg-t">{prev_p[1]}</span></a>')
    if next_p:
        pager += (f'<a class="pg pg-next" href="post{next_p[0]}.html">'
                  f'<span class="pg-l">다음 글</span>'
                  f'<span class="pg-t">{next_p[1]}</span></a>')

    scored = []
    for p in POSTS:
        if p[0] == n:
            continue
        s = len(set(p[5]) & set(tp))
        if s:
            scored.append((s, -abs(p[0] - n), p))
    scored.sort(reverse=True)
    rel = "".join(f'<li><a href="post{p[0]}.html"><span class="rel-k">'
                  f'{" · ".join(TOPICS[t][0] for t in p[5][:2])}</span>'
                  f'<span class="rel-t">{p[1]}</span></a></li>' for _, _, p in scored[:3])

    tags = "".join(f'<li><a href="blog.html#t-{t}">{TOPICS[t][0]}</a></li>' for t in tp)
    desc = html.escape(plain(summ))[:155]
    ld = ('{"@context":"https://schema.org","@type":"BlogPosting",'
          '"headline":"%s","description":"%s","url":"%s/post%d.html",'
          '"mainEntityOfPage":{"@type":"WebPage","@id":"%s/post%d.html"},'
          '"datePublished":"%s","dateModified":"%s","inLanguage":"ko",'
          '"image":"%s/images/profile.jpg",'
          '"about":[%s],"keywords":"%s","author":%s,'
          '"publisher":{"@type":"Person","name":"Hijo Kang","url":"%s/about.html"},'
          '"isPartOf":{"@type":"Blog","name":"강희조의 글","url":"%s/blog.html"}}'
          % (t_ko, desc, SITE, n, SITE, n, date_iso, date_iso, SITE,
             ",".join('{"@type":"Thing","name":"%s"}' % TOPICS[t][1] for t in tp),
             ", ".join(TOPICS[t][0] for t in tp), person_ld(), SITE, SITE))
    crumb = crumbs_ld([("홈", "/"), ("글", "/blog.html"), (t_ko, f"/post{n}.html")])

    body = f"""{nav("blog.html")}
<main class="wrap">
  <article class="essay">
    <p class="crumb"><a href="index.html">홈</a> <span>›</span>
      <a href="blog.html">글</a> <span>›</span> 글 {n}</p>
    <header class="essay-head">
      <p class="essay-kicker">{" · ".join(TOPICS[t][0] for t in tp)}</p>
      <h1 class="essay-title">{t_ko}</h1>
      <p class="essay-en">{t_en}</p>
      <p class="essay-meta"><time datetime="{date_iso}">{disp}</time>
        <span class="dot">·</span> 글 {n}
        <span class="dot">·</span> {F["name_ko"]}</p>
    </header>

    <div class="essay-body">
{paras}
    </div>

    <ul class="chips chips-link essay-tags">{tags}</ul>

    <aside class="author">
      <img class="author-img" src="images/profile.jpg" alt="{F["name_ko"]}"
        width="72" height="72" loading="lazy">
      <div class="author-body">
        <p class="author-name">글 · {F["name_ko"]} <span class="p-en">Hijo Kang</span></p>
        <p class="author-role">{F["dept_ko"]} {F["rank_ko"]}<br>
          Ph.D. in Linguistics, Stony Brook University</p>
        <p class="author-fields">음성학 · 음운론 · 형태론</p>
        <p class="author-more"><a href="about.html">소개 보기 →</a>
          <a href="research.html">연구 보기 →</a></p>
      </div>
    </aside>

    <nav class="pager">{pager}</nav>

    <section class="related">
      <h2 class="rel-title">함께 읽기</h2>
      <ul class="rels">{rel}</ul>
    </section>

{comments}
  </article>
</main>
{foot()}
{chr(10).join(scripts)}"""
    return page(f"{t_ko} | {F['name_ko']}", desc, f"/post{n}.html", body,
                extra=jsonld(ld) + jsonld(crumb), og_type="article")


# ── 영문 ────────────────────────────────────────────────────────────────

def build_en_home():
    fields = "".join(f"""
      <article class="field">
        <p class="field-en">{ko}</p>
        <h3 class="field-ko">{en}</h3>
        <p class="field-desc">{d_en}</p>
      </article>""" for ko, en, _, d_en in FIELDS)
    pubs = "".join(f"""
      <li class="pub"><span class="pub-year">{y}</span>
        <span class="pub-body"><span class="pub-title">{t}</span>
        <span class="pub-src">{j} {v}</span></span></li>""" for y, t, j, v in PUBS)
    body = f"""{nav("index.html", "en")}
<main>
  <section class="hero">
    <div class="wrap">
      <p class="hero-en">{F["name_en"].upper()}</p>
      <h1 class="hero-ko">{F["name_en"]}</h1>
      <p class="hero-tag">{F["tagline_en"]}</p>
      <p class="hero-role">{F["rank_en"]}, Department of English Language and Literature<br>
        Chonnam National University<br>Phonetics · Phonology · Morphology</p>
      <p class="hero-cta"><a class="btn" href="research.html">Research</a>
        <a class="btn btn-ghost" href="writing.html">Writing</a></p>
    </div>
  </section>
  <section class="band"><div class="wrap">
    <h2 class="sec-title">Research Areas</h2>
    <div class="fields">{fields}</div>
  </div></section>
  <section class="band"><div class="wrap">
    <h2 class="sec-title">Publications</h2>
    <ul class="pubs">{pubs}</ul>
    <p class="more"><a href="research.html">See research →</a></p>
  </div></section>
  <section class="band"><div class="wrap">
    <h2 class="sec-title">Writing</h2>
    <p class="band-lede">Essays on language change, speech sounds, and learning a second
      language. Written in Korean, with English summaries.</p>
    <p class="more"><a href="writing.html">See all essays →</a></p>
  </div></section>
</main>
{foot("en")}"""
    return page(f'{F["name_en"]} | Phonetics, Phonology, Morphology',
                f'{F["name_en"]}, {F["rank_en"]} of English Language and Literature at '
                'Chonnam National University. Phonetics, phonology, and morphology.',
                "/en/index.html", body, lang="en", alt=("/", "/en/index.html"),
                extra=jsonld(person_ld()))


def build_en_about():
    career = "".join(f'<li class="cv"><span class="cv-what">{w}</span>'
                     f'<span class="cv-when">{t}</span></li>' for w, t in CAREER_EN)
    edu = "".join(f'<li class="cv"><span class="cv-what">{d}</span>'
                  f'<span class="cv-when">{s}</span></li>' for d, s in EDU_EN)
    body = f"""{nav("about.html", "en")}
<main class="wrap doc">
  <p class="crumb"><a href="index.html">Home</a> <span>›</span> About</p>
  <h1 class="doc-title">About</h1>
  <p class="doc-lede">{F["tagline_en"]}</p>
  <div class="profile">
    <div class="profile-img"><img src="../images/profile.jpg" alt="{F["name_en"]}"
      width="240" height="300" loading="lazy"></div>
    <div class="profile-body">
      <p class="p-name">{F["name_en"]} <span class="p-en">강희조</span></p>
      <p class="p-role">{F["rank_en"]}, Department of English Language and Literature,
        Chonnam National University</p>
      <p>I teach introduction to English linguistics, phonetics, and phonology, and my
        research analyses a range of languages — English and Korean among them — from a
        phonological perspective.</p>
      <ul class="chips">{"".join(f'<li>{en}</li>' for _, en, _, _ in FIELDS)}</ul>
    </div>
  </div>
  <h2 class="doc-h2">Appointments</h2>
  <ul class="cvlist">{career}</ul>
  <h2 class="doc-h2">Education</h2>
  <ul class="cvlist">{edu}</ul>
  <h2 class="doc-h2">Contact</h2>
  <table class="kv">
    <tr><th>Email</th><td><a href="mailto:{F["email_univ"]}">{F["email_univ"]}</a></td></tr>
    <tr><th>Office</th><td>{F["office_en"]}</td></tr>
    <tr><th>Phone</th><td>+82-62-530-3165</td></tr>
    <tr><th>Department</th><td><a href="{F["jnu_url"]}" rel="noopener">Faculty profile</a></td></tr>
  </table>
</main>
{foot("en")}"""
    return page(f'About | {F["name_en"]}',
                f'{F["name_en"]} — {F["rank_en"]} at Chonnam National University. '
                'Ph.D. in Linguistics, Stony Brook University.',
                "/en/about.html", body, lang="en", alt=("/about.html", "/en/about.html"),
                extra=jsonld('{"@context":"https://schema.org","@type":"ProfilePage",'
                             '"mainEntity":%s}' % person_ld()), og_type="profile")


def build_en_research():
    fields = "".join(f"""
    <article class="field-long"><p class="field-en">{ko}</p>
      <h3 class="field-ko">{en}</h3><p>{d_en}</p></article>""" for ko, en, _, d_en in FIELDS)
    threads = ""
    for i, (ko, en, _, desc_en, pi, po, _) in enumerate(THREADS, 1):
        pl = "".join(f'<li><span class="pub-year">{PUBS[k][0]}</span>'
                     f'<span class="pub-body"><span class="pub-title">{PUBS[k][1]}</span>'
                     f'<span class="pub-src">{PUBS[k][2]} {PUBS[k][3]}</span></span></li>'
                     for k in pi)
        el = "".join(f'<li><a href="../post{n}.html" hreflang="ko">'
                     f'{dict((p[0], p[2]) for p in POSTS)[n]}</a>'
                     f'<span class="g-date">in Korean</span></li>' for n in po)
        threads += f"""
    <section class="thread"><p class="thread-no">Thread {i}</p>
      <h3 class="thread-title">{en}</h3><p class="thread-en">{ko}</p>
      <p class="thread-desc">{desc_en}</p>
      <div class="thread-grid">
        <div><h4 class="thread-h">Papers</h4><ul class="pubs tight">{pl}</ul></div>
        <div><h4 class="thread-h">Related essays</h4><ul class="linklist">{el}</ul></div>
      </div></section>"""
    allpubs = "".join(f"""
      <li class="pub"><span class="pub-year">{y}</span>
        <span class="pub-body"><span class="pub-title">{t}</span>
        <span class="pub-src">{j} {v}</span></span></li>""" for y, t, j, v in PUBS)
    body = f"""{nav("research.html", "en")}
<main class="wrap doc">
  <p class="crumb"><a href="index.html">Home</a> <span>›</span> Research</p>
  <h1 class="doc-title">Research</h1>
  <p class="doc-lede">Phonetics, phonology, and morphology — observing how speech sounds
    are realised and how they change, with English and Korean side by side.</p>
  <h2 class="doc-h2">Areas</h2>
  <div class="fields-long">{fields}</div>
  <h2 class="doc-h2">Threads</h2>
  {threads}
  <h2 class="doc-h2">Publications</h2>
  <ul class="pubs">{allpubs}</ul>
</main>
{foot("en")}"""
    return page(f'Research | {F["name_en"]}',
                'Phonetics, phonology and morphology: variation and analogy in Korean '
                'inflection, L2 stress acquisition, and duration in Korean oral stops.',
                "/en/research.html", body, lang="en",
                alt=("/research.html", "/en/research.html"))


def build_en_teaching():
    secs = ""
    for level, courses in COURSES:
        lv = "Undergraduate" if level == "학부" else "Graduate"
        rows = "".join(f'<li class="course"><span class="course-ko">{en}</span>'
                       f'<span class="course-en">{ko}</span></li>' for ko, en in courses)
        secs += f'<h2 class="doc-h2">{lv}</h2><ul class="courses">{rows}</ul>'
    body = f"""{nav("teaching.html", "en")}
<main class="wrap doc">
  <p class="crumb"><a href="index.html">Home</a> <span>›</span> Teaching</p>
  <h1 class="doc-title">Teaching</h1>
  <p class="doc-lede">Introduction to English linguistics, phonetics, and phonology.</p>
  {secs}
  <div class="note"><p>Syllabi and assignments are posted through the university LMS.
    For questions, write to <a href="mailto:{F["email_univ"]}">{F["email_univ"]}</a>.
    Office: {F["office_en"]}.</p></div>
</main>
{foot("en")}"""
    return page(f'Teaching | {F["name_en"]}',
                'Courses in phonetics, phonology, and English linguistics at Chonnam '
                'National University.',
                "/en/teaching.html", body, lang="en",
                alt=("/teaching.html", "/en/teaching.html"))


def build_en_writing():
    rows = "".join(f"""
      <li class="row">
        <a class="row-link" href="../post{n}.html" hreflang="ko">
          <span class="row-kicker">{" · ".join(TOPICS[t][1] for t in tp)}</span>
          <span class="row-title"><span class="row-no">{n}</span>{t_en}</span>
          <span class="row-sum">{s_en}</span>
        </a>
        <span class="row-date">{ym.replace("-", ". ")}</span>
      </li>""" for n, _, t_en, ym, _, tp, _, s_en in reversed(POSTS))
    body = f"""{nav("writing.html", "en")}
<main class="wrap doc">
  <p class="crumb"><a href="index.html">Home</a> <span>›</span> Writing</p>
  <h1 class="doc-title">Writing</h1>
  <p class="doc-lede">Essays on language change, speech sounds, and second-language
    learning — roughly two a month.</p>
  <div class="note"><p><strong>The essays are written in Korean.</strong> Titles and
    summaries below are in English; following a link opens the Korean text.</p></div>
  <h2 class="doc-h2">All essays <span class="count">{len(POSTS)}</span></h2>
  <ul class="rows">{rows}</ul>
</main>
{foot("en")}"""
    return page(f'Writing | {F["name_en"]}',
                'Essays on language change, phonetics and second-language learning by '
                f'{F["name_en"]}. Written in Korean with English summaries.',
                "/en/writing.html", body, lang="en", alt=("/blog.html", "/en/writing.html"))


# ── 부속 파일 ───────────────────────────────────────────────────────────

def build_sitemap():
    urls = [("/", "1.0"), ("/about.html", "0.9"), ("/research.html", "0.9"),
            ("/blog.html", "0.9"), ("/teaching.html", "0.7"),
            ("/en/index.html", "0.8"), ("/en/about.html", "0.7"),
            ("/en/research.html", "0.7"), ("/en/writing.html", "0.7"),
            ("/en/teaching.html", "0.6")]
    urls += [(f"/post{p[0]}.html", "0.8") for p in POSTS]
    items = "".join(
        f"\n  <url><loc>{SITE}{u}</loc><lastmod>{BUILD_DATE}</lastmod>"
        f"<priority>{pr}</priority></url>" for u, pr in urls)
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
            f"{items}\n</urlset>\n")


def build_robots():
    return f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n"


MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def build_feed():
    items = ""
    for n, t_ko, _, ym, day, tp, summ, _ in reversed(POSTS):
        y, mo = ym.split("-")
        pub = f"{day} {MONTHS[int(mo) - 1]} {y} 09:00:00 +0900"
        cats = "".join(f"<category>{TOPICS[t][0]}</category>" for t in tp)
        items += f"""
    <item>
      <title>{html.escape(t_ko)}</title>
      <link>{SITE}/post{n}.html</link>
      <guid isPermaLink="true">{SITE}/post{n}.html</guid>
      <description>{html.escape(summ)}</description>
      <pubDate>{pub}</pubDate>
      <dc:creator>{F["name_ko"]}</dc:creator>{cats}
    </item>"""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:dc="http://purl.org/dc/elements/1.1/"
     xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>{F["name_ko"]} | 언어의 변화에 관한 글</title>
    <link>{SITE}/blog.html</link>
    <atom:link href="{SITE}/feed.xml" rel="self" type="application/rss+xml"/>
    <description>{F["dept_ko"]} {F["rank_ko"]} {F["name_ko"]}의 글. 음성학·음운론·형태론.</description>
    <language>ko</language>{items}
  </channel>
</rss>
"""


def build_404():
    body = f"""{nav("")}
<main class="wrap doc">
  <h1 class="doc-title">찾는 쪽이 없습니다</h1>
  <p class="doc-lede">주소가 바뀌었거나, 지워진 쪽일 수 있습니다.</p>
  <ul class="linklist">
    <li><a href="/">홈</a></li>
    <li><a href="/blog.html">글 목록</a></li>
    <li><a href="/research.html">연구</a></li>
    <li><a href="/about.html">소개</a></li>
  </ul>
</main>
{foot()}"""
    return page("404 | 강희조", "찾는 쪽이 없습니다.", "/404.html", body)


# ── 실행 ────────────────────────────────────────────────────────────────

def main(src_dir, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(os.path.join(out_dir, "en"), exist_ok=True)

    w = lambda rel, txt: open(os.path.join(out_dir, rel), "w", encoding="utf-8").write(txt)

    w("index.html", build_home())
    w("about.html", build_about())
    w("research.html", build_research())
    w("teaching.html", build_teaching())
    w("blog.html", build_index_of_posts())
    for meta in POSTS:
        w(f"post{meta[0]}.html", build_post(meta, src_dir))
    w("en/index.html", build_en_home())
    w("en/about.html", build_en_about())
    w("en/research.html", build_en_research())
    w("en/teaching.html", build_en_teaching())
    w("en/writing.html", build_en_writing())
    w("sitemap.xml", build_sitemap())
    w("robots.txt", build_robots())
    w("feed.xml", build_feed())
    w("404.html", build_404())

    css = os.path.join(os.path.dirname(os.path.abspath(__file__)), "style.css")
    if os.path.exists(css):
        shutil.copy(css, os.path.join(out_dir, "style.css"))

    print(f"완료 → {out_dir} ({len(os.listdir(out_dir))}개 항목)")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
