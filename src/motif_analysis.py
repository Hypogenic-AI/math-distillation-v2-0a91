"""Find distinguishing features between TP and FP for each motif."""
import json
from collections import Counter, defaultdict
from cheatsheet_predictor import (
    parse_equation, is_var, tree_vars, tree_vars_set,
    compute_features, get_bare_source_features, normalize_bare_law,
    term_to_str, check_contradiction_motifs
)

# Load all datasets
all_items = []
for name, path in [('normal', 'data_normal.jsonl'), ('hard1', 'data_hard1.jsonl'),
                    ('hard2', 'data_hard2.jsonl'), ('hard3', 'data_hard3.jsonl')]:
    with open(f'/workspaces/math-distillation-v2-0a91/{path}') as f:
        for line in f:
            row = json.loads(line)
            eq_a = parse_equation(row['equation1'])
            eq_b = parse_equation(row['equation2'])
            fa = compute_features(eq_a)
            fb = compute_features(eq_b)
            bsf_a = get_bare_source_features(eq_a)
            bsf_b = get_bare_source_features(eq_b)

            motif = check_contradiction_motifs(eq_a, eq_b) if bsf_a else None

            all_items.append({
                'ds': name,
                'eq1': row['equation1'],
                'eq2': row['equation2'],
                'actual': row['answer'],
                'fa': fa, 'fb': fb,
                'bsf_a': bsf_a,
                'motif': motif,
                'eq_a': eq_a,
                'eq_b': eq_b,
            })

# For each problematic motif, find features that distinguish TP from FP
problematic_motifs = ['C6', 'C8', 'C9', 'C14', 'C1', 'C3', 'C13', 'C10']

for motif_name in problematic_motifs:
    motif_key = f'contradiction_{motif_name}'
    items = [d for d in all_items if d['motif'] == motif_name]
    if not items:
        continue

    tps = [d for d in items if d['actual'] == True]
    fps = [d for d in items if d['actual'] == False]

    print(f"\n{'='*60}")
    print(f"MOTIF {motif_name}: {len(tps)} TP, {len(fps)} FP")

    if not fps:
        print("  No FPs - motif is safe")
        continue

    # Check features that might separate TP from FP
    features_to_check = [
        ('vB', lambda d: d['fb']['vars']),
        ('sB', lambda d: d['fb']['size']),
        ('bare_B', lambda d: d['fb']['bare']),
        ('SET_B', lambda d: d['fb']['SET']),
        ('XOR_B', lambda d: d['fb']['XOR']),
        ('LP_B', lambda d: d['fb']['LP']),
        ('RP_B', lambda d: d['fb']['RP']),
        ('AB_B', lambda d: d['fb']['AB']),
        ('iB', lambda d: d['fb']['imb']),
        ('vA', lambda d: d['fa']['vars']),
        ('sA', lambda d: d['fa']['size']),
        ('xTop', lambda d: d['bsf_a']['x_top'] if d['bsf_a'] else None),
        ('topShape', lambda d: d['bsf_a']['top_shape'] if d['bsf_a'] else None),
        ('Lx', lambda d: d['bsf_a']['Lx'] if d['bsf_a'] else None),
        ('Rx', lambda d: d['bsf_a']['Rx'] if d['bsf_a'] else None),
        ('x_count', lambda d: d['bsf_a']['x_count'] if d['bsf_a'] else None),
        ('square', lambda d: d['bsf_a']['square'] if d['bsf_a'] else None),
        ('norm_src', lambda d: term_to_str(normalize_bare_law(d['eq_a'])[1]) if normalize_bare_law(d['eq_a']) else None),
    ]

    for fname, ffunc in features_to_check:
        tp_vals = Counter(ffunc(d) for d in tps)
        fp_vals = Counter(ffunc(d) for d in fps)
        # Check if any value cleanly separates
        all_vals = set(tp_vals.keys()) | set(fp_vals.keys())
        for val in sorted(all_vals, key=str):
            tp_count = tp_vals.get(val, 0)
            fp_count = fp_vals.get(val, 0)
            if tp_count > 0 and fp_count == 0 and tp_count >= 3:
                pass  # TP-only value (good for keeping)
            elif fp_count > 0 and tp_count == 0 and fp_count >= 3:
                print(f"  {fname}={val}: FP-ONLY ({fp_count} FP, 0 TP) → could filter out")
            elif fp_count > 0 and tp_count > 0:
                tp_rate = tp_count / (tp_count + fp_count)
                if tp_rate < 0.3 and fp_count >= 3:
                    print(f"  {fname}={val}: LOW TP rate {tp_rate:.2f} ({tp_count} TP, {fp_count} FP)")

    # Show the unique normalized source equations for FPs
    fp_sources = Counter(d['eq1'] for d in fps)
    print(f"\n  FP source equations:")
    for src, cnt in fp_sources.most_common(5):
        norm = normalize_bare_law(parse_equation(src))
        if norm:
            print(f"    {cnt}x: {src}  →  norm: {term_to_str(norm[1])}")
        else:
            print(f"    {cnt}x: {src}")

# Also check T4, T5, T7, T8
print("\n\n=== T-RULE ANALYSIS ===")

# For each hard3 item, check what the cheatsheet rule is and trace through
from cheatsheet_predictor import predict

t_rules = ['T4', 'T5', 'T7', 'T8', 'T1', 'T6']
for tr in t_rules:
    items = [d for d in all_items if True]  # need to check
    # Run predictor on all items and collect those hitting this rule
    rule_items = []
    for d in all_items:
        verdict, rule, _ = predict(d['eq1'], d['eq2'])
        if rule == tr:
            rule_items.append({**d, 'predicted': verdict, 'rule': rule})

    if not rule_items:
        continue

    tps = [d for d in rule_items if d['predicted'] == d['actual']]
    fps = [d for d in rule_items if d['predicted'] != d['actual'] and d['predicted'] == True]

    print(f"\n{tr}: {len(tps)} TP, {len(fps)} FP (total {len(rule_items)})")
    if fps:
        # Check source features
        for d in fps[:5]:
            bsf = d['bsf_a']
            if bsf:
                print(f"  FP: Lx={bsf['Lx']} Rx={bsf['Rx']} xt={bsf['x_top']} ts={bsf['top_shape']} rv={bsf['rhs_vars']}")
            print(f"    {d['eq1']}  =>  {d['eq2']}  (ds={d['ds']})")
