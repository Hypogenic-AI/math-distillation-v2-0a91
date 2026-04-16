"""
Python implementation of the cheatsheet rules for equational implication over magmas.
Implements STEP 0 through STEP 5 exactly as described in the cheatsheet.
"""
import re
import json
import sys
from collections import Counter

# ============================================================
# PARSING
# ============================================================

def parse_term(s):
    """Parse a term string into a tree. Variables are strings, products are ('*', left, right)."""
    s = s.strip()
    tokens = []
    i = 0
    while i < len(s):
        if s[i] in '()*=':
            tokens.append(s[i])
            i += 1
        elif s[i].isalpha():
            tokens.append(s[i])
            i += 1
        else:
            i += 1
    pos = [0]
    def parse_expr():
        left = parse_primary()
        while pos[0] < len(tokens) and tokens[pos[0]] == '*':
            pos[0] += 1
            right = parse_primary()
            left = ('*', left, right)
        return left
    def parse_primary():
        if pos[0] >= len(tokens):
            return 'x'
        if tokens[pos[0]] == '(':
            pos[0] += 1
            expr = parse_expr()
            if pos[0] < len(tokens) and tokens[pos[0]] == ')':
                pos[0] += 1
            return expr
        else:
            var = tokens[pos[0]]
            pos[0] += 1
            return var
    return parse_expr()

def parse_equation(eq_str):
    sides = eq_str.split('=')
    return (parse_term(sides[0]), parse_term(sides[1]))

def term_to_str(t):
    if isinstance(t, str):
        return t
    return f"({term_to_str(t[1])} * {term_to_str(t[2])})"

def is_var(t):
    return isinstance(t, str)

def tree_vars(t):
    if isinstance(t, str):
        return [t]
    return tree_vars(t[1]) + tree_vars(t[2])

def tree_vars_set(t):
    return set(tree_vars(t))

def leftmost_var(t):
    if isinstance(t, str):
        return t
    return leftmost_var(t[1])

def rightmost_var(t):
    if isinstance(t, str):
        return t
    return rightmost_var(t[2])

def has_square(t):
    """Check if term contains a subterm of the form u*u where u is any term."""
    if isinstance(t, str):
        return False
    if t[1] == t[2]:
        return True
    return has_square(t[1]) or has_square(t[2])

def rename_vars(t, mapping):
    """Rename variables in a term according to mapping."""
    if isinstance(t, str):
        return mapping.get(t, t)
    return ('*', rename_vars(t[1], mapping), rename_vars(t[2], mapping))

def get_var_order_in_term(t):
    """Get variables in order of first appearance in a term."""
    seen = []
    for v in tree_vars(t):
        if v not in seen:
            seen.append(v)
    return seen

# ============================================================
# STEP 0: SOURCE-COLLAPSE LEMMAS
# ============================================================

def normalize_bare_law(eq):
    """Normalize a bare law: single var on left, rename bare var to x, others by first appearance on product side."""
    lhs, rhs = eq
    if is_var(lhs) and not is_var(rhs):
        bare_var = lhs
        product_side = rhs
    elif is_var(rhs) and not is_var(lhs):
        bare_var = rhs
        product_side = lhs
    else:
        return None

    # Build mapping: bare_var -> x, then other vars by first appearance on product side
    product_vars = tree_vars(product_side)
    mapping = {bare_var: 'x'}
    next_name = ['y', 'z', 'w', 'u', 'v', 'a', 'b', 'c', 'd', 'e']
    name_idx = 0
    for v in product_vars:
        if v not in mapping:
            mapping[v] = next_name[name_idx] if name_idx < len(next_name) else f'v{name_idx}'
            name_idx += 1

    normalized_product = rename_vars(product_side, mapping)
    return ('x', normalized_product)

def check_collapse_lemma(eq):
    """Check if equation matches a known collapse lemma. Returns 'left_proj', 'right_proj', or None."""
    norm = normalize_bare_law(eq)
    if norm is None:
        return None

    x_term = norm[0]  # should be 'x'
    prod = norm[1]
    prod_str = term_to_str(prod)

    # LEFT PROJECTION patterns
    # x = x*(y*(z*(x*y)))
    lp1 = ('*', 'x', ('*', 'y', ('*', 'z', ('*', 'x', 'y'))))
    # x = x*((y*z)*(z*z))
    lp2 = ('*', 'x', ('*', ('*', 'y', 'z'), ('*', 'z', 'z')))

    if prod == lp1 or prod == lp2:
        return 'left_proj'

    # RIGHT PROJECTION
    # x = (((y*z)*x)*z)*x
    rp1 = ('*', ('*', ('*', ('*', 'y', 'z'), 'x'), 'z'), 'x')

    if prod == rp1:
        return 'right_proj'

    return None

def collapse_term(t, projection):
    """Collapse a term under left or right projection."""
    if isinstance(t, str):
        return t
    if projection == 'left_proj':
        return collapse_term(t[1], projection)
    else:  # right_proj
        return collapse_term(t[2], projection)

def check_constant_product_lemma(eq):
    """Check if equation matches the non-bare constant-product family."""
    lhs, rhs = eq
    if is_var(lhs) or is_var(rhs):
        return False

    # Normalize by first appearance
    all_vars = tree_vars(lhs) + tree_vars(rhs)
    mapping = {}
    names = ['x', 'y', 'z', 'w', 'u', 'v', 'a', 'b', 'c', 'd']
    idx = 0
    for v in all_vars:
        if v not in mapping:
            mapping[v] = names[idx] if idx < len(names) else f'v{idx}'
            idx += 1

    norm_lhs = rename_vars(lhs, mapping)
    norm_rhs = rename_vars(rhs, mapping)

    # Check: left side is exactly x*y
    if norm_lhs != ('*', 'x', 'y'):
        return False

    # Check: right side is a product term U * V
    if is_var(norm_rhs):
        return False

    U = norm_rhs[1]
    V = norm_rhs[2]

    # Every occurrence of x on the right side lies in V and none in U
    u_vars = tree_vars_set(U)
    v_vars = tree_vars_set(V)

    if 'x' in u_vars:
        return False
    if 'x' not in v_vars:
        return False

    return True

def constant_product_collapse(t):
    """Under CONSTANT-PRODUCT collapse: non-variable products -> 'c', variables stay."""
    if isinstance(t, str):
        return t
    return 'c'

# ============================================================
# STEP 0B: BARE-SOURCE CONTRADICTION MOTIFS
# ============================================================

def get_bare_source_features(eq):
    """Compute features for STEP 0B. Returns dict or None if not bare."""
    lhs, rhs = eq

    # Ensure bare: one side is a single variable
    if is_var(lhs) and not is_var(rhs):
        bare_var = lhs
        product_side = rhs
    elif is_var(rhs) and not is_var(lhs):
        bare_var = rhs
        product_side = lhs
    else:
        return None

    # x is the distinguished variable (the bare side)
    x = bare_var

    prod_vars = tree_vars(product_side)
    prod_vars_set = set(prod_vars)

    # rhsVars
    rhs_vars = len(prod_vars_set)

    # rhsTotals: sorted occurrence counts
    counts = Counter(prod_vars)
    rhs_totals = ''.join(str(c) for c in sorted(counts.values()))

    # Lx, Rx
    lx = leftmost_var(product_side) == x
    rx = rightmost_var(product_side) == x

    # xTop
    if not is_var(product_side):
        U = product_side[1]
        V = product_side[2]
        x_in_U = x in tree_vars_set(U)
        x_in_V = x in tree_vars_set(V)
        if x_in_U and x_in_V:
            x_top = 'both'
        elif x_in_U:
            x_top = 'left'
        elif x_in_V:
            x_top = 'right'
        else:
            x_top = 'none'
    else:
        x_top = 'none'

    # square
    square = has_square(product_side)

    # topShape
    if not is_var(product_side):
        U = product_side[1]
        V = product_side[2]
        if is_var(U) and not is_var(V):
            top_shape = 'v-m'
        elif not is_var(U) and is_var(V):
            top_shape = 'm-v'
        elif not is_var(U) and not is_var(V):
            top_shape = 'm-m'
        else:
            top_shape = 'v-v'
    else:
        top_shape = 'var'

    # x_count on product side
    x_count = counts.get(x, 0)

    return {
        'rhs_vars': rhs_vars,
        'rhs_totals': rhs_totals,
        'Lx': lx,
        'Rx': rx,
        'x_top': x_top,
        'square': square,
        'top_shape': top_shape,
        'x_count': x_count,
        'counts': counts,
        'x': x,
    }

def check_contradiction_motifs(eq_a, eq_b):
    """Check STEP 0B contradiction motifs. Returns True if any motif fires, False/None otherwise."""
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

    # C1
    if rv == 4 and not lx and not rx:
        return 'C1'

    # C2
    if rv == 3 and rt == '113' and not lx and not rx:
        return 'C2'

    # C3
    if not lx and xt == 'left' and sq and ts == 'm-v':
        return 'C3'

    # C4
    if rv == 3 and rt == '112' and not lx and not rx and xt == 'right' and ts == 'v-m':
        return 'C4'

    # C5
    if rv == 4 and rt == '1112' and not lx and not rx and xt == 'right' and ts == 'v-m':
        return 'C5'

    # C6
    if rv == 3 and xt == 'right' and ts == 'v-m' and xc == 2:
        return 'C6'

    # C7
    if rv == 3 and not lx and not rx and xt == 'left' and ts == 'm-v' and xc == 2:
        return 'C7'

    # C8
    if rv == 3 and lx and xt == 'left' and ts == 'm-v':
        return 'C8'

    # C9
    if rv == 3 and rt == '122' and lx and not rx and xt == 'both' and ts == 'v-m':
        return 'C9'

    # C10
    if rv == 3 and rt == '122' and not lx and rx and xc == 2:
        return 'C10'

    # C11 (subsumed by C2 when lx=false, rx=false)
    if rv == 3 and rt == '113' and not lx and not rx and xt == 'right' and ts == 'v-m':
        return 'C11'

    # C12 (subsumed by C2)
    if rv == 3 and rt == '113' and not lx and not rx and xt == 'left' and ts == 'm-v':
        return 'C12'

    # C13
    if rv == 4 and rt == '1112' and not lx and rx:
        return 'C13'

    # C14 - depends on B being bare
    b_lhs, b_rhs = eq_b
    b_is_bare = (is_var(b_lhs) and not is_var(b_rhs)) or (is_var(b_rhs) and not is_var(b_lhs))
    if b_is_bare and rv == 3 and rt == '113' and rx and not sq:
        return 'C14'

    return None

# ============================================================
# STEP 1: COMPUTE FEATURES
# ============================================================

def compute_features(eq):
    """Compute features for an equation as described in STEP 1."""
    lhs, rhs = eq

    lhs_vars = tree_vars(lhs)
    rhs_vars = tree_vars(rhs)

    all_vars_set = set(lhs_vars) | set(rhs_vars)

    size = len(lhs_vars) + len(rhs_vars)
    n_vars = len(all_vars_set)

    # imbalance
    lhs_counts = Counter(lhs_vars)
    rhs_counts = Counter(rhs_vars)
    imb = 0
    for v in all_vars_set:
        imb += abs(lhs_counts.get(v, 0) - rhs_counts.get(v, 0))

    # bare
    bare = (is_var(lhs) and not is_var(rhs)) or (is_var(rhs) and not is_var(lhs))
    # Also handle both vars case
    if is_var(lhs) and is_var(rhs):
        bare = True  # edge case

    # LP: leftmost variable matches across sides
    lp = leftmost_var(lhs) == leftmost_var(rhs)

    # RP: rightmost variable matches across sides
    rp = rightmost_var(lhs) == rightmost_var(rhs)

    # SET: both sides use same variable set
    set_match = set(lhs_vars) == set(rhs_vars)

    # XOR: every variable has same parity on both sides
    xor_match = True
    for v in all_vars_set:
        if lhs_counts.get(v, 0) % 2 != rhs_counts.get(v, 0) % 2:
            xor_match = False
            break

    # AB: every variable has exactly the same count on both sides
    ab_match = True
    for v in all_vars_set:
        if lhs_counts.get(v, 0) != rhs_counts.get(v, 0):
            ab_match = False
            break

    return {
        'size': size,
        'vars': n_vars,
        'imb': imb,
        'bare': bare,
        'LP': lp,
        'RP': rp,
        'SET': set_match,
        'XOR': xor_match,
        'AB': ab_match,
    }

# ============================================================
# MAIN PREDICTOR
# ============================================================

def predict(eq1_str, eq2_str):
    """
    Predict whether eq1 implies eq2 over all magmas.
    Returns (verdict: bool, rule: str, details: dict)
    """
    eq_a = parse_equation(eq1_str)
    eq_b = parse_equation(eq2_str)

    # Quick identity check
    if eq_a == eq_b:
        return (True, 'identity', {})

    # STEP 0: SOURCE-COLLAPSE LEMMAS
    # Check if A is bare
    a_lhs, a_rhs = eq_a
    a_is_bare = (is_var(a_lhs) and not is_var(a_rhs)) or (is_var(a_rhs) and not is_var(a_lhs))

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

    # NON-BARE CONSTANT-PRODUCT LEMMA
    if check_constant_product_lemma(eq_a):
        b_lhs, b_rhs = eq_b
        cl = constant_product_collapse(b_lhs)
        cr = constant_product_collapse(b_rhs)
        if cl == cr:
            return (True, 'constant_product', {})
        else:
            return (False, 'constant_product_false', {})

    # STEP 0B: BARE-SOURCE CONTRADICTION MOTIFS
    if a_is_bare:
        motif = check_contradiction_motifs(eq_a, eq_b)
        if motif is not None:
            return (True, f'contradiction_{motif}', {})

    # STEP 1: COMPUTE FEATURES
    fa = compute_features(eq_a)
    fb = compute_features(eq_b)

    # STEP 2: SEPARATOR TESTS
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

    # STEP 3: FALSE GUARDS
    # G1
    if (fa['bare'] and not fb['bare'] and fa['size'] == fb['size'] and
        fb['vars'] < fa['vars'] and fb['imb'] > fa['imb'] and fa['XOR']):
        return (False, 'G1', {})

    # G2
    if (fa['bare'] and fa['vars'] == 2 and not fb['bare'] and
        fb['vars'] > fa['vars'] and fb['size'] >= fa['size']):
        return (False, 'G2', {})

    # G3
    if (not fa['bare'] and fa['vars'] >= 5 and not fb['bare'] and
        fb['vars'] < fa['vars'] and fb['size'] == fa['size']):
        return (False, 'G3', {})

    # G4
    if (not fa['bare'] and not fb['bare'] and fb['size'] == fa['size'] and
        fb['vars'] <= fa['vars'] - 2):
        return (False, 'G4', {})

    # STEP 4: STRUCTURAL RULES
    sA, sB = fa['size'], fb['size']
    vA, vB = fa['vars'], fb['vars']
    iA, iB = fa['imb'], fb['imb']

    # T4
    if fa['bare'] and vA >= 4 and vB == 2:
        return (True, 'T4', {})

    # T6
    if fa['bare'] and not fa['RP'] and fa['XOR'] and vB == 2 and fb['RP']:
        return (True, 'T6', {})

    # T7
    if not fa['bare'] and vA == 3 and iA == 2 and vB == 3 and not fb['XOR']:
        return (True, 'T7', {})

    # T8
    if vA == 3 and not fa['XOR'] and fb['bare'] and not fb['RP']:
        return (True, 'T8', {})

    # F1
    if vB == vA:
        return (False, 'F1', {})

    # F2
    if iB < iA:
        return (False, 'F2', {})

    # F3
    if sB < sA:
        return (False, 'F3', {})

    # T1
    if fa['bare'] and vA >= 3 and sB > sA:
        return (True, 'T1', {})

    # T2
    if fa['bare'] and fb['bare'] and vA >= 3 and vB > vA and iB > iA:
        return (True, 'T2', {})

    # T5
    if vB < vA and iB > iA:
        return (True, 'T5', {})

    # STEP 5: EXTENDED RULES
    # D3
    a_lhs_vars = tree_vars(eq_a[0])
    a_rhs_vars = tree_vars(eq_a[1])
    a_all_counts = Counter(a_lhs_vars + a_rhs_vars)
    uniform = len(set(a_all_counts.values())) == 1

    if uniform and vB < vA:
        # Check if B is bare of the form x = x * (...)
        b_lhs, b_rhs = eq_b
        b_is_bare_xform = False
        if is_var(b_lhs) and not is_var(b_rhs):
            # Check if rhs is x * (...) where x is the bare var
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
    """Evaluate the cheatsheet predictor on a JSONL dataset file."""
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

            verdict, rule, details = predict(eq1, eq2)
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
        ('normal', 'data_normal.jsonl'),
        ('hard1', 'data_hard1.jsonl'),
        ('hard2', 'data_hard2.jsonl'),
        ('hard3', 'data_hard3.jsonl'),
    ]

    for name, path in datasets:
        filepath = f'/workspaces/math-distillation-v2-0a91/{path}'
        result = evaluate_dataset(filepath)
        print(f"\n{'='*60}")
        print(f"Dataset: {name}")
        print(f"Accuracy: {result['correct']}/{result['total']} = {result['accuracy']:.4f}")
        print(f"Errors: {len(result['errors'])}")
        print(f"Rule statistics:")
        for rule, count in sorted(result['rule_stats'].items(), key=lambda x: -x[1]):
            print(f"  {rule}: {count}")

        # Count error types
        if result['errors']:
            fp = sum(1 for e in result['errors'] if e['predicted'] == True)
            fn = sum(1 for e in result['errors'] if e['predicted'] == False)
            print(f"False positives (predicted TRUE, actual FALSE): {fp}")
            print(f"False negatives (predicted FALSE, actual TRUE): {fn}")
