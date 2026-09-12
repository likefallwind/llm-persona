#!/usr/bin/env python3
"""Draw the study design with the terminology used in the English manuscript."""
import os
os.environ.setdefault('MPLCONFIGDIR', '/tmp/llm-persona-matplotlib-v4')
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

from run_personality_formal_stage_v3 import BASE, ROOT, verify_files

OUT = ROOT / 'paper/educational_personality_v4/figures'


def rows(path):
    return [json.loads(line) for line in path.open() if line.strip()]


def main():
    freeze_path = BASE / 'design_freeze.json'
    freeze = json.loads(freeze_path.read_text())
    verify_files(freeze['files'])
    train = rows(BASE / 'training/scenarios.jsonl')
    confirm = rows(BASE / 'confirmation/scenarios.jsonl')
    manifest = rows(BASE / 'training/generation_manifest.jsonl')
    confirmations = rows(BASE / 'confirmation/generation_manifest.jsonl')
    models = len({r['model'] for r in manifest})
    repeats = len({r['repeat'] for r in manifest})
    states = len({(r['progress'], r['affect']) for r in train})
    main = [r for r in confirm if r['panel'] == 'main' and r['arm'] == 'canonical']
    intervention = [r for r in confirm if r['panel'] == 'main' and r['arm'] != 'canonical']
    counts = {
        'training_questions': len({r['template'] for r in train}),
        'training_source_families': len({r['source_family'] for r in train}),
        'confirmation_source_families': len({r['source_family'] for r in main}),
        'intervention_source_families': len({r['source_family'] for r in intervention}),
        'training_answers': len(manifest),
        'canonical_confirmation_answers': len(main) * models * repeats,
        'additional_intervention_answers': len(intervention) * models * repeats,
        'opportunity_answers': sum(r['panel'].startswith('opportunity_') for r in confirm) * models * repeats,
        'sentinel_answers': sum(r['panel'] == 'training_sentinel' for r in confirm) * models * repeats,
    }
    expected = dict(training_questions=32, training_source_families=30,
                    confirmation_source_families=32, intervention_source_families=16,
                    training_answers=1280, canonical_confirmation_answers=1280,
                    additional_intervention_answers=2560, opportunity_answers=160, sentinel_answers=40)
    if counts != expected or (models, repeats, states) != (5, 2, 4):
        raise ValueError('Frozen design differs from the displayed schematic')
    if len(confirmations) != sum(counts[k] for k in
            ['canonical_confirmation_answers', 'additional_intervention_answers', 'opportunity_answers', 'sentinel_answers']):
        raise ValueError('Confirmation request accounting differs')
    if {r['source_family'] for r in train} & {r['source_family'] for r in main}:
        raise ValueError('Main training and confirmation source families overlap')

    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 14,
                         'svg.fonttype': 'none', 'pdf.fonttype': 42})
    fig, ax = plt.subplots(figsize=(12, 6.4))
    fig.subplots_adjust(left=.015, right=.985, top=.98, bottom=.02)
    ax.set(xlim=(0, 1), ylim=(0, 1)); ax.axis('off')
    ax.text(.5, .97, 'Study design: separate problems, predictions saved before response collection',
            ha='center', va='top', fontsize=17, fontweight='bold', color='#203544')

    def box(x, y, title, body, color, height=.32):
        ax.add_patch(FancyBboxPatch((x, y), .295, height,
                     boxstyle='round,pad=0.008,rounding_size=0.015',
                     facecolor=color, edgecolor='#A5B2BA', linewidth=1.1))
        ax.text(x + .1475, y + height - .033, title, ha='center', va='top',
                fontsize=16, fontweight='bold', color='#203544')
        ax.text(x + .1475, y + height - .096, body, ha='center', va='top',
                fontsize=13.5, linespacing=1.45, color='#263B48')

    box(.02, .565, 'Training answers',
        '32 questions / 30 source families\nFour subjects / standard prompt\n5 models · 4 states · 2 requests\n1,280 answers', '#EAF2F8')
    box(.3525, .565, 'Fix predictions',
        'Fit and tune on training sources\nSave predictions and fitted models\nPrimary tests and robustness checks\nBefore collecting test answers', '#F0F1F3')
    box(.685, .565, 'Test answers',
        '32 separate source families\nSame subjects / standard prompt\n5 models · 4 states · 2 requests\n1,280 answers', '#E8F3EF')
    for left, right in [(.319, .341), (.652, .673)]:
        ax.add_patch(FancyArrowPatch((left, .724), (right, .724),
                     arrowstyle='-|>', mutation_scale=17, linewidth=1.5, color='#526674'))
    ax.text(.5, .495, 'Three research questions tested on the new responses',
            ha='center', va='center', fontsize=15, fontweight='bold', color='#203544')
    box(.02, .145, 'RQ1 · Recurring behavior',
        'Repeat agreement and profiles\nTwo requests under identical inputs\nReport how often each action occurs\n32 new source families', '#EAF2F8', .285)
    box(.3525, .145, 'RQ2 · Behavior prediction',
        'Four nested predictors:\nsubject + state; model defaults;\nmodel × subject; model × state\nLosses averaged by source', '#E8F3EF', .285)
    box(.685, .145, 'RQ3 · Instruction effects',
        '16 matched source families\nStandard; neutral A/B; ASK; EXPLAIN\nAll student states; two requests\n2,560 additional answers', '#FAF0E5', .285)
    ax.text(.5, .08, 'Additional checks: 160 complete/missing-information answers + 40 reference-question replies.',
            ha='center', va='center', fontsize=12.5, color='#526674')
    ax.text(.5, .032, 'All counts describe the fixed design. Repeated requests and prompt variants do not add independent sources.',
            ha='center', va='center', fontsize=12.5, color='#526674')
    OUT.mkdir(parents=True, exist_ok=True)
    for extension in ['png', 'svg', 'pdf']:
        fig.savefig(OUT / f'study_design.{extension}', dpi=250, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    inputs = [freeze_path, BASE / 'training/scenarios.jsonl', BASE / 'confirmation/scenarios.jsonl',
              BASE / 'training/generation_manifest.jsonl', BASE / 'confirmation/generation_manifest.jsonl',
              Path(__file__).resolve()]
    report = dict(status='frozen design schematic; no outcome data or completion claim',
                  counts=counts, models=models, repeats=repeats, student_states=states,
                  new_api_calls=0, empirical=False,
                  input_hashes={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs})
    (OUT / 'study_design_provenance.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
