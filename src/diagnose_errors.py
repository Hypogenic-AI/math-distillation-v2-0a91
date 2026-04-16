"""Diagnose hard3 errors in detail."""
import json
from collections import Counter
from cheatsheet_predictor import predict, parse_equation, is_var, tree_vars, compute_features, get_bare_source_features

# Load hard3
errors_fp = []  # false positives (predicted TRUE, actual FALSE)
errors_fn = []  # false negatives (predicted FALSE, actual TRUE)

with open('/workspaces/math-distillation-v2-0a91/data_hard3.jsonl') as f:
    for line in f:
        row = json.loads(line)
        eq1 = row['equation1']
        eq2 = row['equation2']
        actual = row['answer']
        verdict, rule, details = predict(eq1, eq2)
        if verdict != actual:
            entry = {
                'id': row['id'],
                'eq1': eq1,
                'eq2': eq2,
                'actual': actual,
                'predicted': verdict,
                'rule': rule,
            }
            if verdict and not actual:
                errors_fp.append(entry)
            else:
                errors_fn.append(entry)

print(f"Total errors: {len(errors_fp) + len(errors_fn)}")
print(f"False positives: {len(errors_fp)}")
print(f"False negatives: {len(errors_fn)}")

# Analyze false positives by rule
print("\n=== FALSE POSITIVES (predicted TRUE, actual FALSE) ===")
fp_rules = Counter(e['rule'] for e in errors_fp)
for rule, count in fp_rules.most_common():
    print(f"  {rule}: {count}")
    examples = [e for e in errors_fp if e['rule'] == rule][:3]
    for ex in examples:
        print(f"    {ex['eq1']}  =>  {ex['eq2']}")

# Analyze false negatives by rule
print("\n=== FALSE NEGATIVES (predicted FALSE, actual TRUE) ===")
fn_rules = Counter(e['rule'] for e in errors_fn)
for rule, count in fn_rules.most_common():
    print(f"  {rule}: {count}")
    examples = [e for e in errors_fn if e['rule'] == rule][:3]
    for ex in examples:
        print(f"    {ex['eq1']}  =>  {ex['eq2']}")

# Analyze features of false negative cases
print("\n=== FALSE NEGATIVE FEATURE ANALYSIS ===")
fn_bare_a = sum(1 for e in errors_fn if is_var(parse_equation(e['eq1'])[0]) or is_var(parse_equation(e['eq1'])[1]))
fn_bare_b = sum(1 for e in errors_fn if is_var(parse_equation(e['eq2'])[0]) or is_var(parse_equation(e['eq2'])[1]))
print(f"  A is bare: {fn_bare_a}/{len(errors_fn)}")
print(f"  B is bare: {fn_bare_b}/{len(errors_fn)}")

# Vars distribution for FN
print("\n  vA distribution (FN):")
va_dist = Counter()
vb_dist = Counter()
va_vb_diff = Counter()
for e in errors_fn:
    fa = compute_features(parse_equation(e['eq1']))
    fb = compute_features(parse_equation(e['eq2']))
    va_dist[fa['vars']] += 1
    vb_dist[fb['vars']] += 1
    va_vb_diff[fa['vars'] - fb['vars']] += 1
for k in sorted(va_dist):
    print(f"    vA={k}: {va_dist[k]}")
print("  vB distribution (FN):")
for k in sorted(vb_dist):
    print(f"    vB={k}: {vb_dist[k]}")
print("  vA-vB distribution (FN):")
for k in sorted(va_vb_diff):
    print(f"    vA-vB={k}: {va_vb_diff[k]}")

# Analyze features of false positive cases
print("\n=== FALSE POSITIVE FEATURE ANALYSIS ===")
fp_bare_a = sum(1 for e in errors_fp if is_var(parse_equation(e['eq1'])[0]) or is_var(parse_equation(e['eq1'])[1]))
fp_bare_b = sum(1 for e in errors_fp if is_var(parse_equation(e['eq2'])[0]) or is_var(parse_equation(e['eq2'])[1]))
print(f"  A is bare: {fp_bare_a}/{len(errors_fp)}")
print(f"  B is bare: {fp_bare_b}/{len(errors_fp)}")

print("\n  FP by rule with feature details:")
for e in errors_fp[:20]:
    fa = compute_features(parse_equation(e['eq1']))
    fb = compute_features(parse_equation(e['eq2']))
    bsf = get_bare_source_features(parse_equation(e['eq1']))
    bsf_str = ""
    if bsf:
        bsf_str = f" rv={bsf['rhs_vars']} rt={bsf['rhs_totals']} Lx={bsf['Lx']} Rx={bsf['Rx']} xt={bsf['x_top']} ts={bsf['top_shape']}"
    print(f"  {e['rule']:20s} vA={fa['vars']} vB={fb['vars']} sA={fa['size']} sB={fb['size']}{bsf_str}")
    print(f"    {e['eq1']}  =>  {e['eq2']}")

# Now let's check: for the FN with rule F1, what are the features?
print("\n=== F1 FALSE NEGATIVES (vA == vB but actually TRUE) ===")
f1_fn = [e for e in errors_fn if e['rule'] == 'F1']
for e in f1_fn[:10]:
    fa = compute_features(parse_equation(e['eq1']))
    fb = compute_features(parse_equation(e['eq2']))
    print(f"  vA={fa['vars']} vB={fb['vars']} sA={fa['size']} sB={fb['size']} iA={fa['imb']} iB={fb['imb']} bareA={fa['bare']} bareB={fb['bare']}")
    print(f"    {e['eq1']}  =>  {e['eq2']}")

print("\n=== D4 FALSE NEGATIVES (default FALSE, but actually TRUE) ===")
d4_fn = [e for e in errors_fn if e['rule'] == 'D4_default']
for e in d4_fn[:10]:
    fa = compute_features(parse_equation(e['eq1']))
    fb = compute_features(parse_equation(e['eq2']))
    print(f"  vA={fa['vars']} vB={fb['vars']} sA={fa['size']} sB={fb['size']} iA={fa['imb']} iB={fb['imb']} bareA={fa['bare']} bareB={fb['bare']}")
    print(f"    {e['eq1']}  =>  {e['eq2']}")

print("\n=== F2 FALSE NEGATIVES (iB < iA but actually TRUE) ===")
f2_fn = [e for e in errors_fn if e['rule'] == 'F2']
for e in f2_fn[:10]:
    fa = compute_features(parse_equation(e['eq1']))
    fb = compute_features(parse_equation(e['eq2']))
    print(f"  vA={fa['vars']} vB={fb['vars']} sA={fa['size']} sB={fb['size']} iA={fa['imb']} iB={fb['imb']} bareA={fa['bare']} bareB={fb['bare']}")
    print(f"    {e['eq1']}  =>  {e['eq2']}")
