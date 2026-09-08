"""Check the integrated draft's new numeric claims and frozen evidence locally."""
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / 'paper/educational_personality_v4'
BASE = ROOT / 'artifacts/educational_personality_v4'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    checks = []
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
    appendix_text = ' '.join((PAPER / 'sections/cue_transfer_details.tex').read_text().split())
    assert 'has not been executed' in appendix_text
    assert '尚未执行' in chinese
    report = {'status': 'specified local checks passed; not scientific completion',
              'checks': checks, 'scientific_quality_goal_complete': False,
              'archive_behavior_validation_executed': False,
              'audit_script_sha256': sha(Path(__file__)),
              'review_scope': 'new estimates and evidence hashes; not full independent manuscript review'}
    (PAPER / 'evidence_audit.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
