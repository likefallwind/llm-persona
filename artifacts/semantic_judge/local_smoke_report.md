# Local Ollama semantic-judge smoke test

All prompts were processed on `127.0.0.1`; no source text was sent externally.

| model | sample | prompt chars | elapsed seconds | valid JSON | confidence |
|---|---|---:|---:|---|---:|
| qwen3:8b | LongTutor | 40,539 | 322.2 | yes | 1 |
| qwen3:8b | MathTutorBench scaffolding | 4,435 | 43.8 | yes | 1 |
| llama3.1:8b | MathTutorBench scaffolding | 4,435 | 80.3 | yes | 1 |
| mistral-nemo:12b | MathTutorBench scaffolding | 4,435 | 143.1 | yes | 1 |

The structured-output path works, including a 28,573-token LongTutor prompt, but
all four annotations self-report minimum confidence.  The long Qwen annotation
assigns identical eight-dimensional profiles to five of six candidates, suggesting
poor discrimination.  A full 1,080-call local panel would also be impractical at
the observed throughput.  These models are therefore excluded as primary judges;
they may be used only for a small sensitivity audit if later evidence shows useful
agreement.  This is a measurement-quality decision, not a convenience substitution.
