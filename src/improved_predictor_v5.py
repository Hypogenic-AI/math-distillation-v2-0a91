"""
Improved predictor v5 - balanced approach preserving hard2 accuracy.
"""
import json
from collections import Counter
from cheatsheet_predictor import (
    parse_equation, is_var, tree_vars, tree_vars_set,
    compute_features, get_bare_source_features, normalize_bare_law,
    check_collapse_lemma, collapse_term, check_constant_product_lemma,
    constant_product_collapse, rename_vars, has_square
)


def check_contradiction_motifs_v5(eq_a, eq_b):
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

    fb = compute_features(eq_b)

    # C1: add topShape != m-m
    if rv == 4 and not lx and not rx and ts != 'm-m':
        return 'C1'

    # C2: unchanged
    if rv == 3 and rt == '113' and not lx and not rx:
        return 'C2'

    # C3: add rv >= 3
    if not lx and xt == 'left' and sq and ts == 'm-v' and rv >= 3:
        return 'C3'

    # C4: unchanged (100%)
    if rv == 3 and rt == '112' and not lx and not rx and xt == 'right' and ts == 'v-m':
        return 'C4'

    # C5: unchanged
    if rv == 4 and rt == '1112' and not lx and not rx and xt == 'right' and ts == 'v-m':
        return 'C5'

    # C6: add Rx=FALSE (removes all 20 FPs)
    if rv == 3 and xt == 'right' and ts == 'v-m' and xc == 2 and not rx:
        return 'C6'

    # C7: unchanged (100%)
    if rv == 3 and not lx and not rx and xt == 'left' and ts == 'm-v' and xc == 2:
        return 'C7'

    # C8: REMOVED (too unreliable everywhere)

    # C9: Keep but add restrictions: not XOR_B, not square(A), iB >= 3
    if (rv == 3 and rt == '122' and lx and not rx and xt == 'both' and ts == 'v-m'
        and not fb['XOR'] and not sq and fb['imb'] >= 3):
        return 'C9'

    # C10: add RP_B=TRUE
    if rv == 3 and rt == '122' and not lx and rx and xc == 2 and fb['RP']:
        return 'C10'

    # C13: add RP_B=TRUE
    if rv == 4 and rt == '1112' and not lx and rx and fb['RP']:
        return 'C13'

    # C14: REMOVED (too unreliable)

    return None


def predict_v5(eq1_str, eq2_str):
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
            cl = collapse_term(b_lhs, proj)
            cr = collapse_term(b_rhs, proj)
            if cl == cr:
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
        motif = check_contradiction_motifs_v5(eq_a, eq_b)
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
    if (fa['bare'] and not fb['bare'] and fa['size'] == fb['size'] and
        fb['vars'] < fa['vars'] and fb['imb'] > fa['imb'] and fa['XOR']):
        return (False, 'G1', {})

    if (fa['bare'] and fa['vars'] == 2 and not fb['bare'] and
        fb['vars'] > fa['vars'] and fb['size'] >= fa['size']):
        return (False, 'G2', {})

    if (not fa['bare'] and fa['vars'] >= 5 and not fb['bare'] and
        fb['vars'] < fa['vars'] and fb['size'] == fa['size']):
        return (False, 'G3', {})

    if (not fa['bare'] and not fb['bare'] and fb['size'] == fa['size'] and
        fb['vars'] <= fa['vars'] - 2):
        return (False, 'G4', {})

    # STEP 4: Structural rules (REORDERED)
    sA, sB = fa['size'], fb['size']
    vA, vB = fa['vars'], fb['vars']
    iA, iB = fa['imb'], fb['imb']

    bsf = get_bare_source_features(eq_a) if a_is_bare else None

    # T4: add Lx=FALSE
    if fa['bare'] and vA >= 4 and vB == 2 and bsf and not bsf['Lx']:
        return (True, 'T4', {})

    # T6: restrict to vA >= 3
    if fa['bare'] and not fa['RP'] and fa['XOR'] and vB == 2 and fb['RP'] and vA >= 3:
        return (True, 'T6', {})

    # T7: REMOVED (25% accuracy)

    # T8: unchanged
    if vA == 3 and not fa['XOR'] and fb['bare'] and not fb['RP']:
        return (True, 'T8', {})

    # T1: MOVED BEFORE F1
    if fa['bare'] and vA >= 3 and sB > sA:
        return (True, 'T1', {})

    # F1: unchanged
    if vB == vA:
        return (False, 'F1', {})

    # F2: REMOVED
    # (was: iB < iA → FALSE, only 33.6% accurate)

    # F3: unchanged
    if sB < sA:
        return (False, 'F3', {})

    # T2: unchanged
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
            verdict, rule, _ = predict_v5(row['equation1'], row['equation2'])
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

    print("V5 RESULTS (vs baseline):")
    baselines = {'normal': 0.710, 'hard1': 0.652, 'hard2': 0.995, 'hard3': 0.5275}
    for name, path in datasets:
        result = evaluate_dataset(path)
        fp = sum(1 for e in result['errors'] if e['predicted'] == True)
        fn = sum(1 for e in result['errors'] if e['predicted'] == False)
        delta = result['accuracy'] - baselines[name]
        print(f"\n{name}: {result['correct']}/{result['total']} = {result['accuracy']:.4f} "
              f"(baseline {baselines[name]:.4f}, delta {delta:+.4f}) FP:{fp} FN:{fn}")
        for rule, count in sorted(result['rule_stats'].items(), key=lambda x: -x[1])[:15]:
            print(f"  {rule}: {count}")
