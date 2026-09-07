#!/usr/bin/env python3
"""Package the completed agent editorial review with live evidence/PDF checks.

This records an agent's explicit scientific and visual assessment; it is not an
independent review, a new statistical analysis, or a submission operation.
The original experiment controllers intentionally retain paper_complete=false.
"""
import datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

import pandas as pd

from recover_personality_content_validation_v3 import verify as verify_content_amendment

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / 'paper/educational_personality_v3'
BASE = ROOT / 'artifacts/educational_personality_v2/prospective_formal'
REVIEW = ROOT / 'artifacts/educational_personality_v2/manuscript_structure_review'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    verify_content_amendment()
    inspected = {}
    hash_checks = 0

    def report(path):
        nonlocal hash_checks
        value = json.loads(path.read_text())
        inspected[str(path.relative_to(ROOT))] = sha(path)
        for field in ['files', 'inputs', 'input_hashes', 'input_sha256', 'source_sha256', 'report_hashes', 'scripts']:
            mapping = value.get(field, {})
            if not isinstance(mapping, dict):
                continue
            for name, expected in mapping.items():
                if not isinstance(expected, str) or not re.fullmatch('[0-9a-f]{64}', expected):
                    continue
                target = ROOT / name
                if sha(target) != expected:
                    raise ValueError('Stale evidence/build hash: ' + name)
                hash_checks += 1
        return value

    for stage, expected in [('training', 3840), ('confirmation', 12120), ('content_sensitivity', 2584)]:
        choice = report(BASE / stage / 'measurement_selection.json')
        diagnostics = ROOT / choice['diagnostics']
        data = report(diagnostics / 'summary.json')
        count = data.get('valid_judge_requests', data.get('valid_requests'))
        assert count == expected and data['invalid_or_missing'] == 0, stage
        assert sha(diagnostics / 'coverage.csv') == choice['coverage_sha256'], stage
    primary = report(BASE / 'confirmation_analysis/summary.json')
    assert primary['prediction_sources'] == 32 and primary['primary_hypothesis_tests'] == 6
    robust = report(BASE / 'confirmation_robustness/summary.json')
    assert (robust['judge_panels'], robust['generator_deletion_panels'], robust['training_resamples']) == (8, 5, 200)
    content = report(BASE / 'content_sensitivity/analysis/summary.json')
    assert content['selected_responses'] == dict(all_canonical=1280, mathematics=320,
        without_unanimous_error_slots=1255, without_any_error_slots=1065, without_error_or_uncertain_slots=1065)
    assert content['diagnostic_anchor_rule_met'] and content['new_hypothesis_tests'] == 0
    budget = report(BASE / 'confirmation_budget_sensitivity/summary.json')
    assert budget['primary_effects'] == 6 and budget['assignments_per_primary_event'] == 4
    report(BASE / 'confirmation_reporting/summary.json')
    report(BASE / 'content_independent_checkpoint/checkpoint_equivalence_audit.json')
    report(BASE / 'complete_main_checkpoint/checkpoint_equivalence_audit.json')
    for rel in ['confirmation/run/pipeline_state.json', 'confirmation_reporting/run/pipeline_state.json',
                'content_sensitivity/pipeline_state.json']:
        assert report(BASE / rel)['status'] == 'complete'
    tables = report(REVIEW / 'bilingual_table_audit_20260907.json')
    assert len(tables['checks']) == 16
    for rel in ['build/build_provenance.json', 'build/acl/build_provenance.json']:
        report(PAPER / rel)

    en = (PAPER / 'sections/results.tex').read_text()
    en = re.sub(r'\\begin\{(table|figure)\}.*?\\end\{\1\}', '', en, flags=re.S)
    en = re.sub(r'\\(?:section|subsection|paragraph|label)\{[^}]*\}', '', en)
    paragraphs_en = [p.strip() for p in re.split(r'\n\s*\n', en) if p.strip()]
    zh = (PAPER / 'manuscript_zh.md').read_text()
    result_zh = zh.split('## 独立确认结果\n', 1)[1].split('## 讨论\n', 1)[0]
    paragraphs_zh = [p.strip() for p in re.split(r'\n\s*\n', result_zh)
                     if p.strip() and not p.startswith(('#', '|', '!'))]
    ids = [['E07', 'E12', 'E13'], ['Q01'], ['Q01', 'E14'], ['Q02'], ['Q03'], ['Q06'],
           ['Q04'], ['Q05'], ['Q06'], ['Q05', 'E10'], ['Q07'], ['Q07'], ['E13'], ['Q08'], ['Q08']]
    selectors = [
        'complete confirmation coverage and three primary event pairwise positive-agreement ranges; 4040 answers/12120 codes/32320 event rows',
        'default_profiles.csv: five models x three primary events, 256 answers/model; joint_action_counts.csv: MiniMax-M3/main/canonical/both=81',
        'repeated_default_profiles.csv/repeat_diagnostics.csv: canonical reasoning_elicitation, 128 pairs/model, source intervals; positive/negative agreement separate',
        'primary_prediction_comparisons.csv: comparison=default_vs_context, all three events; prediction_brier.csv: context/default_profile',
        'primary_prediction_comparisons.csv: comparison=student_state_vs_domain, all three events; prediction_brier.csv: domain_profile/conditional_profile',
        'student_state_profiles.csv: affect_acknowledgement, deepseek-v4-pro/doubao-seed-2.0-lite, four student states, 64 answers/cell',
        'prediction_brier.csv: training_style_profile/default_profile, all three events; descriptive only',
        'matched_prompt_profiles.csv: ask/explain, five models x three events; same16 sources/128 answers per model/arm',
        'matched_prompt_profiles.csv: explain/reasoning_elicitation and explain/answer_reveal; exact EXPLAIN instruction permits questions',
        'matched_prompt_profiles.csv: glm-5.3 neutral_b versus canonical; confirmation_neutral_bounds, 30 comparisons/16 sources/halfwidth .9414136203',
        'judge_gain_ranges.csv: default_vs_context/student_state_vs_domain, three events, eight panels; same observations',
        'generator_deletion_comparisons.csv: without glm-5.3/default revelation+elicitation, without MiniMax-M2.7/default acknowledgement; training_resampling_quantiles.csv all200 resamples',
        'confirmation_budget_sensitivity/primary_ranges.csv: six estimates and Holm values invariant across four assignments/event; other two coders agree',
        'content_sensitivity/analysis/subset_comparisons.csv: all5 subsets x all6 gains and intervals; retained32 sources except mathematics8, 1280/320/1255/1065/1065 answers',
        'content_sensitivity/analysis/anchor_diagnostics.csv: all4 reviewer/class rows6/6; response_flags.csv: 5 unanimous/49 either/0 uncertain, positive10/54; selected-target caveat',
    ]
    assert len(paragraphs_en) == len(paragraphs_zh) == len(ids) == 15
    claims = [{'section': 'results', 'paragraph': i+1, 'evidence_ids': eid,
               'row_selector_and_denominator': selector, 'english': a, 'chinese': b,
               'review': 'Both versions checked against the cited complete evidence; scope and unfavorable results retained.'}
              for i, (a, b, eid, selector) in enumerate(zip(paragraphs_en, paragraphs_zh, ids, selectors))]
    for name, heading, following in [('abstract', '摘要', '引言'), ('conclusion', '结论', '研究局限')]:
        claims.append({'section': name, 'english': (PAPER / f'sections/{name}.tex').read_text(),
                       'chinese': zh.split('## '+heading+'\n', 1)[1].split('## '+following+'\n', 1)[0],
                       'evidence_ids': ['E01', 'E03', 'E06', 'E07', 'E09', 'Q01', 'Q02', 'Q03', 'Q05', 'Q06', 'Q07', 'Q08', 'Q10'],
                       'review': 'Synthesis of the mapped results, not a new psychological, learning-gain, universal-pair or education-unique claim.'})
    figure_map = {'study_design': ['E06', 'E07', 'E09'], 'measurement_pilot': ['E03', 'E04', 'E05'],
                  'confirmation_prediction_gains_publication': ['Q02', 'Q03'],
                  'confirmation_default_repetition_publication': ['Q01'],
                  'confirmation_student_states_publication': ['Q06'],
                  'confirmation_prompt_changes_publication': ['Q05', 'Q06', 'E10']}
    figures = []
    for path in sorted((PAPER / 'sections').glob('*.tex')):
        for block in re.findall(r'\\begin\{figure\}.*?\\end\{figure\}', path.read_text(), re.S):
            name = re.search(r'figures/([^}]+)\.pdf', block)[1]
            figures.append({'figure': name, 'evidence_ids': figure_map[name], 'english_block': block,
                            'chinese_caption_line': next(line for line in zh.splitlines() if '(figures/'+name+'.pdf)' in line),
                            'review': 'Counts, scales, rounding, interval types and inference limits checked; rendered labels inspected.'})
    assert len(figures) == 6

    pdfs = {}
    reading_receipt = json.loads((PAPER / 'build/build_provenance.json').read_text())
    acl_receipt = json.loads((PAPER / 'build/acl/build_provenance.json').read_text())
    for name, rel, expected_pages in [('en', 'build/working_draft_en.pdf', 26),
                                      ('zh', 'build/working_draft_zh.pdf', 20),
                                      ('acl', 'build/acl/anonymous_acl_draft.pdf', 21)]:
        path = PAPER / rel
        info = subprocess.check_output(['pdfinfo', str(path)], text=True)
        pages = int(re.search(r'Pages:\s+(\d+)', info)[1]); assert pages == expected_pages
        log = path.with_suffix('.log').read_text(); text = path.with_suffix('.txt').read_text()
        assert not re.search(r'Overfull|Missing character|Citation .+ undefined|There were undefined references', log)
        assert not re.search(r'Incomplete working draft|still being completed|repairs are pending|待补跑|补跑待确认', text)
        assert not re.search(r'/home/|MINIMAX_API_KEY|API_GATEWAY|likefallwind|(?<!\w)sk-[A-Za-z0-9]{20,}', text)
        fonts = subprocess.check_output(['pdffonts', str(path)], text=True)
        font_rows = [line for line in fonts.splitlines()[2:] if line.strip()]
        for line in font_rows:
            match = re.search(r'\s+(yes|no)\s+(yes|no)\s+(yes|no)\s+\d+\s+\d+\s*$', line)
            assert match and match[1] == 'yes'
        expected = acl_receipt['pdf_sha256'] if name == 'acl' else reading_receipt['pdf_sha256'][path.name]
        assert sha(path) == expected
        pdfs[name] = {'path': str(path.relative_to(ROOT)), 'sha256': expected, 'pages': pages,
                      'all_pages_layout_inspected': True, 'inspection_method': 'Rendered page overview sheets; dense final content tables additionally inspected at page resolution.',
                      'fonts_embedded': True, 'unresolved_citations_or_overfull_or_missing_glyphs': False}
    sources = [PAPER/'main.tex', PAPER/'manuscript_zh.md', PAPER/'references.bib',
               *sorted((PAPER/'sections').glob('*.tex')), *sorted((PAPER/'figures').glob('*.pdf')),
               ROOT/'research/69_completed_content_and_final_scientific_assessment.md', Path(__file__).resolve()]
    review = {'reviewed_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'status': 'research analyses, bilingual scientific synthesis and final rendered manuscripts complete',
              'paper_complete': True, 'new_human_annotation': False,
              'reviewer': 'Research agent; this is not independent external peer review.',
              'scientific_assessment': 'research/69_completed_content_and_final_scientific_assessment.md',
              'evidence_ledger': 'paper/educational_personality_v3/evidence_ledger.md',
              'hash_checks_passed': hash_checks, 'bilingual_numerical_checks': len(tables['checks']),
              'central_claim_review': claims, 'empirical_figure_caption_review': figures,
              'pdfs': pdfs, 'evidence_sha256': inspected,
              'source_sha256': {str(p.relative_to(ROOT)): sha(p) for p in sources},
              'retained_scientific_limits': ['Only five deployed configurations, four authored English domains, and one wording for each affect cue.',
                  'No human personality, learning gain, education-unique mechanism, universal pairwise separation or unseen-model inference.',
                  'Generator deletion attenuates effects; neutral equivalence unresolved; natural-error positive agreement only18.5%.',
                  'Content screens select on outputs and do not causally control ability; repeated analyses are not independent replications.',
                  'Budget, transport and serialization deviations and original failures remain preserved.'],
              'not_performed': ['External conference submission', 'Public release of all raw API histories', 'Independent peer review'],
              'conference_acceptance_guaranteed': False,
              'legacy_controller_paper_complete_flags': 'Remain false by design; this separate manuscript-level receipt records final synthesis.'}
    (PAPER / 'final_review.json').write_text(json.dumps(review, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({'status': review['status'], 'hash_checks': hash_checks,
                      'bilingual_result_paragraph_pairs': len(paragraphs_en), 'figure_caption_pairs': len(figures),
                      'pdf_pages': {k:v['pages'] for k,v in pdfs.items()}}, ensure_ascii=False))


if __name__ == '__main__':
    main()
