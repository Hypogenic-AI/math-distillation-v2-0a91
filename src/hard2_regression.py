"""Analyze hard2 regression cases."""
import json
from cheatsheet_predictor import predict as predict_baseline
from improved_predictor_v7 import predict_v7
from cheatsheet_predictor import parse_equation, compute_features, get_bare_source_features, is_var

with open('/workspaces/math-distillation-v2-0a91/data_hard2.jsonl') as f:
    items = [json.loads(line) for line in f]

# Find cases where baseline is right but improved is wrong
regressions = []
for row in items:
    bv, br, _ = predict_baseline(row['equation1'], row['equation2'])
    iv, ir, _ = predict_v7(row['equation1'], row['equation2'])
    actual = row['answer']
    if bv == actual and iv != actual:
        regressions.append({
            'eq1': row['equation1'], 'eq2': row['equation2'],
            'actual': actual, 'base_rule': br, 'imp_rule': ir,
        })

print(f"Hard2 regressions: {len(regressions)}")
for r in regressions:
    eq_a = parse_equation(r['eq1'])
    fa = compute_features(eq_a)
    bsf = get_bare_source_features(eq_a)
    print(f"\n  actual={r['actual']} base_rule={r['base_rule']} imp_rule={r['imp_rule']}")
    if bsf:
        print(f"  rv={bsf['rhs_vars']} Lx={bsf['Lx']} Rx={bsf['Rx']} xt={bsf['x_top']} ts={bsf['top_shape']} sq={bsf['square']} xc={bsf['x_count']}")
    print(f"  {r['eq1']}  =>  {r['eq2']}")
