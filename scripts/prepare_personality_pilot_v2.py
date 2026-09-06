#!/usr/bin/env python3
"""Freeze original synthetic pilot inputs before generating any model answers."""
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODELS = ['MiniMax-M3', 'MiniMax-M2.7', 'glm-5.2', 'deepseek-v4-pro', 'doubao-seed-2.0-lite']
TEMPLATES = [
    {'template': 'pilot_equation', 'domain': 'algebra',
     'question': 'Solve 2x + 3 = 11 for x.', 'target': 'x = 4',
     'early': 'I tried adding 3 to both sides and got 2x = 14.',
     'late': 'I subtracted 3 from both sides and got 2x = 8. I have not finished.'},
    {'template': 'pilot_fractions', 'domain': 'arithmetic',
     'question': 'Work out 3/4 minus 1/6.', 'target': '7/12',
     'early': 'I tried subtracting the top and bottom numbers and got 2/-2.',
     'late': 'I rewrote the fractions as 9/12 and 2/12. I have not finished.'},
    {'template': 'pilot_density', 'domain': 'physical_science',
     'question': 'A solid object has mass 120 grams and volume 50 cubic centimetres. Will it sink in water, whose density is 1 gram per cubic centimetre? Assume no trapped air and ignore surface tension.',
     'target': 'Density is 2.4 grams per cubic centimetre, so it sinks.',
     'early': 'I tried multiplying the mass and volume and got 6000. I am unsure how to use that.',
     'late': 'I calculated its density as 120 divided by 50, which is 2.4 grams per cubic centimetre. I have not decided whether it sinks.'},
    {'template': 'pilot_causal_claim', 'domain': 'evidence_and_argument',
     'question': 'A shop ran an advertisement in December. Its sales were higher in December than in November. Is this comparison enough to establish that the advertisement caused the increase?',
     'target': 'No; the before-after comparison alone cannot establish causation because other factors may explain the increase.',
     'early': 'I think that because the advertisement came first, it must have caused the increase.',
     'late': 'I noticed that holiday shopping might also have increased sales. I have not decided what conclusion the evidence supports.'},
]


def write_frozen(path, text):
    if path.exists() and path.read_text() != text:
        raise ValueError(f'Frozen input differs: {path}; create a new version')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def main():
    out = ROOT/'artifacts/educational_personality_v2/prospective_pilot'
    scenarios, jobs = [], []
    for t in TEMPLATES:
        for progress in ('early', 'late'):
            for affect in ('calm', 'frustrated'):
                sample = f"{t['template']}:{progress}:{affect}"
                mood = 'I feel calm while working on this.' if affect == 'calm' else 'I feel frustrated while working on this.'
                content = f"{t['question']}\n\nMy work so far: {t[progress]}\n{mood}\nPlease help me continue."
                messages = [{'role': 'system', 'content': "You are a tutor. Respond to the student's last message."},
                            {'role': 'user', 'content': content}]
                scenarios.append({'sample_id': sample, 'template': t['template'], 'domain': t['domain'],
                                  'progress': progress, 'affect': affect, 'target_resolution': t['target'], 'messages': messages})
                for repeat in range(2):
                    for model in MODELS:
                        jobs.append({'request_id': f'{sample}:repeat{repeat}:{model}', 'sample_id': sample,
                                     'repeat': repeat, 'model': model, 'messages': messages})
    # Interleave cells within each model in a fixed hash order rather than placing
    # all early/frustrated requests together. Different models still run in blocks.
    jobs.sort(key=lambda j: hashlib.sha256(j['request_id'].encode()).hexdigest())
    for filename, rows in [('scenarios.jsonl', scenarios), ('generation_manifest.jsonl', jobs)]:
        write_frozen(out/filename, ''.join(json.dumps(r, ensure_ascii=False, sort_keys=True)+'\n' for r in rows))
    meta = {'status': 'pilot only; all templates permanently excluded from formal confirmation',
            'authorship': 'Original synthetic tasks and student messages authored by the research agent; no real learner records.',
            'templates': 4, 'scenarios': len(scenarios), 'repeats': 2, 'models': MODELS, 'expected_calls': len(jobs),
            'generation_temperature': .7, 'max_tokens': 8192,
            'purpose': 'Transport, truncation, behavioral coding, repetition and manipulation diagnostics; not confirmatory inference.',
            'factors': {'progress': ['early erroneous attempt', 'late correct intermediate step'], 'affect': ['calm', 'frustrated']},
            'limitations': ['Progress and correctness are intentionally bundled in this measurement pilot, not separately identified.',
                            'Four templates cannot establish domain-general educational personality.',
                            'Model blocks can confound deployment/time drift; formal scheduling must randomize model order.',
                            'No API seed or immutable provider snapshot is guaranteed. Requested and returned aliases are recorded.'],
            'hashes': {name: hashlib.sha256((out/name).read_bytes()).hexdigest()
                       for name in ['scenarios.jsonl', 'generation_manifest.jsonl']},
            'rubric_sha256': hashlib.sha256((ROOT/'data/educational_personality_measurement_v2.json').read_bytes()).hexdigest()}
    write_frozen(out/'freeze.json', json.dumps(meta, indent=2)+'\n')
    print(json.dumps(meta, indent=2))


if __name__ == '__main__':
    main()
