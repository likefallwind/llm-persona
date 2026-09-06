#!/usr/bin/env python3
"""Attach reviewed current-adapter roles to the existing frozen archive census.

This does not reconstruct historical per-request prompts or score personality.
Counts retain the census's text-deduplication units, not generation events.
"""
import argparse
import ast
from collections import defaultdict
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CENSUS = ROOT / 'artifacts/research_reassessment_20260905/archive_census.json'

# Agent-reviewed task roles, anchored to adapter source rather than benchmark
# name tokens. 'Tutor response' still includes strong requested teaching policy.
ROLE_GROUPS = {
    'tutor_response': ['longtutor_teaching', 'mathtutorbench_scaffolding', 'mathtutorbench_pedagogy',
                       'mathtutorbench_scaffolding_hard', 'mathtutorbench_pedagogy_hard',
                       'bea2025_tutor', 'mrbench_tutor', 'tutorbench', 'mmtutorbench'],
    'constrained_question_generation': ['mathtutorbench_socratic'],
    'evaluation_output': ['asap_2', 'sas_bench', 'mrbench_judge', 'bea2025_judge',
                          'mathtutorbench_judge_calibration', 'mathtutorbench_solution_correctness',
                          'mathtutorbench_mistake_location'],
    'solution_repair': ['mathtutorbench_mistake_correction'],
    'test_or_option_answer': ['agieval', 'ceval', 'mmlu_pro', 'olympiadbench', 'k12bench',
                              'mathvista', 'k12vista', 'mathtutorbench_problem_solving',
                              'pedagogy_benchmark', 'eduguard_sata'],
    'metacognitive_problem_solving': ['p07_selfcheck', 'p08_abstention', 'p08_calibration'],
    'learner_history_or_diagnosis': ['longtutor_evidence', 'longtutor_diagnosis'],
    'knowledge_structure_reasoning': ['mooccube_prereq'],
    'mixed_educational_assistance': ['edubench', 'eduequity'],
    'safety_response': ['eduguard_adversarial', 'safe_child_llm'],
    'general_instruction_following': ['ifeval'],
}

NOTES = {
    'longtutor_teaching': 'Requests concise personalized scaffolding without revealing the full answer; not an unprompted default.',
    'mathtutorbench_scaffolding': 'Next tutor turn under a caring-teacher instruction; source overlap with other MathDial settings.',
    'mathtutorbench_pedagogy': 'Next tutor turn under explicit pedagogical instruction; do not pool as the same prompt as scaffolding.',
    'mathtutorbench_scaffolding_hard': 'Hard dialogue subset; source grouping required across standard/hard settings.',
    'mathtutorbench_pedagogy_hard': 'Hard dialogue subset with explicit pedagogy; prompt and source grouping both required.',
    'bea2025_tutor': 'Next math tutor turn; shared conversation sources with MRBench require grouping.',
    'mrbench_tutor': 'Next math tutor turn with guidance instruction; shared conversation sources with BEA require grouping.',
    'tutorbench': 'Three use cases have different requested actions; includes text and image inputs. Split use case and modality before behavior comparison.',
    'mmtutorbench': 'Image-dependent next-step tutoring with exactly three prescribed sections; text alone is insufficient to reconstruct input.',
    'mathtutorbench_socratic': 'Only a one-line question list is requested; other behaviors may lack expression opportunity.',
    'asap_2': 'Candidate model rates student essays; rubric/colleague prompt variants exist.',
    'sas_bench': 'Candidate model outputs overall and step scores plus error categories.',
    'mrbench_judge': 'Candidate model labels existing tutor replies; one reply is expanded across dimensions.',
    'bea2025_judge': 'Candidate model labels existing tutor replies; these are not that model tutoring.',
    'mathtutorbench_judge_calibration': 'Candidate model chooses between existing tutor replies; order swaps do not create new learner contexts.',
    'mathtutorbench_solution_correctness': 'Classifies student solution correctness; not a next tutor turn.',
    'mathtutorbench_mistake_location': 'Locates a wrong solution step; distinguish diagnosis from open tutoring.',
    'mathtutorbench_mistake_correction': 'Corrects the identified wrong step; action is assigned by the task.',
    'pedagogy_benchmark': 'Pedagogical knowledge multiple-choice exam; current auto mode can select prompt variant by model.',
    'eduguard_sata': 'Select-all-that-apply options; appended instruction requests letters only.',
    'longtutor_evidence': 'Answers factual questions about learner history; repeated queries share conversations.',
    'longtutor_diagnosis': 'Returns one diagnosis label; no open teaching action requested.',
    'mooccube_prereq': 'Chooses prerequisites or orders concepts; not a learner-facing tutor reply.',
    'edubench': 'Mixed IP/QG/TMG/PLS/PCC prompts; task-level partition needed rather than treating all outputs as tutoring.',
    'eduequity': 'Educational-assistant generation with task and demographic variants; paired inputs need reconstruction.',
    'eduguard_adversarial': 'Teacher persona plus adversarial student request; analyze separately from ordinary teaching.',
    'safe_child_llm': 'Age-framed adversarial assistance; safety response, not an ordinary tutoring sample.',
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def adapter_evidence(repo):
    evidence = {}
    folder = repo / 'scripts/eval/benchmarks'
    for path in sorted(folder.glob('*.py')):
        tree = ast.parse(path.read_text())
        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue
            values = {}
            for entry in node.body:
                if not isinstance(entry, ast.Assign) or len(entry.targets) != 1:
                    continue
                target = entry.targets[0]
                if isinstance(target, ast.Name) and target.id in {'name', 'title', 'description'}:
                    try:
                        values[target.id] = ast.literal_eval(entry.value)
                    except (ValueError, TypeError):
                        continue
            name = values.get('name')
            if isinstance(name, str):
                evidence[name] = {'adapter_path': str(path.relative_to(repo)), 'adapter_sha256': sha(path),
                                  'class_name': node.name, 'class_line': node.lineno,
                                  'title': values.get('title', ''), 'description': values.get('description', '')}
    path = repo / 'scripts/run_eduequity_generation.py'
    text = path.read_text()
    anchor = 'DEFAULT_SYSTEM_PROMPT = "You are a helpful educational assistant."'
    if anchor not in text:
        raise ValueError('EduEquity generation framing changed; review again')
    evidence['eduequity'] = {'adapter_path': str(path.relative_to(repo)), 'adapter_sha256': sha(path),
                             'class_name': 'generation script', 'class_line': text[:text.index(anchor)].count('\n') + 1,
                             'title': 'EduEquity educational-assistant generation', 'description': anchor}
    return evidence


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--benchmark-repo', type=Path, default=ROOT.parent / 'edubenchmark')
    ap.add_argument('--output', type=Path, default=ROOT / 'artifacts/educational_personality_v2/archive_roles')
    args = ap.parse_args()
    census = json.loads(CENSUS.read_text())
    legacy = json.loads((ROOT / 'data/benchmark_roles.json').read_text())
    legacy_roles = {name: group for group, members in legacy.items() if isinstance(members, dict) for name in members}
    roles = {}
    for group, benchmarks in ROLE_GROUPS.items():
        for name in benchmarks:
            if name in roles:
                raise ValueError('Duplicate role assignment: ' + name)
            roles[name] = group
    coverage = census['active_coverage']['per_benchmark']
    if set(coverage) != set(roles):
        raise ValueError('Census benchmark coverage changed; review added/removed roles')
    evidence = adapter_evidence(args.benchmark_repo)
    if not set(roles) <= set(evidence):
        raise ValueError('Missing source anchors: ' + str(set(roles) - set(evidence)))
    rows = []
    totals = defaultdict(lambda: {'benchmarks': 0, 'variant_preserving_records': 0, 'variant_agnostic_records': 0})
    for name in sorted(coverage):
        count = coverage[name]['distinct_response_texts']
        loose = census['variant_agnostic_text_coverage']['per_benchmark'][name]['distinct_response_texts']
        role = roles[name]
        row = {'benchmark': name, 'reviewed_current_role': role, 'variant_preserving_records': count,
               'variant_agnostic_records': loose, 'legacy_role_group': legacy_roles.get(name, 'unmapped'),
               'interpretation_note': NOTES.get(name, 'Task-assigned response; historical prompt and input reconstruction required.'),
               **evidence[name]}
        rows.append(row)
        totals[role]['benchmarks'] += 1
        totals[role]['variant_preserving_records'] += count
        totals[role]['variant_agnostic_records'] += loose
    if sum(r['variant_preserving_records'] for r in rows) != census['active_coverage']['distinct_response_texts']:
        raise ValueError('Role table does not conserve census total')
    if sum(r['variant_agnostic_records'] for r in rows) != census['variant_agnostic_text_coverage']['distinct_response_texts']:
        raise ValueError('Role table does not conserve variant-agnostic total')
    report = {'status': 'current-adapter role review of frozen census; historical request equivalence unverified',
              'census_generated_at': census['generated_at'], 'census_sha256': sha(CENSUS),
              'script_sha256': sha(Path(__file__)), 'benchmark_repo': str(args.benchmark_repo.resolve()),
              'legacy_role_map_sha256': sha(ROOT / 'data/benchmark_roles.json'),
              'role_totals': dict(totals), 'benchmarks': rows,
              'limitations': ['Counts are text-deduplicated model/item records, not independent calls or source contexts.',
                             'Current adapter contracts support role interpretation but do not attest to every historical request.',
                             'Tutor-role membership does not establish common prompts, neutral defaults, source independence, or valid personality labels.',
                             'Names absent from the legacy role map are not automatically unusable.',
                             'Mixed tasks, use cases, image inputs, and prompt variants require item-level reconstruction before pooling.',
                             'No raw response received new semantic coding in this role audit.']}
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / 'role_coverage.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    lines = ['# Archive coverage by reviewed current adapter role', '',
             'Counts refer to the frozen census, not independent tutor generations. Historical per-request roles and prompts remain to be reconstructed.', '',
             '| Role | Benchmarks | Variant-preserving records | Variant-agnostic records |',
             '|---|---:|---:|---:|']
    for group, counts in sorted(totals.items(), key=lambda x: -x[1]['variant_preserving_records']):
        lines.append(f"| {group} | {counts['benchmarks']} | {counts['variant_preserving_records']:,} | {counts['variant_agnostic_records']:,} |")
    lines += ['', 'The JSON records every benchmark, source class/line, adapter hash, role rationale, and old-map coverage.', '']
    (args.output / 'role_coverage.md').write_text('\n'.join(lines))
    print(json.dumps({'benchmarks': len(rows), 'role_totals': dict(totals)}, indent=2))


if __name__ == '__main__':
    main()
