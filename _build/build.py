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
    "office": "인문대 2호관 404호",
    "office_en": "Humanities Bldg. 2, Room 404",
    "tel": "062-530-3165",
    "email_univ": "hijokang@jnu.ac.kr",
    "jnu_url": ("https://ell.jnu.ac.kr/ell/14378/subview.do?enc="
                "Zm5jdDF8QEB8JTJGcHJvZiUyRmVsbCUyRjI2MyUyRjI2OTUlMkZ2aWV3LmRvJTNG"),
    # 첫 화면의 키 메시지. 이름은 이미 머리글에 있으므로, 여기서는 이 사이트가
    # 무엇을 말하는 곳인지를 먼저 말한다. 연구(변이·유추)와 에세이(언어 변화)이
    # 함께 향하는 한 문장이다.
    "key_kicker": "PHONETICS · PHONOLOGY · MORPHOLOGY",
    "key_ko": "말소리는 지금도 변하고 있습니다",
    "key_sub_ko": "그 변화에는 규칙이 있습니다. 한국어와 영어를 함께 놓고 "
                  "그 규칙을 찾습니다.",
    "key_en": "Speech sounds are still changing",
    "key_sub_en": "And the change follows rules. I look for them with Korean and "
                  "English side by side.",
}

# 각 쪽의 키 메시지. 지어낸 말이 아니라 이 사이트에 이미 있는 문장에서 가져왔다.
#   프로필 — 소개 글의 '표면의 차이를 걷어내면 그 아래에서 비슷한 일이…'
#   연구분야 — 연구 갈래 설명의 '귀로는 잘 구별되지 않는 미세한 조절을 측정한다'
#   강의 — 담당 과목(음성학·음운론·영어학개론)이 실제로 다루는 일
#   에세이 — 글 목록 설명의 '강의실에서 다 하지 못한 이야기'
PAGE_KEY = {
    # 프로필은 본문이 짧아 설명글 없이 큰 문장 하나로 세운다
    "about": ("프로필", "말소리의 변화를 관찰하고, 그 안의 규칙을 찾습니다",
              "Profile",
              "Observing how speech sounds change, and finding the patterns behind them"),
    "research": ("연구분야", "소리로 스쳐 지나가는 차이를, 숫자로 붙잡습니다",
                 "Research", "Catching in numbers the differences that slip past as sound"),
    "teaching": ("강의", "말소리를 듣고, 적고, 설명하는 법을 가르칩니다",
                 "Teaching", "How to hear a speech sound, write it down, and explain it"),
    "writing": ("에세이", "강의실에서 다 하지 못한 이야기를 적습니다",
                "Essays", "The things there was never time for in class"),
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

# 연구업적.
# 출처는 셋을 합쳤다 — 학과 교수소개 페이지(정본), Crossref(「강희조」·「Hijo Kang」),
# OpenAlex. DOI 가 있는 항목은 모두 DOI 로 원제·권호·쪽수를 확인했다.
# 저자는 (한글, 영문) 쌍이고, 기록에 영문 표기가 없으면 한글을 그대로 쓴다.
KANG = ("강희조", "Hijo Kang")
OH = ("오미라", "Mira Oh")
KIM_HJ = ("김현주", "Hyun-Ju Kim")
KO_SY = ("고성연", "Seongyeon Ko")
YUN = ("윤지원", "Jiwon Yun")
LEE_ES = ("이은숙", "Eunsuk Lee")
LEE_HY = ("이효영", "이효영")
KIM_DH = ("김다희", "Dahee Kim")
KIM_YJ = ("김연주", "Yeonju Kim")


def P(pid, year, title, venue_ko, venue_en, detail, authors, doi=None,
      kind="article", title_ko=None):
    return {"id": pid, "year": year, "title": title, "title_ko": title_ko,
            "venue_ko": venue_ko, "venue_en": venue_en, "detail": detail,
            "authors": authors, "doi": doi, "kind": kind}


PUBS = [
    P("l2immersion", "2024",
      "The Effect of L2 Immersion on English Stress Perception and Production by "
      "Korean Learners",
      "음성·음운·형태론 연구", "Studies in Phonetics, Phonology and Morphology",
      "30-2, 145–170", [KANG]),
    P("bidirdur", "2024",
      "A phonetic study of bidirectional duration modulation in Korean oral stops",
      "언어", "Korean Journal of Linguistics", "49-1, 1–20", [KANG]),
    P("coronal", "2024",
      "The Roles of Phonology, Morphology, and Frequency in the Variation of "
      "Noun-final Coronal Obstruents in Korean",
      "언어학 연구", "Studies in Linguistics", "73, 7–33", [KANG, KIM_HJ],
      "10.17002/sil..73.202410.7"),
    P("vot", "2024",
      "A perception-based analysis of voice onset time (VOT) dissimilation in Korean",
      "말소리와 음성과학", "Phonetics and Speech Sciences", "16-1, 25–31", [KANG, OH],
      "10.13064/ksss.2024.16.1.025"),
    P("linsert", "2023",
      "An Analogy-based Study of Optional /l/-insertion in Korean Verbal Conjugation",
      "언어학 연구", "Studies in Linguistics", "69, 1–19", [KANG, OH],
      "10.17002/sil..69.202310.1",
      title_ko="한국어 용언 활용에 나타나는 선택적 /ㄹ/ 삽입에 대한 유추 기반 분석"),
    P("lstem", "2023",
      "한국어 ‘ㄹ’ 말음 어간의 활용에서 나타나는 변이의 양상: 구어 말뭉치 및 설문을 통한 연구",
      "언어", "Korean Journal of Linguistics", "48-2, 399–416", [KANG]),
    P("harmonycorpus", "2023",
      "Transition of vowel harmony in Korean verbal conjugation: Patterns of "
      "variation in a spoken corpus",
      "말소리와 음성과학", "Phonetics and Speech Sciences", "15-2, 21–29", [KANG],
      "10.13064/ksss.2023.15.2.021"),
    P("durmod", "2020",
      "Duration modulation in Korean stops: nonlocal similarity avoidance vs. "
      "timing regulation",
      "음성·음운·형태론 연구", "Studies in Phonetics, Phonology and Morphology",
      "26-1, 103–125", [OH, KIM_DH, KANG], "10.17959/sppm.2020.26.1.103"),
    P("hrealize", "2019", "The Realizations of /h/ in Seoul and Gwangju Koreans",
      "언어학", "EONEOHAG", "84, 175–198", [KANG, LEE_HY], "10.17290/jlsk.2019..84.175"),
    P("tensify", "2019",
      "The Asymmetric tense consonant effects in compound and word-initial tensification",
      "음성·음운·형태론 연구", "Studies in Phonetics, Phonology and Morphology",
      "25-1, 3–30", [KANG, OH], "10.17959/sppm.2019.25.1.3"),
    P("stressperc", "2019",
      "Segmental and suprasegmental effects on Korean listeners’ English stress perception",
      "언어", "Korean Journal of Linguistics", "44-4, 721–747", [KANG, KIM_HJ],
      "10.18855/lisoko.2019.44.4.002"),
    P("review", "2019",
      "A Review of the Studies in English Linguistics from Studies in British and "
      "American Language and Literature",
      "영미어문학", "The British and American Language and Literature Association of Korea",
      "135, 93–111", [KANG, LEE_ES], "10.21297/ballak.2019.135.93"),
    P("prosodic", "2017", "The Prosodic Effect of Compound Tensification in Korean",
      "언어학 연구", "Studies in Linguistics", "45, 1–27", [KIM_YJ, KANG],
      "10.17002/sil..45.201710.1"),
    P("ewen", "2017", "Vowels of Beryozovka Ewen: An acoustic phonetic study",
      "알타이학보", "ALTAI HAKPO", "27, 1–23", [KANG, YUN, KO_SY],
      "10.15816/ask.2017..27.001"),
    P("laryngeal", "2016",
      "Dynamic and static aspects of laryngeal co-occurrence restrictions in Korean",
      "음성·음운·형태론 연구", "Studies in Phonetics, Phonology and Morphology",
      "22-1, 3–34", [KANG], "10.17959/sppm.2016.22.1.3"),
    P("harmonytime", "2016",
      "Variation and Change of Korean Vowel Harmony in Verbal Conjugation: "
      "An Apparent Time and Real Time Study",
      "언어학", "EONEOHAG", "76, 27–56", [KANG], "10.17290/jlsk.2016..76.27"),
    P("stressacoustic", "2016",
      "Acoustic Correlates of English Stress in Korean L2 Learners’ Perception",
      "영어학", "Korean Journal of English Language and Linguistics", "16-2, 169–196",
      [KANG, KIM_HJ], "10.15738/kjell.16.2.201606.169"),
    P("nanai", "2016",
      "A phonetic study of Nanai vowels: Using automated post-transcriptional "
      "processing techniques",
      "알타이학보", "ALTAI HAKPO", "26, 29–44", [YUN, KO_SY, KANG],
      "10.15816/ask.2016..26.003"),
    P("ocpmemory", "2015", "Interaction of perception and memory in segmental OCP",
      "알타이학보", "ALTAI HAKPO", "25, 145–165", [KANG], "10.15816/ask.2015..25.010"),
    P("inconsistency", "2014", "Inconsistency in Phonological Phenomena",
      "언어학", "EONEOHAG", "70, 93–115", [KANG], "10.17290/jlsk.2014..70.93",
      title_ko="음운 현상의 동기적 비일관성과 음운 이론"),
    P("hiatus", "2013",
      "Phonetic grounding of position and height asymmetries in hiatus resolution: "
      "An acoustic analysis of Korean VV sequences",
      "음성·음운·형태론 연구", "Studies in Phonetics, Phonology and Morphology",
      "19-2, 217–232", [KANG], "10.17959/sppm.2013.19.2.217"),
    P("manchu", "2013", "Segmental OCP in Manchu syllables",
      "알타이학보", "ALTAI HAKPO", "23, 1–22", [KANG], "10.15816/ask.2013..23.001"),
    P("diss", "2012",
      "Diachrony in Synchrony: Korean vowel harmony in verbal conjugation",
      "박사학위논문, Stony Brook University", "Ph.D. dissertation, Stony Brook University",
      "", [KANG], None, "dissertation"),
    P("tongueroot", "2011",
      "A phonetic study of the tongue root contrast in Buriat and Ewen",
      "LSA 연차대회 확장초록", "LSA Annual Meeting Extended Abstracts", "2",
      [KANG, KO_SY], "10.3765/exabs.v0i0.536", "conference"),
    P("blshiatus", "2010",
      "Position and Height Asymmetries in Hiatus Resolution: A case study of "
      "Korean VV sequences",
      "버클리 언어학회 논문집", "Proceedings of the Annual Meeting of the Berkeley "
      "Linguistics Society", "36-1, 174", [KANG], "10.3765/bls.v36i1.3910", "conference"),
    P("jasahiatus", "2010",
      "Position and height asymmetries in hiatus resolution: Are they phonetically "
      "driven phenomena?",
      "미국음향학회지", "The Journal of the Acoustical Society of America",
      "127-3 (Suppl.), 2018", [KANG], "10.1121/1.3385263", "conference"),
]

PUB_BY_ID = {p["id"]: p for p in PUBS}


def pub_li(p, lang="ko", show_authors=True):
    """논문 한 줄. 저자가 여럿일 때만 이름을 적고, DOI 가 있으면 건다."""
    i = 0 if lang == "ko" else 1
    title = p["title_ko"] if (lang == "ko" and p.get("title_ko")) else p["title"]
    venue = p["venue_ko"] if lang == "ko" else p["venue_en"]
    src = f"{venue} {p['detail']}".strip()
    extra = ""
    if show_authors and len(p["authors"]) > 1:
        extra = f'<span class="pub-au">{" · ".join(a[i] for a in p["authors"])}</span>'
    if p["doi"]:
        extra += (f'<a class="pub-doi" href="https://doi.org/{p["doi"]}" '
                  f'rel="noopener">DOI</a>')
    return (f'<li class="pub"><span class="pub-year">{p["year"]}</span>'
            f'<span class="pub-body"><span class="pub-title">{title}</span>'
            f'<span class="pub-src">{src}</span>'
            f'{f"<span class=\'pub-meta\'>{extra}</span>" if extra else ""}'
            f'</span></li>')


def pubs_list(items, lang="ko", cls="pubs"):
    return f'<ul class="{cls}">{"".join(pub_li(p, lang) for p in items)}</ul>'


def pubs_by_kind(kind):
    return [p for p in PUBS if p["kind"] == kind]


# 절 제목 앞 아이콘. 선만 쓰고 칠하지 않는다 — 사이트의 다른 요소와 같은 규칙.
# 16px 격자 안에서 1.5~14.5 사이에 그린다.
ICONS = {
    # 말소리 파형 — 연구 분야
    "wave": '<path d="M2 6v4M5.2 3.2v9.6M8.4 5v6M11.6 2.4v11.2M14.8 6.4v3.2"/>',
    # 논문 한 쪽
    "doc": ('<path d="M4.5 1.8h4.6l3.4 3.4v9a1 1 0 0 1-1 1H4.5a1 1 0 0 1-1-1V2.8'
            'a1 1 0 0 1 1-1z"/><path d="M9.1 1.8v3.4h3.4"/>'
            '<path d="M6 9.2h4M6 11.6h4"/>'),
    # 학사모 — 학력
    "cap": ('<path d="M8 2.2 15 5.6 8 9 1 5.6z"/>'
            '<path d="M4.2 7.1v3.5c0 1.1 1.7 2 3.8 2s3.8-.9 3.8-2V7.1"/>'),
    # 펼친 책 — 학위논문·강의
    "book": ('<path d="M8 4.6C8 3.3 6.6 2.6 4.9 2.6H1.8v9.2h3.1c1.7 0 3.1.7 3.1 2"/>'
             '<path d="M8 4.6c0-1.3 1.4-2 3.1-2h3.1v9.2h-3.1c-1.7 0-3.1.7-3.1 2"/>'
             '<path d="M8 4.6v9.2"/>'),
    # 퍼져 나가는 소리 — 학술대회 발표
    "talk": ('<circle cx="4.2" cy="8" r="1.7"/>'
             '<path d="M7.8 4.9a4.6 4.6 0 0 1 0 6.2"/>'
             '<path d="M10.9 2.5a8.2 8.2 0 0 1 0 11"/>'),
    # 서류가방 — 경력
    "career": ('<path d="M2.4 5.2h11.2a1 1 0 0 1 1 1v6.4a1 1 0 0 1-1 1H2.4'
               'a1 1 0 0 1-1-1V6.2a1 1 0 0 1 1-1z"/>'
               '<path d="M5.9 5.2V3.7a1 1 0 0 1 1-1h2.2a1 1 0 0 1 1 1v1.5"/>'
               '<path d="M1.4 8.7h13.2"/>'),
    # 편지 — 연락처
    "mail": ('<path d="M2.4 4h11.2a1 1 0 0 1 1 1v6.2a1 1 0 0 1-1 1H2.4a1 1 0 0 1-1-1V5'
             'a1 1 0 0 1 1-1z"/><path d="m1.7 5 6.3 4.1L14.3 5"/>'),
    # 줄글 목록 — 글 전체
    "list": ('<path d="M2 4.4h1.2M2 8h1.2M2 11.6h1.2"/>'
             '<path d="M5.8 4.4h8.2M5.8 8h8.2M5.8 11.6h8.2"/>'),
    # 꼬리표 — 주제로 찾기
    "tag": ('<path d="M8.8 2.4H3.4a1 1 0 0 0-1 1v5.4a1 1 0 0 0 .3.7l5.4 5.4a1 1 0 0 0 '
            '1.4 0l4.7-4.7a1 1 0 0 0 0-1.4L9.5 2.7a1 1 0 0 0-.7-.3z"/>'
            '<circle cx="5.9" cy="5.9" r="1.1"/>'),
    # 접어 둔 자리 — 이 달의 글
    "mark": '<path d="M4.2 2.2h7.6v11.6l-3.8-2.9-3.8 2.9z"/>',
    # 사람 — 소개
    "person": ('<circle cx="8" cy="5.5" r="2.6"/>'
               '<path d="M2.9 13.8a5.6 5.6 0 0 1 10.2 0"/>'),
}


def icon(name):
    return (f'<svg class="sec-icon" viewBox="0 0 16 16" aria-hidden="true" '
            f'focusable="false" xmlns="http://www.w3.org/2000/svg">'
            f'{ICONS[name]}</svg>')


def h2(title, name, cls="doc-h2", extra=""):
    """아이콘을 앞에 단 절 제목."""
    return (f'<h2 class="{cls}">{icon(name)}'
            f'<span class="sec-label">{title}</span>{extra}</h2>')


def _jitter(seed, n):
    """정해진 씨앗에서 나오는 흔들림. 매번 같은 그림이 나온다."""
    x = seed
    out = []
    for _ in range(n):
        x = (1103515245 * x + 12345) % 2147483648
        a = x / 2147483648
        x = (1103515245 * x + 12345) % 2147483648
        b = x / 2147483648
        out.append((a * 2 - 1, b * 2 - 1))
    return out


def art_research():
    """연구분야 — 모음 포먼트 도면.

    실제 음성학 논문의 F1-F2 산점도를 그대로 옮겼다. 모음마다 측정값이 흩어지고,
    그 분포를 타원으로 감싼다. 점선 화살표는 세대를 지나며 일어난 이동이다.
    """
    import math

    L, R, T, B = 78, 452, 56, 300

    grid = "".join(
        f'<line x1="{L}" y1="{T + (B - T) * i / 4:.1f}" x2="{R}" '
        f'y2="{T + (B - T) * i / 4:.1f}"/>' for i in range(1, 4))
    grid += "".join(
        f'<line x1="{L + (R - L) * i / 4:.1f}" y1="{T}" '
        f'x2="{L + (R - L) * i / 4:.1f}" y2="{B}"/>' for i in range(1, 4))

    ticks = "".join(f'<line x1="{L + (R - L) * i / 4:.1f}" y1="{B}" '
                    f'x2="{L + (R - L) * i / 4:.1f}" y2="{B + 6}"/>'
                    for i in range(5))
    ticks += "".join(f'<line x1="{L - 6}" y1="{T + (B - T) * i / 4:.1f}" '
                     f'x2="{L}" y2="{T + (B - T) * i / 4:.1f}"/>' for i in range(5))

    # (이름, 중심x, 중심y, 반지름x, 반지름y, 기울기, 점 개수, 씨앗, 강조여부)
    clusters = [
        ("i", 132, 96, 33, 21, -20, 13, 7, False),
        ("u", 396, 108, 29, 23, 16, 12, 23, False),
        ("e", 176, 194, 37, 23, -8, 14, 41, True),
        ("a", 286, 268, 42, 26, 7, 15, 59, False),
    ]
    dots, rings, labels = [], [], []
    for name, cx, cy, rx, ry, rot, n, seed, hot in clusters:
        cls = " hot" if hot else ""
        for k, (jx, jy) in enumerate(_jitter(seed, n)):
            t = math.atan2(jy, jx)
            r = (jx * jx + jy * jy) ** 0.5
            r = min(r, 1.0) ** 0.75
            px = cx + math.cos(t) * rx * r * 0.92
            py = cy + math.sin(t) * ry * r * 0.92
            # 측정값이 하나씩 찍히듯 천천히 드러났다 잦아든다
            delay = (seed * 0.13 + k * 0.31) % 3.4
            dots.append(f'<circle class="pt{cls}" cx="{px:.1f}" cy="{py:.1f}" '
                        f'r="2.2" style="animation-delay:-{delay:.2f}s"/>')
        rings.append(f'<ellipse class="ell{cls}" cx="{cx}" cy="{cy}" rx="{rx}" '
                     f'ry="{ry}" transform="rotate({rot} {cx} {cy})"/>')
        labels.append(f'<text x="{cx}" y="{cy - ry - 9}">{name}</text>')

    # 이동 — e 에서 a 쪽으로
    shift = ('<path class="shift" d="M204 210 C 236 228, 250 240, 262 252"/>'
             '<path class="head" d="M255 240 L266 256 L248 255 Z"/>')

    return f'''<svg class="page-art art-plot" viewBox="0 0 520 340" role="img"
  aria-label="모음별 포먼트 측정값이 흩어진 산점도와 그 분포를 감싼 타원, 이동을 나타낸 화살표"
  xmlns="http://www.w3.org/2000/svg">
  <g class="grid">{grid}</g>
  <g class="tick">{ticks}</g>
  <path class="axis" d="M{L} {T}V{B}H{R}"/>
  <g class="rings">{"".join(rings)}</g>
  <g class="pts">{"".join(dots)}</g>
  {shift}
  <g class="lab">{"".join(labels)}</g>
  <text class="ax" x="{(L + R) / 2:.0f}" y="{B + 30}">F2</text>
  <text class="ax" x="{L - 22}" y="{(T + B) / 2:.0f}"
    transform="rotate(-90 {L - 22} {(T + B) / 2:.0f})">F1</text>
</svg>'''


def art_teaching():
    """강의 — 음절 구조 나무. 음운론 수업에서 맨 처음 그리는 그림."""
    nodes = [("σ", 260, 54), ("O", 150, 158), ("R", 366, 158),
             ("N", 300, 264), ("C", 432, 264)]
    edges = [(260, 54, 150, 158), (260, 54, 366, 158),
             (366, 158, 300, 264), (366, 158, 432, 264)]
    import math

    # 가지는 위에서 아래로 차례차례 그어진다 — 칠판에 나무를 그리는 순서 그대로.
    # 선 길이를 재서 stroke-dasharray 에 넣어야 '그어지는' 모양이 나온다.
    lines = []
    for gi, (a, b, c, d) in enumerate(edges):
        y1, y2 = b + 15, d - 15
        lag = 0.0 if gi < 2 else 0.9      # 위 두 가지 먼저, 아래 두 가지 나중
        # pathLength 로 길이를 100 으로 맞춘다 — keyframes 에서 var() 를 쓰지
        # 않게 되어 사파리를 포함해 어디서나 같게 그어진다
        lines.append(f'<line x1="{a}" y1="{y1}" x2="{c}" y2="{y2}" '
                     f'pathLength="100" style="animation-delay:{lag:.2f}s"/>')
    lines = "".join(lines)

    # 마디는 제 가지가 다 그어진 뒤에 톡 하고 켜진다
    step = {"σ": 0.0, "O": 0.9, "R": 0.9, "N": 1.8, "C": 1.8}
    circles = "".join(f'<circle cx="{x}" cy="{y}" r="15" '
                      f'style="animation-delay:{step[t]:.2f}s"/>'
                      for t, x, y in nodes)
    labels = "".join(f'<text x="{x}" y="{y + 5.5}" '
                     f'style="animation-delay:{step[t]:.2f}s">{t}</text>'
                     for t, x, y in nodes)

    # 아래 파형은 움직이지 않는다 — 나무가 그려지는 동안 시선이 흩어지지 않게
    # 바닥에 깔린 채로만 둔다
    feet = []
    for gi, x in enumerate((150, 300, 432)):
        for i in range(7):
            h = 7 + abs(math.sin(gi * 1.7 + i * 0.9)) * 20
            fx = x - 34 + i * 11.5
            feet.append(f'<rect x="{fx - 0.9:.1f}" y="{318 - h:.1f}" width="1.8" '
                        f'height="{h:.1f}" rx="0.9"/>')
    feet = "".join(feet)
    return f'''<svg class="page-art art-teach-tree" viewBox="0 0 520 360" role="img"
  aria-label="음절 구조를 나타낸 나무 그림과 그 아래의 말소리 파형"
  xmlns="http://www.w3.org/2000/svg">
  <g class="art-edge">{lines}</g>
  <g class="art-node-o">{circles}</g>
  <g class="art-label">{labels}</g>
  <line class="art-base" x1="86" y1="318" x2="470" y2="318"/>
  <g class="art-foot">{feet}</g>
</svg>'''


def art_writing():
    """에세이 — 겹쳐 놓인 원고.

    뒤로 지난 호들이 쌓이고, 맨 앞 장에 제목·본문·그리고 글 속 도판으로
    말소리 파형이 들어 있다. 말소리에 관한 글이라는 성격을 그대로 옮겼다.
    """
    import math

    # 뒤에 쌓인 지난 원고 두 장
    back = ('<rect class="sheet back2" x="150" y="30" width="286" height="268" />'
            '<rect class="sheet back1" x="136" y="42" width="286" height="268" />')

    x0, y0, w = 118, 56, 286
    front = f'<rect class="sheet front" x="{x0}" y="{y0}" width="{w}" height="268"/>'

    tx = x0 + 26
    # 글이 실제로 써지듯 왼쪽부터 한 줄씩 그어진다. 줄마다 시작 시각을 심는다.
    d = [0.0]

    def w_line(cls, y, wd, gap=0.34):
        d[0] += gap
        return (f'<line class="{cls}" x1="{tx}" y1="{y}" x2="{tx + wd}" y2="{y}" '
                f'style="animation-delay:{d[0]:.2f}s"/>')

    head = (w_line("ttl", y0 + 34, 176, 0.30)
            + w_line("ttl", y0 + 52, 120)
            + w_line("rule", y0 + 70, 44))

    body = ""
    y = y0 + 92
    for wd in (232, 210, 226, 168):
        body += w_line("txt", y, wd)
        y += 15

    # 글 속 도판 — 파형
    fy = y + 18
    fig = f'<rect class="fig" x="{tx}" y="{fy - 26}" width="232" height="52"/>'
    bars = []
    for i in range(34):
        a = (math.sin(i * 1.71) * 0.5 + math.sin(i * 0.63) * 0.31
             + math.sin(i * 2.87) * 0.19)
        env = math.sin(min(i / 33, 1.0) * math.pi) ** 0.55
        h = abs(a) * env * 19 + 1.2
        bx = tx + 12 + i * 6.2
        # 글 속 도판이 살아 움직인다 — 한 방향으로 지나가는 물결
        bars.append(f'<rect x="{bx - 0.7:.1f}" y="{fy - h:.1f}" width="1.4" '
                    f'height="{2 * h:.1f}" rx="0.7" '
                    f'style="animation-delay:{2.6 + i * 0.045:.2f}s"/>')
    fig += f'<g class="wv">{"".join(bars)}</g>'

    tail = ""
    y = fy + 40
    d[0] = 3.9
    for wd in (226, 196):
        tail += w_line("txt", y, wd)
        y += 15

    return f'''<svg class="page-art art-sheets" viewBox="0 0 520 340" role="img"
  aria-label="겹쳐 놓인 원고 더미. 맨 앞 장에 제목과 본문, 그리고 말소리 파형 도판이 있다"
  xmlns="http://www.w3.org/2000/svg">
  {back}
  {front}
  {head}
  <g>{body}</g>
  {fig}
  <g>{tail}</g>
</svg>'''


def doc_head(crumb, key, lede, art=None, lang="ko"):
    """문서형 쪽의 머리.

    첫 화면과 같은 차례로 읽힌다 — 작은 쪽 이름, 키 메시지, 그리고 설명.
    쪽 이름은 작게 남겨 길찾기를 돕고, 큰 글자는 그 쪽이 하는 말이 가져간다.
    art 를 주면 오른쪽에 그림이 붙고, 없으면 한 단으로 선다.
    """
    kicker, title = (key[0], key[1]) if lang == "ko" else (key[2], key[3])
    sub = f'<p class="doc-lede">{lede}</p>' if lede else ""
    text = f'''<div class="doc-head-text">
      {crumb}
      <p class="doc-kicker">{kicker}</p>
      <h1 class="doc-title">{title}</h1>
      {sub}
    </div>'''
    if art is None:
        return f'<div class="doc-head doc-head-solo">{text}</div>'
    return f'''<div class="doc-head">
    {text}
    <div class="doc-head-art">{art}</div>
  </div>'''


def hero_svg():
    """첫 화면 그림 — 움직이는 파형.

    왼쪽은 실제 말소리처럼 제각각 떨리고(변화), 오른쪽은 일정한 간격으로 물결이
    지나간다(규칙). 키 메시지 '말소리는 지금도 변하고 있습니다 / 그 변화에는
    규칙이 있습니다'를 그대로 움직임으로 옮긴 것이다.

    움직임은 CSS 만으로 만든다. 막대마다 시작 시각과 주기를 다르게 심어 두고,
    나머지는 style.css 의 keyframes 가 맡는다. 자바스크립트를 쓰지 않는다.
    """
    import math

    W, H, MID = 560, 440, 214

    raw = []
    n_raw, x0, step = 44, 34, 5.9
    for i in range(n_raw):
        a = (math.sin(i * 1.73) * 0.46 + math.sin(i * 0.61) * 0.30
             + math.sin(i * 3.11) * 0.16 + math.sin(i * 0.23) * 0.08)
        env = 0.45 + 0.55 * math.sin(min(i / n_raw, 1.0) * math.pi) ** 0.7
        h = abs(a) * env * 96 + 3
        x = x0 + i * step
        # 제각각인 떨림 — 주기와 시작 시각을 막대마다 다르게 준다
        dur = 1.55 + abs(math.sin(i * 2.17)) * 1.15
        delay = (i * 0.047 + abs(math.sin(i * 1.31)) * 0.6) % 2.2
        raw.append(f'<rect x="{x - 0.8:.1f}" y="{MID - h:.1f}" width="1.6" '
                   f'height="{2 * h:.1f}" rx="0.8" '
                   f'style="animation-duration:{dur:.2f}s;'
                   f'animation-delay:-{delay:.2f}s"/>')

    reg = []
    n_reg, rx0, rstep = 15, 322, 13.4
    for i in range(n_reg):
        h = 26 + 40 * math.sin((i + 0.5) / n_reg * math.pi)
        x = rx0 + i * rstep
        # 한 방향으로 지나가는 물결 — 주기는 같고 시작 시각만 고르게 밀린다
        reg.append(f'<rect x="{x - 0.8:.1f}" y="{MID - h:.1f}" width="1.6" '
                   f'height="{2 * h:.1f}" rx="0.8" '
                   f'style="animation-delay:-{i * 0.16:.2f}s"/>')

    def curve(y0, y1, y2, y3):
        return (f'M34 {y0} C 150 {y1}, 240 {y2}, 320 {y2} '
                f'S 470 {y3}, 526 {y3}')

    f1 = curve(MID - 128, MID - 168, MID - 116, MID - 104)
    f2 = curve(MID + 132, MID + 176, MID + 118, MID + 108)

    ticks = "".join(f'<line x1="{34 + i * 61.6:.1f}" y1="{MID + 150}" '
                    f'x2="{34 + i * 61.6:.1f}" y2="{MID + 158}"/>' for i in range(9))

    return f'''<svg class="hero-art" viewBox="0 0 {W} {H}" role="img"
  aria-label="왼쪽에서 제각각 떨리던 말소리 파형이 오른쪽으로 가면서 일정한 물결로 정리되는 그림"
  xmlns="http://www.w3.org/2000/svg">
  <g class="art-wave">{"".join(raw)}</g>
  <g class="art-reg">{"".join(reg)}</g>
  <path class="art-formant" d="{f1}"/>
  <path class="art-formant" d="{f2}"/>
  <line class="art-axis" x1="34" y1="{MID}" x2="526" y2="{MID}"/>
  <g class="art-tick">{ticks}</g>
  <line class="art-divide" x1="303" y1="{MID - 150}" x2="303" y2="{MID + 150}"/>
  <circle class="art-dot" cx="303" cy="{MID}" r="3.2"/>
</svg>'''

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
#
# ※ '일'은 실제 발행일이 아니다. 확인된 것은 **월까지**뿐이다 —
#   원본 글에도 "2026년 3월"처럼 월만 적혀 있고, 저장소 이력도 글 1~10 이
#   2026-08-05 에 한꺼번에 올라가 발행일을 알려주지 않는다.
#   그래서 같은 달의 앞 글은 01, 뒤 글은 15 로 두었다. 화면에는 월만 보이고,
#   이 값은 RSS·구조화 데이터에서 **글 순서를 지키는 용도**로만 쓰인다.
#   교수님께 실제 날짜를 받으면 이 칸만 고치면 된다.
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
     "모음조화와 ‘ㄹ’ 말음 어간의 활용이 세대를 지나며 어떻게 흔들리는지를 말뭉치와 설문으로 "
     "기술하고, 그 변이를 빈도와 유추로 설명한다. 박사학위논문에서 시작해 지금까지 이어지는 "
     "가장 긴 줄기다.",
     "How vowel harmony and the inflection of ㄹ-final stems shift across generations, "
     "described from corpora and surveys and explained through frequency and analogy.",
     ["linsert", "lstem", "harmonycorpus", "coronal", "harmonytime", "diss"],
     [9, 10, 12], ["영어음운론", "영어음운론심화"]),
    ("제2언어의 강세 습득", "Acquiring Stress in a Second Language",
     "한국인 학습자가 영어 강세를 어떤 음향 단서로 듣고 어떻게 발화하는지, 그리고 몰입 환경이 "
     "그 차이를 얼마나 바꾸는지를 다룬다.",
     "Which acoustic cues Korean learners rely on to hear and produce English stress, and "
     "how far immersion changes them.",
     ["l2immersion", "stressperc", "stressacoustic"],
     [2, 5, 8], ["영어음성학", "영어학개론"]),
    ("조음과 음향의 미세한 조절", "Fine-Grained Articulatory and Acoustic Control",
     "폐쇄음의 길이와 성대 진동 시작 시간처럼, 귀로는 잘 구별되지 않는 미세한 조절을 측정한다. "
     "모음 연쇄가 어떻게 해소되는지를 다룬 초기 연구도 여기에 닿아 있다.",
     "Measuring fine control that the ear barely separates — stop duration, voice onset "
     "time — reaching back to early work on how vowel sequences resolve.",
     ["bidirdur", "vot", "durmod", "laryngeal", "hiatus", "blshiatus", "jasahiatus"],
     [6, 11, 13], ["영어음성학", "영어학개관"]),
    ("알타이 제어의 모음과 현장 음성학", "Vowels of Altaic Languages and Field Phonetics",
     "부리야트어, 에벤어, 나나이어, 만주어처럼 사라져 가는 언어의 모음 체계를 현장에서 녹음해 "
     "음향적으로 분석했다. 한국어에서 본 원리가 다른 언어에서도 작동하는지를 확인하는 자리다.",
     "Acoustic fieldwork on the vowel systems of endangered languages — Buriat, Ewen, "
     "Nanai, Manchu — testing whether principles found in Korean hold elsewhere.",
     ["ewen", "nanai", "manchu", "ocpmemory", "tongueroot"],
     [4, 5, 6], ["영어음성학", "영어학개론"]),
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
    """글 하나에서 문단·댓글칸·스크립트를 꺼낸다.

    두 판을 모두 읽는다. 그래서 이 스크립트가 **자기가 찍어낸 결과를 다시 읽어**
    같은 결과를 낼 수 있다(멱등). 개편 전 원본이 없어도 다시 찍을 수 있다.

      개편 전: <div class="content">   하드랩된 평문
      개편 후: <div class="essay-body"> <p> 문단들
    """
    src = open(path, encoding="utf-8").read()

    a = src.find('<div class="content">')
    if a >= 0:
        b = src.find("</div>", a)
        paras = paragraphs(src[a + len('<div class="content">'):b])
    else:
        blk = div_block(src, '<div class="essay-body">')
        if not blk:
            raise SystemExit(f"{path}: 본문을 찾지 못했습니다")
        paras = [m.group(1).strip()
                 for m in re.finditer(r"<p>(.*?)</p>", blk, re.S)]

    comments = div_block(src, '<div class="comments-section">')
    # 구조화 데이터(ld+json)는 매번 새로 만드므로 가져오지 않는다 — 가져오면 겹친다
    scripts = [s for s in re.findall(r"<script\b.*?</script>", src, re.S)
               if "application/ld+json" not in s]
    return paras, comments, scripts


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
        f'<meta property="og:image" content="{SITE}/images/og-image.jpg">',
        '<meta property="og:image:width" content="1200">',
        '<meta property="og:image:height" content="630">',
        f'<meta property="og:image:alt" content="{F["name_ko"]} · {F["name_en"]}">',
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
    items = ([("about.html", "프로필"), ("research.html", "연구분야"),
              ("teaching.html", "강의"), ("blog.html", "에세이")] if lang == "ko" else
             [("about.html", "Profile"), ("research.html", "Research"),
              ("teaching.html", "Teaching"), ("writing.html", "Essays")])
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
    pubs = "".join(pub_li(p) for p in pubs_by_kind("article")[:4])
    ld = ('{"@context":"https://schema.org","@type":"WebSite","name":"강희조 | Hijo Kang",'
          '"url":"%s","inLanguage":["ko","en"],"about":["Phonetics","Phonology","Morphology"],'
          '"author":%s}' % (SITE, person_ld()))
    body = f"""{nav("index.html")}
<main>
  <section class="hero">
    <div class="wrap hero-in">
      <div class="hero-text">
        <p class="hero-en">{F["key_kicker"]}</p>
        <h1 class="hero-ko">{F["key_ko"]}</h1>
        <p class="hero-tag">{F["key_sub_ko"]}</p>
        <p class="hero-role">{F["name_ko"]} · {F["dept_ko"]} {F["rank_ko"]}</p>
        <p class="hero-cta"><a class="btn" href="research.html">연구 보기</a>
          <a class="btn btn-ghost" href="blog.html">에세이 읽기</a></p>
      </div>
      <div class="hero-figure">{hero_svg()}</div>
    </div>
  </section>

  <section class="band">
    <div class="wrap">
      {h2("이 달의 에세이", "mark", "sec-title")}
      <a class="feature" href="post{feat[0]}.html">
        <p class="feature-kicker">{" · ".join(TOPICS[t][0] for t in feat[5])}</p>
        <h3 class="feature-title">{feat[1]}</h3>
        <p class="feature-sum">{feat[6]}</p>
        <p class="feature-meta">{feat[0]}번째 글 · {feat[3].split("-")[0]}년 {int(feat[3].split("-")[1])}월</p>
      </a>
    </div>
  </section>

  <section class="band">
    <div class="wrap">
      {h2("연구 분야", "wave", "sec-title")}
      <div class="fields">{fields}</div>
    </div>
  </section>

  <section class="band">
    <div class="wrap">
      {h2("최근 에세이", "list", "sec-title")}
      <ul class="rows">{latest_html}</ul>
      <p class="more"><a href="blog.html">에세이 전체 보기 →</a></p>
    </div>
  </section>

  <section class="band">
    <div class="wrap">
      {h2("대표 논문", "doc", "sec-title")}
      <ul class="pubs">{pubs}</ul>
      <p class="more"><a href="research.html">연구 전체 보기 →</a></p>
    </div>
  </section>

  <section class="band">
    <div class="wrap">
      {h2("강의", "book", "sec-title")}
      <p class="band-lede">학부에서 영어음성학, 영어음운론, 영어학개론, 영어학개관을,
        대학원에서 영어음운론과 영어음운론심화를 맡고 있습니다.</p>
      <p class="more"><a href="teaching.html">강의 전체 보기 →</a></p>
    </div>
  </section>

  <section class="band">
    <div class="wrap about-strip">
      {h2("프로필", "person", "sec-title")}
      <p class="band-lede">영어와 관련된 언어학개론, 음성학, 음운론을 가르치고 있으며,
        영어 및 한국어를 포함한 다양한 언어를 음운론적 관점에서 분석하는 연구를 수행하고
        있습니다.</p>
      <p class="more"><a href="about.html">프로필 자세히 보기 →</a></p>
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
  {doc_head('<p class="crumb"><a href="index.html">홈</a> <span>›</span> 프로필</p>',
            PAGE_KEY["about"], "")}

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

  {h2("경력", "career")}
  <ul class="cvlist">{career}</ul>

  {h2("학력", "cap")}
  <ul class="cvlist">{edu}</ul>

  {h2("연락처", "mail")}
  <table class="kv">
    <tr><th>이메일</th><td><a href="mailto:{F["email_univ"]}">{F["email_univ"]}</a></td></tr>
    <tr><th>연구실</th><td>{F["office"]}</td></tr>
    <tr><th>전화</th><td>{F["tel"]}</td></tr>
    <tr><th>학과 소개</th><td><a href="{F["jnu_url"]}" rel="noopener">전남대학교 영어영문학과
      교수 소개</a></td></tr>
  </table>

  <div class="note">
    <p>연구 분야와 논문 목록은 <a href="research.html">연구</a>에, 담당 과목은
      <a href="teaching.html">강의</a>에 정리해 두었습니다.</p>
  </div>
</main>
{foot()}"""
    return page(f'프로필 | {F["name_ko"]}',
                f'{F["name_ko"]}({F["name_en"]}) — {F["dept_ko"]} {F["rank_ko"]}. '
                'Stony Brook University 언어학 박사. 음성학·음운론·형태론.',
                "/about.html", body, alt=("/about.html", "/en/about.html"),
                extra=jsonld(ld) + jsonld(crumbs_ld([("홈", "/"), ("프로필", "/about.html")])),
                og_type="profile")


def build_research():
    LANG = "ko"
    fields = "".join(f"""
    <article class="field-long">
      <p class="field-en">{en}</p>
      <h3 class="field-ko">{ko}</h3>
      <p>{d}</p>
    </article>""" for ko, en, d, _ in FIELDS)
    threads = ""
    for i, (ko, en, desc, _, pi, po, cs) in enumerate(THREADS, 1):
        pl = "".join(pub_li(PUB_BY_ID[k], LANG) for k in pi)
        el = "".join(f'<li><a href="post{n}.html">{dict((p[0], p[1]) for p in POSTS)[n]}</a></li>'
                     for n in po)
        cl = "".join(f"<li>{c}</li>" for c in cs)
        threads += f"""
    <section class="thread">
      <p class="thread-no">{i:02d}</p>
      <h3 class="thread-title">{ko}</h3>
      <p class="thread-en">{en}</p>
      <p class="thread-desc">{desc}</p>
      <div class="thread-grid">
        <div><h4 class="thread-h">논문</h4><ul class="pubs tight">{pl}</ul></div>
        <div><h4 class="thread-h">이어지는 글</h4><ul class="linklist">{el}</ul></div>
        <div><h4 class="thread-h">관련 강의</h4><ul class="linklist plain">{cl}</ul></div>
      </div>
    </section>"""
    arts = pubs_by_kind("article")
    body = f"""{nav("research.html")}
<main class="wrap doc">
  {doc_head('<p class="crumb"><a href="index.html">홈</a> <span>›</span> 연구분야</p>',
            PAGE_KEY["research"],
            "음성학, 음운론, 형태론. 영어와 한국어를 함께 놓고 말소리의 실현과 "
            "변화를 관찰합니다.", art_research())}

  {h2("연구 분야", "wave")}
  <div class="fields-long">{fields}</div>
  <p class="doc-note">아래는 논문과 글, 강의가 어떻게 이어지는지를 주제별로 묶은
    것입니다.</p>
  {threads}

  {h2("학술지 논문", "doc", extra=f'<span class="count">{len(arts)}편</span>')}
  {pubs_list(arts, LANG)}

  {h2("학위논문", "book")}
  {pubs_list(pubs_by_kind("dissertation"), LANG)}

  {h2("학술대회 발표", "talk")}
  {pubs_list(pubs_by_kind("conference"), LANG)}

  <p class="doc-note">서지는 <a href="{F["jnu_url"]}" rel="noopener">학과 교수 소개
    페이지</a>와 Crossref·OpenAlex 기록을 대조해 정리했습니다. DOI 가 있는 항목은
    제목을 눌러 원문 정보로 갈 수 있습니다.</p>
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
        secs += (h2(level, "book") + f'<ul class="courses">{rows}</ul>')
    body = f"""{nav("teaching.html")}
<main class="wrap doc">
  {doc_head('<p class="crumb"><a href="index.html">홈</a> <span>›</span> 강의</p>',
            PAGE_KEY["teaching"],
            "영어와 관련된 언어학개론, 음성학, 음운론을 가르치고 있습니다.",
            art_teaching())}
  {secs}
  {h2("수강생에게", "mail")}
  <div class="note">
    <p>강의계획서와 과제 안내는 학교 LMS를 통해 공지합니다. 수업 관련 문의는
      <a href="mailto:{F["email_univ"]}">{F["email_univ"]}</a>로 편하게 연락 주세요.
      연구실은 {F["office"]}입니다.</p>
    <p>수업에서 다루는 개념 가운데 몇 가지는 <a href="blog.html">에세이</a>에서 더 편한 말로
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
          '"name":"에세이","url":"%s/blog.html","inLanguage":"ko","author":%s,'
          '"hasPart":[%s]}' % (SITE, person_ld(), ",".join(
              '{"@type":"BlogPosting","headline":"%s","url":"%s/post%d.html",'
              '"datePublished":"%s-%s"}' % (p[1], SITE, p[0], p[3], p[4]) for p in POSTS)))
    body = f"""{nav("blog.html")}
<main class="wrap doc">
  {doc_head('<p class="crumb"><a href="index.html">홈</a> <span>›</span> 에세이</p>',
            PAGE_KEY["writing"],
            "언어의 변화와 그 규칙에 관한 글. 한 달에 두 편 정도 적어 둡니다.",
            art_writing())}
  <ul class="chips chips-link">{chips}</ul>

  {h2("전체", "list", extra=f'<span class="count">{len(POSTS)}편</span>')}
  <ul class="rows">{rows}</ul>

  {h2("주제로 찾기", "tag")}
  <div class="groups">{groups}</div>
</main>
{foot()}"""
    return page(f'에세이 | {F["name_ko"]}',
                '언어의 변화, 말소리, 외국어 습득에 관한 글 13편. 전남대 영어영문학과 '
                f'{F["name_ko"]} 교수가 씁니다.',
                "/blog.html", body, alt=("/blog.html", "/en/writing.html"),
                extra=jsonld(ld) + jsonld(crumbs_ld([("홈", "/"), ("에세이", "/blog.html")])))


def build_post(meta, src_dir):
    n, t_ko, t_en, ym, day, tp, summ, summ_en = meta
    para_list, comments, scripts = read_source(os.path.join(src_dir, f"post{n}.html"))
    paras = "\n".join(f"<p>{p}</p>" for p in para_list)
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
          '"image":"%s/images/og-image.jpg",'
          '"about":[%s],"keywords":"%s","author":%s,'
          '"publisher":{"@type":"Person","name":"Hijo Kang","url":"%s/about.html"},'
          '"isPartOf":{"@type":"Blog","name":"강희조의 글","url":"%s/blog.html"}}'
          % (t_ko, desc, SITE, n, SITE, n, date_iso, date_iso, SITE,
             ",".join('{"@type":"Thing","name":"%s"}' % TOPICS[t][1] for t in tp),
             ", ".join(TOPICS[t][0] for t in tp), person_ld(), SITE, SITE))
    crumb = crumbs_ld([("홈", "/"), ("에세이", "/blog.html"), (t_ko, f"/post{n}.html")])

    body = f"""{nav("blog.html")}
<main class="wrap">
  <article class="essay">
    <p class="crumb"><a href="index.html">홈</a> <span>›</span>
      <a href="blog.html">에세이</a> <span>›</span> {n}번째 글</p>
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
      <img class="author-img" src="images/profile-square.jpg" alt="{F["name_ko"]}"
        width="72" height="72" loading="lazy">
      <div class="author-body">
        <p class="author-name">글 · {F["name_ko"]} <span class="p-en">Hijo Kang</span></p>
        <p class="author-role">{F["dept_ko"]} {F["rank_ko"]}<br>
          Ph.D. in Linguistics, Stony Brook University</p>
        <p class="author-fields">음성학 · 음운론 · 형태론</p>
        <p class="author-more"><a href="about.html">프로필 보기 →</a>
          <a href="research.html">연구 보기 →</a></p>
      </div>
    </aside>

    <nav class="pager">{pager}</nav>

    <section class="related">
      {h2("함께 읽기", "list", "rel-title")}
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
    LANG = "en"
    fields = "".join(f"""
      <article class="field">
        <p class="field-en">{ko}</p>
        <h3 class="field-ko">{en}</h3>
        <p class="field-desc">{d_en}</p>
      </article>""" for ko, en, _, d_en in FIELDS)
    pubs = "".join(pub_li(p, LANG) for p in pubs_by_kind("article")[:5])
    body = f"""{nav("index.html", "en")}
<main>
  <section class="hero">
    <div class="wrap hero-in">
      <div class="hero-text">
        <p class="hero-en">{F["key_kicker"]}</p>
        <h1 class="hero-ko">{F["key_en"]}</h1>
        <p class="hero-tag">{F["key_sub_en"]}</p>
        <p class="hero-role">{F["name_en"]} · {F["rank_en"]},
          Chonnam National University</p>
        <p class="hero-cta"><a class="btn" href="research.html">Research</a>
          <a class="btn btn-ghost" href="writing.html">Essays</a></p>
      </div>
      <div class="hero-figure">{hero_svg()}</div>
    </div>
  </section>
  <section class="band"><div class="wrap">
    {h2("Research Areas", "wave", "sec-title")}
    <div class="fields">{fields}</div>
  </div></section>
  <section class="band"><div class="wrap">
    {h2("Publications", "doc", "sec-title")}
    <ul class="pubs">{pubs}</ul>
    <p class="more"><a href="research.html">See research →</a></p>
  </div></section>
  <section class="band"><div class="wrap">
    {h2("Essays", "list", "sec-title")}
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
  {doc_head('<p class="crumb"><a href="index.html">Home</a> <span>›</span> Profile</p>',
            PAGE_KEY["about"], "", None, "en")}
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
  {h2("Appointments", "career")}
  <ul class="cvlist">{career}</ul>
  {h2("Education", "cap")}
  <ul class="cvlist">{edu}</ul>
  {h2("Contact", "mail")}
  <table class="kv">
    <tr><th>Email</th><td><a href="mailto:{F["email_univ"]}">{F["email_univ"]}</a></td></tr>
    <tr><th>Office</th><td>{F["office_en"]}</td></tr>
    <tr><th>Phone</th><td>+82-62-530-3165</td></tr>
    <tr><th>Department</th><td><a href="{F["jnu_url"]}" rel="noopener">Faculty profile</a></td></tr>
  </table>
</main>
{foot("en")}"""
    return page(f'Profile | {F["name_en"]}',
                f'{F["name_en"]} — {F["rank_en"]} at Chonnam National University. '
                'Ph.D. in Linguistics, Stony Brook University.',
                "/en/about.html", body, lang="en", alt=("/about.html", "/en/about.html"),
                extra=jsonld('{"@context":"https://schema.org","@type":"ProfilePage",'
                             '"mainEntity":%s}' % person_ld()), og_type="profile")


def build_en_research():
    LANG = "en"
    fields = "".join(f"""
    <article class="field-long"><p class="field-en">{ko}</p>
      <h3 class="field-ko">{en}</h3><p>{d_en}</p></article>""" for ko, en, _, d_en in FIELDS)
    threads = ""
    for i, (ko, en, _, desc_en, pi, po, _) in enumerate(THREADS, 1):
        pl = "".join(pub_li(PUB_BY_ID[k], LANG) for k in pi)
        el = "".join(f'<li><a href="../post{n}.html" hreflang="ko">'
                     f'{dict((p[0], p[2]) for p in POSTS)[n]}</a>'
                     f'<span class="g-date">in Korean</span></li>' for n in po)
        threads += f"""
    <section class="thread"><p class="thread-no">{i:02d}</p>
      <h3 class="thread-title">{en}</h3><p class="thread-en">{ko}</p>
      <p class="thread-desc">{desc_en}</p>
      <div class="thread-grid">
        <div><h4 class="thread-h">Papers</h4><ul class="pubs tight">{pl}</ul></div>
        <div><h4 class="thread-h">Related essays</h4><ul class="linklist">{el}</ul></div>
      </div></section>"""
    arts = pubs_by_kind("article")
    body = f"""{nav("research.html", "en")}
<main class="wrap doc">
  {doc_head('<p class="crumb"><a href="index.html">Home</a> <span>›</span> Research</p>',
            PAGE_KEY["research"],
            "Phonetics, phonology, and morphology — observing how speech sounds "
            "are realised and how they change, with English and Korean side by side.",
            art_research(), "en")}
  {h2("Research Areas", "wave")}
  <div class="fields-long">{fields}</div>
  <p class="doc-note">Below, papers, essays and courses are grouped by topic.</p>
  {threads}
  {h2("Journal Articles", "doc", extra=f'<span class="count">{len(arts)}</span>')}
  {pubs_list(arts, LANG)}
  {h2("Dissertation", "book")}
  {pubs_list(pubs_by_kind("dissertation"), LANG)}
  {h2("Conference Presentations", "talk")}
  {pubs_list(pubs_by_kind("conference"), LANG)}
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
        secs += (h2(lv, "book") + f'<ul class="courses">{rows}</ul>')
    body = f"""{nav("teaching.html", "en")}
<main class="wrap doc">
  {doc_head('<p class="crumb"><a href="index.html">Home</a> <span>›</span> Teaching</p>',
            PAGE_KEY["teaching"],
            "Introduction to English linguistics, phonetics, and phonology.",
            art_teaching(), "en")}
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
  {doc_head('<p class="crumb"><a href="index.html">Home</a> <span>›</span> Essays</p>',
            PAGE_KEY["writing"],
            "Essays on language change, speech sounds, and second-language "
            "learning — roughly two a month.", art_writing(), "en")}
  <div class="note"><p><strong>The essays are written in Korean.</strong> Titles and
    summaries below are in English; following a link opens the Korean text.</p></div>
  {h2("All essays", "list", extra=f'<span class="count">{len(POSTS)}</span>')}
  <ul class="rows">{rows}</ul>
</main>
{foot("en")}"""
    return page(f'Essays | {F["name_en"]}',
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
    <li><a href="/blog.html">에세이 목록</a></li>
    <li><a href="/research.html">연구</a></li>
    <li><a href="/about.html">프로필</a></li>
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
