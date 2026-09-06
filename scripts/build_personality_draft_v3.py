#!/usr/bin/env python3
"""Build explicitly unfinished English/Chinese reading drafts with local TeX.

The Chinese source uses a deliberately small Markdown subset: headings,
paragraphs, numbered/bulleted lists, bold spans, inline code, BibTeX citations,
and local PDF figures. Unsupported
tables or fenced code fail instead of silently disappearing from the PDF.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / 'paper/educational_personality_v3'
BUILD = PAPER / 'build'


def escape(value):
    special = {'\\': r'\textbackslash{}', '&': r'\&', '%': r'\%', '$': r'\$',
               '#': r'\#', '_': r'\_', '{': r'\{', '}': r'\}',
               '~': r'\textasciitilde{}', '^': r'\textasciicircum{}'}
    return ''.join(special.get(char, char) for char in value)


def inline(value):
    tokens = re.split(r'(\*\*[^*]+\*\*|`[^`]+`|\[@[a-zA-Z0-9_-]+(?:;\s*@[a-zA-Z0-9_-]+)*\])', value)
    parts = []
    for token in tokens:
        if token.startswith('**') and token.endswith('**'):
            parts.append(r'\textbf{' + escape(token[2:-2]) + '}')
        elif token.startswith('`') and token.endswith('`'):
            parts.append(r'\texttt{' + escape(token[1:-1]) + '}')
        elif token.startswith('[@'):
            keys = re.findall(r'@([a-zA-Z0-9_-]+)', token)
            parts.append(r'\citep{' + ','.join(keys) + '}')
        else:
            parts.append(escape(token))
    return ''.join(parts)


def chinese_tex(markdown):
    lines = markdown.splitlines()
    if not lines or not lines[0].startswith('# '):
        raise ValueError('Chinese manuscript must begin with its title')
    body, opened = [], None
    for line in lines[1:]:
        if line.startswith('```') or line.startswith('|'):
            raise ValueError('Extend the renderer before adding tables or code fences')
        kind = 'itemize' if line.startswith('- ') else 'enumerate' if re.match(r'^\d+\. ', line) else None
        if opened and kind != opened:
            body.append(r'\end{' + opened + '}')
            opened = None
        if kind and opened != kind:
            body.append(r'\begin{' + kind + '}')
            opened = kind
        picture = re.fullmatch(r'!\[([^\]]+)\]\((figures/[a-zA-Z0-9_-]+\.pdf)\)', line)
        if picture:
            if not (PAPER / picture[2]).is_file():
                raise ValueError('Missing Chinese manuscript figure')
            body.extend([r'\begin{figure}[htbp]\centering',
                         r'\includegraphics[width=\linewidth]{' + picture[2] + '}',
                         r'\caption{' + inline(picture[1]) + '}', r'\end{figure}'])
        elif kind:
            body.append(r'\item ' + inline(re.sub(r'^(?:- |\d+\. )', '', line)))
        elif line.startswith('### '):
            body.append(r'\subsection{' + inline(line[4:]) + '}')
        elif line.startswith('## '):
            body.append(r'\section{' + inline(line[3:]) + '}')
        elif line.startswith('#'):
            raise ValueError('Unsupported heading depth')
        else:
            body.append(inline(line))
    if opened:
        body.append(r'\end{' + opened + '}')
    return '\n'.join([
        r'\documentclass[11pt,a4paper,UTF8]{ctexart}',
        r'\usepackage[margin=2.2cm]{geometry}',
        r'\usepackage{amsmath,graphicx,booktabs}',
        r'\usepackage[section]{placeins}',
        r'\usepackage[round,authoryear]{natbib}',
        r'\usepackage[colorlinks=true,allcolors=blue]{hyperref}',
        r'\setlength{\emergencystretch}{3em}',
        r'\setlength{\parskip}{0.25em}',
        r'\title{' + inline(lines[0][2:]) + '}',
        r'\author{匿名工作稿中文阅读版}\date{}',
        r'\begin{document}\maketitle',
        *body, r'\bibliographystyle{plainnat}', r'\bibliography{references}', r'\end{document}', '',
    ])


def run(name, command):
    env = os.environ.copy()
    env['BIBINPUTS'] = str(PAPER) + os.pathsep + env.get('BIBINPUTS', '')
    with (BUILD / (name + '.log')).open('w') as log:
        completed = subprocess.run(command, cwd=PAPER, env=env, stdout=log,
                                   stderr=subprocess.STDOUT, timeout=180)
    if completed.returncode:
        raise RuntimeError(name + ' failed; inspect ' + str(BUILD / (name + '.log')))


def main():
    BUILD.mkdir(parents=True, exist_ok=True)
    zh = chinese_tex((PAPER / 'manuscript_zh.md').read_text())
    (BUILD / 'reading_zh.tex').write_text(zh)
    for language, engine, source in [('en', 'pdflatex', 'main.tex'), ('zh', 'xelatex', 'build/reading_zh.tex')]:
        job = 'working_draft_' + language
        command = [engine, '-interaction=nonstopmode', '-halt-on-error', '-no-shell-escape',
                   '-output-directory=build', '-jobname=' + job, source]
        run(job + '_pass1', command)
        run(job + '_bibliography', ['bibtex', 'build/' + job])
        run(job + '_pass2', command)
        run(job + '_pass3', command)
        run(job + '_text', ['pdftotext', '-layout', 'build/' + job + '.pdf', 'build/' + job + '.txt'])
        text = (BUILD / (job + '.txt')).read_text()
        if ('Incomplete working draft' if language == 'en' else '工作稿') not in text:
            raise ValueError('Draft-status label missing from extracted PDF')
        if re.search(r'Citation .+ undefined|There were undefined references', (BUILD / (job + '.log')).read_text()):
            raise ValueError('Unresolved citation or reference in ' + language)
    sources = [PAPER / 'main.tex', PAPER / 'manuscript_zh.md', PAPER / 'references.bib',
               *sorted((PAPER / 'sections').glob('*.tex')), PAPER / 'figures/measurement_pilot.pdf',
               PAPER / 'figures/study_design.pdf', Path(__file__).resolve()]
    result = {'status': 'reading drafts built; scientific results and submission checks incomplete',
              'source_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
              'pdf_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(BUILD.glob('working_draft_*.pdf'))},
              'visual_inspection_required': True, 'paper_complete': False}
    (BUILD / 'build_provenance.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
