"""Check the integrated draft's new numeric claims and frozen evidence locally."""
import csv
import hashlib
import json
import itertools
from pathlib import Path
from audit_personality_manuscript_tables_v3 import tex_rows
from build_personality_evidence_inventory_v4 import rows as evidence_rows, rendered as evidence_rendered

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / 'paper/educational_personality_v4'
BASE = ROOT / 'artifacts/educational_personality_v4'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit_prompt_response():
    """Compare the added secondary-result reporting with saved aggregates."""
    base = ROOT / 'artifacts/prompt_contingent_signatures_v1'
    sources = ['prompt_vs_model_scale.csv', 'model_semantic_elasticity.csv',
               'rank_stability.csv', 'headroom_adjusted_elasticity_heterogeneity.csv',
               'cross_prompt_model_attribution.csv', 'decision.json']
    def read(name):
        with (base / name).open() as f:
            return list(csv.DictReader(f))
    details = (PAPER / 'sections/prompt_response_details.tex').read_text()
    names = {'cognitive_load': 'Response complexity', 'elicitation': 'Semantic elicitation',
             'help_directness': 'Assistance directness'}
    scale = read('prompt_vs_model_scale.csv')
    profiles = read('model_semantic_elasticity.csv')
    expected_scale, expected_order = [], []
    for task in ('standard', 'hard'):
        for dim, label in names.items():
            row = next(r for r in scale if r['task'] == 'mathdial_' + task and r['dimension'] == dim)
            a, lo, hi = [float(row[k]) for k in ('absolute_prompt_over_baseline_range',
                          'ratio_bootstrap_ci_low', 'ratio_bootstrap_ci_high')]
            assert abs(a - abs(float(row['shared_prompt_mean_delta'])) / float(row['baseline_model_range'])) < 1e-12
            expected_scale.append([task.capitalize(), label, f'{a:.3f} [{lo:.3f}, {hi:.3f}]'])
        for model, label in [('doubao-seed-2.0-pro', 'Doubao-Seed-2.0-Pro'), ('glm-5.2', 'GLM-5.2')]:
            row = next(r for r in profiles if r['task'] == 'mathdial_' + task and r['dimension'] == 'help_directness' and r['model'] == model)
            a, b, c, lo, hi = [float(row[k]) for k in ('generic_mean', 'pedagogy_mean', 'mean_delta', 'bootstrap_ci_low', 'bootstrap_ci_high')]
            assert abs(b - a - c) < 1e-12
            expected_order.append([task.capitalize(), label, f'{a:.2f}', f'{b:.2f}', f'{c:.2f} [{lo:.2f}, {hi:.2f}]'])
    assert tex_rows(details, 'tab:prompt-scale') == expected_scale
    assert tex_rows(details, 'tab:prompt-order-example') == expected_order
    for task in ('standard', 'hard'):
        group = [r for r in profiles if r['task'] == 'mathdial_' + task and r['dimension'] == 'help_directness']
        comparable, reversals = 0, 0
        for a, b in itertools.combinations(group, 2):
            before = float(a['generic_mean']) - float(b['generic_mean'])
            after = float(a['pedagogy_mean']) - float(b['pedagogy_mean'])
            if before and after:
                comparable += 1
                reversals += before * after < 0
        row = next(r for r in read('rank_stability.csv') if r['task'] == 'mathdial_' + task and r['dimension'] == 'help_directness')
        assert (reversals, comparable) == (int(row['pairwise_rank_reversals']), int(row['comparable_model_pairs']))
        assert f'{reversals}/{comparable}' in details
        for key in ('generic_to_pedagogy_spearman', 'exact_two_sided_p'):
            assert f'{float(row[key]):.3f}' in details
    heterogeneity = read('headroom_adjusted_elasticity_heterogeneity.csv')
    for dim in names:
        rows = [next(r for r in heterogeneity if r['task'] == 'mathdial_' + task and r['dimension'] == dim) for task in ('standard', 'hard')]
        assert '/'.join(str(int(r['complete_nonboundary_contexts'])) for r in rows) in details
        assert '/'.join(f"{float(r['permutation_q_within_task']):.4f}" for r in rows) in details
    attribution = read('cross_prompt_model_attribution.csv')
    pooled = [r for r in attribution if r['train_task'] == r['test_task'] == 'ALL']
    assert len(pooled) == 2
    for row in pooled:
        values = [float(row[k]) for k in ('accuracy', 'bootstrap_ci_low', 'bootstrap_ci_high')]
        assert f'{values[0]:.3f} [{values[1]:.3f}, {values[2]:.3f}]' in details
        assert int(row['feature_count']) == 8 and int(row['model_count']) == 6
        assert float(row['bootstrap_ci_low']) > float(row['chance_accuracy'])
    cross = [r for r in attribution if r['train_task'] != r['test_task']]
    assert len(cross) == 4
    assert all(float(r['bootstrap_ci_low']) > float(r['chance_accuracy']) for r in cross)
    assert f"{min(float(r['accuracy']) for r in cross):.3f} to {max(float(r['accuracy']) for r in cross):.3f}" in details
    decision = json.loads((base / 'decision.json').read_text())
    assert decision['analysis_status'] == 'post_hoc_secondary_audit_on_frozen_outputs'
    assert decision['replicated_semantic_elasticity_dimensions'] == ['elicitation', 'help_directness']
    return {'check': 'secondary prompt scale, ordering, adjusted heterogeneity and attribution match saved sources',
            'scale_rows': 6, 'illustrative_model_rows': 4, 'attribution_directions': 6,
            'source_sha256': {str((base / name).relative_to(ROOT)): sha(base / name) for name in sources}}


def main():
    checks = [audit_prompt_response()]
    assert not (PAPER / 'manuscript_zh.md').exists()
    assert not (PAPER / 'behavior_evidence_table_zh.md').exists()
    assert sorted(p.relative_to(PAPER).as_posix() for p in (PAPER / 'build').rglob('*.pdf')) == ['build/acl/anonymous_acl_draft.pdf']
    checks.append({'check': 'one canonical English manuscript PDF; Chinese manuscript retired'})
    inventory = json.loads((PAPER / 'behavior_evidence_inventory.json').read_text())
    for group in ('source_sha256', 'output_sha256'):
        for name, expected in inventory[group].items():
            assert sha(ROOT / name) == expected, name
    assert inventory['renderer_sha256'] == sha(ROOT / 'scripts/build_personality_evidence_inventory_v4.py')
    assert inventory['rows'] == evidence_rows()
    expected_tex = evidence_rendered(evidence_rows())
    assert (PAPER / 'sections/behavior_evidence_table.tex').read_text() == expected_tex
    checks.append({'check': 'ten integrated behavioral evidence rows independently reread from saved source fields; English table agrees',
                   'rows': len(inventory['rows']), 'numbers': 2*len(inventory['rows'])})
    previous = ROOT / 'paper/educational_personality_v3'
    table_proof = json.loads((ROOT / 'artifacts/educational_personality_v2/manuscript_structure_review/bilingual_table_audit_20260907.json').read_text())
    for name, expected in table_proof['input_sha256'].items():
        assert sha(ROOT / name) == expected, name
    table_specs = [('confirmation_details.tex', 'tab:default-rates'),
                   ('confirmation_details.tex', 'tab:absolute-losses'),
                   ('confirmation_details.tex', 'tab:matched-prompts'),
                   ('confirmation_details.tex', 'tab:secondary-events'),
                   ('confirmation_details.tex', 'tab:content-subsets'),
                   ('confirmation_details.tex', 'tab:primary-tests')]
    for file, label in table_specs:
        old_file = 'results.tex' if label == 'tab:default-rates' else file
        assert tex_rows((previous / 'sections' / old_file).read_text(), label) == tex_rows((PAPER / 'sections' / file).read_text(), label)
    checks.append({'check': 'six first-stage tables preserve previously audited values; all source hashes verified',
                   'english_tables': 6, 'prior_audit_checks': len(table_proof['checks'])})
    for study in ('cue_transfer', 'archive_validation'):
        lock = json.loads((BASE / study / 'design_freeze.json').read_text())
        for name, expected in lock['files'].items():
            assert sha(ROOT / name) == expected, name
        checks.append({'check': study + ' frozen files', 'count': len(lock['files'])})
    english = (PAPER / 'sections/cue_transfer_details.tex').read_text()
    with (BASE / 'cue_transfer/analysis/primary_transfer.csv').open() as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 6
    for row in rows:
        en_row = next(line for line in english.splitlines()
                      if line.startswith(row['arm'].capitalize() + ' &')
                      and {'answer_reveal': 'Default: reveal',
                           'reasoning_elicitation': 'Default: elicit',
                           'affect_acknowledgement': 'State: acknowledge'}[row['event']] in line)
        for key in ('gain', 'bootstrap_95_low', 'bootstrap_95_high'):
            number = f"{float(row[key]):.5f}"
            en_number = number.replace('-0.', '-.').removeprefix('0')
            assert en_number in en_row, (row['arm'], row['event'], key)
    checks.append({'check': 'six primary English table estimates and intervals', 'count': 18})
    receipt = json.loads((PAPER / 'figures/expression_transfer.json').read_text())
    for name, expected in receipt['sources'].items():
        assert sha(ROOT / name) == expected, name
    assert sha(PAPER / 'figures/expression_transfer.pdf') == receipt['figure_sha256']
    assert len(receipt['points']) == 12
    checks.append({'check': 'figure sources and output hashes', 'points': 12})
    discovery = json.loads((PAPER / 'figures/discovery_figures.json').read_text())
    for group in ('sources', 'outputs'):
        for name, expected in discovery[group].items():
            assert sha(ROOT / name) == expected, name
    with (ROOT / 'artifacts/educational_personality_v2/prospective_formal/confirmation_descriptive/matched_prompt_profiles.csv').open() as f:
        matched = {(r['model'], r['event'], r['arm']): float(r['present']) for r in csv.DictReader(f)}
    assert len(discovery['matched_points']) == 30
    for point in discovery['matched_points']:
        assert point['sources'] == 16 and point['responses'] == 128
        assert point['rate'] == matched[point['model'], point['event'], point['arm']]
    with (BASE / 'archive_validation/analysis_identified/event_rates.csv').open() as f:
        archive_rates = {(r['model'], r['event'], r['arm']): r for r in csv.DictReader(f)}
    assert len(discovery['archive_points']) == 28
    for point in discovery['archive_points']:
        assert point == archive_rates[point['model'], point['event'], point['arm']]
    checks.append({'check': 'discovery figure inputs, outputs, 30 matched rates and 28 archive rates with intervals verified',
                   'figure_points': 58})
    for sub in ('build/acl',):
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
        same = row['comparison'].startswith('same_')
        en_prefix = f"{row['arm'].capitalize()} & {event_en} & {'Same' if same else 'Other'} instruction &"
        en_line = next(s for s in archive_text.splitlines() if s.startswith(en_prefix))
        for key in ('mean', 'bootstrap_95_low', 'bootstrap_95_high'):
            value = f"{float(row[key]):.5f}"
            assert value in en_line, (row, key)
    checks.append({'check': 'all twelve archived English gain estimates and intervals', 'numbers': 36})
    model_names = {'deepseek-v4-pro': 'DeepSeek-V4-Pro', 'doubao-seed-2.0-pro': 'Doubao-2.0-Pro',
                   'glm-5.2': 'GLM-5.2', 'minimax-m2.7': 'MiniMax-M2.7', 'minimax-m3': 'MiniMax-M3',
                   'qwen3.5-4b': 'Qwen3.5-4B', 'qwen3.8-27b': 'Qwen3.8-27B'}
    with (archive / 'event_rates.csv').open() as f:
        rate_rows = list(csv.DictReader(f))
    assert len(rate_rows) == 42
    positions = {'answer_reveal': 2, 'reasoning_elicitation': 3, 'affect_acknowledgement': 4}
    for row in rate_rows:
        en_prefix = f"{model_names[row['model']]} & {row['arm'].capitalize()} &"
        en_line = next(s for s in archive_text.splitlines() if s.startswith(en_prefix))
        en_cells = [c.strip().rstrip('\\').strip() for c in en_line.split('&')]
        expected = f"{100 * float(row['mean']):.2f}"
        assert en_cells[positions[row['event']]] == expected
    checks.append({'check': 'all archived English event rates', 'numbers': 42})
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
    assert 'The original requirement for complete coding therefore failed.' in archive_text
    screen = (PAPER / 'sections/behavior_evidence_details.tex').read_text()
    screen_names = {'help_directness': 'Assistance directness', 'elicitation': 'Elicitation',
                    'autonomy_support': 'Autonomy support', 'affective_warmth': 'Affective warmth',
                    'diagnostic_specificity': 'Diagnostic specificity', 'personalization': 'Personalization',
                    'cognitive_load': 'Response complexity', 'epistemic_caution': 'Epistemic caution'}
    screen_source = ROOT / 'artifacts/submission_decision/dimension_decisions.csv'
    with screen_source.open() as f:
        screen_rows = list(csv.DictReader(f))
    for row in screen_rows:
        cells = [screen_names[row['dimension']]] + [
            'Pass' if row[k] == 'True' else 'Fail' for k in
            ('reliable_semantic_measurement', 'cross_task_semantic_signature', 'validated_pedagogical_disposition')]
        assert ' & '.join(cells) + r'\\' in screen, cells
    checks.append({'check': 'all eight cumulative semantic screening decisions match saved results',
                   'count': len(screen_rows), 'source_sha256': sha(screen_source)})
    cue_source = ROOT / 'data/educational_personality_cue_transfer_v4.json'
    cues = json.loads(cue_source.read_text())
    for arm in ('canonical', 'explicit', 'implicit', 'peer_control'):
        pairs = cues[arm] if isinstance(cues[arm], list) else [cues[arm]]
        for pair in pairs:
            for cue in pair.values():
                assert cue.replace('"', '``', 1).replace('"', "''") in english, cue
    checks.append({'check': 'all twenty exact expression stimuli appear in appendix',
                   'count': 20, 'source_sha256': sha(cue_source)})
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
