# Computational Tools

## Previous Iteration Workspace
- URL: https://github.com/Hypogenic-AI/math-distillation-d448-claude
- Purpose: Contains the v1 predictor implementation, rule analysis, evaluation scripts, and 6.6KB cheatsheet
- Location: code/math-distillation-d448-claude/
- Key scripts:
  - `src/final_predictor.py` — V3 predictor with 7-stage decision procedure (17.3KB)
  - `src/analyze_rules.py` — Rule extraction from implication matrix
  - `src/analyze_deep.py` — Form/signature analysis
  - `src/evaluate_final.py` — Evaluation harness
  - `results/cheatsheet.txt` — 6.6KB final cheatsheet (primary deliverable of v1)
- Notes: Achieves 87.4% on normal, 63.8% on hard1, 54.5% on hard2, 71.8% on hard3
