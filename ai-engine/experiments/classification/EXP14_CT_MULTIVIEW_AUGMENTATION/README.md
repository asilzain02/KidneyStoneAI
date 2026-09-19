# EXP14_CT_MULTIVIEW_AUGMENTATION

## Objective
Tests whether multi-view representation (original + CLAHE + soft-edge) combined with CT-safe augmentation improves external domain generalisation.

## Model
EfficientNet-B0 (3 channels input). 4-class output.

## Execution
```powershell
# Train
python ai-engine/experiments/classification/EXP14_CT_MULTIVIEW_AUGMENTATION/train_exp14.py

# Evaluate
python ai-engine/experiments/classification/EXP14_CT_MULTIVIEW_AUGMENTATION/evaluate_exp14.py
```
