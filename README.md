# Mathematics Distillation Challenge v2

Iterative improvement of a rule-based cheatsheet for the SAIR Mathematics Distillation Challenge Stage 1. The cheatsheet helps an LLM determine whether one equational law implies another over all magmas.

## Key Results

- **Hard3**: 52.75% → 63.5% (+10.75 pp)
- **Normal**: 71.0% → 82.4% (+11.4 pp)  
- **Hard1**: 65.2% → 73.9% (+8.7 pp)
- **Hard2**: 99.5% → 95.5% (-4.0 pp)
- **Overall**: 69.8% → 79.1% (+9.3 pp)

## Files

- `results/improved_cheatsheet.txt` - The final improved cheatsheet (7.8KB)
- `results/evaluation_summary.json` - Evaluation results
- `src/cheatsheet_predictor.py` - Python implementation of baseline cheatsheet
- `src/improved_predictor_v7.py` - Python implementation of improved cheatsheet
- `src/diagnose_errors.py` - Error diagnosis scripts
- `src/motif_analysis.py` - Per-motif feature analysis
- `REPORT.md` - Full research report

## Reproducing

```bash
source .venv/bin/activate
cd src
python improved_predictor_v7.py  # Runs evaluation on all 4 splits
```
