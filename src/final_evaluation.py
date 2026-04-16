"""Final comprehensive evaluation of the improved cheatsheet predictor."""
import json
import math
from collections import Counter, defaultdict
from improved_predictor_v7 import predict_v7, evaluate_dataset
from cheatsheet_predictor import predict as predict_baseline

datasets = [
    ('normal', '/workspaces/math-distillation-v2-0a91/data_normal.jsonl'),
    ('hard1', '/workspaces/math-distillation-v2-0a91/data_hard1.jsonl'),
    ('hard2', '/workspaces/math-distillation-v2-0a91/data_hard2.jsonl'),
    ('hard3', '/workspaces/math-distillation-v2-0a91/data_hard3.jsonl'),
]

print("=" * 80)
print("FINAL EVALUATION: Baseline vs Improved (v7)")
print("=" * 80)

total_baseline_correct = 0
total_improved_correct = 0
total_items = 0

for name, path in datasets:
    # Baseline
    base_correct = 0
    base_total = 0
    imp_correct = 0
    imp_total = 0
    base_ll = 0
    imp_ll = 0

    with open(path) as f:
        for line in f:
            row = json.loads(line)
            actual = row['answer']

            # Baseline
            bv, br, _ = predict_baseline(row['equation1'], row['equation2'])
            if bv == actual:
                base_correct += 1
            bp = 0.99 if bv else 0.01
            base_ll += math.log(bp) if actual else math.log(1 - bp)
            base_total += 1

            # Improved
            iv, ir, _ = predict_v7(row['equation1'], row['equation2'])
            if iv == actual:
                imp_correct += 1
            ip = 0.99 if iv else 0.01
            imp_ll += math.log(ip) if actual else math.log(1 - ip)
            imp_total += 1

    base_acc = base_correct / base_total
    imp_acc = imp_correct / imp_total
    delta = imp_acc - base_acc

    total_baseline_correct += base_correct
    total_improved_correct += imp_correct
    total_items += base_total

    print(f"\n{name}:")
    print(f"  Baseline: {base_correct}/{base_total} = {base_acc:.4f} (avg LL: {base_ll/base_total:.4f})")
    print(f"  Improved: {imp_correct}/{imp_total} = {imp_acc:.4f} (avg LL: {imp_ll/imp_total:.4f})")
    print(f"  Delta: {delta:+.4f} ({'+' if delta > 0 else ''}{int(delta*base_total)} items)")

print(f"\n{'='*80}")
print(f"OVERALL:")
print(f"  Baseline: {total_baseline_correct}/{total_items} = {total_baseline_correct/total_items:.4f}")
print(f"  Improved: {total_improved_correct}/{total_items} = {total_improved_correct/total_items:.4f}")
print(f"  Delta: {(total_improved_correct-total_baseline_correct)/total_items:+.4f}")

# Detailed hard3 error breakdown
print(f"\n{'='*80}")
print("HARD3 ERROR BREAKDOWN (Improved v7)")
print("=" * 80)

result = evaluate_dataset('/workspaces/math-distillation-v2-0a91/data_hard3.jsonl')

# Per-rule accuracy
print("\nPer-rule accuracy on hard3:")
rule_items = defaultdict(lambda: {'tp': 0, 'fp': 0, 'tn': 0, 'fn': 0})

with open('/workspaces/math-distillation-v2-0a91/data_hard3.jsonl') as f:
    for line in f:
        row = json.loads(line)
        verdict, rule, _ = predict_v7(row['equation1'], row['equation2'])
        actual = row['answer']
        if verdict and actual:
            rule_items[rule]['tp'] += 1
        elif verdict and not actual:
            rule_items[rule]['fp'] += 1
        elif not verdict and actual:
            rule_items[rule]['fn'] += 1
        else:
            rule_items[rule]['tn'] += 1

print(f"{'Rule':<25} {'Total':>6} {'Correct':>7} {'FP':>4} {'FN':>4} {'Acc':>6}")
print("-" * 55)
for rule in sorted(rule_items.keys(), key=lambda r: -(rule_items[r]['tp']+rule_items[r]['fp']+rule_items[r]['tn']+rule_items[r]['fn'])):
    s = rule_items[rule]
    total = s['tp'] + s['fp'] + s['tn'] + s['fn']
    correct = s['tp'] + s['tn']
    acc = correct / total if total > 0 else 0
    print(f"{rule:<25} {total:>6} {correct:>7} {s['fp']:>4} {s['fn']:>4} {acc:>6.3f}")

# Summary of changes
print(f"\n{'='*80}")
print("SUMMARY OF CHEATSHEET CHANGES")
print("=" * 80)
print("""
STEP 0 - Added simple projection collapse lemmas:
  - x = x * y → LEFT PROJECTION (p*q = p)
  - x = y * x → RIGHT PROJECTION (p*q = q)

STEP 0B - Improved contradiction motifs:
  - C1: Added topShape != m-m (removed 5 FPs, 0 TP lost)
  - C3: Added rhsVars >= 3 (removed 6 FPs)
  - C6: Added Rx(A)=FALSE (removed 20 FPs, lost 7 TPs)
  - C8: REMOVED (31.9% accuracy)
  - C9: Added XOR(B)=FALSE, square(A)=FALSE, imb(B)>=3
  - C10: Added RP(B)=TRUE (removed 10 FPs)
  - C11, C12: Removed (subsumed by C2)
  - C13: Added RP(B)=TRUE (removed 21 FPs)
  - C14: REMOVED (15.4% accuracy)

STEP 4 - Fixed structural rules:
  - T4: Added Lx(A)=FALSE (removed 9 FPs)
  - T6: Added vA >= 3
  - T7: REMOVED (25% accuracy)
  - T1: MOVED BEFORE F1 (catches bare vA>=3, sB>sA first)
  - F2: REMOVED (33.6% accuracy - worse than random)
  - T5: REMOVED (21.7% accuracy)

STEP 5 - Added new rule:
  - NR1: bare(A) with vA >= 5 → TRUE (past all guards)
""")
