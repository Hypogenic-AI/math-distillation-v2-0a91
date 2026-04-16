# Literature Review: Improving Hard3 Performance in the Mathematics Distillation Challenge

## Research Area Overview

The Mathematics Distillation Challenge (Tao & Davis, SAIR Foundation, 2026) asks participants to compress the implication structure of 4694 equational laws on magmas into a <10KB text cheatsheet that enables weak LLMs to predict whether equation E1 implies equation E2. The previous iteration achieved 87.4% on normal, 63.8% on hard1, 54.5% on hard2, and **71.8% on hard3**. This review focuses on diagnosing hard3 failure modes and identifying new techniques to improve performance.

## Key Definitions

**Magma.** A set M with a binary operation `*: M x M -> M`. No axioms required.

**Equational law.** An identity like `x * (y * z) = (x * y) * z` (associativity). The 4694 laws in the challenge have at most 4 occurrences of `*`.

**Implication (E1 |= E2).** Every magma satisfying E1 also satisfies E2. Of 22M pairs, 37.12% are true implications.

**Equation forms** (from v1 predictor):
- **Trivial:** `x = x`
- **Singleton:** `x = y` (forces all elements equal)
- **Absorbing:** `x = f(y,z,...)` where x doesn't appear in f (forces all elements equal)
- **Standard (lhs_var):** `x = f(x,y,...)` where x appears on both sides
- **General:** Both sides contain `*` operations

**Signature (a,b).** Number of `*` operations on left-hand side (a) and right-hand side (b).

**Conjugacy/Duality.** Swapping `x*y` with `y*x` maps laws to their conjugates. Conjugate theories have identical Stone spectra.

**Stone pairing** (Berlioz & Mellies, 2026). For equation E and finite magma A, `<E|A>` = probability that a random variable assignment satisfies E in A. Values in [0,1].

## Key Papers

### Paper 1: The Equational Theories Project (Bolan et al., 2025)
- **arXiv:** 2512.07087
- **Main Results:** Complete determination of all 22,033,636 implications. 8,178,279 (37.12%) true. 1415 equivalence classes. A CNN achieves 99.7% accuracy. Only 524 distinct finite magmas (size <=4) needed to refute 96.3% of false implications.
- **Key Techniques for Our Work:**
  1. Finite magma counterexamples refute most false implications
  2. Syntactic rewriting generates direct implications
  3. Variable multiplicities and modular arithmetic detect non-implications
  4. ATPs (Vampire, Prover9) establish hard implications via superposition
  5. Canonizers map equivalent terms to normal forms
  6. Linear/quadratic magma constructions: `x*y = ax+by mod n`
- **Relevance:** The techniques catalog defines what can be encoded in a cheatsheet.

### Paper 2: The Latent Space of Equational Theories (Berlioz & Mellies, 2026)
- **arXiv:** 2601.20759
- **Main Results:**
  - Stone pairings create a feature space where PCA reveals: X-axis ~ expectation, Y-axis ~ variance, Z-axis ~ conjugacy
  - Equivalent theories cluster tightly (reversible edges 7x shorter than atomic edges)
  - Implications flow in oriented, well-structured patterns through the latent space
  - Signature (a,b) is cleanly separated in the latent space
  - "Contrarian edges" (hard implications) have unusual shapes in the latent space
- **Key Insight for Hard3:** The notion that implications have a "mainstream direction" (higher expectation, higher variance) and that hard implications are "contrarian" — going against this flow — directly explains why hard3 problems are hard. They are deliberately curated to include these contrarian cases.

## Analysis of V1 Predictor Performance on Hard3

### Performance Summary

| Split | Accuracy | Avg Log-Likelihood |
|-------|----------|--------------------|
| normal | 87.4% | -0.180 |
| hard1 | 63.8% | -0.646 |
| hard2 | 54.5% | -0.600 |
| hard3 | 71.8% | -0.453 |

### Error Breakdown on Hard3

**113 errors out of 400 problems:**
- **98 false negatives** (predicted False, actual True) — the dominant failure mode
- **15 false positives** (predicted True, actual False)

### False Negative Root Causes

The 98 false negatives fall into clear categories:

1. **p=0.5 bucket (31 cases):** ALL are `lhs_var -> lhs_var` with `nvd=+1`. The probability map assigns exactly 0.50, which rounds to False. These are true implications where E1 has one more variable than E2. The BFS rewriting failed to find the proof, and no counterexample was found (correctly), but the heuristic probability is too low.

2. **p=0.25-0.4 bucket (41 cases):** Mostly `lhs_var -> lhs_var` with `nvd=0`. The probability map assigns ~0.34 for same-variable-count pairs, but these particular pairs happen to be true implications. BFS rewriting failed.

3. **p=0.1-0.25 bucket (18 cases):** `lhs_var -> lhs_var` and `lhs_var -> general` with `nvd=-1`. The probability map penalizes cases where E1 has fewer variables, but these are true implications where a structurally simpler equation unexpectedly implies a more complex one.

4. **p<=0.02 bucket (5 cases):** Confident wrong predictions. These are cases like 2-var -> 4-var implications that violate the "more variables = stronger" heuristic. Example: `x = y * (x * x)` implies `x = y * (z * (z * (w * x)))`.

### False Positive Root Causes

The 15 false positives are mostly at p=0.51-0.62 — marginal predictions just above threshold. These are `lhs_var -> lhs_var` or `lhs_var -> general` where the heuristic slightly favors True but the implication is actually False.

### Key Insight: The Core Problem

The v1 predictor's variable count heuristic is well-calibrated on average but cannot distinguish individual cases within the same (form, nvd) bucket. Hard3 is curated to contain exactly these ambiguous cases. Improving hard3 requires **finer-grained structural features** beyond variable count.

## Proof Techniques in the Literature

### For establishing implications (relevant to reducing false negatives)
1. **BFS rewriting** — Currently limited to 500 steps, tree size <=30. Many hard implications require longer chains.
2. **ATP superposition** — Vampire/Prover9 can prove implications that BFS cannot, but are too heavy for a cheatsheet.
3. **Canonizers** — Map terms to normal forms; if E1 and E2 have the same normal form, they're equivalent. Could detect more equivalences.
4. **Expansion trees / Herbrand theorem** — Berlioz & Mellies conjecture that parallel implications share similar proof structures (expansion trees).
5. **Transitivity chains** — If E1 => E3 and E3 => E2, then E1 => E2. The predictor doesn't exploit known intermediate results.

### For refuting implications (relevant to reducing false positives)
1. **Finite magma search** — V1 uses ~200 magmas. The ETP found 524 critical magmas. Expanding the magma library could help.
2. **Linear/quadratic constructions** — `x*y = ax+by+cxy mod n`. V1 includes these for small n.
3. **Greedy infinite constructions** — Build magmas element-by-element. Not feasible for cheatsheet but informs which structures to include.

## Gaps and Opportunities for Improving Hard3

### Gap 1: BFS Rewriting Depth
The BFS limit of 500 steps and tree size 30 is too small for many hard implications. Some implications require chains of 10+ rewrites with intermediate terms growing to size 50+. Increasing these limits (or using smarter search strategies like bidirectional BFS or guided search) could convert many false negatives to true positives.

### Gap 2: Structural Features Beyond Variable Count
The current heuristic relies primarily on (form1, form2, nvd). Additional features that could help:
- **Tree depth** of expressions
- **Variable multiplicities** (how many times each variable appears)
- **Nesting patterns** (left-heavy vs right-heavy trees)
- **Subterm sharing** between E1 and E2
- **Idempotent subterms** (x*x patterns)
- **Self-referential structure** (does the LHS variable appear at the root, leaves, or intermediate positions in the RHS?)

### Gap 3: Stone Pairing Features
The Berlioz & Mellies paper shows that Stone pairings (satisfaction probabilities on random magmas) are highly informative. Computing Stone pairings for the specific equation pairs in hard3 could provide a strong signal for implications. Equations with similar Stone spectra are more likely to be equivalent or in an implication relationship.

### Gap 4: Equivalence Class Exploitation
Many of the 4694 equations are equivalent to each other (1415 equivalence classes). If E1 is equivalent to E1' and E1' => E2 is easier to prove/disprove, this could help. The predictor doesn't currently exploit transitivity through known equivalences.

### Gap 5: The nvd=+1 Threshold Problem
31 of 113 errors are because `lhs_var -> lhs_var` at nvd=+1 maps to probability 0.50 (exactly at threshold). Simply adjusting this probability slightly upward (e.g., to 0.52) would correctly classify many of these as True, at the cost of some additional false positives. This is a calibration issue.

## Recommendations for Proof Strategy

1. **Recalibrate heuristic probabilities** using the hard3 training data. The current probabilities were calibrated on the full 22M matrix; hard3 has a different distribution.

2. **Enhance BFS rewriting** with larger limits, bidirectional search, and smarter term selection.

3. **Add structural features** to the cheatsheet: tree depth ratio, variable multiplicity patterns, and subterm overlap between E1 and E2.

4. **Implement Stone pairing approximation** — even a rough estimate of satisfaction probability on a few canonical magmas provides signal.

5. **Expand counterexample magma library** — include all 524 critical magmas from the ETP project, not just ~200.

6. **Exploit idempotent structure** — many hard3 equations contain `x*x` subterms; idempotency-related reasoning patterns may help.

7. **For the cheatsheet specifically**: focus on encoding decision rules that an LLM can follow, rather than computational procedures. The LLM cannot run BFS, but it can check structural patterns.
