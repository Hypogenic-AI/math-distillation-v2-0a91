# Resources Catalog

## Summary
This document catalogs all resources gathered for improving hard3 performance in the Mathematics Distillation Challenge v2.

## Papers
Total papers downloaded: 2

| Title | Authors | Year | File | Key Results |
|-------|---------|------|------|-------------|
| The Equational Theories Project | Bolan, Tao, et al. | 2025 | papers/tao_et_al_2025_etp.pdf | Complete 22M implication graph; 524 counterexample magmas; CNN 99.7% accuracy |
| The Latent Space of Equational Theories | Berlioz, Mellies | 2026 | papers/berlioz_mellies_2026_latent_space.pdf | Stone pairings; latent space via PCA; implication flows; contrarian edges = hard implications |

Note: Both papers were already deeply analyzed in the previous iteration. The previous iteration's repo contains chunked versions and detailed notes.

## Prior Results Catalog

| Result | Source | Statement Summary | Used For |
|--------|--------|-------------------|----------|
| 37.12% base rate | ETP | 8,178,279 of 22,033,636 implications are true | Default probability when undecided |
| 524 critical magmas | ETP | 524 distinct size-2-to-4 magmas refute 96.3% of false implications | Counterexample search |
| 1415 equivalence classes | ETP | 4694 laws form 1415 equivalence classes | Transitivity exploitation |
| Absorbing => everything | ETP/v1 | Absorbing equations (x = f(y,z,...), x not in f) imply all equations | 100% reliable rule |
| General =/=> Standard | ETP/v1 | General-form equations never imply standard-form equations | 100% reliable rule |
| Signature direction | v1 | If sig(E1)[0] > 0 and sig(E2)[0] = 0 (with ops), then FALSE | 99.97% reliable rule |
| Variable count heuristic | v1 | More variables = stronger constraint; nvd correlates with implication probability | Primary heuristic (but insufficient for hard3) |
| Stone pairing clustering | Berlioz & Mellies | Equivalent theories cluster tightly in Stone pairing space | Potential new feature |
| Implication flows | Berlioz & Mellies | Implications flow radially in latent space; contrarian edges are hard | Explains why hard3 is hard |

## Dataset Splits

| Split | Examples | TRUE | FALSE | V1 Accuracy |
|-------|----------|------|-------|-------------|
| normal | 1,000 | 500 | 500 | 87.4% |
| hard1 | 69 | 24 | 45 | 63.8% |
| hard2 | 200 | 100 | 100 | 54.5% |
| hard3 | 400 | 195 | 205 | 71.8% |

Downloaded to: `data_normal.jsonl`, `data_hard1.jsonl`, `data_hard2.jsonl`, `data_hard3.jsonl`

## V1 Error Analysis on Hard3

| Error Type | Count | Root Cause |
|------------|-------|------------|
| False negatives at p=0.5 | 31 | nvd=+1 lhs_var->lhs_var maps to exactly 0.50; BFS rewriting fails |
| False negatives at p=0.25-0.4 | 41 | nvd=0 heuristic predicts ~0.34 but implication is true; no computational signal |
| False negatives at p=0.1-0.25 | 18 | nvd=-1 heuristic too low; structurally simpler E1 implies more complex E2 |
| False negatives at p<=0.02 | 5+3 | Variable count heuristic confidently wrong (e.g., 2-var => 4-var) |
| False positives at p=0.51-0.62 | 15 | Marginal predictions just above threshold |

**Key finding:** 98 of 113 errors are false negatives. The predictor is too conservative — it defaults to FALSE too aggressively when BFS rewriting and counterexample search fail to reach a decision.

## Computational Tools

| Tool | Purpose | Location | Notes |
|------|---------|----------|-------|
| V1 Predictor | 7-stage decision procedure | code/math-distillation-d448-claude/src/final_predictor.py | Baseline implementation |
| V1 Cheatsheet | 6.6KB text for LLM evaluation | code/math-distillation-d448-claude/results/cheatsheet.txt | Current best submission |
| pypdf | PDF reading | pip package | For reading papers |
| datasets (HuggingFace) | Loading competition data | pip package | For loading splits |

## Resource Gathering Notes

### Search Strategy
- Used paper-finder with diligent mode for "equational theories magmas implications"
- Searched arXiv directly for the two key papers (Berlioz & Mellies, ETP project)
- Cloned the previous iteration's workspace as specified in the research brief
- Downloaded all four competition data splits from HuggingFace

### Selection Criteria
- Focused on the two papers directly relevant to the equational theories implication problem
- The broader universal algebra literature (varieties, lattices of equational theories) was searched but is less directly applicable to the distillation challenge, which is primarily a computational/heuristic problem rather than a theoretical one

### Challenges Encountered
- The competition website (competition.sair.foundation) returned 403 errors; competition rules were reconstructed from the previous iteration's documentation
- The full implication matrix (22M entries) is referenced in the previous iteration but the data files are not in the cloned repo (they were at a different path on the original machine)

## Recommendations for Proof Construction

1. **Primary strategy: Improve the Python predictor** — The main improvements should come from:
   - Recalibrating heuristic probabilities for the hard3 distribution
   - Enhancing BFS rewriting (larger limits, bidirectional search)
   - Adding structural features beyond variable count (tree depth, variable multiplicities, subterm patterns)
   - Implementing Stone pairing approximation for additional signal

2. **Key prerequisites:** Understanding why BFS rewriting fails on hard3 cases (terms grow too large? Wrong rewrite direction? Need intermediate lemmas?)

3. **Computational tools:** The existing Python predictor framework is the right tool. No new computational frameworks needed — just refinement of the existing approach.

4. **Potential difficulties:**
   - The cheatsheet must be <10KB text, so any improvement must be expressible as rules an LLM can follow
   - Hard3 problems are curated to be at the boundary of decidability — many genuinely require deep algebraic reasoning
   - Improving false negative rate may increase false positive rate (precision-recall tradeoff)
   - The evaluation metric is log-loss, so calibrated probabilities matter more than binary accuracy
