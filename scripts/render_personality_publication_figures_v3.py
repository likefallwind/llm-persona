#!/usr/bin/env python3
"""Publication-size variants of frozen result plots; no statistical changes."""
import datetime
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import plot_personality_confirmation_v3 as plot
from matplotlib.text import Text
from run_personality_formal_stage_v3 import verify_files

SHORT_MODELS = ['M2.7', 'M3', 'DeepSeek', 'Doubao', 'GLM']
SHORT_EVENTS = ['Reveal', 'Elicit', 'Acknowledge']


def strip_figure_notes(fig):
    # The complete statistical qualifications remain in manuscript captions.
    for label in list(fig.texts):
        label.remove()
    for label in fig.findobj(Text):
        label.set_fontsize(8.5)


def main():
    receipt = plot.BASE / 'confirmation_reporting/summary.json'
    report = json.loads(receipt.read_text())
    verify_files(report['scripts'])
    verify_files(report['report_hashes'])
    source = plot.BASE / 'confirmation_analysis'
    names = ['primary_prediction_comparisons.csv', 'default_profiles.csv',
             'repeat_diagnostics.csv', 'student_state_profiles.csv', 'paired_prompt_effects.csv']
    paths = [source / name for name in names]
    frames = {p.name: pd.read_csv(p) for p in paths}
    bounds = plot.BASE / 'confirmation_neutral_bounds/neutral_equivalence_interpretation.csv'
    plot.configure()
    plot.plt.rcParams['font.size'] = 8.5
    figures = {}

    gain = plot.gain_figure(frames['primary_prediction_comparisons.csv'])
    strip_figure_notes(gain)
    gain.set_size_inches(6.3, 2.25)
    for ax, title in zip(gain.axes, ['Default increment', 'Student-state increment']):
        for text in list(ax.texts):
            text.remove()  # Exact six adjusted p-values are in the numeric table.
        ax.set_title(title, fontsize=9)
        ax.set_yticks(range(3), SHORT_EVENTS)
        ax.set_xlabel('Brier improvement', fontsize=8.5)
    gain.axes[0].set_xticks([0, .05, .10, .15])
    gain.axes[1].set_xticks([0, .005, .010, .015])
    gain.subplots_adjust(left=.17, right=.99, top=.85, bottom=.23, wspace=.24)
    figures['confirmation_prediction_gains_publication'] = gain

    profile = plot.profile_figure(frames['default_profiles.csv'], frames['repeat_diagnostics.csv'])
    strip_figure_notes(profile)
    profile.set_size_inches(6.3, 2.65)
    for ax, title in zip(profile.axes[:3], ['Occurrence', 'Repeat: present', 'Repeat: absent']):
        values = ax.images[0].get_array()
        for label in ax.texts:
            x, y = map(int, label.get_position())
            value = values[y, x]
            label.set_text('NA' if np.ma.is_masked(value) or not np.isfinite(value)
                           else f'{100 * value:.1f}')
            label.set_fontsize(8.5)
        ax.set_yticks(range(5), SHORT_MODELS)
        ax.set_xticks(range(3), SHORT_EVENTS, rotation=25, ha='right')
        ax.set_title(title, fontsize=8.5)
    profile.axes[3].set_position([.95, .29, .012, .55])
    profile.subplots_adjust(left=.11, right=.935, top=.84, bottom=.29, wspace=.16)
    figures['confirmation_default_repetition_publication'] = profile

    state = plot.state_figure(frames['student_state_profiles.csv'])
    strip_figure_notes(state)
    state.set_size_inches(6.3, 3.15)
    for ax, title in zip(state.axes, ['Answer revelation', 'Reasoning elicitation', 'Affect acknowledgement']):
        ax.set_title(title, fontsize=8.5)
        ax.set_xticks([0, 1, 3, 4], ['C', 'F', 'C', 'F'])
        ax.text(.5, -.22, 'Wrong', transform=ax.get_xaxis_transform(), ha='center', fontsize=8.5)
        ax.text(3.5, -.22, 'Partial', transform=ax.get_xaxis_transform(), ha='center', fontsize=8.5)
    for legend in list(state.legends):
        legend.remove()
    handles, _ = state.axes[0].get_legend_handles_labels()
    state.legend(handles, SHORT_MODELS, ncol=5, loc='upper center',
                 frameon=False, fontsize=8.5, handletextpad=.2, columnspacing=1.1)
    state.axes[0].set_ylabel('Observed probability', fontsize=8.5)
    state.subplots_adjust(left=.09, right=.99, top=.73, bottom=.20, wspace=.17)
    figures['confirmation_student_states_publication'] = state

    prompt = plot.prompt_figure(frames['paired_prompt_effects.csv'], pd.read_csv(bounds))
    strip_figure_notes(prompt)
    prompt.set_size_inches(6.3, 4.7)
    for i, ax in enumerate(prompt.axes):
        ax.set_title(SHORT_EVENTS[i % 3] + (' / neutral' if i < 3 else ' / instruction'), fontsize=8.5)
        ax.set_yticks(range(5), SHORT_MODELS)
        ax.set_xticks([-1, -.5, 0, .5, 1])
        ax.set_xlabel('')
    prompt.subplots_adjust(left=.11, right=.99, top=.83, bottom=.11, hspace=.34, wspace=.16)
    prompt.supxlabel('Alternative minus canonical probability', fontsize=8.5, y=.02)
    for legend in prompt.legends:
        legend.set_bbox_to_anchor((.55, .98))
        for text in legend.get_texts():
            text.set_fontsize(8.5)
    figures['confirmation_prompt_changes_publication'] = prompt

    outputs = []
    for name, fig in figures.items():
        for suffix in ['pdf', 'png', 'svg']:
            path = plot.OUT / (name + '.' + suffix)
            fig.savefig(path, dpi=300, bbox_inches='tight', facecolor='white')
            outputs.append(path)
        plot.plt.close(fig)
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    result = {'rendered_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'changes': ['6.3-inch source width and 8.5-point labels for two-column placement',
                          'Shorter deployment/action labels and removal of repeated figure notes',
                          'Profile cells are percentages to one decimal; color scale remains probability',
                          'Gain p-values retained in the numeric manuscript table instead of tiny plot labels'],
              'new_api_calls': 0, 'new_estimates': 0, 'frozen_reporting_files_changed': False,
              'source_sha256': {str(p.relative_to(plot.ROOT)): sha(p) for p in
                                [*paths, bounds, receipt, Path(plot.__file__), Path(__file__).resolve()]},
              'output_sha256': {str(p.relative_to(plot.ROOT)): sha(p) for p in outputs}}
    (plot.OUT / 'publication_figures_provenance.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'figures': list(figures), 'new_estimates': 0}))


if __name__ == '__main__':
    main()
