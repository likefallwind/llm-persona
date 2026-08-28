# Fresh-checkout reproduction audit

Snapshot: 2026-08-28. Status: **fresh-checkout public-package audit passed**.

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

## Observed fresh-checkout result

Candidate commit `7d71f15` was cloned without hard links into a new temporary
directory. The audit reused the working machine's pinned virtual environment and
set `PYTHONDONTWRITEBYTECODE=1`; it was therefore checkout-isolated but not
dependency-isolated. No private upstream corpus or ignored raw response stream
was copied into the clone.

| Gate | Result |
|---|---:|
| Unit tests | 87/87 passed |
| Registered release claims | 123/123 passed |
| Git-eligible artifact privacy | 446/446 passed |
| Manifest paths and SHA-256 values | 647/647 passed |
| Anonymous ACL PDF audit | passed, 10 pages |
| Deterministic main-figure rebuild | passed |
| Worktree after all checks | clean |

The PDF audit confirms that content ends on page 8, later pages contain no main
content, author/title metadata are blank, all fonts are embedded and non-Type-3,
and no configured identity or local-home pattern is present.

## Boundary

No clean-room run can recreate provider-side generations exactly: most archived
generation settings and all seed/prompt-version fields are absent, and deployed
aliases may drift. Reproduction therefore means recomputing public analyses from
frozen derived inputs and verifying their hashes and decisions; it does not mean
regenerating identical provider text or private learner histories.
