#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
paper_dir="$repo_root/paper/zh"
paper_python="$repo_root/.venv/bin/python"

if [[ ! -x "$paper_python" ]]; then
  printf 'Missing project Python environment: %s\n' "$paper_python" >&2
  exit 1
fi
"$paper_python" "$repo_root/scripts/make_chinese_paper_figure.py"

cd "$paper_dir"
xelatex -interaction=nonstopmode -halt-on-error main_zh.tex
bibtex main_zh
xelatex -interaction=nonstopmode -halt-on-error main_zh.tex
xelatex -interaction=nonstopmode -halt-on-error main_zh.tex
mv -f main_zh.pdf paper_zh.pdf

printf 'Built %s\n' "$paper_dir/paper_zh.pdf"
