#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [[ -z "${1:-}" ]]; then
  echo "사용법: _build/release.sh '에세이 제목'" >&2
  exit 2
fi

python3 _build/build.py . .
git diff --check
git add _build/posts.json content/published post*.html index.html blog.html \
  research.html teaching.html about.html en sitemap.xml robots.txt feed.xml 404.html \
  _build/build.py _build/post_tool.py _build/release.sh README.md _config.yml
git diff --cached --quiet && { echo "발행할 변경이 없습니다."; exit 1; }
git -c user.name="Hijo Kang" -c user.email="hijokang@jnu.ac.kr" \
  commit -m "에세이 발행: $1"
git push origin main
echo "발행 완료: GitHub Pages 배포를 확인하세요."
