"""Plot observed teaching choices and instruction contrasts from audited tables."""
import csv
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'paper/educational_personality_v4/figures'
FORMAL = ROOT / 'artifacts/educational_personality_v2/prospective_formal'
ARCHIVE = ROOT / 'artifacts/educational_personality_v4/archive_validation/analysis_identified'
INPUTS = [FORMAL / 'confirmation_descriptive/matched_prompt_profiles.csv',
          FORMAL / 'confirmation_analysis/source_prompt_rates.csv',
          ARCHIVE / 'event_rates.csv']
MODELS = ['MiniMax-M2.7', 'MiniMax-M3', 'deepseek-v4-pro',
          'doubao-seed-2.0-lite', 'glm-5.3']
NAMES = ['MiniMax-M2.7', 'MiniMax-M3', 'DeepSeek-V4-Pro',
         'Doubao-2.0-Lite', 'GLM-5.3']
EVENTS = [('answer_reveal', 'Answer revelation'),
          ('reasoning_elicitation', 'Reasoning elicitation')]


def rows(path):
    with path.open() as f:
        return list(csv.DictReader(f))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(fig, name):
    outputs = {}
    for suffix in ['pdf', 'svg', 'png']:
        path = OUT / (name + '.' + suffix)
        kw = {'metadata': {'CreationDate': None, 'ModDate': None}} if suffix == 'pdf' else {}
        fig.savefig(path, dpi=220, **kw)
        outputs[str(path.relative_to(ROOT))] = sha(path)
    plt.close(fig)
    return outputs


def main():
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10,
                         'pdf.fonttype': 42, 'ps.fonttype': 42,
                         'svg.hashsalt': 'persona-discovery-v4'})
    matched, source, archive = map(rows, INPUTS)
    lookup = {(r['model'], r['event'], r['arm']): float(r['present']) for r in matched}
    assert len(lookup) == len(matched) == 75
    families = {r['source_family'] for r in source if r['arm'] == 'ask'}
    assert len(families) == 16
    plotted = []
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.35), sharey=True)
    fig.subplots_adjust(left=.18, right=.91, bottom=.20, top=.75, wspace=.18)
    for ax, (event, title), letter in zip(axes, EVENTS, 'AB'):
        data = []
        for model in MODELS:
            values = []
            for arm in ['canonical', 'ask', 'explain']:
                rates = [float(r['present']) for r in source
                         if (r['model'], r['event'], r['arm']) == (model, event, arm)
                         and r['source_family'] in families]
                assert len(rates) == 16
                mean = lookup[model, event, arm]
                assert abs(sum(rates)/16 - mean) < 1e-12
                assert abs(mean*128-round(mean*128)) < 1e-10
                values.append(mean*100)
                plotted.append({'model': model, 'event': event, 'arm': arm,
                                'sources': 16, 'responses': 128, 'rate': mean})
            data.append(values)
        data = np.array(data)
        mesh = ax.imshow(data, vmin=0, vmax=100, cmap='Blues', aspect='auto')
        for i in range(5):
            for j in range(3):
                ax.text(j, i, f'{data[i,j]:.1f}', ha='center', va='center',
                        color='white' if data[i,j] >= 65 else '#17324d', fontsize=11)
        ax.set_title(f'{letter}  {title}', loc='left', fontweight='bold', fontsize=11, pad=10)
        ax.set_xticks([0, 1, 2], ['General\ntutoring', 'ASK\nnext step', 'EXPLAIN\nsolution'])
        ax.set_yticks(range(5), NAMES)
        ax.tick_params(length=0, pad=8)
        ax.set_xticks(np.arange(-.5, 3, 1), minor=True)
        ax.set_yticks(np.arange(-.5, 5, 1), minor=True)
        ax.grid(which='minor', color='white', linewidth=2)
        ax.tick_params(which='minor', length=0)
        ax.spines[:].set_visible(False)
    cax = fig.add_axes([.935, .20, .013, .55])
    fig.colorbar(mesh, cax=cax, ticks=[0, 50, 100])
    cax.set_title('%', fontsize=9, pad=8)
    fig.suptitle('Shared instructions can align one action and leave another different',
                 x=.04, ha='left', y=.98, fontsize=12, fontweight='bold')
    fig.text(.04, .885, 'Same 16 problems in every condition · 128 replies per model and condition',
             color='#526170', fontsize=10)
    fig.text(.18, .025, 'Actions can co-occur. EXPLAIN permits follow-up reasoning; these rates do not rank teaching quality.',
             fontsize=8, color='#526170')
    outputs = save(fig, 'teaching_choices_under_instructions')

    old_models = ['minimax-m2.7', 'minimax-m3', 'deepseek-v4-pro', 'doubao-seed-2.0-pro',
                  'glm-5.2', 'qwen3.5-4b', 'qwen3.8-27b']
    old_names = ['MiniMax-M2.7', 'MiniMax-M3', 'DeepSeek-V4-Pro', 'Doubao-2.0-Pro',
                 'GLM-5.2', 'Qwen3.5-4B', 'Qwen3.8-27B']
    index = {(r['model'], r['event'], r['arm']): r for r in archive}
    assert len(index) == len(archive) == 42
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 4.1), sharey=True)
    fig.subplots_adjust(left=.18, right=.97, bottom=.17, top=.70, wspace=.15)
    archived = []
    for ax, (event, title), letter in zip(axes, EVENTS, 'AB'):
        for i, model in enumerate(old_models):
            pair = [index[model, event, arm] for arm in ['scaffolding', 'pedagogy']]
            ax.plot([float(r['mean'])*100 for r in pair], [i, i], color='#c9cfd4', lw=1, zorder=1)
            for row, color, marker in zip(pair, ['#176b91', '#bd582c'], ['o', 's']):
                v, lo, hi = [float(row[k])*100 for k in ['mean', 'bootstrap_95_low', 'bootstrap_95_high']]
                assert int(row['sources']) == 256 and lo <= v <= hi
                ax.errorbar(v, i, xerr=[[v-lo], [hi-v]], fmt=marker, markersize=5,
                            color=color, linewidth=1.2, capsize=2, zorder=3,
                            label=('General tutoring' if row['arm']=='scaffolding' else 'Explicit probing') if i==0 else None)
                archived.append(dict(row))
        ax.set_title(f'{letter}  {title}', loc='left', fontweight='bold', fontsize=11, pad=10)
        ax.set_xlim(-3, 103)
        ax.set_xticks([0, 25, 50, 75, 100])
        ax.set_xlabel('Observed replies (%)')
        ax.set_yticks(range(7), old_names)
        ax.set_ylim(6.5, -.5)
        ax.grid(axis='x', color='#e9edf0')
        ax.set_axisbelow(True)
        ax.spines[['top', 'right', 'left']].set_visible(False)
        ax.tick_params(axis='y', length=0)
    axes[1].legend(loc='lower left', bbox_to_anchor=(-.55, 1.22), ncol=2,
                   frameon=False, fontsize=9, handletextpad=.4)
    fig.suptitle('Archived tutoring: explicit probing compresses observed model differences',
                 x=.04, ha='left', y=.99, fontsize=12, fontweight='bold')
    fig.text(.04, .91, 'Seven historical deployments · 256 paired sources · Both instructions limit replies to two sentences',
             fontsize=9, color='#526170')
    fig.text(.18, .025, 'Bars: source-bootstrap 95% intervals. Historical configurations differ from the prospective panel.',
             fontsize=8, color='#526170')
    outputs.update(save(fig, 'archive_instruction_profiles'))
    receipt = {'purpose': 'Descriptive illustrations of existing findings; no new hypothesis tests',
               'sources': {str(p.relative_to(ROOT)): sha(p) for p in [*INPUTS, Path(__file__)]},
               'matched_source_ids': sorted(families), 'matched_points': plotted,
               'archive_points': archived, 'outputs': outputs,
               'checks': {'matched_rates_recomputed_from_16_sources': 30,
                          'archive_rates_and_existing_intervals': 28},
               'quality_scores_or_learner_gains': False}
    (OUT / 'discovery_figures.json').write_text(json.dumps(receipt, indent=2)+'\n')
    print(json.dumps(receipt['checks']))


if __name__ == '__main__':
    main()
