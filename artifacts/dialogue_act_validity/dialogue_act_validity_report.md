# Human-labelled dialogue-act validity

This analysis uses MathDial's existing human teacher-move labels and a conventional character TF-IDF linear classifier. No LLM judge and no new human annotation is used. Generated response text is represented only by hashes and predicted labels in the saved artifacts.

## Problem-grouped classifier validation

| classifier_variant   |   human_teacher_turns |   unique_problems |   accuracy |   balanced_accuracy |   macro_f1 |
|:---------------------|----------------------:|------------------:|-----------:|--------------------:|-----------:|
| char_svm             |                 18541 |              1111 |      0.562 |               0.564 |      0.559 |
| word_svm             |                 18541 |              1111 |      0.568 |               0.565 |      0.565 |
| hybrid_svm           |                 18541 |              1111 |      0.574 |               0.571 |      0.571 |

| classifier_variant   | label   |   precision |   recall |   f1-score |   support |
|:---------------------|:--------|------------:|---------:|-----------:|----------:|
| char_svm             | probing |       0.390 |    0.400 |      0.395 |  4236.000 |
| char_svm             | focus   |       0.552 |    0.514 |      0.532 |  6789.000 |
| char_svm             | telling |       0.501 |    0.523 |      0.512 |  3086.000 |
| char_svm             | generic |       0.778 |    0.817 |      0.797 |  4430.000 |
| word_svm             | probing |       0.395 |    0.405 |      0.400 |  4236.000 |
| word_svm             | focus   |       0.547 |    0.542 |      0.545 |  6789.000 |
| word_svm             | telling |       0.508 |    0.495 |      0.502 |  3086.000 |
| word_svm             | generic |       0.809 |    0.816 |      0.812 |  4430.000 |
| hybrid_svm           | probing |       0.397 |    0.404 |      0.401 |  4236.000 |
| hybrid_svm           | focus   |       0.551 |    0.546 |      0.548 |  6789.000 |
| hybrid_svm           | telling |       0.535 |    0.517 |      0.526 |  3086.000 |
| hybrid_svm           | generic |       0.803 |    0.819 |      0.811 |  4430.000 |

All turns sharing a MathDial problem ID remain in the same fold, so the score does not rely on seeing another conversation about the same math problem.

## Bridge target coverage

| benchmark                       |   ambiguous |   bridge_direct |   exact_human_lookup |   unmatched |
|:--------------------------------|------------:|----------------:|---------------------:|------------:|
| mathtutorbench_pedagogy         |           2 |               0 |                 1004 |         144 |
| mathtutorbench_pedagogy_hard    |           0 |             265 |                    1 |          61 |
| mathtutorbench_scaffolding      |           2 |               0 |                 1004 |         144 |
| mathtutorbench_scaffolding_hard |           0 |             265 |                    1 |          61 |

`exact_human_lookup` means the held-out teacher response text maps to one unambiguous human label in the original MathDial release. `bridge_direct` uses the label retained in the bridge file. Ambiguous and unmatched targets are excluded before model outcomes are examined.

## Objective action match by model and prompt

| classifier_variant   | family   | arm      | model                |   count |   mean |
|:---------------------|:---------|:---------|:---------------------|--------:|-------:|
| char_svm             | hard     | generic  | deepseek-v4-flash    |     266 |  0.147 |
| char_svm             | hard     | generic  | deepseek-v4-pro      |     266 |  0.184 |
| char_svm             | hard     | generic  | doubao-seed-2.0-lite |     266 |  0.222 |
| char_svm             | hard     | generic  | doubao-seed-2.0-pro  |     266 |  0.165 |
| char_svm             | hard     | generic  | glm-5.2              |     266 |  0.301 |
| char_svm             | hard     | generic  | minimax-m2.7         |     266 |  0.117 |
| char_svm             | hard     | generic  | minimax-m3           |     266 |  0.165 |
| char_svm             | hard     | generic  | qwen3.5-4b           |     266 |  0.192 |
| char_svm             | hard     | generic  | qwen3.8-27b          |     266 |  0.132 |
| char_svm             | hard     | pedagogy | deepseek-v4-flash    |     266 |  0.335 |
| char_svm             | hard     | pedagogy | deepseek-v4-pro      |     266 |  0.410 |
| char_svm             | hard     | pedagogy | doubao-seed-2.0-lite |     266 |  0.350 |
| char_svm             | hard     | pedagogy | doubao-seed-2.0-pro  |     266 |  0.331 |
| char_svm             | hard     | pedagogy | glm-5.2              |     266 |  0.429 |
| char_svm             | hard     | pedagogy | minimax-m2.7         |     266 |  0.368 |
| char_svm             | hard     | pedagogy | minimax-m3           |     266 |  0.425 |
| char_svm             | hard     | pedagogy | qwen3.5-4b           |     266 |  0.286 |
| char_svm             | hard     | pedagogy | qwen3.8-27b          |     266 |  0.308 |
| char_svm             | standard | generic  | deepseek-v4-flash    |    1004 |  0.315 |
| char_svm             | standard | generic  | deepseek-v4-pro      |    1004 |  0.380 |
| char_svm             | standard | generic  | doubao-seed-2.0-lite |    1004 |  0.377 |
| char_svm             | standard | generic  | doubao-seed-2.0-pro  |    1004 |  0.375 |
| char_svm             | standard | generic  | glm-5.2              |    1004 |  0.426 |
| char_svm             | standard | generic  | minimax-m2.7         |    1004 |  0.265 |
| char_svm             | standard | generic  | minimax-m3           |    1004 |  0.308 |
| char_svm             | standard | generic  | qwen3.5-4b           |    1004 |  0.343 |
| char_svm             | standard | generic  | qwen3.8-27b          |    1004 |  0.256 |
| char_svm             | standard | pedagogy | deepseek-v4-flash    |    1004 |  0.429 |
| char_svm             | standard | pedagogy | deepseek-v4-pro      |    1004 |  0.480 |
| char_svm             | standard | pedagogy | doubao-seed-2.0-lite |    1004 |  0.436 |
| char_svm             | standard | pedagogy | doubao-seed-2.0-pro  |    1004 |  0.451 |
| char_svm             | standard | pedagogy | glm-5.2              |    1004 |  0.466 |
| char_svm             | standard | pedagogy | minimax-m2.7         |    1004 |  0.433 |
| char_svm             | standard | pedagogy | minimax-m3           |    1004 |  0.467 |
| char_svm             | standard | pedagogy | qwen3.5-4b           |    1004 |  0.435 |
| char_svm             | standard | pedagogy | qwen3.8-27b          |    1004 |  0.434 |
| hybrid_svm           | hard     | generic  | deepseek-v4-flash    |     266 |  0.143 |
| hybrid_svm           | hard     | generic  | deepseek-v4-pro      |     266 |  0.162 |
| hybrid_svm           | hard     | generic  | doubao-seed-2.0-lite |     266 |  0.165 |
| hybrid_svm           | hard     | generic  | doubao-seed-2.0-pro  |     266 |  0.162 |
| hybrid_svm           | hard     | generic  | glm-5.2              |     266 |  0.278 |
| hybrid_svm           | hard     | generic  | minimax-m2.7         |     266 |  0.109 |
| hybrid_svm           | hard     | generic  | minimax-m3           |     266 |  0.150 |
| hybrid_svm           | hard     | generic  | qwen3.5-4b           |     266 |  0.169 |
| hybrid_svm           | hard     | generic  | qwen3.8-27b          |     266 |  0.165 |
| hybrid_svm           | hard     | pedagogy | deepseek-v4-flash    |     266 |  0.308 |
| hybrid_svm           | hard     | pedagogy | deepseek-v4-pro      |     266 |  0.391 |
| hybrid_svm           | hard     | pedagogy | doubao-seed-2.0-lite |     266 |  0.289 |
| hybrid_svm           | hard     | pedagogy | doubao-seed-2.0-pro  |     266 |  0.323 |
| hybrid_svm           | hard     | pedagogy | glm-5.2              |     266 |  0.436 |
| hybrid_svm           | hard     | pedagogy | minimax-m2.7         |     266 |  0.301 |
| hybrid_svm           | hard     | pedagogy | minimax-m3           |     266 |  0.410 |
| hybrid_svm           | hard     | pedagogy | qwen3.5-4b           |     266 |  0.289 |
| hybrid_svm           | hard     | pedagogy | qwen3.8-27b          |     266 |  0.274 |
| hybrid_svm           | standard | generic  | deepseek-v4-flash    |    1004 |  0.352 |
| hybrid_svm           | standard | generic  | deepseek-v4-pro      |    1004 |  0.372 |
| hybrid_svm           | standard | generic  | doubao-seed-2.0-lite |    1004 |  0.363 |
| hybrid_svm           | standard | generic  | doubao-seed-2.0-pro  |    1004 |  0.336 |
| hybrid_svm           | standard | generic  | glm-5.2              |    1004 |  0.408 |
| hybrid_svm           | standard | generic  | minimax-m2.7         |    1004 |  0.261 |
| hybrid_svm           | standard | generic  | minimax-m3           |    1004 |  0.318 |
| hybrid_svm           | standard | generic  | qwen3.5-4b           |    1004 |  0.320 |
| hybrid_svm           | standard | generic  | qwen3.8-27b          |    1004 |  0.289 |
| hybrid_svm           | standard | pedagogy | deepseek-v4-flash    |    1004 |  0.447 |
| hybrid_svm           | standard | pedagogy | deepseek-v4-pro      |    1004 |  0.466 |
| hybrid_svm           | standard | pedagogy | doubao-seed-2.0-lite |    1004 |  0.442 |
| hybrid_svm           | standard | pedagogy | doubao-seed-2.0-pro  |    1004 |  0.449 |
| hybrid_svm           | standard | pedagogy | glm-5.2              |    1004 |  0.470 |
| hybrid_svm           | standard | pedagogy | minimax-m2.7         |    1004 |  0.445 |
| hybrid_svm           | standard | pedagogy | minimax-m3           |    1004 |  0.456 |
| hybrid_svm           | standard | pedagogy | qwen3.5-4b           |    1004 |  0.429 |
| hybrid_svm           | standard | pedagogy | qwen3.8-27b          |    1004 |  0.436 |
| word_svm             | hard     | generic  | deepseek-v4-flash    |     266 |  0.162 |
| word_svm             | hard     | generic  | deepseek-v4-pro      |     266 |  0.203 |
| word_svm             | hard     | generic  | doubao-seed-2.0-lite |     266 |  0.150 |
| word_svm             | hard     | generic  | doubao-seed-2.0-pro  |     266 |  0.188 |
| word_svm             | hard     | generic  | glm-5.2              |     266 |  0.267 |
| word_svm             | hard     | generic  | minimax-m2.7         |     266 |  0.128 |
| word_svm             | hard     | generic  | minimax-m3           |     266 |  0.188 |
| word_svm             | hard     | generic  | qwen3.5-4b           |     266 |  0.147 |
| word_svm             | hard     | generic  | qwen3.8-27b          |     266 |  0.195 |
| word_svm             | hard     | pedagogy | deepseek-v4-flash    |     266 |  0.327 |
| word_svm             | hard     | pedagogy | deepseek-v4-pro      |     266 |  0.353 |
| word_svm             | hard     | pedagogy | doubao-seed-2.0-lite |     266 |  0.248 |
| word_svm             | hard     | pedagogy | doubao-seed-2.0-pro  |     266 |  0.338 |
| word_svm             | hard     | pedagogy | glm-5.2              |     266 |  0.395 |
| word_svm             | hard     | pedagogy | minimax-m2.7         |     266 |  0.271 |
| word_svm             | hard     | pedagogy | minimax-m3           |     266 |  0.372 |
| word_svm             | hard     | pedagogy | qwen3.5-4b           |     266 |  0.305 |
| word_svm             | hard     | pedagogy | qwen3.8-27b          |     266 |  0.323 |
| word_svm             | standard | generic  | deepseek-v4-flash    |    1004 |  0.368 |
| word_svm             | standard | generic  | deepseek-v4-pro      |    1004 |  0.396 |
| word_svm             | standard | generic  | doubao-seed-2.0-lite |    1004 |  0.387 |
| word_svm             | standard | generic  | doubao-seed-2.0-pro  |    1004 |  0.359 |
| word_svm             | standard | generic  | glm-5.2              |    1004 |  0.412 |
| word_svm             | standard | generic  | minimax-m2.7         |    1004 |  0.296 |
| word_svm             | standard | generic  | minimax-m3           |    1004 |  0.332 |
| word_svm             | standard | generic  | qwen3.5-4b           |    1004 |  0.311 |
| word_svm             | standard | generic  | qwen3.8-27b          |    1004 |  0.332 |
| word_svm             | standard | pedagogy | deepseek-v4-flash    |    1004 |  0.442 |
| word_svm             | standard | pedagogy | deepseek-v4-pro      |    1004 |  0.469 |
| word_svm             | standard | pedagogy | doubao-seed-2.0-lite |    1004 |  0.440 |
| word_svm             | standard | pedagogy | doubao-seed-2.0-pro  |    1004 |  0.445 |
| word_svm             | standard | pedagogy | glm-5.2              |    1004 |  0.479 |
| word_svm             | standard | pedagogy | minimax-m2.7         |    1004 |  0.445 |
| word_svm             | standard | pedagogy | minimax-m3           |    1004 |  0.443 |
| word_svm             | standard | pedagogy | qwen3.5-4b           |    1004 |  0.425 |
| word_svm             | standard | pedagogy | qwen3.8-27b          |    1004 |  0.417 |

## Cross-classifier directional robustness

| classifier_variant   | family   |   model_count |   positive_models |   minimum_delta |   mean_delta |   maximum_delta |
|:---------------------|:---------|--------------:|------------------:|----------------:|-------------:|----------------:|
| char_svm             | hard     |             9 |                 9 |           0.094 |        0.180 |           0.259 |
| char_svm             | standard |             9 |                 9 |           0.040 |        0.110 |           0.178 |
| hybrid_svm           | hard     |             9 |                 9 |           0.109 |        0.169 |           0.259 |
| hybrid_svm           | standard |             9 |                 9 |           0.062 |        0.114 |           0.184 |
| word_svm             | hard     |             9 |                 9 |           0.098 |        0.145 |           0.184 |
| word_svm             | standard |             9 |                 9 |           0.053 |        0.091 |           0.149 |

All 54 classifier × difficulty × model prompt contrasts are positive if `positive_models` equals 9 in every row.

## Paired prompt effect on matching the human next action

| classifier_variant   | family   | model                |   n_pairs |   generic_match |   pedagogy_match |   mean_delta |   bootstrap_ci_low |   bootstrap_ci_high |   improved_pairs |   worsened_pairs |   mcnemar_exact_p |
|:---------------------|:---------|:---------------------|----------:|----------------:|-----------------:|-------------:|-------------------:|--------------------:|-----------------:|-----------------:|------------------:|
| char_svm             | hard     | deepseek-v4-flash    |       266 |           0.147 |            0.335 |        0.188 |              0.124 |               0.256 |               72 |               22 |             0.000 |
| char_svm             | hard     | deepseek-v4-pro      |       266 |           0.184 |            0.410 |        0.226 |              0.162 |               0.293 |               77 |               17 |             0.000 |
| char_svm             | hard     | doubao-seed-2.0-lite |       266 |           0.222 |            0.350 |        0.128 |              0.060 |               0.195 |               62 |               28 |             0.000 |
| char_svm             | hard     | doubao-seed-2.0-pro  |       266 |           0.165 |            0.331 |        0.165 |              0.098 |               0.233 |               68 |               24 |             0.000 |
| char_svm             | hard     | glm-5.2              |       266 |           0.301 |            0.429 |        0.128 |              0.064 |               0.195 |               60 |               26 |             0.000 |
| char_svm             | hard     | minimax-m2.7         |       266 |           0.117 |            0.368 |        0.252 |              0.184 |               0.323 |               84 |               17 |             0.000 |
| char_svm             | hard     | minimax-m3           |       266 |           0.165 |            0.425 |        0.259 |              0.188 |               0.331 |               88 |               19 |             0.000 |
| char_svm             | hard     | qwen3.5-4b           |       266 |           0.192 |            0.286 |        0.094 |              0.030 |               0.158 |               52 |               27 |             0.007 |
| char_svm             | hard     | qwen3.8-27b          |       266 |           0.132 |            0.308 |        0.177 |              0.113 |               0.241 |               65 |               18 |             0.000 |
| char_svm             | standard | deepseek-v4-flash    |      1004 |           0.315 |            0.429 |        0.115 |              0.077 |               0.152 |              256 |              141 |             0.000 |
| char_svm             | standard | deepseek-v4-pro      |      1004 |           0.380 |            0.480 |        0.100 |              0.063 |               0.136 |              239 |              139 |             0.000 |
| char_svm             | standard | doubao-seed-2.0-lite |      1004 |           0.377 |            0.436 |        0.059 |              0.022 |               0.096 |              204 |              145 |             0.002 |
| char_svm             | standard | doubao-seed-2.0-pro  |      1004 |           0.375 |            0.451 |        0.076 |              0.039 |               0.112 |              214 |              138 |             0.000 |
| char_svm             | standard | glm-5.2              |      1004 |           0.426 |            0.466 |        0.040 |              0.003 |               0.078 |              210 |              170 |             0.045 |
| char_svm             | standard | minimax-m2.7         |      1004 |           0.265 |            0.433 |        0.168 |              0.131 |               0.207 |              283 |              114 |             0.000 |
| char_svm             | standard | minimax-m3           |      1004 |           0.308 |            0.467 |        0.159 |              0.121 |               0.197 |              284 |              124 |             0.000 |
| char_svm             | standard | qwen3.5-4b           |      1004 |           0.343 |            0.435 |        0.093 |              0.053 |               0.132 |              243 |              150 |             0.000 |
| char_svm             | standard | qwen3.8-27b          |      1004 |           0.256 |            0.434 |        0.178 |              0.141 |               0.215 |              281 |              102 |             0.000 |
| hybrid_svm           | hard     | deepseek-v4-flash    |       266 |           0.143 |            0.308 |        0.165 |              0.105 |               0.226 |               60 |               16 |             0.000 |
| hybrid_svm           | hard     | deepseek-v4-pro      |       266 |           0.162 |            0.391 |        0.229 |              0.162 |               0.301 |               82 |               21 |             0.000 |
| hybrid_svm           | hard     | doubao-seed-2.0-lite |       266 |           0.165 |            0.289 |        0.124 |              0.068 |               0.184 |               50 |               17 |             0.000 |
| hybrid_svm           | hard     | doubao-seed-2.0-pro  |       266 |           0.162 |            0.323 |        0.162 |              0.086 |               0.229 |               72 |               29 |             0.000 |
| hybrid_svm           | hard     | glm-5.2              |       266 |           0.278 |            0.436 |        0.158 |              0.086 |               0.229 |               71 |               29 |             0.000 |
| hybrid_svm           | hard     | minimax-m2.7         |       266 |           0.109 |            0.301 |        0.192 |              0.128 |               0.256 |               69 |               18 |             0.000 |
| hybrid_svm           | hard     | minimax-m3           |       266 |           0.150 |            0.410 |        0.259 |              0.188 |               0.331 |               92 |               23 |             0.000 |
| hybrid_svm           | hard     | qwen3.5-4b           |       266 |           0.169 |            0.289 |        0.120 |              0.049 |               0.188 |               65 |               33 |             0.002 |
| hybrid_svm           | hard     | qwen3.8-27b          |       266 |           0.165 |            0.274 |        0.109 |              0.045 |               0.173 |               56 |               27 |             0.002 |
| hybrid_svm           | standard | deepseek-v4-flash    |      1004 |           0.352 |            0.447 |        0.096 |              0.058 |               0.133 |              244 |              148 |             0.000 |
| hybrid_svm           | standard | deepseek-v4-pro      |      1004 |           0.372 |            0.466 |        0.095 |              0.058 |               0.132 |              231 |              136 |             0.000 |
| hybrid_svm           | standard | doubao-seed-2.0-lite |      1004 |           0.363 |            0.442 |        0.080 |              0.043 |               0.118 |              228 |              148 |             0.000 |
| hybrid_svm           | standard | doubao-seed-2.0-pro  |      1004 |           0.336 |            0.449 |        0.114 |              0.077 |               0.150 |              251 |              137 |             0.000 |
| hybrid_svm           | standard | glm-5.2              |      1004 |           0.408 |            0.470 |        0.062 |              0.024 |               0.099 |              226 |              164 |             0.002 |
| hybrid_svm           | standard | minimax-m2.7         |      1004 |           0.261 |            0.445 |        0.184 |              0.146 |               0.222 |              297 |              112 |             0.000 |
| hybrid_svm           | standard | minimax-m3           |      1004 |           0.318 |            0.456 |        0.138 |              0.098 |               0.180 |              286 |              147 |             0.000 |
| hybrid_svm           | standard | qwen3.5-4b           |      1004 |           0.320 |            0.429 |        0.110 |              0.072 |               0.147 |              253 |              143 |             0.000 |
| hybrid_svm           | standard | qwen3.8-27b          |      1004 |           0.289 |            0.436 |        0.147 |              0.110 |               0.184 |              265 |              117 |             0.000 |
| word_svm             | hard     | deepseek-v4-flash    |       266 |           0.162 |            0.327 |        0.165 |              0.098 |               0.229 |               65 |               21 |             0.000 |
| word_svm             | hard     | deepseek-v4-pro      |       266 |           0.203 |            0.353 |        0.150 |              0.086 |               0.218 |               63 |               23 |             0.000 |
| word_svm             | hard     | doubao-seed-2.0-lite |       266 |           0.150 |            0.248 |        0.098 |              0.038 |               0.158 |               48 |               22 |             0.003 |
| word_svm             | hard     | doubao-seed-2.0-pro  |       266 |           0.188 |            0.338 |        0.150 |              0.083 |               0.218 |               67 |               27 |             0.000 |
| word_svm             | hard     | glm-5.2              |       266 |           0.267 |            0.395 |        0.128 |              0.056 |               0.203 |               70 |               36 |             0.001 |
| word_svm             | hard     | minimax-m2.7         |       266 |           0.128 |            0.271 |        0.143 |              0.083 |               0.207 |               59 |               21 |             0.000 |
| word_svm             | hard     | minimax-m3           |       266 |           0.188 |            0.372 |        0.184 |              0.113 |               0.256 |               78 |               29 |             0.000 |
| word_svm             | hard     | qwen3.5-4b           |       266 |           0.147 |            0.305 |        0.158 |              0.086 |               0.229 |               69 |               27 |             0.000 |
| word_svm             | hard     | qwen3.8-27b          |       266 |           0.195 |            0.323 |        0.128 |              0.060 |               0.195 |               60 |               26 |             0.000 |
| word_svm             | standard | deepseek-v4-flash    |      1004 |           0.368 |            0.442 |        0.075 |              0.037 |               0.113 |              227 |              152 |             0.000 |
| word_svm             | standard | deepseek-v4-pro      |      1004 |           0.396 |            0.469 |        0.073 |              0.037 |               0.109 |              212 |              139 |             0.000 |
| word_svm             | standard | doubao-seed-2.0-lite |      1004 |           0.387 |            0.440 |        0.053 |              0.016 |               0.091 |              202 |              149 |             0.005 |
| word_svm             | standard | doubao-seed-2.0-pro  |      1004 |           0.359 |            0.445 |        0.087 |              0.050 |               0.123 |              225 |              138 |             0.000 |
| word_svm             | standard | glm-5.2              |      1004 |           0.412 |            0.479 |        0.067 |              0.028 |               0.106 |              225 |              158 |             0.001 |
| word_svm             | standard | minimax-m2.7         |      1004 |           0.296 |            0.445 |        0.149 |              0.112 |               0.186 |              266 |              116 |             0.000 |
| word_svm             | standard | minimax-m3           |      1004 |           0.332 |            0.443 |        0.112 |              0.074 |               0.151 |              251 |              139 |             0.000 |
| word_svm             | standard | qwen3.5-4b           |      1004 |           0.311 |            0.425 |        0.115 |              0.076 |               0.153 |              260 |              145 |             0.000 |
| word_svm             | standard | qwen3.8-27b          |      1004 |           0.332 |            0.417 |        0.086 |              0.046 |               0.125 |              241 |              155 |             0.000 |

| classifier_variant   | family   |   generic_match |   pedagogy_match |   mean_delta |
|:---------------------|:---------|----------------:|-----------------:|-------------:|
| char_svm             | hard     |           0.180 |            0.360 |        0.180 |
| char_svm             | standard |           0.338 |            0.448 |        0.110 |
| hybrid_svm           | hard     |           0.167 |            0.336 |        0.169 |
| hybrid_svm           | standard |           0.335 |            0.449 |        0.114 |
| word_svm             | hard     |           0.181 |            0.326 |        0.145 |
| word_svm             | standard |           0.355 |            0.445 |        0.091 |

## Match by human target action

| classifier_variant   | family   | arm      | target_act   |   count |   mean |
|:---------------------|:---------|:---------|:-------------|--------:|-------:|
| char_svm             | hard     | generic  | generic      |       9 |  0.111 |
| char_svm             | hard     | generic  | probing      |    2385 |  0.181 |
| char_svm             | hard     | pedagogy | generic      |       9 |  0.222 |
| char_svm             | hard     | pedagogy | probing      |    2385 |  0.361 |
| char_svm             | standard | generic  | focus        |    4221 |  0.462 |
| char_svm             | standard | generic  | generic      |     693 |  0.153 |
| char_svm             | standard | generic  | probing      |    3690 |  0.223 |
| char_svm             | standard | generic  | telling      |     432 |  0.414 |
| char_svm             | standard | pedagogy | focus        |    4221 |  0.542 |
| char_svm             | standard | pedagogy | generic      |     693 |  0.179 |
| char_svm             | standard | pedagogy | probing      |    3690 |  0.429 |
| char_svm             | standard | pedagogy | telling      |     432 |  0.125 |
| hybrid_svm           | hard     | generic  | generic      |       9 |  0.111 |
| hybrid_svm           | hard     | generic  | probing      |    2385 |  0.167 |
| hybrid_svm           | hard     | pedagogy | generic      |       9 |  0.111 |
| hybrid_svm           | hard     | pedagogy | probing      |    2385 |  0.337 |
| hybrid_svm           | standard | generic  | focus        |    4221 |  0.464 |
| hybrid_svm           | standard | generic  | generic      |     693 |  0.150 |
| hybrid_svm           | standard | generic  | probing      |    3690 |  0.211 |
| hybrid_svm           | standard | generic  | telling      |     432 |  0.442 |
| hybrid_svm           | standard | pedagogy | focus        |    4221 |  0.579 |
| hybrid_svm           | standard | pedagogy | generic      |     693 |  0.177 |
| hybrid_svm           | standard | pedagogy | probing      |    3690 |  0.390 |
| hybrid_svm           | standard | pedagogy | telling      |     432 |  0.125 |
| word_svm             | hard     | generic  | generic      |       9 |  0.111 |
| word_svm             | hard     | generic  | probing      |    2385 |  0.181 |
| word_svm             | hard     | pedagogy | generic      |       9 |  0.000 |
| word_svm             | hard     | pedagogy | probing      |    2385 |  0.327 |
| word_svm             | standard | generic  | focus        |    4221 |  0.499 |
| word_svm             | standard | generic  | generic      |     693 |  0.136 |
| word_svm             | standard | generic  | probing      |    3690 |  0.227 |
| word_svm             | standard | generic  | telling      |     432 |  0.394 |
| word_svm             | standard | pedagogy | focus        |    4221 |  0.588 |
| word_svm             | standard | pedagogy | generic      |     693 |  0.180 |
| word_svm             | standard | pedagogy | probing      |    3690 |  0.371 |
| word_svm             | standard | pedagogy | telling      |     432 |  0.111 |

## How the prompt changes the inferred action distribution

| classifier_variant   | family   | predicted_act   |   generic |   pedagogy |   pedagogy_minus_generic |
|:---------------------|:---------|:----------------|----------:|-----------:|-------------------------:|
| char_svm             | hard     | focus           |     0.374 |      0.479 |                    0.104 |
| char_svm             | hard     | generic         |     0.033 |      0.064 |                    0.032 |
| char_svm             | hard     | probing         |     0.181 |      0.360 |                    0.179 |
| char_svm             | hard     | telling         |     0.412 |      0.097 |                   -0.315 |
| char_svm             | standard | focus           |     0.417 |      0.481 |                    0.064 |
| char_svm             | standard | generic         |     0.056 |      0.085 |                    0.029 |
| char_svm             | standard | probing         |     0.173 |      0.360 |                    0.187 |
| char_svm             | standard | telling         |     0.355 |      0.075 |                   -0.280 |
| hybrid_svm           | hard     | focus           |     0.406 |      0.515 |                    0.109 |
| hybrid_svm           | hard     | generic         |     0.038 |      0.055 |                    0.017 |
| hybrid_svm           | hard     | probing         |     0.167 |      0.337 |                    0.170 |
| hybrid_svm           | hard     | telling         |     0.389 |      0.094 |                   -0.296 |
| hybrid_svm           | standard | focus           |     0.434 |      0.525 |                    0.091 |
| hybrid_svm           | standard | generic         |     0.061 |      0.082 |                    0.022 |
| hybrid_svm           | standard | probing         |     0.162 |      0.327 |                    0.165 |
| hybrid_svm           | standard | telling         |     0.344 |      0.066 |                   -0.278 |
| word_svm             | hard     | focus           |     0.423 |      0.533 |                    0.110 |
| word_svm             | hard     | generic         |     0.033 |      0.045 |                    0.012 |
| word_svm             | hard     | probing         |     0.182 |      0.328 |                    0.147 |
| word_svm             | hard     | telling         |     0.362 |      0.094 |                   -0.269 |
| word_svm             | standard | focus           |     0.469 |      0.538 |                    0.070 |
| word_svm             | standard | generic         |     0.055 |      0.084 |                    0.029 |
| word_svm             | standard | probing         |     0.180 |      0.315 |                    0.135 |
| word_svm             | standard | telling         |     0.296 |      0.063 |                   -0.234 |

## Interpretation boundary

This is independent of LLM-as-judge preferences, but it measures action-type agreement with the observed human teacher, not student learning or full response quality. The classifier's grouped cross-validation score bounds how literally generated-label matches should be interpreted.
