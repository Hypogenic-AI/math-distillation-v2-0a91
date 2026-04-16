"""Deep analysis of hard3 errors to find better rules."""
import json
from collections import Counter, defaultdict
from cheatsheet_predictor import (
    predict, parse_equation, is_var, tree_vars, tree_vars_set,
    compute_features, get_bare_source_features, leftmost_var, rightmost_var,
    has_square, term_to_str, normalize_bare_law
)

# Load all hard3 data
all_data = []
with open('/workspaces/math-distillation-v2-0a91/data_hard3.jsonl') as f:
    for line in f:
        row = json.loads(line)
        eq_a = parse_equation(row['equation1'])
        eq_b = parse_equation(row['equation2'])
        fa = compute_features(eq_a)
        fb = compute_features(eq_b)
        bsf = get_bare_source_features(eq_a)
        verdict, rule, _ = predict(row['equation1'], row['equation2'])
        all_data.append({
            'id': row['id'],
            'eq1': row['equation1'],
            'eq2': row['equation2'],
            'actual': row['answer'],
            'predicted': verdict,
            'rule': rule,
            'fa': fa,
            'fb': fb,
            'bsf': bsf,
            'eq_a': eq_a,
            'eq_b': eq_b,
        })

errors = [d for d in all_data if d['predicted'] != d['actual']]
fn = [d for d in errors if not d['predicted'] and d['actual']]
fp = [d for d in errors if d['predicted'] and not d['actual']]

# ============================================================
# ANALYSIS 1: What makes C-motif FPs different from TPs?
# ============================================================

print("=== C-MOTIF ANALYSIS ===")
c_rules = ['contradiction_C1', 'contradiction_C6', 'contradiction_C8',
           'contradiction_C9', 'contradiction_C10', 'contradiction_C13',
           'contradiction_C14']

for cr in c_rules:
    items = [d for d in all_data if d['rule'] == cr]
    if not items:
        continue
    correct_items = [d for d in items if d['predicted'] == d['actual']]
    wrong_items = [d for d in items if d['predicted'] != d['actual']]

    print(f"\n{cr}: {len(correct_items)} correct, {len(wrong_items)} wrong")

    # What distinguishes correct from wrong?
    for label, group in [("CORRECT (TRUE→TRUE)", correct_items), ("WRONG (TRUE→FALSE)", wrong_items)]:
        if not group:
            continue
        print(f"  {label}:")
        vb_dist = Counter(d['fb']['vars'] for d in group)
        bare_b = sum(1 for d in group if d['fb']['bare'])
        set_b = sum(1 for d in group if d['fb']['SET'])
        xor_b = sum(1 for d in group if d['fb']['XOR'])
        sb_dist = Counter(d['fb']['size'] for d in group)
        print(f"    vB: {dict(vb_dist)}, bareB: {bare_b}/{len(group)}")
        print(f"    SET_B: {set_b}/{len(group)}, XOR_B: {xor_b}/{len(group)}")
        print(f"    sB: {dict(sb_dist)}")

# ============================================================
# ANALYSIS 2: F1 FN patterns - what makes vA==vB TRUE?
# ============================================================

print("\n\n=== F1 FALSE NEGATIVE ANALYSIS ===")
f1_fn = [d for d in fn if d['rule'] == 'F1']
f1_all = [d for d in all_data if d['rule'] == 'F1']

print(f"F1 total: {len(f1_all)}, FN: {len(f1_fn)}, TN: {len(f1_all) - len(f1_fn)}")

# Check: what if we look at bare(A) + vA>=3 + sB>sA?
f1_bare_va3_sb_gt = [d for d in f1_all if d['fa']['bare'] and d['fa']['vars'] >= 3 and d['fb']['size'] > d['fa']['size']]
f1_bare_va3_sb_gt_true = sum(1 for d in f1_bare_va3_sb_gt if d['actual'])
print(f"\nF1 with bare(A), vA>=3, sB>sA: {len(f1_bare_va3_sb_gt)} total, {f1_bare_va3_sb_gt_true} TRUE")

# What about bare(A), vA>=3, sB==sA?
f1_bare_va3_sb_eq = [d for d in f1_all if d['fa']['bare'] and d['fa']['vars'] >= 3 and d['fb']['size'] == d['fa']['size']]
f1_bare_va3_sb_eq_true = sum(1 for d in f1_bare_va3_sb_eq if d['actual'])
print(f"F1 with bare(A), vA>=3, sB==sA: {len(f1_bare_va3_sb_eq)} total, {f1_bare_va3_sb_eq_true} TRUE")

# What about bare(A) + sB > sA (any vA)?
f1_bare_sb_gt = [d for d in f1_all if d['fa']['bare'] and d['fb']['size'] > d['fa']['size']]
f1_bare_sb_gt_true = sum(1 for d in f1_bare_sb_gt if d['actual'])
print(f"F1 with bare(A), sB>sA: {len(f1_bare_sb_gt)} total, {f1_bare_sb_gt_true} TRUE")

# What about non-bare cases?
f1_nonbare = [d for d in f1_all if not d['fa']['bare']]
f1_nonbare_true = sum(1 for d in f1_nonbare if d['actual'])
print(f"F1 with non-bare(A): {len(f1_nonbare)} total, {f1_nonbare_true} TRUE")

# What about bare A, vA==2?
f1_bare_v2 = [d for d in f1_all if d['fa']['bare'] and d['fa']['vars'] == 2]
f1_bare_v2_true = sum(1 for d in f1_bare_v2 if d['actual'])
print(f"F1 with bare(A), vA==2: {len(f1_bare_v2)} total, {f1_bare_v2_true} TRUE")

# ============================================================
# ANALYSIS 3: F2 FN patterns
# ============================================================

print("\n\n=== F2 FALSE NEGATIVE ANALYSIS ===")
f2_all = [d for d in all_data if d['rule'] == 'F2']
f2_fn_items = [d for d in fn if d['rule'] == 'F2']
print(f"F2 total: {len(f2_all)}, FN: {len(f2_fn_items)}, TN: {len(f2_all) - len(f2_fn_items)}")

# Check: bare(A) + vA>=3 cases
f2_bare_va3 = [d for d in f2_all if d['fa']['bare'] and d['fa']['vars'] >= 3]
f2_bare_va3_true = sum(1 for d in f2_bare_va3 if d['actual'])
print(f"F2 with bare(A), vA>=3: {len(f2_bare_va3)} total, {f2_bare_va3_true} TRUE")

# bare(A) + vB > vA cases
f2_bare_vb_gt = [d for d in f2_all if d['fa']['bare'] and d['fb']['vars'] > d['fa']['vars']]
f2_bare_vb_gt_true = sum(1 for d in f2_bare_vb_gt if d['actual'])
print(f"F2 with bare(A), vB>vA: {len(f2_bare_vb_gt)} total, {f2_bare_vb_gt_true} TRUE")

# non-bare(A) cases
f2_nonbare = [d for d in f2_all if not d['fa']['bare']]
f2_nonbare_true = sum(1 for d in f2_nonbare if d['actual'])
print(f"F2 with non-bare(A): {len(f2_nonbare)} total, {f2_nonbare_true} TRUE")

# bare(A), vA>=3, vB<vA
f2_bare_va3_vb_lt = [d for d in f2_all if d['fa']['bare'] and d['fa']['vars'] >= 3 and d['fb']['vars'] < d['fa']['vars']]
f2_bare_va3_vb_lt_true = sum(1 for d in f2_bare_va3_vb_lt if d['actual'])
print(f"F2 with bare(A), vA>=3, vB<vA: {len(f2_bare_va3_vb_lt)} total, {f2_bare_va3_vb_lt_true} TRUE")

# ============================================================
# ANALYSIS 4: D4 FN patterns
# ============================================================

print("\n\n=== D4 DEFAULT FALSE NEGATIVE ANALYSIS ===")
d4_all = [d for d in all_data if d['rule'] == 'D4_default']
d4_fn_items = [d for d in fn if d['rule'] == 'D4_default']
print(f"D4 total: {len(d4_all)}, FN: {len(d4_fn_items)}, TN: {len(d4_all) - len(d4_fn_items)}")

# Check features
for d in d4_fn_items[:15]:
    print(f"  vA={d['fa']['vars']} vB={d['fb']['vars']} sA={d['fa']['size']} sB={d['fb']['size']} "
          f"iA={d['fa']['imb']} iB={d['fb']['imb']} bareA={d['fa']['bare']} bareB={d['fb']['bare']} "
          f"LPA={d['fa']['LP']} RPA={d['fa']['RP']} XORA={d['fa']['XOR']}")
    print(f"    {d['eq1']}  =>  {d['eq2']}")

# Pattern: bare(A) with vB > vA
d4_bare_vb_gt = [d for d in d4_fn_items if d['fa']['bare'] and d['fb']['vars'] > d['fa']['vars']]
print(f"\nD4 FN with bare(A), vB>vA: {len(d4_bare_vb_gt)}")

# What about non-bare A with vB > vA?
d4_nonbare_vb_gt = [d for d in d4_fn_items if not d['fa']['bare'] and d['fb']['vars'] > d['fa']['vars']]
print(f"D4 FN with non-bare(A), vB>vA: {len(d4_nonbare_vb_gt)}")

# Pattern: bare(A), vA >= 3
d4_bare_va3 = [d for d in d4_fn_items if d['fa']['bare'] and d['fa']['vars'] >= 3]
print(f"D4 FN with bare(A), vA>=3: {len(d4_bare_va3)}")

# ============================================================
# ANALYSIS 5: T4 FP patterns - what makes T4 wrong?
# ============================================================
print("\n\n=== T4 FALSE POSITIVE ANALYSIS ===")
t4_all = [d for d in all_data if d['rule'] == 'T4']
t4_fp_items = [d for d in fp if d['rule'] == 'T4']
print(f"T4 total: {len(t4_all)}, FP: {len(t4_fp_items)}, TP: {len(t4_all) - len(t4_fp_items)}")

for d in t4_fp_items:
    bsf = d['bsf']
    if bsf:
        print(f"  rv={bsf['rhs_vars']} rt={bsf['rhs_totals']} Lx={bsf['Lx']} Rx={bsf['Rx']} "
              f"xt={bsf['x_top']} ts={bsf['top_shape']} vA={d['fa']['vars']} vB={d['fb']['vars']}")
    print(f"    {d['eq1']}  =>  {d['eq2']}")

# ============================================================
# ANALYSIS 6: What's the overall TRUE/FALSE distribution in hard3?
# ============================================================
print("\n\n=== HARD3 CLASS DISTRIBUTION ===")
true_count = sum(1 for d in all_data if d['actual'])
false_count = sum(1 for d in all_data if not d['actual'])
print(f"TRUE: {true_count}, FALSE: {false_count}")
print(f"Always-TRUE baseline: {true_count/len(all_data):.4f}")
print(f"Always-FALSE baseline: {false_count/len(all_data):.4f}")

# ============================================================
# ANALYSIS 7: For hard3 only, what is accuracy on specific subgroups?
# ============================================================
print("\n\n=== HARD3 SUBGROUP ANALYSIS ===")

# bare A, bare B
for ba_label, ba_filter in [("bare_A", lambda d: d['fa']['bare']), ("non-bare_A", lambda d: not d['fa']['bare'])]:
    for bb_label, bb_filter in [("bare_B", lambda d: d['fb']['bare']), ("non-bare_B", lambda d: not d['fb']['bare'])]:
        group = [d for d in all_data if ba_filter(d) and bb_filter(d)]
        if not group:
            continue
        correct = sum(1 for d in group if d['predicted'] == d['actual'])
        true_in_group = sum(1 for d in group if d['actual'])
        print(f"  {ba_label} + {bb_label}: {len(group)} total, {correct} correct ({correct/len(group):.3f}), "
              f"{true_in_group} actual TRUE ({true_in_group/len(group):.3f})")
