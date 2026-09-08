import json
from pathlib import Path
import sys
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from recover_personality_cue_json_v4 import close_outer_object


def test_only_outer_brace_is_added_without_changing_values():
    text = '{"events":{"x":{"present":1,"evidence_lines":[1]}}'
    repaired, codes = close_outer_object(text, 'A visible line.', ['x'])
    assert repaired == text + '}' and codes == {'x': 1}


@pytest.mark.parametrize('text', [
    '{"events":{"x":{"present":1,"evidence_lines":[1]}}}',
    '{"events":{"x":{"present":1,"evidence_lines":[1]}',
    '{"events":{"x":{"present":1 "evidence_lines":[1]}}',
    '{"events":{"x":{"present":1,"evidence_lines":[99]}}',
    '{"events":{"x":{"present":1,"evidence_lines":[1]},"x":{"present":0,"evidence_lines":[]}}',
])
def test_other_failures_or_valid_json_are_not_silently_accepted(text):
    with pytest.raises(ValueError):
        close_outer_object(text, 'A visible line.', ['x'])
