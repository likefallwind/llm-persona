# One remaining transport failure after six-code budget amendment

The bounded six-code amendment completed on 2026-09-07 at 01:14:21 UTC with five
valid responses and one remaining failure. Request
`37540fcbc506f35f7359:glm-5.3` returned HTTP 502 twice, after 300.086 and 300.069
seconds. The local Gateway's loaded configuration has request_timeout=300;
its httpx client uses that value for upstream reads. The client-side 720-second
timeout therefore did not remove the proxy bottleneck. The failed response has
no token-usage record, so no claim is made about its upstream completion length.

This additional, explicitly recorded transport amendment retains the original
12,114 valid codes and the five valid expanded-budget codes. It permits only
the one remaining request at the same 32,768-token budget, temperature, model,
messages, rubric and parser, at most two new HTTP attempts. It does not reset
either previous repair allowance. Before it starts, verify no active Gateway
client connections, gracefully restart the same task-owned Gateway with
REQUEST_TIMEOUT=660, and retain all other loaded settings and the statistics
file. Client timeout remains 720 seconds; connect timeout and concurrency caps
are unchanged. Preserve old/new process identities, source hashes, terminal
states and a local health/model-route check without recording credentials.

The selected request belongs to the missing-information opportunity probe and
does not add a canonical prediction case. Selection is solely by observed
transport failure. No primary confirmation results have been computed when this
amendment is recorded. On success, the same separate-budget validator and exact
union check precede the unchanged primary and robustness scripts. All six-code
uncertainty checks recorded in research/64 remain required. If the new bounded
attempts fail, stop for a fresh review; there is no automatic further retry.
