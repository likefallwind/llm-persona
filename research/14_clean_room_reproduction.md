# Fresh-checkout reproduction audit

Audit date: 2026-08-19 (Asia/Shanghai)  
Frozen result commit: `f495256`  
Source branch: `agent/semantic-result-freeze-v2`

## Scope and terminology

This audit used a newly cloned checkout in
`/tmp/llm-persona-cleanroom.biVsRP/repo`.  It reused the machine's already
installed Python interpreter and packages.  It is therefore a **fresh-checkout
reproduction**, not evidence of a fresh or dependency-isolated environment.
No private upstream corpus and no live semantic annotation stream were copied
into the checkout.

## Checks and observed results

The following public-package gates were executed from the fresh checkout:

| Gate | Result |
|---|---:|
| Unit tests | 10/10 passed |
| Registered claims | 51/51 matched frozen artifacts |
| Git-eligible privacy audit | 128/128 paths passed |
| Paper figure rebuild | passed |
| Reproducibility-manifest path/hash verification | 182/182 matched |
| Worktree after checks | clean |

The test suite includes the executable semantic decision hierarchy, semantic
completion/stream recovery, and manifest eligibility logic.  The claim verifier
checks the exact values used in the manuscript; it does not regenerate the
private upstream model responses.  The manifest check confirms each declared
Git-eligible path existed and matched its stored SHA-256.

## Boundary of the result

This audit establishes that a clean checkout can verify the frozen public
analysis package and rebuild its paper figures with the dependencies already on
this machine.  It does not establish:

- provider-side response regeneration, because seeds, prompt versions, and most
  generation settings were not retained;
- installation from a lockfile into an empty environment;
- reproduction of private-corpus analyses without the frozen derived artifacts;
  or
- portability to another operating system or TeX distribution.

The ACL submission-package branch adds a separately pinned style-file build. A
new dependency runner can verify the frozen public package, but full cross-machine
recomputation remains impossible without the private upstream inputs described
above.

## Independent dependency-runner verification

Draft PR #3 triggered GitHub Actions run
[`32257044437`](https://github.com/likefallwind/llm-persona/actions/runs/32257044437)
at submission-package commit `d7b7bec`. GitHub provisioned a new Ubuntu runner,
checked out the commit, configured Python 3.13, and installed the exact versions
in `requirements.txt`. The requirements are version-pinned but do not include
package hashes.

The independent runner passed Python/shell syntax, 10/10 tests, 51/51 registered
claims, public artifact privacy structure, deterministic figure rebuilding, and
a final clean-worktree check. It had no private upstream corpus or ignored live
annotation JSONL, so this is dependency-isolated verification of the frozen
public package, not a rerun of private-input analysis or provider generation.
