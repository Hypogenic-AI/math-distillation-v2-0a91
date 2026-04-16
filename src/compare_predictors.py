"""Compare the cheatsheet predictor with the computational predictor."""
import json
import sys
sys.path.insert(0, '/workspaces/math-distillation-v2-0a91/code/math-distillation-d448-claude/src')
from final_predictor import predict_implication_v3
from improved_predictor_v5 import predict_v5

# Load hard3
results = []
with open('/workspaces/math-distillation-v2-0a91/data_hard3.jsonl') as f:
    for line in f:
        row = json.loads(line)
        # Cheatsheet prediction
        cs_verdict, cs_rule, _ = predict_v5(row['equation1'], row['equation2'])
        # Computational prediction
        comp_prob = predict_implication_v3(row['equation1'], row['equation2'])
        comp_verdict = comp_prob > 0.5
        actual = row['answer']

        results.append({
            'id': row['id'],
            'eq1': row['equation1'],
            'eq2': row['equation2'],
            'actual': actual,
            'cs_verdict': cs_verdict,
            'cs_rule': cs_rule,
            'comp_prob': comp_prob,
            'comp_verdict': comp_verdict,
        })

# Compute accuracies
cs_correct = sum(1 for r in results if r['cs_verdict'] == r['actual'])
comp_correct = sum(1 for r in results if r['comp_verdict'] == r['actual'])
print(f"Cheatsheet v5: {cs_correct}/400 = {cs_correct/400:.4f}")
print(f"Computational: {comp_correct}/400 = {comp_correct/400:.4f}")

# Cases where computational is right but cheatsheet is wrong
comp_right_cs_wrong = [r for r in results if r['comp_verdict'] == r['actual'] and r['cs_verdict'] != r['actual']]
print(f"\nComputational correct, cheatsheet wrong: {len(comp_right_cs_wrong)}")

# What rules are these cases hitting?
from collections import Counter
rules = Counter(r['cs_rule'] for r in comp_right_cs_wrong)
for rule, count in rules.most_common():
    print(f"  {rule}: {count}")

# Focus on the most impactful: D4_default FN where comp says TRUE
d4_fn_comp_true = [r for r in comp_right_cs_wrong if r['cs_rule'] == 'D4_default' and r['actual'] == True]
print(f"\nD4 FN where computational also says TRUE: {len(d4_fn_comp_true)}")
for r in d4_fn_comp_true[:10]:
    print(f"  comp_prob={r['comp_prob']:.3f}: {r['eq1']}  =>  {r['eq2']}")

# F1 FN where comp says TRUE
f1_fn_comp_true = [r for r in comp_right_cs_wrong if r['cs_rule'] == 'F1' and r['actual'] == True]
print(f"\nF1 FN where computational also says TRUE: {len(f1_fn_comp_true)}")
for r in f1_fn_comp_true[:10]:
    print(f"  comp_prob={r['comp_prob']:.3f}: {r['eq1']}  =>  {r['eq2']}")

# Cases where both are wrong
both_wrong = [r for r in results if r['cs_verdict'] != r['actual'] and r['comp_verdict'] != r['actual']]
print(f"\nBoth wrong: {len(both_wrong)}")

# Cases where cheatsheet is right but computational is wrong
cs_right_comp_wrong = [r for r in results if r['cs_verdict'] == r['actual'] and r['comp_verdict'] != r['actual']]
print(f"Cheatsheet correct, computational wrong: {len(cs_right_comp_wrong)}")
