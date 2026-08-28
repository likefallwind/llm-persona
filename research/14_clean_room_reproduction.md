# Fresh-checkout reproduction audit

Snapshot: 2026-08-28. Status: **refresh required after the final commit**.

## What has been verified in the working checkout

The current release pipeline rebuilds every completed analysis available from
local governed inputs, verifies registered manuscript claims, runs the full test
suite, checks Git-eligible artifact privacy, rebuilds paper figures, regenerates
the SHA-256 manifest, and audits the anonymous ACL PDF. The general-personality
archive audit and affiliation pilot are now included in both the private-input
finalizer and public reproduction path.

The release no longer tracks the historical raw response/judge JSONL files or
the path-bearing semantic log that caused the repository-wide privacy gate to
fail. Those files remain local under existing ignore rules. Public affiliation
artifacts contain conditions, hashes, derived ratings, profiles, and decisions,
not raw provider or judge response text.

## Required final clean-room procedure

After committing the current manuscript and release artifacts:

1. clone that exact local commit into a new temporary directory;
2. install or reuse the pinned dependencies, explicitly recording which;
3. run the public reproduction command, tests, registered-claim verifier,
   privacy audit, manifest verifier, and ACL submission audit;
4. confirm that every generated public artifact leaves the checkout clean; and
5. record the commit, command outputs, dependency provenance, and any private
   input that was intentionally unavailable.

Until that refresh is recorded, prior clean-room and CI runs remain useful
historical evidence but do not certify the newly added affiliation artifacts or
the 2026-08-28 manuscript.

## Boundary

No clean-room run can recreate provider-side generations exactly: most archived
generation settings and all seed/prompt-version fields are absent, and deployed
aliases may drift. Reproduction therefore means recomputing public analyses from
frozen derived inputs and verifying their hashes and decisions; it does not mean
regenerating identical provider text or private learner histories.
