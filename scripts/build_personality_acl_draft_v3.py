#!/usr/bin/env python3
"""Build an anonymous ACL-layout draft from the shared English manuscript.

This does not run experiments, add empirical sections, or certify submission
readiness. The official style is pinned and unmodified. All chapters remain
shared with the English reading draft; only the wrapper changes.
"""
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / 'paper/educational_personality_v3'
STYLE = PAPER / 'third_party/acl_style_files'
BUILD = PAPER / 'build/acl'
JOB = 'anonymous_acl_draft'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    receipt = json.loads((STYLE / 'provenance.json').read_text())
    for name, expected in receipt['files'].items():
        if sha(STYLE / name) != expected:
            raise ValueError('Pinned official template changed: ' + name)
    source = (PAPER / 'main.tex').read_text()
    title = re.search(r'\\title\{(.*?)\}\s*\\author', source, re.S)
    if not title or source.count(r'\begin{document}') != 1:
        raise ValueError('Cannot identify canonical title/document')
    body = source.split(r'\begin{document}', 1)[1]
    if body.count(r'\bibliographystyle{plainnat}') != 1:
        raise ValueError('Unexpected canonical bibliography wrapper')
    body = body.replace(r'\bibliographystyle{plainnat}', '')
    body = body.replace(r'\bibliography{references}', r'\FloatBarrier' + '\n' + r'\bibliography{references}')
    body = body.replace(r'\appendix', r'\clearpage' + '\n' + r'\appendix')
    wrapper = r'''\documentclass[11pt]{article}
\usepackage[review]{acl}
\usepackage{times,latexsym}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{amsmath,booktabs,graphicx,microtype,xurl,placeins}
% These floats contain diagrams/tables designed for the full text width.
% No official style file or page/font dimensions are modified.
\renewenvironment{figure}[1][t]{\begin{figure*}[#1]}{\end{figure*}}
\renewenvironment{table}[1][t]{\begin{table*}[#1]}{\end{table*}}
\title{TITLE}
\author{Anonymous}
\date{}
\hypersetup{pdfauthor={},pdfsubject={Educational personality research manuscript}}
\begin{document}
'''.replace('TITLE', title[1]) + body
    BUILD.mkdir(parents=True, exist_ok=True)
    tex = BUILD / 'main_acl.tex'
    tex.write_text(wrapper)
    env = os.environ.copy()
    for key in ['TEXINPUTS', 'BSTINPUTS']:
        env[key] = str(STYLE) + os.pathsep + env.get(key, '')
    env['BIBINPUTS'] = str(PAPER) + os.pathsep + env.get('BIBINPUTS', '')
    command = ['pdflatex', '-interaction=nonstopmode', '-halt-on-error', '-no-shell-escape',
               '-output-directory=build/acl', '-jobname=' + JOB, 'build/acl/main_acl.tex']
    steps = [('pass1', command), ('bibliography', ['bibtex', 'build/acl/' + JOB]),
             ('pass2', command), ('pass3', command)]
    for name, args in steps:
        with (BUILD / (name + '.log')).open('w') as log:
            run = subprocess.run(args, cwd=PAPER, env=env, stdout=log,
                                 stderr=subprocess.STDOUT, timeout=180)
        if run.returncode:
            raise RuntimeError('ACL draft build failed: ' + name)
    # Two-column lineno references can need an extra pass even after BibTeX
    # citations have resolved. Require the auxiliary references to stabilize.
    reference_warning = r'Package lineno Warning: Line number reference failed|Rerun to get cross-references right|Label\(s\) may have changed'
    for pass_number in range(4, 9):
        before = sha(BUILD / (JOB + '.aux'))
        with (BUILD / f'pass{pass_number}.log').open('w') as log:
            subprocess.run(command, cwd=PAPER, env=env, stdout=log,
                           stderr=subprocess.STDOUT, check=True, timeout=180)
        latest_log = (BUILD / (JOB + '.log')).read_text()
        if before == sha(BUILD / (JOB + '.aux')) and not re.search(reference_warning, latest_log):
            break
    else:
        raise ValueError('LaTeX line-number/cross-reference state did not stabilize')
    pdf = BUILD / (JOB + '.pdf')
    subprocess.run(['pdftotext', '-layout', str(pdf), str(BUILD / (JOB + '.txt'))], check=True)
    extracted = (BUILD / (JOB + '.txt')).read_text()
    if 'Educational Personalities?' not in extracted:
        raise ValueError('Manuscript title missing from extracted PDF')
    log = (BUILD / (JOB + '.log')).read_text()
    fatal = re.findall(r'^.*(?:Missing character|Citation .+ undefined|There were undefined references|multiply defined).*$', log, re.M)
    if fatal:
        raise ValueError('Unresolved reference/glyph warning: ' + '; '.join(fatal))
    info = subprocess.check_output(['pdfinfo', str(pdf)], text=True)
    fonts = subprocess.check_output(['pdffonts', str(pdf)], text=True)
    (BUILD / 'pdfinfo.txt').write_text(info)
    (BUILD / 'pdffonts.txt').write_text(fonts)
    font_rows = [line for line in fonts.splitlines()[2:] if line.strip()]
    font_flags = [re.search(r'\s+(yes|no)\s+(yes|no)\s+(yes|no)\s+\d+\s+\d+\s*$', line) for line in font_rows]
    if not font_flags or any(not match or match[1] != 'yes' for match in font_flags):
        raise ValueError('Could not verify embedded fonts')
    if not re.search(r'Page size:\s+595\.27\d* x 841\.89\d* pts', info):
        raise ValueError('Unexpected page size; requires A4')
    sources = [PAPER / 'main.tex', PAPER / 'references.bib',
               *sorted((PAPER / 'sections').glob('*.tex')),
               *sorted((PAPER / 'figures').glob('*.pdf')),
               *sorted(STYLE.iterdir()), tex, Path(__file__).resolve()]
    result = {'built_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'status': 'Anonymous ACL-layout PDF built; scientific and visual review recorded separately',
              'template_commit': receipt['commit'], 'official_style_files_modified': False,
              'shared_chapter_sources': True, 'build_certifies_scientific_completion': False,
              'empirical_sections_present': all((PAPER / 'sections' / (name + '.tex')).is_file()
                                                for name in ['abstract', 'results', 'discussion', 'conclusion']),
              'visual_inspection_required': True, 'fonts_embedded': True, 'a4_page_size': True,
              'line_number_and_cross_references_stable': True, 'latex_passes': pass_number,
              'pages': int(re.search(r'Pages:\s+(\d+)', info)[1]),
              'overfull_warnings': re.findall(r'^.*Overfull.*$', log, re.M),
              'source_sha256': {str(p.relative_to(ROOT)): sha(p) for p in sources},
              'pdf_sha256': sha(pdf)}
    (BUILD / 'build_provenance.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({key: value for key, value in result.items() if key != 'source_sha256'}, indent=2))


if __name__ == '__main__':
    main()
