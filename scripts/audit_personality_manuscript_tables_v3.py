#!/usr/bin/env python3
"""Compare bilingual manuscript tables directly with complete analysis CSVs.

This editorial check never computes a new statistical estimate. It verifies
row order, retained values, rounding precision and bilingual numerical parity.
"""
import datetime
import hashlib
import json
from pathlib import Path
import re

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / 'paper/educational_personality_v3'
BASE = ROOT / 'artifacts/educational_personality_v2/prospective_formal'
MODELS = ['MiniMax-M2.7', 'MiniMax-M3', 'deepseek-v4-pro', 'doubao-seed-2.0-lite', 'glm-5.3']
EVENTS = ['answer_reveal', 'reasoning_elicitation', 'affect_acknowledgement']


def tex_rows(source, label):
    matches = [block for block in re.findall(r'\\begin\{table\}.*?\\end\{table\}', source, re.S)
               if r'\label{' + label + '}' in block]
    if len(matches) != 1:
        raise ValueError('Expected one table: ' + label)
    block = matches[0].split(r'\midrule', 1)[1].split(r'\bottomrule', 1)[0]
    return [[cell.strip() for cell in row.strip().split('&')]
            for row in block.split('\\\\') if '&' in row]


def md_rows(source, start):
    matches = [block for block in re.findall(r'(?:^\|[^\n]*(?:\n|$))+', source, re.M)
               if block.startswith(start)]
    if len(matches) != 1:
        raise ValueError('Expected one Chinese table: ' + start)
    return [[cell.strip() for cell in row.strip().strip('|').split('|')]
            for row in matches[0].strip().splitlines()[2:]]


def cells(rows, skip):
    return np.array([[float(cell.replace('%', '').strip()) for cell in row[skip:]]
                     for row in rows])


def main():
    selection = json.loads((BASE / 'confirmation/measurement_selection.json').read_text())
    measurement = json.loads((ROOT / selection['diagnostics'] / 'summary.json').read_text())
    if measurement['valid_judge_requests'] != 12120 or measurement['invalid_or_missing']:
        raise ValueError('Complete confirmation measurement is required')
    result_path = PAPER / 'sections/results.tex'
    detail_path = PAPER / 'sections/confirmation_details.tex'
    zh_path = PAPER / 'manuscript_zh.md'
    result, detail, zh = (p.read_text() for p in [result_path, detail_path, zh_path])
    paths = [result_path, detail_path, zh_path, BASE / 'confirmation/measurement_selection.json']
    def read(relative):
        path = BASE / relative
        paths.append(path)
        return pd.read_csv(path)
    defaults = read('confirmation_analysis/default_profiles.csv').set_index(['model', 'event'])
    losses = read('confirmation_analysis/prediction_brier.csv').set_index(['baseline', 'event'])
    prompts = read('confirmation_descriptive/matched_prompt_profiles.csv').set_index(['model', 'event', 'arm'])
    primary = read('confirmation_analysis/primary_prediction_comparisons.csv').set_index(['event', 'comparison'])
    checks = []
    def check(name, english, chinese, expected, tolerance):
        expected = np.array(expected)
        for language, values in [('en', english), ('zh', chinese)]:
            if values.shape != expected.shape:
                raise ValueError(f'{name}/{language}: wrong table shape')
            if np.any(np.abs(values - expected) > tolerance + 1e-12):
                raise ValueError(f'{name}/{language}: mismatched number')
            checks.append({'table': name, 'language': language, 'cells': values.size,
                           'max_abs_rounding_difference': float(np.max(np.abs(values - expected))),
                           'absolute_tolerance': tolerance})
        if not np.array_equal(english, chinese):
            raise ValueError(name + ': bilingual values differ')
    check('default_rates', cells(tex_rows(result, 'tab:default-rates'), 1),
          cells(md_rows(zh, '| 部署 | 答案揭示 |'), 1),
          [[100 * defaults.loc[(m, e), 'mean'] for e in EVENTS] for m in MODELS], .05)
    predictors = ['context', 'default_profile', 'domain_profile', 'conditional_profile', 'training_style_profile']
    check('absolute_losses', cells(tex_rows(detail, 'tab:absolute-losses'), 1),
          cells(md_rows(zh, '| 预测器 |'), 1),
          [[losses.loc[(b, e), 'brier'] for e in EVENTS] for b in predictors], .0000005)
    arms = ['canonical', 'neutral_a', 'neutral_b', 'ask', 'explain']
    check('matched_prompt_rates', cells(tex_rows(detail, 'tab:matched-prompts'), 2),
          cells(md_rows(zh, '| 部署／事件 |'), 1),
          [[100 * prompts.loc[(m, e, a), 'present'] for a in arms] for m in MODELS for e in EVENTS], .05)
    secondary = ['worked_explanation', 'learner_choice', 'epistemic_qualification',
                 'information_request', 'unsupported_ability_claim']
    check('secondary_rates', cells(tex_rows(detail, 'tab:secondary-events'), 1),
          cells(md_rows(zh, '| 部署 | 解释 |'), 1),
          [[100 * defaults.loc[(m, e), 'mean'] for e in secondary] for m in MODELS], .05)
    content = read('content_sensitivity/analysis/subset_comparisons.csv').set_index(['subset', 'event', 'comparison'])
    subsets = ['all_canonical', 'mathematics', 'without_unanimous_error_slots',
               'without_any_error_slots', 'without_error_or_uncertain_slots']
    en_content = tex_rows(detail, 'tab:content-subsets')
    zh_content = md_rows(zh, '| 子集 | 来源／回答 |')
    check('content_subset_gains', cells(en_content, 2), cells(zh_content, 2),
          [[content.loc[(subset, event, comparison), 'mean_difference']
            for comparison in ['default_vs_context', 'student_state_vs_domain'] for event in EVENTS]
           for subset in subsets], .000005)
    for i, subset in enumerate(subsets):
        row = content.loc[(subset, EVENTS[0], 'default_vs_context')]
        expected_count = f'{int(row.sources)}/{int(row.responses)}'
        if en_content[i][1] != expected_count or zh_content[i][1] != expected_count:
            raise ValueError('Content retained-source/response count differs: ' + subset)
    en_rows = tex_rows(detail, 'tab:primary-tests')
    zh_rows = md_rows(zh, '| 行为与增量 |')
    if len(en_rows) != 6 or len(zh_rows) != 6:
        raise ValueError('All six primary comparisons must be retained')
    def primary_values(row, skip):
        estimate, interval, p = row[skip:]
        p = p.strip('$')
        scientific = re.fullmatch(r'([\d.]+)\\times10\^\{(-?\d+)\}', p)
        p = float(scientific[1]) * 10 ** int(scientific[2]) if scientific else float(p)
        lo, hi = [float(x.strip()) for x in interval.strip('[]').split(',')]
        return [float(estimate), lo, hi, p]
    for i, (event, comparison) in enumerate((e, c) for e in EVENTS for c in
                                            ['default_vs_context', 'student_state_vs_domain']):
        row = primary.loc[(event, comparison)]
        expected = row[['mean_difference', 'bootstrap_95_low', 'bootstrap_95_high', 'p_holm_six']].to_numpy(float)
        en, cn = np.array(primary_values(en_rows[i], 2)), np.array(primary_values(zh_rows[i], 1))
        for language, observed in [('en', en), ('zh', cn)]:
            if not np.allclose(observed[:3], expected[:3], atol=.0000005, rtol=0):
                raise ValueError('Primary effect or interval differs: ' + event)
            # Ordinary p-values have six decimal places; tiny p-values use
            # three significant digits in scientific notation.
            p_tolerance = .0000005 if expected[3] >= .00001 else expected[3] * .002
            if not np.isclose(observed[3], expected[3], atol=p_tolerance, rtol=0):
                raise ValueError('Adjusted p-value differs: ' + event)
        if not np.allclose(en, cn, atol=0, rtol=1e-14):
            raise ValueError('Primary bilingual table differs')
        checks.append({'table': 'primary_tests', 'event': event, 'comparison': comparison,
                       'languages': ['en', 'zh'], 'estimates': en.tolist(), 'status': 'verified'})
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    out = ROOT / 'artifacts/educational_personality_v2/manuscript_structure_review'
    out.mkdir(exist_ok=True)
    receipt = {'checked_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
               'status': 'six empirical tables in both languages agree with complete analysis values',
               'checks': checks, 'new_estimates': 0,
               'limitation': 'This checks table values and fixed row ordering, not every prose claim or semantic validity.',
               'input_sha256': {str(p.relative_to(ROOT)): sha(p) for p in [*paths, Path(__file__).resolve()]}}
    (out / 'bilingual_table_audit_20260907.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({'status': receipt['status'], 'checks': len(checks)}))


if __name__ == '__main__':
    main()
