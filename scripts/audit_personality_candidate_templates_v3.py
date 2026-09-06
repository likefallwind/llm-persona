#!/usr/bin/env python3
"""Audit candidate content before freezing a prospective study.

Checks arithmetic keys and declared dependence; it does not certify all semantic
content, learner realism, or experimental power.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import re
import unicodedata


SOLVERS = {
    'ratio_partition': lambda x: x['total']*x['blue_parts']/(x['blue_parts']+x['red_parts']),
    'discount_price': lambda x: x['price']*(1-x['discount_percent']/100),
    'rectangle_width': lambda x: x['perimeter']/2-x['length'],
    'arithmetic_mean': lambda x: sum(x['values'])/len(x['values']),
    'single_draw_probability': lambda x: x['favorable']/(x['favorable']+x['other']),
    'speed_units': lambda x: x['km_per_hour']*1000/3600,
    'arithmetic_sequence': lambda x: x['first']+(x['n']-1)*x['difference'],
    'map_scale': lambda x: x['plan_cm']*x['scale']/100,
    'circuit_current': lambda x: x['voltage']/x['resistance'],
    'net_force': lambda x: x['mass']*x['acceleration'],
    'thermal_energy': lambda x: x['mass']*x['specific_heat']*x['temperature_change'],
    'wave_speed': lambda x: x['frequency']*x['wavelength'],
    'simple_inheritance': lambda x: x['p_first_a']*x['p_second_a'],
    'conservation_of_mass': lambda x: x['carbon_mass']+x['oxygen_mass'],
    'classifier_precision': lambda x: x['true_positives']/(x['true_positives']+x['false_positives']),
    'expected_points': lambda x: x['probability']*x['high']+(1-x['probability'])*x['low'],
    'weighted_mean': lambda x: sum(s*w for s,w in zip(x['scores'],x['weights']))/sum(x['weights']),
}


def normalize(text, remove_numbers=False):
    text = unicodedata.normalize('NFKC', text).casefold()
    if remove_numbers:
        text = re.sub(r'\d+(?:\.\d+)?', '<number>', text)
    return re.sub(r'\s+', ' ', text).strip()


def audit(bank_path, pilot_path, output):
    bank = json.loads(bank_path.read_text())
    rows = bank['templates']
    required = ['id', 'domain', 'source_family', 'question', 'target_resolution', 'reference',
                'incorrect_attempt', 'correct_partial_work']
    if len(rows) != len({r['id'] for r in rows}):
        raise ValueError('Duplicate template IDs')
    for row in rows:
        if any(not isinstance(row.get(key), str) or not row[key].strip() for key in required):
            raise ValueError('Missing candidate content: ' + str(row.get('id')))
        if row['incorrect_attempt'] == row['correct_partial_work']:
            raise ValueError('Learner states are identical')
    question_forms = defaultdict(list)
    families = defaultdict(list)
    numeric = []
    for row in rows:
        question_forms[normalize(row['question'], True)].append(row['id'])
        families[row['source_family']].append({'template': row['id'], 'domain': row['domain']})
        check = row.get('numeric_check')
        if check is not None:
            if row['id'] not in SOLVERS:
                raise ValueError('Missing arithmetic verifier')
            computed = SOLVERS[row['id']](check)
            if not math.isclose(computed, check['expected'], rel_tol=1e-10, abs_tol=1e-10):
                raise ValueError('Incorrect arithmetic key: ' + row['id'])
            numeric.append({'template': row['id'], 'computed': computed, 'expected': check['expected'], 'pass': True})
    duplicates = [ids for ids in question_forms.values() if len(ids) > 1]
    if duplicates:
        raise ValueError('Question templates differ only in numbers: ' + str(duplicates))
    pilot = [json.loads(line) for line in pilot_path.read_text().splitlines() if line.strip()]
    # Existing pilot messages put the question before the first blank line.
    pilot_questions = {normalize(row['messages'][-1]['content'].split('\n\n', 1)[0], True) for row in pilot}
    overlap = [row['id'] for row in rows if normalize(row['question'], True) in pilot_questions]
    if overlap:
        raise ValueError('Exact numeric-normalized pilot question overlap: ' + str(overlap))
    report = {'status': 'candidate-content checks passed; not a formal-design freeze',
              'templates': len(rows), 'declared_source_families': len(families),
              'domains': dict(Counter(row['domain'] for row in rows)),
              'source_families_with_multiple_templates': {k:v for k,v in families.items() if len(v)>1},
              'numeric_checks': numeric, 'numeric_normalized_pilot_overlap': overlap,
              'question_sha256': {row['id']: hashlib.sha256(normalize(row['question']).encode()).hexdigest() for row in rows},
              'bank_sha256': hashlib.sha256(bank_path.read_bytes()).hexdigest(),
              'pilot_scenarios_sha256': hashlib.sha256(pilot_path.read_bytes()).hexdigest(),
              'limitations': ['Arithmetic is checked from structured quantities, not automatically parsed from prose.',
                             'No overlap here means no exact numeric-normalized text match, not semantic or pretraining independence.',
                             'Paired learner-state plausibility and reference prose still require separate content review.',
                             'Every declared source family must remain in one train/test partition, including cross-domain families.',
                             'No new model generations have been run on this bank.',
                             'Four domains with eight templates each do not establish representativeness of all education.']}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ['question_sha256','numeric_checks']}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bank', type=Path, default=Path('data/educational_personality_candidate_templates_v3.json'))
    parser.add_argument('--pilot', type=Path, default=Path('artifacts/educational_personality_v2/prospective_pilot/scenarios.jsonl'))
    parser.add_argument('--output', type=Path, default=Path('artifacts/educational_personality_v2/formal_design/candidate_content_audit.json'))
    args = parser.parse_args()
    audit(args.bank, args.pilot, args.output)
