"""Render the linked transfer comparisons directly from completed analysis tables."""
import csv
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / 'paper/educational_personality_v4'
FIRST = ROOT / 'artifacts/educational_personality_v2/prospective_formal/confirmation_analysis/primary_prediction_comparisons.csv'
CUE = ROOT / 'artifacts/educational_personality_v4/cue_transfer/analysis/all_forecast_comparisons.csv'


def main():
    with FIRST.open() as f:
        first = list(csv.DictReader(f))
    with CUE.open() as f:
        cue = list(csv.DictReader(f))
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9,
                         'pdf.fonttype': 42, 'ps.fonttype': 42})
    fig, axes = plt.subplots(1, 3, figsize=(9.2, 3.1), sharey=True)
    specs = [('answer_reveal', 'default', 'Revelation: default gain'),
             ('reasoning_elicitation', 'default', 'Elicitation: default gain'),
             ('affect_acknowledgement', 'conditional', 'Acknowledgement: state gain')]
    plotted = []
    for ax, (event, comparison, title) in zip(axes, specs):
        old_name = 'default_vs_context' if comparison == 'default' else 'student_state_vs_domain'
        old = next(r for r in first if r['event'] == event and r['comparison'] == old_name)
        rows = [(old, 'mean_difference', 'First confirmation')]
        rows += [(next(r for r in cue if r['event'] == event and r['comparison'] == comparison
                       and r['arm'] == arm), 'gain', arm)
                 for arm in ('canonical', 'explicit', 'implicit')]
        for y, (row, key, arm) in zip((3, 2, 1, 0), rows):
            gain, lo, hi = (float(row[k]) for k in (key, 'bootstrap_95_low', 'bootstrap_95_high'))
            color = '#777777' if y == 3 else '#176B91' if y == 2 else '#B65334'
            ax.errorbar(gain, y, xerr=[[gain-lo], [hi-gain]], fmt='o', color=color,
                        capsize=3, markersize=5, linewidth=1.5)
            plotted.append(dict(event=event, comparison=comparison, arm=arm,
                                gain=gain, low=lo, high=hi))
        ax.axvline(0, color='#999999', linewidth=.8, linestyle='--')
        ax.set_title(title, fontsize=9)
        ax.set_xlabel('Brier loss reduction')
        ax.set_ylim(-.6, 3.6)
        ax.grid(axis='x', color='#eeeeee')
        ax.spines[['top', 'right']].set_visible(False)
        ax.set_axisbelow(True)
        ax.tick_params(axis='x', labelsize=8)
        if comparison == 'conditional':
            ax.set_xticks([-.01, 0, .01])
        elif event == 'answer_reveal':
            ax.set_xticks([0, .05, .10])
    axes[0].set_yticks([3, 2, 1, 0], ['New problems\n(original wording)',
                                    'Same problems\n(contemporary original)',
                                    'Same problems\n(explicit synonyms)',
                                    'Same problems\n(implicit cues)'])
    fig.tight_layout(w_pad=2)
    target = PAPER / 'figures/expression_transfer.pdf'
    fig.savefig(target, metadata={'CreationDate': None, 'ModDate': None})
    plt.close(fig)
    receipt = {'sources': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                           for p in (FIRST, CUE, Path(__file__))},
               'points': plotted, 'figure_sha256': hashlib.sha256(target.read_bytes()).hexdigest()}
    target.with_suffix('.json').write_text(json.dumps(receipt, indent=2) + '\n')


if __name__ == '__main__':
    main()
