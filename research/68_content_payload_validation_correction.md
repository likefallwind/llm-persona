# Content-review payload serialization correction

Recorded on 2026-09-07 after the first content-review pass and before any
content-subset results or repair requests. This corrects a validator defect;
it does not change the measurement rubric or add a repair allowance.

All 2,584 first-pass requests returned records. The runner accepted `--temperature
0` through argparse's float conversion and transmitted JSON `temperature: 0.0`.
The frozen content validator instead reconstructed the payload using the integer
literal `0`. Their JSON encodings have different hashes, even though their
numerical sampling parameter is identical. The original diagnostic consequently
rejected every record and the seed step stopped because it found no reusable
record. Original diagnostics, logs and controller terminal state remain intact.

A direct audit of all 2,584 records establishes:

- all prompt hashes match the frozen input messages;
- all response hashes match the persisted response string;
- all payload hashes match reconstruction using the recorded float `0.0`;
- none matches the validator's integer serialization;
- the original unchanged content parser accepts 2,577 responses and rejects
  seven: two explanations exceed its allowed structure/length and five contain
  invalid evidence-line references.

The separate adapter `scripts/recover_personality_content_validation_v3.py`
checks that the actual temperature is numeric zero, reconstructs the exact
payload using its recorded representation, and retains every other identity,
sampling, integrity, completion and semantic-structure check. It rejects
Boolean sampling values, altered budgets and changed hashes. The original
content scripts, request runner, policy, freeze and original records are not
edited. An integration test uses the actual runner with a mocked transport to
reproduce the defect and verify the correction; tests also retain rejection of
invalid evidence and tampered identities, parameters and hashes.

All 2,577 valid records are reused regardless of verdict or reviewer agreement.
Only the seven original structural failures are eligible for the two remaining
repair passes already authorized by the frozen policy. Each uses the identical
input, reviewer, temperature, 16,384-token ceiling, 360-second client timeout
and two-attempt runner limit. A second repair pass, if necessary, includes only
remaining invalid records. No new tutor response, content criterion, hypothesis
test or training fit is introduced. Provider concurrency remains MiniMax4 and
Gateway8 shared across this runner.

The adapter preserves the stopped controller state before writing a successor
state, requires exclusive access to the content pipeline lock, and refuses to
restart an already-started recovery automatically. Corrected diagnostics record
the adapter and amendment hashes. Complete measurement selection and the
original frozen content analysis are written only after all 2,584 reviews pass.
The supplemental content analysis remains distinct from the unchanged primary
results. This implementation correction and its timing will be disclosed in
the manuscript and final resource/reproducibility record.
