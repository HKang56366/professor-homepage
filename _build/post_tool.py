#!/usr/bin/env python3
"""Timely AI용 에세이 준비·발행 도구.

준비(변경 없음): python3 _build/post_tool.py prepare content/drafts/slug.md
발행(사이트 생성): python3 _build/post_tool.py publish content/drafts/slug.md

publish는 파일만 생성하며 git push는 하지 않는다. 사용자가 발행을 명시적으로
승인한 뒤에만 별도의 release.sh를 실행한다.
"""
from __future__ import annotations

import html
import importlib.util
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILD_PATH = ROOT / "_build" / "build.py"
POSTS_PATH = ROOT / "_build" / "posts.json"
TOPIC_KEYS = {
    "phonetics", "phonology", "morphology", "acquisition", "change",
    "society", "universals", "korean", "english",
}
REQUIRED = {"title", "title_en", "date", "topics", "summary", "summary_en"}


def load_build():
    spec = importlib.util.spec_from_file_location("professor_build", BUILD_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def parse_frontmatter(path: Path):
    raw = path.read_text(encoding="utf-8")
    if not raw.startswith("---\n") or "\n---\n" not in raw[4:]:
        raise SystemExit("원고는 --- 로 감싼 front matter로 시작해야 합니다.")
    head, body = raw[4:].split("\n---\n", 1)
    meta = {}
    for line in head.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            raise SystemExit(f"front matter 형식 오류: {line}")
        key, value = line.split(":", 1)
        meta[key.strip()] = value.strip().strip('"').strip("'")
    missing = REQUIRED - meta.keys()
    if missing:
        raise SystemExit("필수 항목 누락: " + ", ".join(sorted(missing)))
    if not re.fullmatch(r"20\d\d-\d\d-\d\d", meta["date"]):
        raise SystemExit("date는 YYYY-MM-DD 형식이어야 합니다.")
    topics = [x.strip() for x in meta["topics"].strip("[]").split(",") if x.strip()]
    bad = set(topics) - TOPIC_KEYS
    if bad:
        raise SystemExit("허용되지 않은 topics: " + ", ".join(sorted(bad)))
    if not topics:
        raise SystemExit("topics를 하나 이상 적어야 합니다.")
    meta["topics"] = topics
    paragraphs = [re.sub(r"\s*\n\s*", " ", p).strip()
                  for p in re.split(r"\n\s*\n", body.strip()) if p.strip()]
    if not paragraphs:
        raise SystemExit("본문이 비어 있습니다.")
    return meta, paragraphs


def inline(text: str) -> str:
    text = html.escape(text, quote=False)
    text = re.sub(r"\[([^]]+)\]\((https?://[^ )]+)\)",
                  r'<a href="\2">\1</a>', text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    return text


def current_posts(build):
    return [list(p[:5]) + [list(p[5])] + list(p[6:]) for p in build.POSTS]


def validate(meta, paragraphs, posts):
    if any(p[1] == meta["title"] for p in posts):
        raise SystemExit("같은 제목의 글이 이미 있습니다.")
    number = max(p[0] for p in posts) + 1
    print(f"검증 완료: {number}번째 글 · {meta['title']}")
    print(f"발행일: {meta['date']} · 주제: {', '.join(meta['topics'])}")
    print(f"본문: {len(paragraphs)}문단 · {sum(len(p.split()) for p in paragraphs)}어절")
    return number


def publish(path: Path, meta, paragraphs, posts, build):
    number = max(p[0] for p in posts) + 1
    year_month, day = meta["date"][:7], meta["date"][8:]
    posts.append([number, meta["title"], meta["title_en"], year_month, day,
                  meta["topics"], meta["summary"], meta["summary_en"]])
    POSTS_PATH.write_text(json.dumps(posts, ensure_ascii=False, indent=2) + "\n",
                          encoding="utf-8")
    body = "\n".join(f"    <p>{inline(p)}</p>" for p in paragraphs)
    source = ROOT / f"post{number}.html"
    source.write_text(f'<!doctype html>\n<div class="essay-body">\n{body}\n</div>\n',
                      encoding="utf-8")
    # JSON을 다시 읽은 build 모듈로 전체 파생물을 생성한다.
    build = load_build()
    build.BUILD_DATE = meta["date"]
    build.main(str(ROOT), str(ROOT))
    archive = ROOT / "content" / "published"
    archive.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, archive / path.name)
    print(f"발행 파일 준비 완료: post{number}.html")
    print("아직 GitHub에는 반영하지 않았습니다. 검토 후 _build/release.sh를 실행하세요.")


def main():
    if len(sys.argv) != 3 or sys.argv[1] not in {"prepare", "publish"}:
        raise SystemExit("사용법: post_tool.py prepare|publish content/drafts/<원고>.md")
    path = Path(sys.argv[2]).resolve()
    if not path.is_file():
        raise SystemExit(f"원고를 찾을 수 없습니다: {path}")
    meta, paragraphs = parse_frontmatter(path)
    build = load_build()
    posts = current_posts(build)
    validate(meta, paragraphs, posts)
    if sys.argv[1] == "publish":
        publish(path, meta, paragraphs, posts, build)
    else:
        print("준비 단계라 파일은 변경하지 않았습니다.")


if __name__ == "__main__":
    main()
