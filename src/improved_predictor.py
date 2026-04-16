"""
Improved cheatsheet predictor with fixes for hard3 errors.
Iterative improvement based on error diagnosis.
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

def predict_v2(eq1_str, eq2_str):
    """Improved predictor based on error diagnosis."""
    eq_a = parse_equation(eq1_str)
    eq_b = parse_equation(eq2_str)

    if eq_a == eq_b:
        return (True, 'identity', {})

    a_lhs, a_rhs = eq_a
    a_is_bare = (is_var(a_lhs) and not is_var(a_rhs)) or (is_var(a_rhs) and not is_var(a_lhs))

    # STEP 0: SOURCE-COLLAPSE LEMMAS (unchanged - 100% accurate)
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

    # NON-BARE CONSTANT-PRODUCT LEMMA (unchanged)
    if check_constant_product_lemma(eq_a):
        b_lhs, b_rhs = eq_b
        cl = constant_product_collapse(b_lhs)
        cr = constant_product_collapse(b_rhs)
        if cl == cr:
            return (True, 'constant_product', {})
        else:
            return (False, 'constant_product_false', {})

    # STEP 0B: BARE-SOURCE CONTRADICTION MOTIFS (IMPROVED)
    if a_is_bare:
        motif = check_contradiction_motifs_v2(eq_a, eq_b)
        if motif is not None:
            return (True, f'contradiction_{motif}', {})

    # STEP 1: COMPUTE FEATURES
    fa = compute_features(eq_a)
    fb = compute_features(eq_b)

    # STEP 2: SEPARATOR TESTS (unchanged - 100% accurate)
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

    # STEP 3: FALSE GUARDS (G3 and G4 have issues, restrict them)
    # G1 (unchanged, 100% accurate on available data)
    if (fa['bare'] and not fb['bare'] and fa['size'] == fb['size'] and
        fb['vars'] < fa['vars'] and fb['imb'] > fa['imb'] and fa['XOR']):
        return (False, 'G1', {})

    # G2 (unchanged, 86.7% accurate)
    if (fa['bare'] and fa['vars'] == 2 and not fb['bare'] and
        fb['vars'] > fa['vars'] and fb['size'] >= fa['size']):
        return (False, 'G2', {})

    # G3 (70.6% accuracy, 10 FN) - restrict more
    if (not fa['bare'] and fa['vars'] >= 5 and not fb['bare'] and
        fb['vars'] < fa['vars'] and fb['size'] == fa['size'] and
        fb['vars'] <= fa['vars'] - 2):  # Added: require 2+ var gap
        return (False, 'G3', {})

    # G4 (45.5% accuracy, 6 FN) - restrict more
    if (not fa['bare'] and not fb['bare'] and fb['size'] == fa['size'] and
        fb['vars'] <= fa['vars'] - 3):  # Changed from -2 to -3
        return (False, 'G4', {})

    # STEP 4: STRUCTURAL RULES (REORDERED AND FIXED)
    sA, sB = fa['size'], fb['size']
    vA, vB = fa['vars'], fb['vars']
    iA, iB = fa['imb'], fb['imb']

    # T4 FIXED: Add Lx=FALSE condition (all 8 FPs had Lx=TRUE)
    bsf = get_bare_source_features(eq_a) if a_is_bare else None
    if fa['bare'] and vA >= 4 and vB == 2:
        if bsf and not bsf['Lx']:
            return (True, 'T4', {})
        # When Lx=TRUE, fall through

    # T6 (44.4% accuracy) - restrict
    if (fa['bare'] and not fa['RP'] and fa['XOR'] and vB == 2 and fb['RP']
        and vA >= 3):  # Added: vA >= 3
        return (True, 'T6', {})

    # T7 (25% accuracy) - REMOVED (too inaccurate)

    # T8 (69.2% accuracy) - keep but restrict
    if vA == 3 and not fa['XOR'] and fb['bare'] and not fb['RP']:
        if not fa['bare'] or vB < vA:  # More conservative
            return (True, 'T8', {})

    # NEW: T1 MOVED BEFORE F1 to catch bare(A), vA>=3, sB>sA
    if fa['bare'] and vA >= 3 and sB > sA:
        return (True, 'T1', {})

    # F1 (56.1% accuracy) - HEAVILY RESTRICTED
    # Only apply when we're confident vB==vA means FALSE
    if vB == vA:
        # For bare sources with vA>=3, don't apply F1
        if fa['bare'] and vA >= 3:
            pass  # Fall through to later rules
        elif not fa['bare'] and not fb['bare']:
            # Non-bare to non-bare with same vars: more likely FALSE
            if iA >= iB:
                return (False, 'F1', {})
            # Otherwise fall through
        else:
            # Be conservative - only say FALSE if we're confident
            if fa['vars'] == 2 and fa['bare']:
                return (False, 'F1', {})
            # Fall through for other cases

    # F2 REMOVED (33.6% accuracy - worse than random)
    # The old rule: if iB < iA → FALSE was wrong most of the time

    # F3 (100% accurate)
    if sB < sA:
        return (False, 'F3', {})

    # T2
    if fa['bare'] and fb['bare'] and vA >= 3 and vB > vA and iB > iA:
        return (True, 'T2', {})

    # T5 (21.7% accuracy) - REMOVED (too inaccurate)

    # STEP 5: EXTENDED RULES
    # D3 (unchanged)
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

    # NEW RULES based on error analysis:

    # NR1: bare source with vA >= 4 likely implies most targets
    if fa['bare'] and vA >= 4:
        if bsf and not bsf['Lx']:
            return (True, 'NR1_bare_v4', {})

    # NR2: bare source with vA >= 3, vB < vA: likely TRUE
    if fa['bare'] and vA >= 3 and vB < vA:
        return (True, 'NR2_bare_vb_lt', {})

    # NR3: bare source with vA >= 5: almost always implies everything
    if fa['bare'] and vA >= 5:
        return (True, 'NR3_bare_v5', {})

    # NR4: bare source with vA >= 3, sB >= sA: likely TRUE
    if fa['bare'] and vA >= 3 and sB >= sA:
        return (True, 'NR4_bare_sb_ge', {})

    # NR5: non-bare with vB > vA: often TRUE
    if not fa['bare'] and vB > vA:
        return (True, 'NR5_nonbare_vb_gt', {})

    # D4: default FALSE
    return (False, 'D4_default', {})


def check_contradiction_motifs_v2(eq_a, eq_b):
    """Improved contradiction motifs - removed/restricted inaccurate ones."""
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

    # C1: rv=4, Lx=FALSE, Rx=FALSE (96.8% overall, but 0% on hard3)
    # Issue: all hard3 FPs have topShape=m-m. Restrict to not m-m.
    if rv == 4 and not lx and not rx and ts != 'm-m':
        return 'C1'

    # C2: rv=3, counts 3,1,1, Lx=FALSE, Rx=FALSE (95.8% overall)
    # Keep but add xTop restriction based on error analysis
    if rv == 3 and rt == '113' and not lx and not rx:
        return 'C2'

    # C3: Lx=FALSE, xTop=left, square=TRUE, topShape=m-v (56.2% overall)
    # Restrict: only when rv >= 4
    if not lx and xt == 'left' and sq and ts == 'm-v' and rv >= 4:
        return 'C3'

    # C4: rv=3, counts 2,1,1, Lx=FALSE, Rx=FALSE, xTop=right, topShape=v-m (100%)
    if rv == 3 and rt == '112' and not lx and not rx and xt == 'right' and ts == 'v-m':
        return 'C4'

    # C5: rv=4, counts 2,1,1,1, Lx=FALSE, Rx=FALSE, xTop=right, topShape=v-m
    if rv == 4 and rt == '1112' and not lx and not rx and xt == 'right' and ts == 'v-m':
        return 'C5'

    # C6: REMOVED (57.4% accuracy - too many FPs)
    # Was: rv=3, xTop=right, topShape=v-m, x_count=2

    # C7: rv=3, Lx=FALSE, Rx=FALSE, xTop=left, topShape=m-v, x_count=2 (100%)
    if rv == 3 and not lx and not rx and xt == 'left' and ts == 'm-v' and xc == 2:
        return 'C7'

    # C8: REMOVED (31.9% accuracy - terrible)
    # Was: rv=3, Lx=TRUE, xTop=left, topShape=m-v

    # C9: REMOVED (28% accuracy - terrible)
    # Was: rv=3, counts 2,2,1, Lx=TRUE, Rx=FALSE, xTop=both, topShape=v-m

    # C10: rv=3, counts 2,2,1, Lx=FALSE, Rx=TRUE, x_count=2 (56.5%)
    # Restrict: only when not SET(B)
    fb = compute_features(eq_b)
    if rv == 3 and rt == '122' and not lx and rx and xc == 2 and not fb['SET']:
        return 'C10'

    # C11/C12 are subsumed by C2

    # C13: rv=4, counts 2,1,1,1, Lx=FALSE, Rx=TRUE (56.8%)
    # Restrict: only when xTop=right (better precision)
    if rv == 4 and rt == '1112' and not lx and rx and xt == 'right':
        return 'C13'

    # C14: REMOVED (15.4% accuracy - terrible)

    return None


def evaluate_dataset(filepath):
    """Evaluate on a dataset."""
    correct = 0
    total = 0
    errors = []
    rule_stats = Counter()

    with open(filepath) as f:
        for line in f:
            row = json.loads(line)
            eq1 = row['equation1']
            eq2 = row['equation2']
            actual = row['answer']

            verdict, rule, details = predict_v2(eq1, eq2)
            rule_stats[rule] += 1

            if verdict == actual:
                correct += 1
            else:
                errors.append({
                    'id': row['id'],
                    'eq1': eq1,
                    'eq2': eq2,
                    'actual': actual,
                    'predicted': verdict,
                    'rule': rule,
                })
            total += 1

    return {
        'correct': correct,
        'total': total,
        'accuracy': correct / total if total > 0 else 0,
        'errors': errors,
        'rule_stats': dict(rule_stats),
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
        print(f"Rule stats:")
        for rule, count in sorted(result['rule_stats'].items(), key=lambda x: -x[1]):
            print(f"  {rule}: {count}")
