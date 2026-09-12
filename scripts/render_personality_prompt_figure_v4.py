"""Keep the existing prompt-effect plot and use clearer axis wording."""
import hashlib
import json
from pathlib import Path

import pandas as pd
import render_personality_publication_figures_v3 as publication


def main():
    plot = publication.plot
    receipt = plot.BASE / 'confirmation_reporting/summary.json'
    report = json.loads(receipt.read_text())
    publication.verify_files(report['scripts'])
    publication.verify_files(report['report_hashes'])
    rates = plot.BASE / 'confirmation_analysis/paired_prompt_effects.csv'
    bounds = plot.BASE / 'confirmation_neutral_bounds/neutral_equivalence_interpretation.csv'
    out = plot.ROOT / 'paper/educational_personality_v4/figures'
    plot.configure()
    plot.plt.rcParams['font.size'] = 8.5
    fig = plot.prompt_figure(pd.read_csv(rates), pd.read_csv(bounds))
    publication.strip_figure_notes(fig)
    fig.set_size_inches(6.3, 4.7)
    for i, ax in enumerate(fig.axes):
        ax.set_title(publication.SHORT_EVENTS[i % 3] +
                     (' / neutral' if i < 3 else ' / instruction'), fontsize=8.5)
        ax.set_yticks(range(5), publication.SHORT_MODELS)
        ax.set_xticks([-1, -.5, 0, .5, 1])
        ax.set_xlabel('')
    fig.subplots_adjust(left=.11, right=.99, top=.83, bottom=.11,
                        hspace=.34, wspace=.16)
    fig.supxlabel('Change in action probability from the standard prompt',
                  fontsize=8.5, y=.02)
    for legend in fig.legends:
        legend.set_bbox_to_anchor((.55, .98))
        for label in legend.get_texts():
            label.set_fontsize(8.5)
    outputs = []
    for suffix in ['pdf', 'png', 'svg']:
        path = out / ('confirmation_prompt_changes_publication.' + suffix)
        fig.savefig(path, dpi=300, bbox_inches='tight', facecolor='white')
        if suffix == 'svg':
            path.write_text('\n'.join(line.rstrip() for line in path.read_text().splitlines()) + '\n')
        outputs.append(path)
    plot.plt.close(fig)
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    provenance = {
        'changes': ['Axis wording only; existing estimates and plotting layout retained'],
        'new_api_calls': 0,
        'new_estimates': 0,
        'source_sha256': {str(p.relative_to(plot.ROOT)): sha(p) for p in
                          [rates, bounds, receipt, Path(plot.__file__),
                           Path(publication.__file__), Path(__file__).resolve()]},
        'output_sha256': {str(p.relative_to(plot.ROOT)): sha(p) for p in outputs},
    }
    (out / 'prompt_figure_wording_provenance.json').write_text(
        json.dumps(provenance, indent=2) + '\n')
    print(json.dumps({'axis_wording_updated': True, 'new_estimates': 0}))


if __name__ == '__main__':
    main()
