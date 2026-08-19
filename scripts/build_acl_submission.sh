#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STYLE_DIR="${ACL_STYLE_DIR:?Set ACL_STYLE_DIR to a checkout of acl-org/acl-style-files}"

EXPECTED_ACL_STYLE="19dfeddc2c0e448f3926a0bef048a9db3f3611b46265b760caabd7ada4f361de"
EXPECTED_ACL_BST="6fbb306202290f4b68e74ac1460a8b27398500cb6dfeb4492e74c457eae7cd1e"

check_hash() {
  local expected="$1"
  local path="$2"
  local actual
  actual="$(sha256sum "$path" | awk '{print $1}')"
  if [[ "$actual" != "$expected" ]]; then
    echo "Hash mismatch for $path" >&2
    echo "expected: $expected" >&2
    echo "actual:   $actual" >&2
    exit 1
  fi
}

check_hash "$EXPECTED_ACL_STYLE" "$STYLE_DIR/acl.sty"
check_hash "$EXPECTED_ACL_BST" "$STYLE_DIR/acl_natbib.bst"

BUILD_DIR="$(mktemp -d "${TMPDIR:-/tmp}/llm-persona-acl.XXXXXX")"
trap 'rm -rf "$BUILD_DIR"' EXIT

cp "$REPO_ROOT/paper/submission/main.tex" "$BUILD_DIR/main.tex"
cp "$REPO_ROOT/paper/references.bib" "$BUILD_DIR/references.bib"
cp "$REPO_ROOT/paper/figures/main_findings.pdf" "$BUILD_DIR/main_findings.pdf"
cp "$REPO_ROOT/paper/figures/semantic_findings.pdf" "$BUILD_DIR/semantic_findings.pdf"
cp "$STYLE_DIR/acl.sty" "$BUILD_DIR/acl.sty"
cp "$STYLE_DIR/acl_natbib.bst" "$BUILD_DIR/acl_natbib.bst"

export SOURCE_DATE_EPOCH="1787068800"
export FORCE_SOURCE_DATE=1

(
  cd "$BUILD_DIR"
  pdflatex -halt-on-error -interaction=nonstopmode main.tex
  bibtex main
  pdflatex -halt-on-error -interaction=nonstopmode main.tex
  pdflatex -halt-on-error -interaction=nonstopmode main.tex

  if grep -Eq "There were undefined (citations|references)|Citation.*undefined" main.log; then
    echo "Unresolved citations or references remain after the final LaTeX pass" >&2
    exit 1
  fi
)

cp "$BUILD_DIR/main.pdf" "$REPO_ROOT/paper/submission/submission.pdf"
echo "Built $REPO_ROOT/paper/submission/submission.pdf"
