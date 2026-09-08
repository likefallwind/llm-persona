"""Build the integrated draft using the preserved, validated v3 renderers."""
import hashlib
import json
from pathlib import Path

import build_personality_draft_v3 as reading
import build_personality_acl_draft_v3 as acl

PAPER = Path(__file__).resolve().parents[1] / 'paper/educational_personality_v4'


def main():
    reading.PAPER = PAPER
    reading.BUILD = PAPER / 'build'
    reading.main()
    acl.PAPER = PAPER
    acl.BUILD = PAPER / 'build/acl'
    acl.STYLE = PAPER / 'third_party/acl_style_files'
    acl.main()
    for path in (reading.BUILD / 'build_provenance.json', acl.BUILD / 'build_provenance.json'):
        receipt = json.loads(path.read_text())
        receipt['v4_wrapper_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        receipt['checkpoint'] = 'cue-transfer integrated; archive behavior validation unexecuted'
        receipt['scientific_quality_goal_complete'] = False
        path.write_text(json.dumps(receipt, indent=2) + '\n')


if __name__ == '__main__':
    main()
