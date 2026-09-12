"""Render the integrated paper's supplementary evidence table from saved results.

No fitting, hypothesis tests, API calls, or changes to experimental decisions.
The row sources and selectors are retained for audit rather than pooling panels.
"""
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / 'paper/educational_personality_v4'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows():
    specs = [
        ('E1', 'Assistance directness', 'submission_decision/dimension_decisions.csv', 'dimension', 'help_directness', 'cross_task_icc_3_1', 'median_pairwise_task_spearman', 'semantic screen'),
        ('E2', 'Response complexity', 'submission_decision/dimension_decisions.csv', 'dimension', 'cognitive_load', 'cross_task_icc_3_1', 'median_pairwise_task_spearman', 'semantic screen'),
        ('E3', 'Semantic elicitation', 'submission_decision/dimension_decisions.csv', 'dimension', 'elicitation', 'cross_task_icc_3_1', 'median_pairwise_task_spearman', 'semantic screen'),
        ('E4', 'Expressed confidence', 'epistemic_character_axes_v1/cross_context_stability.csv', 'axis', 'expressed_confidence', 'icc_3_1', 'median_pairwise_spearman', 'exploratory archive'),
        ('E5', 'Revision propensity', 'epistemic_character_axes_v1/cross_context_stability.csv', 'axis', 'revision_propensity', 'icc_3_1', 'median_pairwise_spearman', 'exploratory archive'),
        ('E6', 'Unanswerable abstention', 'epistemic_character_axes_v1/cross_context_stability.csv', 'axis', 'unanswerable_abstention_propensity', 'icc_3_1', 'median_pairwise_spearman', 'exploratory archive'),
        ('E7', 'Attack success', 'normative_boundary_axes_v1/cross_context_stability.csv', 'axis', 'adversarial_attack_success_propensity', 'icc_3_1', 'median_pairwise_spearman', 'exploratory within-task'),
        ('E8', 'SATA incorrect inclusion', 'normative_boundary_axes_v1/cross_context_stability.csv', 'axis', 'sata_incorrect_inclusion_propensity', 'icc_3_1', 'median_pairwise_spearman', 'exploratory within-task'),
        ('E9', 'Next-step actionability', 'confirmatory_character_panel_v1/formal/cross_task_stability.csv', 'dimension', 'next_step_actionability', 'icc_3_1', 'median_pairwise_spearman', 'frozen-split panel'),
    ]
    result = []
    for ident, en, name, key, target, field_a, field_b, scope in specs:
        path = ROOT / 'artifacts' / name
        with path.open() as f:
            matching = [r for r in csv.DictReader(f) if r[key] == target]
        if len(matching) != 1:
            raise ValueError((name, target, len(matching)))
        row = matching[0]
        result.append(dict(id=ident, en=en, source=str(path.relative_to(ROOT)),
                           selector={key: target}, fields=[field_a, field_b],
                           values=[float(row[field_a]), float(row[field_b])], scope=scope))
    path = ROOT / 'artifacts/affiliation_stability_pilot_v1/analysis/decision.json'
    decision = json.loads(path.read_text())
    fields = ['default_cross_domain_spearman', 'default_to_irrelevant_spearman']
    result.append(dict(id='E10', en='Open affiliation',
                       source=str(path.relative_to(ROOT)), selector={'object': 'estimates'}, fields=fields,
                       values=[decision['estimates'][f] for f in fields], scope='targeted five-model pilot'))
    return result


def rendered(records):
    tex = [r'\begin{table}[t]', r'\centering\small', r'\begin{tabular}{llrr}', r'\toprule',
           r'ID & Behavior & Statistic A & Statistic B\\', r'\midrule']
    for r in records:
        a, b = (f'{v:.3f}' for v in r['values'])
        tex.append(f"{r['id']} & {r['en']} & {a} & {b}" + r'\\')
    tex.extend([r'\bottomrule', r'\end{tabular}',
                r'\caption{Quantitative anchors for the supplementary behavioral findings. For E1--E9, A is cross-context ICC(3,1) and B is median pairwise model-rank Spearman correlation. For E10, A is education/non-education rank correlation and B is default/irrelevant-change rank correlation. These measure different forms of recurrence; they are not comparable trait-strength scores or new significance tests.}',
                r'\label{tab:evidence-anchors}', r'\end{table}'])
    return '\n'.join(tex)+'\n'


def main():
    records = rows()
    tex = rendered(records)
    output = PAPER / 'sections/behavior_evidence_table.tex'
    output.write_text(tex)
    sources = sorted({r['source'] for r in records})
    receipt = dict(purpose='Evidence integration only; no new experiments or tests',
                   rows=records,
                   source_sha256={p: sha(ROOT/p) for p in sources},
                   output_sha256={str(output.relative_to(ROOT)): sha(output)},
                   renderer_sha256=sha(Path(__file__)))
    (PAPER / 'behavior_evidence_inventory.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2)+'\n')
    print(f'Rendered {len(records)} evidence rows from {len(sources)} saved result tables/files.')


if __name__ == '__main__':
    main()
