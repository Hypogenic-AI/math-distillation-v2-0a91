"""Compute per-rule accuracy across all datasets."""
import json
from collections import Counter, defaultdict
from cheatsheet_predictor import predict

datasets = [
    ('normal', '/workspaces/math-distillation-v2-0a91/data_normal.jsonl'),
    ('hard1', '/workspaces/math-distillation-v2-0a91/data_hard1.jsonl'),
    ('hard2', '/workspaces/math-distillation-v2-0a91/data_hard2.jsonl'),
    ('hard3', '/workspaces/math-distillation-v2-0a91/data_hard3.jsonl'),
]

# Track per-rule: total, correct, FP, FN
rule_stats = defaultdict(lambda: {'total': 0, 'correct': 0, 'fp': 0, 'fn': 0})

for name, path in datasets:
    with open(path) as f:
        for line in f:
            row = json.loads(line)
            verdict, rule, _ = predict(row['equation1'], row['equation2'])
            actual = row['answer']

            key = (name, rule)
            rule_stats[key]['total'] += 1
            if verdict == actual:
                rule_stats[key]['correct'] += 1
            elif verdict and not actual:
                rule_stats[key]['fp'] += 1
            else:
                rule_stats[key]['fn'] += 1

# Aggregate across datasets
agg = defaultdict(lambda: {'total': 0, 'correct': 0, 'fp': 0, 'fn': 0})
for (ds, rule), stats in rule_stats.items():
    for k in ['total', 'correct', 'fp', 'fn']:
        agg[rule][k] += stats[k]

print(f"{'Rule':<25} {'Total':>6} {'Correct':>7} {'FP':>4} {'FN':>4} {'Acc':>6} {'Verdict':>8}")
print("-" * 70)
for rule in sorted(agg.keys(), key=lambda r: -agg[r]['total']):
    s = agg[rule]
    acc = s['correct'] / s['total'] if s['total'] > 0 else 0
    # What does this rule predict?
    verdict_type = "TRUE" if rule.startswith(('T', 'contradiction', 'collapse_l', 'collapse_r', 'constant_p', 'D3', 'identity')) and not rule.endswith('false') else "FALSE"
    if rule in ('D4_default',):
        verdict_type = "FALSE"
    print(f"{rule:<25} {s['total']:>6} {s['correct']:>7} {s['fp']:>4} {s['fn']:>4} {acc:>6.3f} {verdict_type:>8}")

# Show hard3-specific breakdown
print("\n\n=== HARD3 BREAKDOWN ===")
print(f"{'Rule':<25} {'Total':>6} {'Correct':>7} {'FP':>4} {'FN':>4} {'Acc':>6}")
print("-" * 60)
for (ds, rule), stats in sorted(rule_stats.items(), key=lambda x: (x[0][0], -x[1]['total'])):
    if ds != 'hard3':
        continue
    acc = stats['correct'] / stats['total'] if stats['total'] > 0 else 0
    print(f"{rule:<25} {stats['total']:>6} {stats['correct']:>7} {stats['fp']:>4} {stats['fn']:>4} {acc:>6.3f}")
