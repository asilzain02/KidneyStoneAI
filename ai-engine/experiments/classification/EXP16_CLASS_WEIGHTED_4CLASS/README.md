# EXP16_CLASS_WEIGHTED_4CLASS

## Objective
Tests whether moderate inverse-sqrt-frequency class weighting in the loss function improves stone recall over baseline without causing extreme bias.

## Model
EfficientNet-B0 (224x224). 4-class output. Weighted CrossEntropyLoss.

## Execution
```powershell
# Train
python ai-engine/experiments/classification/EXP16_CLASS_WEIGHTED_4CLASS/train_exp16.py

# Evaluate
python ai-engine/experiments/classification/EXP16_CLASS_WEIGHTED_4CLASS/evaluate_exp16.py
```
