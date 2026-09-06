#!/usr/bin/env python3
"""Render completed prospective results only; never fit or select a model."""
import os
os.environ.setdefault('MPLCONFIGDIR', '/tmp/llm-persona-matplotlib-v3')
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd

from run_personality_formal_stage_v3 import ROOT, BASE, validate_stage, verify_files

OUT = ROOT / 'paper/educational_personality_v3/figures'
EVENTS = ['answer_reveal', 'reasoning_elicitation', 'affect_acknowledgement']
LABELS = ['Answer revelation', 'Reasoning elicitation', 'Affect acknowledgement']
MODELS = ['MiniMax-M2.7', 'MiniMax-M3', 'deepseek-v4-pro', 'doubao-seed-2.0-lite', 'glm-5.3']
MODEL_LABELS = ['MiniMax M2.7', 'MiniMax M3', 'DeepSeek V4 Pro', 'Doubao 2.0 Lite', 'GLM 5.3']
BASELINES = ['context', 'default_profile', 'domain_profile', 'conditional_profile', 'training_style_profile']
BASELINE_LABELS = ['Situation', '+ model default', '+ model × subject', '+ model × student state', 'Situation + training style']
COLORS = ['#A5ADB4', '#377EB8', '#62A6A0', '#784D9B', '#E0A13C']
ARMS = ['neutral_a', 'neutral_b', 'ask', 'explain']
ARM_COLORS = ['#377EB8', '#41978A', '#CE7628', '#8658A6']


def configure():
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 8,
                         'axes.spines.top': False, 'axes.spines.right': False,
                         'axes.spines.left': False, 'pdf.fonttype': 42, 'svg.fonttype': 'none'})


def require_grid(frame, keys, expected):
    if frame.duplicated(keys).any():
        raise ValueError('Duplicate plot cell: ' + str(keys))
    found = set(map(tuple, frame[keys].to_numpy()))
    if found != set(expected):
        raise ValueError('Incomplete or unexpected plot grid: ' + str(keys))


def loss_figure(losses):
    frame = losses[losses.event.isin(EVENTS)]
    require_grid(frame, ['event', 'baseline'], [(e, b) for e in EVENTS for b in BASELINES])
    fig, axes = plt.subplots(1, 3, figsize=(10.5, 3.3), sharex=True, sharey=True)
    upper = max(.05, frame.brier.max() * 1.25)
    for ax, event, title in zip(axes, EVENTS, LABELS):
        values = frame[frame.event.eq(event)].set_index('baseline').loc[BASELINES, 'brier']
        ax.barh(range(5), values, height=.57, color=COLORS)
        for i, value in enumerate(values):
            ax.text(value + upper * .025, i, f'{value:.4f}', va='center', fontsize=8)
        ax.set_xlim(0, upper); ax.set_ylim(4.65, -.65)
        ax.set_yticks(range(5), BASELINE_LABELS)
        ax.tick_params(axis='y', length=0)
        ax.set_title(title); ax.set_xlabel('Source-averaged Brier loss ↓')
        ax.grid(axis='x', alpha=.17); ax.set_axisbelow(True)
    fig.suptitle('Locked predictions on 32 new source problems', fontsize=11)
    fig.subplots_adjust(left=.22, right=.98, bottom=.2, top=.79, wspace=.2)
    return fig


def gain_figure(comparisons):
    names = ['default_vs_context', 'student_state_vs_domain']
    require_grid(comparisons, ['event', 'comparison'], [(e, c) for e in EVENTS for c in names])
    fig, axes = plt.subplots(1, 2, figsize=(10.3, 3.0), sharey=True)
    for ax, name, title, color in zip(axes, names,
            ['Model default over situation', 'Student-state pattern over model × subject'], [COLORS[1], COLORS[3]]):
        data = comparisons[comparisons.comparison.eq(name)].set_index('event').loc[EVENTS]
        for i, (_, r) in enumerate(data.iterrows()):
            ax.hlines(i, r.bootstrap_95_low, r.bootstrap_95_high, color=color, lw=2)
            ax.scatter(r.mean_difference, i, color=color, s=35, zorder=3)
            ax.text(1.02, i, f'pₕ={r.p_holm_six:.3g}', transform=ax.get_yaxis_transform(), va='center', fontsize=8)
        ax.axvline(0, color='#555555', lw=.8)
        ax.set_yticks(range(3), LABELS); ax.set_ylim(2.6, -.6)
        ax.tick_params(axis='y', length=0)
        ax.set_title(title, fontsize=9); ax.set_xlabel('Absolute Brier improvement →')
        ax.margins(x=.18); ax.grid(axis='x', alpha=.17)
    fig.subplots_adjust(left=.2, right=.88, top=.77, bottom=.25, wspace=.55)
    fig.suptitle('The six primary predictive comparisons', fontsize=11)
    fig.text(.2, .035, 'Intervals: 95% source bootstrap. pₕ: one-sided p-value, Holm-adjusted across all six tests.', fontsize=8)
    return fig


def profile_figure(defaults, repeats):
    rates = defaults[defaults.event.isin(EVENTS)]
    agreement = repeats[repeats.event.isin(EVENTS)]
    grid = [(m, e) for m in MODELS for e in EVENTS]
    require_grid(rates, ['model', 'event'], grid)
    require_grid(agreement, ['model', 'event'], grid)
    fig, axes = plt.subplots(1, 3, figsize=(10.5, 3.5), sharey=True)
    panels = [(rates, 'mean', 'Behavior occurrence'),
              (agreement, 'positive_agreement', 'Repeat agreement on presence'),
              (agreement, 'negative_agreement', 'Repeat agreement on absence')]
    cmap = plt.get_cmap('Blues').copy(); cmap.set_bad('#E2E5E8')
    for ax, (frame, column, title) in zip(axes, panels):
        values = frame.pivot(index='model', columns='event', values=column).loc[MODELS, EVENTS].to_numpy(float)
        im = ax.imshow(np.ma.masked_invalid(values), vmin=0, vmax=1, cmap=cmap, aspect='auto')
        for i in range(5):
            for j in range(3):
                v = values[i, j]
                ax.text(j, i, 'NA' if not np.isfinite(v) else f'{100*v:.0f}%', ha='center', va='center',
                        color='white' if np.isfinite(v) and v > .65 else '#222222', fontsize=9)
        ax.set_xticks(range(3), ['Reveal', 'Elicit', 'Acknowledge'], rotation=25, ha='right')
        ax.set_yticks(range(5), MODEL_LABELS); ax.tick_params(length=0)
        ax.set_title(title, fontsize=9)
    fig.subplots_adjust(left=.17, right=.93, top=.79, bottom=.23, wspace=.15)
    fig.colorbar(im, cax=fig.add_axes([.945, .24, .012, .53]), ticks=[0, .5, 1])
    fig.suptitle('Canonical responses: defaults and repeated behavior', fontsize=11)
    fig.text(.17, .015, '256 responses/configuration on 32 sources. NA means no positive or negative pair denominator.', fontsize=8)
    return fig


def prompt_figure(effects, interpretations):
    require_grid(effects, ['model', 'event', 'arm'], [(m, e, a) for m in MODELS for e in EVENTS for a in ARMS])
    require_grid(interpretations, ['model', 'event', 'arm'], [(m, e, a) for m in MODELS for e in EVENTS for a in ARMS[:2]])
    edge = interpretations.set_index(['model', 'event', 'arm']).degenerate_source_interval
    bound = max(1.05, effects.t_interval_low.abs().max() * 1.08, effects.t_interval_high.abs().max() * 1.08)
    fig, axes = plt.subplots(2, 3, figsize=(10.4, 6.4), sharex=True, sharey=True)
    for column, (event, title) in enumerate(zip(EVENTS, LABELS)):
        for row in range(2):
            ax = axes[row, column]
            if row == 0:
                ax.axvspan(-.1, .1, color='#B0B0B0', alpha=.17)
            for k, arm in enumerate(ARMS[row*2:row*2+2]):
                data = effects[effects.event.eq(event) & effects.arm.eq(arm)].set_index('model').loc[MODELS]
                for i, (model, value) in enumerate(data.iterrows()):
                    y = i + (k-.5)*.24
                    color = ARM_COLORS[row*2+k]
                    ax.hlines(y, value.t_interval_low, value.t_interval_high, color=color, lw=1.1)
                    degenerate = row == 0 and bool(edge.loc[(model, event, arm)])
                    ax.scatter(value.mean_difference, y, color=color, marker='x' if degenerate else ['o', 's'][k],
                               s=26, zorder=3)
            ax.axvline(0, color='#666666', lw=.7)
            ax.set_xlim(-bound, bound); ax.set_ylim(4.65, -.65)
            ax.set_yticks(range(5), MODEL_LABELS); ax.tick_params(axis='y', length=0)
            ax.grid(axis='x', alpha=.15)
            ax.set_title(title + (' · neutral wording' if row == 0 else ' · teaching instruction'), fontsize=8.5)
            if row == 1:
                ax.set_xlabel('Alternative minus canonical event probability')
    handles = [Line2D([0], [0], color=c, marker=['o','s'][i%2], label=l, lw=1)
               for i, (c, l) in enumerate(zip(ARM_COLORS, ['Neutral A', 'Neutral B', 'ASK', 'EXPLAIN']))]
    fig.legend(handles=handles, loc='upper center', bbox_to_anchor=(.57, .94), ncol=4, frameon=False)
    fig.suptitle('Paired prompt changes on the same 16 sources', fontsize=11, y=.99)
    fig.subplots_adjust(left=.16, right=.985, top=.84, bottom=.15, hspace=.38, wspace=.13)
    fig.text(.16, .045, 'Neutral: nominal simultaneous 95% t intervals; grey band: ±0.10. Policy: descriptive 95% intervals.\n'
             '× marks degenerate intervals. Population equivalence also requires the separate bounded-source check.', fontsize=8)
    return fig


def state_figure(profiles):
    progress = ['wrong_attempt', 'correct_partial']
    affect = ['calm', 'frustrated']
    frame = profiles[profiles.event.isin(EVENTS)]
    require_grid(frame, ['model', 'event', 'progress', 'affect'], [(m,e,p,a) for m in MODELS for e in EVENTS for p in progress for a in affect])
    fig, axes = plt.subplots(1, 3, figsize=(10.2, 3.7), sharey=True)
    model_colors = ['#377EB8', '#D17B23', '#41978A', '#8658A6', '#C75566']
    for ax, event, title in zip(axes, EVENTS, LABELS):
        for mi, (model, label, color) in enumerate(zip(MODELS, MODEL_LABELS, model_colors)):
            data = frame[frame.model.eq(model) & frame.event.eq(event)].set_index(['progress','affect'])
            values = [data.loc[(p,a), 'mean'] for p in progress for a in affect]
            x = np.array([0,1,3,4]) + (mi-2)*.055
            for start in [0,2]:
                ax.plot(x[start:start+2], values[start:start+2], color=color, lw=1, alpha=.85)
            ax.scatter(x, values, color=color, s=19, label=label, zorder=3)
        ax.set_ylim(-.04,1.04); ax.set_xticks([0,1,3,4], ['Wrong\ncalm','Wrong\nfrustrated','Partial\ncalm','Partial\nfrustrated'])
        ax.set_title(title); ax.grid(axis='y', alpha=.17); ax.tick_params(axis='y', length=0)
    axes[0].set_ylabel('Observed event probability')
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='upper center', ncol=5, frameon=False, bbox_to_anchor=(.53,.94))
    fig.suptitle('Observed responses to the four student-state conditions', fontsize=11, y=.995)
    fig.subplots_adjust(left=.07, right=.99, bottom=.22, top=.76, wspace=.16)
    fig.text(.07,.025,'Each point: 64 responses from 32 sources. Lines connect the affect contrast within one work state; these are descriptive rates.',fontsize=8)
    return fig


CAPTIONS = {
    'confirmation_prediction_losses': 'Brier loss of previously locked forecasts on 32 new source problems, averaged within source and equally across sources. Lower is better. The style competitor uses training response profiles only; it is not a causal style adjustment. Bars have a common zero-based scale and do not show confidence intervals.',
    'confirmation_prediction_gains': 'Six primary predictive comparisons. Positive values indicate lower Brier loss than the specified baseline. Lines are 95% source-bootstrap intervals conditional on the fitted training profiles, not simultaneous intervals; p-values are one-sided and Holm-adjusted across the six tests. A nonsignificant gain does not establish equivalence.',
    'confirmation_default_repetition': 'Canonical confirmation responses: 256 answers per configuration, 32 source problems and two requests per state. Occurrence is separated from positive and negative repetition agreement. NA denotes an absent agreement denominator, not zero agreement. These are observed behaviors, not independent latent personality factors; source-level uncertainty remains in the numerical tables.',
    'confirmation_prompt_changes': 'Paired source-level changes on the same 16 source problems in all role arms. Neutral wording shows nominal Bonferroni simultaneous 95% paired-t intervals across 30 comparisons and a +/-0.10 tolerance; explicit policy arms use descriptive 95% paired-t intervals. Sparse-outcome simulations show that the nominal t coverage can fail, beyond zero-variance cases marked with crosses. These intervals alone do not establish population equivalence; the separate bounded-source audit is required. Effects describe teaching behavior, not improved learning.',
    'confirmation_student_states': 'Canonical event rates in the four controlled student-state conditions on 32 confirmation sources. Each point averages 64 responses. Lines connect calm/frustrated inputs within a work state. Wrong attempt versus correct partial work bundles correctness and progress. These descriptive curves do not replace the locked test of incremental conditional prediction.',
}


def main():
    validate_stage('confirmation')
    analysis = BASE / 'confirmation_analysis'
    summary = json.loads((analysis / 'summary.json').read_text())
    verify_files(summary['inputs'])
    if summary['prediction_sources'] != 32 or summary['prompt_sources'] != 16:
        raise ValueError('Wrong confirmation source counts')
    selection = json.loads((BASE / 'confirmation/measurement_selection.json').read_text())
    measurement = json.loads((ROOT / selection['diagnostics'] / 'summary.json').read_text())
    if measurement['invalid_or_missing'] or measurement['valid_judge_requests'] != 12120:
        raise ValueError('Full confirmation measurement required before publication figures')
    robustness = json.loads((BASE / 'confirmation_robustness/summary.json').read_text())
    verify_files(robustness['input_hashes'])
    if robustness['judge_panels'] != 8 or robustness['generator_deletion_panels'] != 5 or robustness['training_resamples'] != 200:
        raise ValueError('Required robustness calculations are incomplete')
    edge_path = BASE / 'confirmation_inference_edges/neutral_equivalence_interpretation.csv'
    edge_summary_path = edge_path.with_name('summary.json')
    edge_summary = json.loads(edge_summary_path.read_text())
    edge_policy_path = BASE / 'inference_edge_policy.json'
    if edge_summary['policy_sha256'] != hashlib.sha256(edge_policy_path.read_bytes()).hexdigest():
        raise ValueError('Inference edge audit refers to a different interpretation policy')
    edge_policy = json.loads(edge_policy_path.read_text())
    edge_script = ROOT / 'scripts/audit_personality_inference_edges_v3.py'
    if edge_policy['script_sha256'] != hashlib.sha256(edge_script.read_bytes()).hexdigest():
        raise ValueError('Inference edge implementation differs from the recorded policy')
    effects_path = analysis / 'paired_prompt_effects.csv'
    if edge_summary['effects_sha256'] != hashlib.sha256(effects_path.read_bytes()).hexdigest():
        raise ValueError('Inference edge audit refers to different prompt results')
    bounds_path = BASE / 'confirmation_neutral_bounds/neutral_equivalence_interpretation.csv'
    bounds_summary_path = bounds_path.with_name('summary.json')
    bounds_summary = json.loads(bounds_summary_path.read_text())
    bounds_policy_path = BASE / 'neutral_bounds_policy.json'
    verify_files(json.loads(bounds_policy_path.read_text())['files'])
    if (bounds_summary['effects_sha256'] != hashlib.sha256(effects_path.read_bytes()).hexdigest()
            or bounds_summary['policy_sha256'] != hashlib.sha256(bounds_policy_path.read_bytes()).hexdigest()
            or bounds_summary['table_sha256'] != hashlib.sha256(bounds_path.read_bytes()).hexdigest()):
        raise ValueError('Bounded neutral audit refers to different inputs or policy')
    filenames = ['prediction_brier.csv', 'primary_prediction_comparisons.csv', 'default_profiles.csv',
                 'repeat_diagnostics.csv', 'paired_prompt_effects.csv', 'student_state_profiles.csv']
    frames = {name: pd.read_csv(analysis / name) for name in filenames}
    configure()
    figures = {
        'confirmation_prediction_losses': loss_figure(frames['prediction_brier.csv']),
        'confirmation_prediction_gains': gain_figure(frames['primary_prediction_comparisons.csv']),
        'confirmation_default_repetition': profile_figure(frames['default_profiles.csv'], frames['repeat_diagnostics.csv']),
        'confirmation_prompt_changes': prompt_figure(frames['paired_prompt_effects.csv'], pd.read_csv(bounds_path)),
        'confirmation_student_states': state_figure(frames['student_state_profiles.csv']),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    for name, figure in figures.items():
        for ext in ['png', 'svg', 'pdf']:
            figure.savefig(OUT / (name + '.' + ext), dpi=300, bbox_inches='tight', facecolor='white')
        plt.close(figure)
        (OUT / (name + '_caption.md')).write_text(CAPTIONS[name] + '\n')
    paths = [analysis / n for n in filenames] + [edge_path, edge_summary_path, bounds_path, bounds_summary_path,
             bounds_policy_path, analysis / 'summary.json',
             BASE / 'confirmation_robustness/summary.json', edge_policy_path,
             BASE / 'confirmation/measurement_selection.json',
             ROOT / selection['diagnostics'] / 'summary.json', Path(__file__).resolve()]
    provenance = {'status': 'completed confirmation figures rendered; visual and scientific review required',
                  'figures': list(figures), 'paper_complete': False,
                  'source_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
    (OUT / 'confirmation_figures_provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')


if __name__ == '__main__':
    main()
