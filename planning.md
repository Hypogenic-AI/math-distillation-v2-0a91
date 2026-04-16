# Research Plan: Mathematics Distillation Challenge v2

## Motivation & Novelty Assessment

### Why This Research Matters
The SAIR Mathematics Distillation Challenge tests whether mathematical reasoning can be compressed into a cheatsheet that helps an LLM solve equational implication problems. Improving hard3 accuracy directly impacts competition performance and demonstrates that systematic error analysis can improve rule-based mathematical reasoning systems.

### Gap in Existing Work
The previous iteration achieved ~90% on easy cases but only ~52.75% on hard3 (barely above the ~51.25% always-FALSE baseline). The rules were developed based on random samples and not stress-tested against adversarial cases.

### Our Novel Contribution
Systematic per-rule accuracy analysis across all difficulty splits, identifying and fixing rules with accuracy below 35% (essentially anti-correlated with truth). Key finding: several contradiction motifs and structural rules were worse than random on hard cases.

### Experiment Justification
- Experiment 1 (Evaluate baseline): Establishes ground truth per-rule accuracy across all splits
- Experiment 2 (Diagnose errors): Identifies specific features distinguishing TP from FP for each rule
- Experiment 3 (Fix rules): Targeted surgical fixes based on empirical evidence
- Experiment 4 (Add rules): New rules for uncovered cases (collapse lemmas, bare source v4+)

## Research Question
Can systematic error diagnosis and targeted rule improvements significantly improve hard3 accuracy on the SAIR equational implication task while maintaining performance on easier splits?

## Methodology
1. Implement cheatsheet as Python predictor
2. Evaluate on all 4 splits
3. Compute per-rule accuracy
4. For each problematic rule, find distinguishing features between TP and FP
5. Apply surgical fixes and test iteratively

## Success Criteria
- Hard3 accuracy > baseline 52.75% ✓ (achieved 63.5%)
- No severe regressions on other splits ✓ (normal +11.4, hard1 +8.7, hard2 -4.0)
- Cheatsheet under 10KB ✓ (7.8KB)
