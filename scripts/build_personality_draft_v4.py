"""Build the single English draft with the preserved ACL renderer."""
import hashlib
import json
import re
import subprocess
from pathlib import Path

import build_personality_acl_draft_v3 as acl
import build_personality_evidence_inventory_v4 as evidence

PAPER = Path(__file__).resolve().parents[1] / 'paper/educational_personality_v4'


def main():
    evidence.main()
    acl.PAPER = PAPER
    acl.BUILD = PAPER / 'build/acl'
    acl.STYLE = PAPER / 'third_party/acl_style_files'
    acl.main()
    path = acl.BUILD / 'build_provenance.json'
    receipt = json.loads(path.read_text())
    receipt['v4_wrapper_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    aux = (acl.BUILD / (acl.JOB + '.aux')).read_text()
    end = re.search(r'\\newlabel\{sec:main-end\}\{\{[^}]*\}\{(\d+)\}', aux)
    if not end or int(end[1]) > 8:
        raise ValueError('Main content including conclusion must finish within eight pages')
    main = (PAPER / 'main.tex').read_text()
    sequence = ['\\input{sections/conclusion}', '\\label{sec:main-end}',
                '\\input{sections/limitations}', '\\input{sections/ethics}',
                '\\bibliography{references}', '\\appendix']
    positions = [main.index(token) for token in sequence]
    if positions != sorted(positions):
        raise ValueError('Invalid ARR post-conclusion section order')
    text = (acl.BUILD / (acl.JOB + '.txt')).read_text()
    info = (acl.BUILD / 'pdfinfo.txt').read_text()
    fonts = (acl.BUILD / 'pdffonts.txt').read_text()
    urls = subprocess.check_output(['pdfinfo', '-url', str(acl.BUILD / (acl.JOB + '.pdf'))], text=True)
    identity = r'(?i)likefallwind|/home/|/Users/|file://|github\.com/likefallwind|dropbox\.com|drive\.google\.com'
    if re.search(identity, text + info + urls):
        raise ValueError('Author/local-path or tracking-link pattern found in PDF')
    if re.search(r'^Author:[ \t]*\S', info, re.M) or 'Type 3' in fonts:
        raise ValueError('Nonanonymous author metadata or Type 3 fonts')
    if receipt['overfull_warnings']:
        raise ValueError('Overfull boxes require layout review before submission')
    abstract = (PAPER / 'sections/abstract.tex').read_text()
    abstract = re.sub(r'\\(?:begin|end)\{abstract\}', '', abstract)
    abstract = re.sub(r'\\[a-zA-Z]+', '', abstract).replace('{', '').replace('}', '')
    abstract_words = len(abstract.split())
    if abstract_words > 200:
        raise ValueError(f'ACL abstract exceeds 200 words: {abstract_words}')
    receipt['abstract_words'] = abstract_words
    receipt['target_venue'] = 'NAACL 2027 via ARR October 2026, long paper'
    receipt['main_content_end_page'] = int(end[1])
    receipt['main_content_page_limit'] = 8
    receipt['post_conclusion_order_valid'] = True
    receipt['pdf_known_identity_and_tracking_patterns_absent'] = True
    receipt['no_type_3_fonts'] = True
    receipt['author_declarations_and_external_submission_complete'] = False
    receipt['checkpoint'] = 'single-paper behavioral findings, stability, control, and educational implications integrated'
    receipt['manuscript_language'] = 'en'
    receipt['canonical_pdf'] = 'build/acl/anonymous_acl_draft.pdf'
    receipt['archive_original_complete_coding_gate_passed'] = False
    receipt['archive_identified_majority_analysis_complete'] = True
    receipt['scientific_quality_goal_complete'] = False
    path.write_text(json.dumps(receipt, indent=2) + '\n')


if __name__ == '__main__':
    main()
