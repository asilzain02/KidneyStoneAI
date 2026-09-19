# EXP18_B2_320_CT_AUGMENTATION

## Objective
Train an EfficientNet-B2 at 320x320 architecture using CT-specific augmentation (e.g. simulated varied intensity window/leveling captures shifting constraints within [0,1], moderate spatial augmentation) to preserve and robustly evaluate performance externally.

## Core Rules
1. FRESH Model (Starts at ImageNet baseline, NOT finetuned from EXP15).
2. NO External Labels applied during threshold or augmentation adjustments.
3. Strict [batch validation = 8] threshold observed due to GPU restrictions on 320px frame processing.

## Execution
```powershell
# Train New Model
python ai-engine/experiments/classification/EXP18_B2_320_CT_AUGMENTATION/train_exp18.py

# Execute Evaluator
python ai-engine/experiments/classification/EXP18_B2_320_CT_AUGMENTATION/evaluate_exp18.py
```
