"""Protect archive grouping against ID collisions and prompt-boundary mistakes."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from reconstruct_archive_tutor_inputs_v4 import assign_source_groups, method_digest, problem_from_conversation, reference_status


def test_shared_question_groups_distinct_dialogues_across_tasks():
    rows = [{'material_id': 'a:c0', 'problem': 'Solve x + 1 = 2.', 'conversation': 'one'},
            {'material_id': 'b:c7', 'problem': 'Solve  x + 1 = 2.\n', 'conversation': 'two'},
            {'material_id': 'c:c0', 'problem': 'Solve y + 2 = 4.', 'conversation': 'three'}]
    edges = assign_source_groups(rows)
    assert rows[0]['source_group'] == rows[1]['source_group'] != rows[2]['source_group']
    assert edges[0]['evidence'] == 'exact_normalized_question'


def test_empty_questions_do_not_group_and_math_case_is_preserved():
    rows = [{'material_id': str(i), 'problem': problem, 'conversation': str(i)}
            for i, problem in enumerate(['', '', 'Find A.', 'Find a.'])]
    assert assign_source_groups(rows) == []
    assert len({r['source_group'] for r in rows}) == 4


def test_nonbreaking_space_speaker_boundary_excludes_student_answer():
    text = 'Tutor: Hi. The question is: Solve 2x = 8.\n\xa0Student: x = 7.\n\xa0Tutor: Try again.'
    problem, boundary = problem_from_conversation(text)
    assert problem == 'Solve 2x = 8.' and boundary == 'explicit_first_turn_question_marker'
    assert problem_from_conversation('Tutor: Hello.\nStudent: Help.')[0] == ''


def test_ast_audit_distinguishes_prompt_change_from_line_number_change():
    original = 'class Adapter:\n    def load_items(self):\n        return "Tutor"\n'
    same = '# comment\n\n' + original
    changed = original.replace('Tutor', 'Examiner')
    assert method_digest(original, 'Adapter', 'load_items') == method_digest(same, 'Adapter', 'load_items')
    assert method_digest(original, 'Adapter', 'load_items') != method_digest(changed, 'Adapter', 'load_items')


def test_nonempty_placeholder_is_not_a_reference_solution():
    assert reference_status(' N/A ') == 'placeholder'
    assert reference_status('Not Available') == 'placeholder'
    assert reference_status('') == 'absent'
    assert reference_status('x = 4') == 'provided_unvalidated'
