"""Check D4 default cases across datasets for potential new rules."""
import json
from improved_predictor_v7 import predict_v7
from cheatsheet_predictor import parse_equation, compute_features, get_bare_source_features, is_var

for name, path in [('hard2', 'data_hard2.jsonl'), ('hard3', 'data_hard3.jsonl'), ('normal', 'data_normal.jsonl')]:
    d4_items = []
    with open(f'/workspaces/math-distillation-v2-0a91/{path}') as f:
        for line in f:
            row = json.loads(line)
            v, r, _ = predict_v7(row['equation1'], row['equation2'])
            if r == 'D4_default':
                eq_a = parse_equation(row['equation1'])
                fa = compute_features(eq_a)
                bsf = get_bare_source_features(eq_a)
                d4_items.append({
                    'actual': row['answer'],
                    'fa': fa,
                    'bare': fa['bare'],
                    'vA': fa['vars'],
                    'bsf': bsf,
                })

    # Analyze by bare/vA
    print(f"\n=== {name}: D4 default cases ===")
    from collections import Counter
    for bare in [True, False]:
        group = [d for d in d4_items if d['bare'] == bare]
        if not group:
            continue
        true_count = sum(1 for d in group if d['actual'])
        false_count = sum(1 for d in group if not d['actual'])
        print(f"  bare={bare}: {len(group)} total, {true_count} TRUE, {false_count} FALSE")

        if bare:
            va_dist = Counter(d['vA'] for d in group)
            for va in sorted(va_dist):
                va_group = [d for d in group if d['vA'] == va]
                true_va = sum(1 for d in va_group if d['actual'])
                false_va = sum(1 for d in va_group if not d['actual'])
                print(f"    vA={va}: {len(va_group)} total, {true_va} TRUE, {false_va} FALSE "
                      f"({true_va/len(va_group)*100:.0f}% TRUE)")
        else:
            va_dist = Counter(d['vA'] for d in group)
            for va in sorted(va_dist):
                va_group = [d for d in group if d['vA'] == va]
                true_va = sum(1 for d in va_group if d['actual'])
                false_va = sum(1 for d in va_group if not d['actual'])
                print(f"    vA={va}: {len(va_group)} total, {true_va} TRUE, {false_va} FALSE "
                      f"({true_va/len(va_group)*100:.0f}% TRUE)")
