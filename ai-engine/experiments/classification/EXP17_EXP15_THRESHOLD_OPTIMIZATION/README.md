# EXP17_EXP15_THRESHOLD_OPTIMIZATION

## Objective
Optimizes the operating threshold (Stone `P > X`) programmatically using INTERNAL validation data to safely maximize performance constraints, avoiding test-set cheating.
Bypasses manual threshold hunting by sweeping probability distribution across 0.10 to 0.90 points and anchoring the F1 maximum.

## Strategy Guarantee
* NO TRAINING executed.
* NO external labels inspected for tuning.

## Execution
```powershell
# Phase 1: Identify Optimal Threshold
python ai-engine/experiments/classification/EXP17_EXP15_THRESHOLD_OPTIMIZATION/threshold_optimizer.py

# Phase 2: Execute Validated Threshold externally
python ai-engine/experiments/classification/EXP17_EXP15_THRESHOLD_OPTIMIZATION/evaluate_exp17.py
```
