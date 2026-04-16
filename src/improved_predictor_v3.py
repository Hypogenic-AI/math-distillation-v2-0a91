"""
Improved predictor v3 - more conservative changes to avoid regressions.
"""
import json
from collections import Counter
from cheatsheet_predictor import (
    parse_equation, is_var, tree_vars, tree_vars_set,
    compute_features, get_bare_source_features, leftmost_var, rightmost_var,
    has_square, term_to_str, normalize_bare_law, check_collapse_lemma,
    collapse_term, check_constant_product_lemma, constant_product_collapse,
    rename_vars
)


def check_contradiction_motifs_v3(eq_a, eq_b):
    """More conservative contradiction motifs."""
    feats = get_bare_source_features(eq_a)
    if feats is None:
        return None

    rv = feats['rhs_vars']
    rt = feats['rhs_totals']
    lx = feats['Lx']
    rx = feats['Rx']
    xt = feats['x_top']
    sq = feats['square']
    ts = feats['top_shape']
    xc = feats['x_count']

    # C1: Add topShape != m-m restriction (hard3 FPs all had m-m)
    if rv == 4 and not lx and not rx and ts != 'm-m':
        return 'C1'

    # C2: Keep as is (95.8% overall, only 1 FP on hard3)
    if rv == 3 and rt == '113' and not lx and not rx:
        return 'C2'

    # C3: Restrict to rv >= 4 (was 56.2%)
    if not lx and xt == 'left' and sq and ts == 'm-v' and rv >= 4:
        return 'C3'

    # C4: Keep (100% accurate)
    if rv == 3 and rt == '112' and not lx and not rx and xt == 'right' and ts == 'v-m':
        return 'C4'

    # C5: Keep
    if rv == 4 and rt == '1112' and not lx and not rx and xt == 'right' and ts == 'v-m':
        return 'C5'

    # C6: REMOVED (57.4% accuracy)

    # C7: Keep (100% accurate)
    if rv == 3 and not lx and not rx and xt == 'left' and ts == 'm-v' and xc == 2:
        return 'C7'

    # C8: REMOVED (31.9% accuracy)

    # C9: REMOVED (28% accuracy)

    # C10: Keep with restriction
    fb = compute_features(eq_b)
    if rv == 3 and rt == '122' and not lx and rx and xc == 2 and not fb['SET']:
        return 'C10'

    # C13: Restrict to xTop=right
    if rv == 4 and rt == '1112' and not lx and rx and xt == 'right':
        return 'C13'

    # C14: REMOVED (15.4% accuracy)

    return None


def predict_v3(eq1_str, eq2_str):
    eq_a = parse_equation(eq1_str)
    eq_b = parse_equation(eq2_str)

    if eq_a == eq_b:
        return (True, 'identity', {})

    a_lhs, a_rhs = eq_a
    a_is_bare = (is_var(a_lhs) and not is_var(a_rhs)) or (is_var(a_rhs) and not is_var(a_lhs))

    # STEP 0: Collapse lemmas (unchanged)
    if a_is_bare:
        collapse = check_collapse_lemma(eq_a)
        if collapse is not None:
            proj = 'left_proj' if collapse == 'left_proj' else 'right_proj'
            b_lhs, b_rhs = eq_b
            collapsed_l = collapse_term(b_lhs, proj)
            collapsed_r = collapse_term(b_rhs, proj)
            if collapsed_l == collapsed_r:
                return (True, f'collapse_{proj}', {})
            else:
                return (False, f'collapse_{proj}_false', {})

    if check_constant_product_lemma(eq_a):
        b_lhs, b_rhs = eq_b
        cl = constant_product_collapse(b_lhs)
        cr = constant_product_collapse(b_rhs)
        if cl == cr:
            return (True, 'constant_product', {})
        else:
            return (False, 'constant_product_false', {})

    # STEP 0B: Improved contradiction motifs
    if a_is_bare:
        motif = check_contradiction_motifs_v3(eq_a, eq_b)
        if motif is not None:
            return (True, f'contradiction_{motif}', {})

    # STEP 1: Compute features
    fa = compute_features(eq_a)
    fb = compute_features(eq_b)

    # STEP 2: Separators (unchanged)
    if fa['LP'] and not fb['LP']:
        return (False, 'sep_LP', {})
    if fa['RP'] and not fb['RP']:
        return (False, 'sep_RP', {})
    if fa['SET'] and not fb['SET']:
        return (False, 'sep_SET', {})
    if fa['XOR'] and not fb['XOR']:
        return (False, 'sep_XOR', {})
    if fa['AB'] and not fb['AB']:
        return (False, 'sep_AB', {})

    # STEP 3: Guards
    # G1 (unchanged)
    if (fa['bare'] and not fb['bare'] and fa['size'] == fb['size'] and
        fb['vars'] < fa['vars'] and fb['imb'] > fa['imb'] and fa['XOR']):
        return (False, 'G1', {})

    # G2 (unchanged)
    if (fa['bare'] and fa['vars'] == 2 and not fb['bare'] and
        fb['vars'] > fa['vars'] and fb['size'] >= fa['size']):
        return (False, 'G2', {})

    # G3 (unchanged - critical for hard2)
    if (not fa['bare'] and fa['vars'] >= 5 and not fb['bare'] and
        fb['vars'] < fa['vars'] and fb['size'] == fa['size']):
        return (False, 'G3', {})

    # G4 (restrict slightly)
    if (not fa['bare'] and not fb['bare'] and fb['size'] == fa['size'] and
        fb['vars'] <= fa['vars'] - 2):
        return (False, 'G4', {})

    # STEP 4: REORDERED structural rules
    sA, sB = fa['size'], fb['size']
    vA, vB = fa['vars'], fb['vars']
    iA, iB = fa['imb'], fb['imb']

    bsf = get_bare_source_features(eq_a) if a_is_bare else None

    # T4 FIXED: Add Lx=FALSE
    if fa['bare'] and vA >= 4 and vB == 2:
        if bsf and not bsf['Lx']:
            return (True, 'T4', {})

    # T6 (restrict to vA >= 3)
    if fa['bare'] and not fa['RP'] and fa['XOR'] and vB == 2 and fb['RP'] and vA >= 3:
        return (True, 'T6', {})

    # T7: REMOVED (25% accuracy)

    # T8 (unchanged for now)
    if vA == 3 and not fa['XOR'] and fb['bare'] and not fb['RP']:
        return (True, 'T8', {})

    # KEY CHANGE: Move T1 BEFORE F1
    # T1: bare(A), vA>=3, sB>sA → TRUE
    if fa['bare'] and vA >= 3 and sB > sA:
        return (True, 'T1', {})

    # F1 (unchanged position relative to T1, but now T1 catches some cases first)
    if vB == vA:
        return (False, 'F1', {})

    # F2: REMOVED (33.6% accuracy)

    # F3
    if sB < sA:
        return (False, 'F3', {})

    # T2
    if fa['bare'] and fb['bare'] and vA >= 3 and vB > vA and iB > iA:
        return (True, 'T2', {})

    # T5: REMOVED (21.7% accuracy)

    # STEP 5: Extended rules
    a_lhs_vars = tree_vars(eq_a[0])
    a_rhs_vars = tree_vars(eq_a[1])
    a_all_counts = Counter(a_lhs_vars + a_rhs_vars)
    uniform = len(set(a_all_counts.values())) == 1

    if uniform and vB < vA:
        b_lhs, b_rhs = eq_b
        b_is_bare_xform = False
        if is_var(b_lhs) and not is_var(b_rhs):
            if not is_var(b_rhs) and is_var(b_rhs[1]) and b_rhs[1] == b_lhs:
                b_is_bare_xform = True
        elif is_var(b_rhs) and not is_var(b_lhs):
            if not is_var(b_lhs) and is_var(b_lhs[1]) and b_lhs[1] == b_rhs:
                b_is_bare_xform = True
        if b_is_bare_xform:
            return (True, 'D3', {})

    # NEW: For bare source with vA >= 5 and no separator/guard fired,
    # the source almost certainly trivializes
    if fa['bare'] and vA >= 5:
        return (True, 'NR_bare_v5', {})

    # NEW: For bare source with vA >= 4, Lx=FALSE, and no separator/guard fired
    if fa['bare'] and vA >= 4 and bsf and not bsf['Lx']:
        return (True, 'NR_bare_v4_nolx', {})

    # D4: default FALSE
    return (False, 'D4_default', {})


def evaluate_dataset(filepath):
    correct = 0
    total = 0
    errors = []
    rule_stats = Counter()

    with open(filepath) as f:
        for line in f:
            row = json.loads(line)
            verdict, rule, _ = predict_v3(row['equation1'], row['equation2'])
            actual = row['answer']
            rule_stats[rule] += 1
            if verdict == actual:
                correct += 1
            else:
                errors.append({
                    'id': row['id'], 'eq1': row['equation1'], 'eq2': row['equation2'],
                    'actual': actual, 'predicted': verdict, 'rule': rule,
                })
            total += 1

    return {
        'correct': correct, 'total': total,
        'accuracy': correct / total if total > 0 else 0,
        'errors': errors, 'rule_stats': dict(rule_stats),
    }


if __name__ == '__main__':
    datasets = [
        ('normal', '/workspaces/math-distillation-v2-0a91/data_normal.jsonl'),
        ('hard1', '/workspaces/math-distillation-v2-0a91/data_hard1.jsonl'),
        ('hard2', '/workspaces/math-distillation-v2-0a91/data_hard2.jsonl'),
        ('hard3', '/workspaces/math-distillation-v2-0a91/data_hard3.jsonl'),
    ]

    for name, path in datasets:
        result = evaluate_dataset(path)
        fp = sum(1 for e in result['errors'] if e['predicted'] == True)
        fn_count = sum(1 for e in result['errors'] if e['predicted'] == False)
        print(f"\n{'='*60}")
        print(f"Dataset: {name}")
        print(f"Accuracy: {result['correct']}/{result['total']} = {result['accuracy']:.4f}")
        print(f"FP: {fp}, FN: {fn_count}")
        for rule, count in sorted(result['rule_stats'].items(), key=lambda x: -x[1]):
            print(f"  {rule}: {count}")
