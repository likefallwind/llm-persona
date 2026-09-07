"""Prevent empirical table rows from disappearing in the Chinese reading PDF."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from build_personality_draft_v3 import chinese_tex


def test_table_keeps_header_data_alignment_and_following_paragraph():
    rendered = chinese_tex('# 稿件\n\n| 模型 | 事件 |\n|---|---:|\n| M2.7 | 99.6% |\n'
                           '| M3 | 83.2% |\n\n#### 限制\n结尾。\n')
    assert r'\begin{tabular}{lr}' in rendered
    assert r'M2.7 & 99.6\%' in rendered
    assert r'M3 & 83.2\%' in rendered
    assert rendered.index(r'\end{tabular}') < rendered.index(r'\subsubsection{限制}')
    assert '结尾。' in rendered


def test_table_at_end_is_not_dropped():
    rendered = chinese_tex('# 稿件\n| A | B |\n|---|---|\n| x | y |')
    assert r'x & y \\' in rendered
    assert rendered.count(r'\begin{tabular}') == rendered.count(r'\end{tabular}') == 1


@pytest.mark.parametrize('table', [
    '| A | B |\n|---|---|\n| lost |',
    '| A | B |\n|not alignment|---|\n| x | y |',
    '| A | B |\n|---|---|',
])
def test_malformed_tables_fail_instead_of_silently_changing_evidence(table):
    with pytest.raises(ValueError):
        chinese_tex('# 稿件\n' + table)
