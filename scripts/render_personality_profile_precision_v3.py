#!/usr/bin/env python3
"""Render one-decimal labels without changing the frozen reporting implementation.

The original plot and reporting receipts remain intact. This editorial variant
prevents a 99.6% observed rate from being displayed as an exact 100% ceiling.
"""
import datetime
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

import plot_personality_confirmation_v3 as plot
from run_personality_formal_stage_v3 import verify_files


def main():
    receipt = plot.BASE / 'confirmation_reporting/summary.json'
    report = json.loads(receipt.read_text())
    verify_files(report['scripts'])
    verify_files(report['report_hashes'])
    source = plot.BASE / 'confirmation_analysis'
    defaults, repeats = source / 'default_profiles.csv', source / 'repeat_diagnostics.csv'
    plot.configure()
    figure = plot.profile_figure(pd.read_csv(defaults), pd.read_csv(repeats))
    count = 0
    for ax in figure.axes[:3]:
        values = ax.images[0].get_array()
        for label in ax.texts:
            x, y = map(int, label.get_position())
            value = values[y, x]
            label.set_text('NA' if np.ma.is_masked(value) or not np.isfinite(value)
                           else f'{100 * value:.1f}%')
            count += 1
    if count != 45:
        raise ValueError('Unexpected number of profile labels')
    name = 'confirmation_default_repetition_precise'
    outputs = []
    for suffix in ['pdf', 'png', 'svg']:
        path = plot.OUT / (name + '.' + suffix)
        figure.savefig(path, dpi=300, bbox_inches='tight', facecolor='white')
        outputs.append(path)
    plot.plt.close(figure)
    (plot.OUT / (name + '_caption.md')).write_text(
        plot.CAPTIONS['confirmation_default_repetition'] + ' Labels retain one decimal place.\n')
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    result = {'rendered_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'change': 'Only percentage label precision changes from zero to one decimal place.',
              'labels': count, 'new_api_calls': 0, 'frozen_reporting_files_changed': False,
              'source_sha256': {str(p.relative_to(plot.ROOT)): sha(p) for p in
                                [defaults, repeats, receipt, Path(plot.__file__), Path(__file__).resolve()]},
              'output_sha256': {str(p.relative_to(plot.ROOT)): sha(p) for p in outputs}}
    (plot.OUT / (name + '_provenance.json')).write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
