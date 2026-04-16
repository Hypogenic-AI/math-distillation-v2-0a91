"""Verify collapse lemma additions are correct."""
import itertools

def check_eq(table, eq_str):
    """Check if equation holds for all variable assignments in magma."""
    from cheatsheet_predictor import parse_equation, tree_vars_set, is_var

    eq = parse_equation(eq_str)
    vars_list = sorted(tree_vars_set(eq[0]) | tree_vars_set(eq[1]))
    sz = len(table)
    var_idx = {v: i for i, v in enumerate(vars_list)}

    def ev(t, vals):
        if isinstance(t, str):
            return vals[var_idx[t]]
        return table[ev(t[1], vals)][ev(t[2], vals)]

    for vals in itertools.product(range(sz), repeat=len(vars_list)):
        if ev(eq[0], vals) != ev(eq[1], vals):
            return False
    return True

# Test: x = y * x implies right projection
print("=== Verifying x = y * x → RIGHT PROJECTION ===")
# Right projection: a*b = b
right_proj_2 = [[0, 1], [0, 1]]  # a*b = b for size 2
right_proj_3 = [[0, 1, 2], [0, 1, 2], [0, 1, 2]]  # a*b = b for size 3

# Check that right projection satisfies x = y * x
assert check_eq(right_proj_2, "x = y * x"), "Right proj size 2 should satisfy x = y*x"
assert check_eq(right_proj_3, "x = y * x"), "Right proj size 3 should satisfy x = y*x"
print("  Right projection satisfies x = y * x: ✓")

# Check: does x = y * x force right projection?
# Search ALL size-2 magmas that satisfy x = y * x
satisfying = []
for i in range(16):
    table = [[(i >> (2*r+c)) & 1 for c in range(2)] for r in range(2)]
    if check_eq(table, "x = y * x"):
        satisfying.append(table)
        # Check if it's right projection
        is_rp = all(table[r][c] == c for r in range(2) for c in range(2))
        print(f"  Size-2 magma satisfying x=y*x: {table}, is right proj: {is_rp}")

# Check size-3
count_3 = 0
non_rp_3 = []
for vals in itertools.product(range(3), repeat=9):
    table = [[vals[r*3+c] for c in range(3)] for r in range(3)]
    if check_eq(table, "x = y * x"):
        count_3 += 1
        is_rp = all(table[r][c] == c for r in range(3) for c in range(3))
        if not is_rp:
            non_rp_3.append(table)
print(f"  Size-3 magmas satisfying x=y*x: {count_3}, non-right-proj: {len(non_rp_3)}")

# Test: x = x * y implies left projection
print("\n=== Verifying x = x * y → LEFT PROJECTION ===")
left_proj_2 = [[0, 0], [1, 1]]  # a*b = a for size 2

assert check_eq(left_proj_2, "x = x * y"), "Left proj should satisfy x = x*y"
print("  Left projection satisfies x = x * y: ✓")

satisfying_lp = []
for i in range(16):
    table = [[(i >> (2*r+c)) & 1 for c in range(2)] for r in range(2)]
    if check_eq(table, "x = x * y"):
        satisfying_lp.append(table)
        is_lp = all(table[r][c] == r for r in range(2) for c in range(2))
        print(f"  Size-2 magma satisfying x=x*y: {table}, is left proj: {is_lp}")

# Verify the original collapse lemmas too
print("\n=== Verifying original collapse lemmas ===")
print("x = x*((y*z)*(z*z)):")
assert check_eq(left_proj_2, "x = x * ((y * z) * (z * z))"), "Left proj should satisfy this"
assert check_eq(left_proj_2, "x = x * (y * (z * (x * y)))"), "Left proj should satisfy this"
print("  Left projection satisfies both original LP patterns: ✓")

print("x = (((y*z)*x)*z)*x:")
assert check_eq(right_proj_2, "x = (((y * z) * x) * z) * x"), "Right proj should satisfy this"
print("  Right projection satisfies original RP pattern: ✓")
