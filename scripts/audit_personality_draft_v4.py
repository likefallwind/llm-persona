"""Check the integrated draft's new numeric claims and frozen evidence locally."""
import csv
import hashlib
import json
import itertools
from pathlib import Path
from audit_personality_manuscript_tables_v3 import tex_rows, md_rows

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / 'paper/educational_personality_v4'
BASE = ROOT / 'artifacts/educational_personality_v4'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    checks = []
    previous = ROOT / 'paper/educational_personality_v3'
    table_proof = json.loads((ROOT / 'artifacts/educational_personality_v2/manuscript_structure_review/bilingual_table_audit_20260907.json').read_text())
    for name, expected in table_proof['input_sha256'].items():
        assert sha(ROOT / name) == expected, name
    table_specs = [('results.tex', 'tab:default-rates', '| 部署 | 答案揭示 |'),
                   ('confirmation_details.tex', 'tab:absolute-losses', '| 预测器 |'),
                   ('confirmation_details.tex', 'tab:matched-prompts', '| 部署／事件 |'),
                   ('confirmation_details.tex', 'tab:secondary-events', '| 部署 | 解释 |'),
                   ('confirmation_details.tex', 'tab:content-subsets', '| 子集 | 来源／回答 |'),
                   ('confirmation_details.tex', 'tab:primary-tests', '| 行为与增量 |')]
    old_zh = (previous / 'manuscript_zh.md').read_text()
    new_zh = (PAPER / 'manuscript_zh.md').read_text()
    for file, label, header in table_specs:
        assert tex_rows((previous / 'sections' / file).read_text(), label) == tex_rows((PAPER / 'sections' / file).read_text(), label)
        assert md_rows(old_zh, header) == md_rows(new_zh, header)
    checks.append({'check': 'six first-stage tables preserve previously audited values; all source hashes verified',
                   'bilingual_tables': 12, 'prior_audit_checks': len(table_proof['checks'])})
    for study in ('cue_transfer', 'archive_validation'):
        lock = json.loads((BASE / study / 'design_freeze.json').read_text())
        for name, expected in lock['files'].items():
            assert sha(ROOT / name) == expected, name
        checks.append({'check': study + ' frozen files', 'count': len(lock['files'])})
    english = (PAPER / 'sections/cue_results.tex').read_text()
    chinese = (PAPER / 'manuscript_zh.md').read_text()
    with (BASE / 'cue_transfer/analysis/primary_transfer.csv').open() as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 6
    for row in rows:
        en_row = next(line for line in english.splitlines()
                      if line.startswith(row['arm'].capitalize() + ' &')
                      and {'answer_reveal': 'Default: reveal',
                           'reasoning_elicitation': 'Default: elicit',
                           'affect_acknowledgement': 'State: acknowledge'}[row['event']] in line)
        zh_row = next(line for line in chinese.splitlines()
                      if line.startswith('| ' + {'explicit': '显式', 'implicit': '隐含'}[row['arm']] + ' |')
                      and {'answer_reveal': '默认揭示', 'reasoning_elicitation': '默认邀请',
                           'affect_acknowledgement': '状态承接'}[row['event']] in line)
        for key in ('gain', 'bootstrap_95_low', 'bootstrap_95_high'):
            number = f"{float(row[key]):.5f}"
            en_number = number.replace('-0.', '-.').removeprefix('0')
            assert en_number in en_row, (row['arm'], row['event'], key)
            assert number in zh_row, (row['arm'], row['event'], key)
    checks.append({'check': 'six primary bilingual table estimates and intervals', 'count': 18})
    receipt = json.loads((PAPER / 'figures/expression_transfer.json').read_text())
    for name, expected in receipt['sources'].items():
        assert sha(ROOT / name) == expected, name
    assert sha(PAPER / 'figures/expression_transfer.pdf') == receipt['figure_sha256']
    assert len(receipt['points']) == 12
    checks.append({'check': 'figure sources and output hashes', 'points': 12})
    for sub in ('build', 'build/acl'):
        report = json.loads((PAPER / sub / 'build_provenance.json').read_text())
        for name, expected in report.get('source_sha256', {}).items():
            assert sha(ROOT / name) == expected, name
        assert report['scientific_quality_goal_complete'] is False
        assert report['v4_wrapper_sha256'] == sha(ROOT / 'scripts/build_personality_draft_v4.py')
    archive = BASE / 'archive_validation/analysis_identified'
    archive_report = json.loads((archive / 'summary.json').read_text())
    for name, expected in archive_report['input_hashes'].items():
        assert sha(ROOT / name) == expected, name
    assert archive_report['valid_coding_requests'] == 10750
    assert archive_report['missing_coding_requests'] == 2
    assert archive_report['original_complete_coding_gate_passed'] is False
    assert archive_report['missing_labels_imputed'] is False
    code_path = BASE / 'archive_validation/measurement_diagnostics/transport_diagnostic/event_codes.csv'
    votes = {}
    with code_path.open() as f:
        for row in csv.DictReader(f):
            key = row['blind_id'], row['event']
            panel = votes.setdefault(key, {})
            assert row['judge_requested'] not in panel
            panel[row['judge_requested']] = int(row['present'])
    with (archive / 'identified_consensus.csv').open() as f:
        consensus = list(csv.DictReader(f))
    assert len(consensus) == len(votes) == 28672
    assert len({(r['blind_id'], r['event']) for r in consensus}) == len(consensus)
    incomplete_events = 0
    for row in consensus:
        panel = votes[(row['blind_id'], row['event'])]
        n = len(panel)
        possible = {int(sum(panel.values()) + sum(rest) >= 2)
                    for rest in itertools.product((0, 1), repeat=3-n)}
        assert possible == {int(row['present'])}
        assert int(row['valid_coders']) == n
        if n < 3:
            incomplete_events += 1
            assert row['unanimous'] == ''
    assert incomplete_events == 16
    checks.append({'check': 'all archived majorities independently enumerated from observed votes',
                   'events': len(consensus), 'events_with_absent_third_vote': incomplete_events})
    archive_text = (PAPER / 'sections/archive_validation_details.tex').read_text()
    with (archive / 'prediction_gains.csv').open() as f:
        comparisons = list(csv.DictReader(f))
    assert len(comparisons) == 12
    for row in comparisons:
        event_en = {'answer_reveal': 'Reveal', 'reasoning_elicitation': 'Elicit',
                    'affect_acknowledgement': 'Acknowledge'}[row['event']]
        event_zh = {'answer_reveal': '答案揭示', 'reasoning_elicitation': '推理邀请',
                    'affect_acknowledgement': '情绪／困难承接'}[row['event']]
        same = row['comparison'].startswith('same_')
        en_prefix = f"{row['arm'].capitalize()} & {event_en} & {'Same' if same else 'Other'} instruction &"
        zh_prefix = f"| {row['arm']} | {event_zh} | {'同指令' if same else '另一指令'} |"
        en_line = next(s for s in archive_text.splitlines() if s.startswith(en_prefix))
        zh_line = next(s for s in chinese.splitlines() if s.startswith(zh_prefix))
        for key in ('mean', 'bootstrap_95_low', 'bootstrap_95_high'):
            value = f"{float(row[key]):.5f}"
            assert value in en_line and value in zh_line, (row, key)
    checks.append({'check': 'all twelve archived bilingual gain estimates and intervals', 'numbers': 36})
    model_names = {'deepseek-v4-pro': 'DeepSeek-V4-Pro', 'doubao-seed-2.0-pro': 'Doubao-2.0-Pro',
                   'glm-5.2': 'GLM-5.2', 'minimax-m2.7': 'MiniMax-M2.7', 'minimax-m3': 'MiniMax-M3',
                   'qwen3.5-4b': 'Qwen3.5-4B', 'qwen3.8-27b': 'Qwen3.8-27B'}
    with (archive / 'event_rates.csv').open() as f:
        rate_rows = list(csv.DictReader(f))
    assert len(rate_rows) == 42
    positions = {'answer_reveal': 2, 'reasoning_elicitation': 3, 'affect_acknowledgement': 4}
    for row in rate_rows:
        en_prefix = f"{model_names[row['model']]} & {row['arm'].capitalize()} &"
        zh_prefix = f"| {model_names[row['model']]} | {row['arm']} |"
        en_line = next(s for s in archive_text.splitlines() if s.startswith(en_prefix))
        zh_line = next(s for s in chinese.splitlines() if s.startswith(zh_prefix))
        en_cells = [c.strip().rstrip('\\').strip() for c in en_line.split('&')]
        zh_cells = [c.strip() for c in zh_line.strip('|').split('|')]
        expected = f"{100 * float(row['mean']):.2f}"
        assert en_cells[positions[row['event']]] == zh_cells[positions[row['event']]] == expected
    checks.append({'check': 'all archived bilingual event rates', 'numbers': 42})
    bounds_dir = BASE / 'archive_validation/full_coder_bounds'
    bounds_report = json.loads((bounds_dir / 'summary.json').read_text())
    for name, expected in bounds_report['input_hashes'].items():
        assert sha(ROOT / name) == expected, name
    assert bounds_report['sources'] == 256 and bounds_report['actual_missing_labels_imputed'] is False
    definitions = json.loads((bounds_dir / 'scenario_definitions.json').read_text())
    assert len(definitions) == 18
    with (bounds_dir / 'scenario_gains.csv').open() as f:
        scenarios = list(csv.DictReader(f))
    with (bounds_dir / 'gain_bounds.csv').open() as f:
        bounds = list(csv.DictReader(f))
    assert len(scenarios) == 72 and len(bounds) == 36
    for bound in bounds:
        group = [r for r in scenarios if all(r[k] == bound[k] for k in ('judge', 'arm', 'event', 'comparison'))]
        assert len(group) == (4 if bound['judge'] == 'deepseek-v4-pro' else 1)
        assert all(int(r['sources']) == 256 for r in group)
        for prefix, key in [('gain', 'mean'), ('interval_low', 'bootstrap_95_low'), ('interval_high', 'bootstrap_95_high')]:
            values = [float(r[key]) for r in group]
            assert abs(float(bound[prefix + '_min']) - min(values)) < 1e-12
            assert abs(float(bound[prefix + '_max']) - max(values)) < 1e-12
    checks.append({'check': 'full-source coder ranges equal all saved scenario extrema',
                   'sources': 256, 'comparisons': 36, 'eventwise_scenarios': 18})
    assert 'complete-coding gate therefore failed' in archive_text
    assert '原完整编码门槛仍失败' in chinese
    assert '尚无完整验证结果' not in chinese
    report = {'status': 'specified local checks passed; not scientific completion',
              'checks': checks, 'scientific_quality_goal_complete': False,
              'archive_identified_majority_analysis_complete': True,
              'archive_original_complete_coding_gate_passed': False,
              'audit_script_sha256': sha(Path(__file__)),
              'review_scope': 'new estimates, evidence hashes, and observed-vote majority enumeration; not full independent manuscript review'}
    (PAPER / 'evidence_audit.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
