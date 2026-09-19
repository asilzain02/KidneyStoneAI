# EXP15_EFFICIENTNET_B2_320

## Objective
Tests whether a larger backbone and higher resolution preserve fine-grained details for stone discrimination.

## Model
EfficientNet-B2 (320x320). 4-class output.

## Execution
```powershell
# Train
python ai-engine/experiments/classification/EXP15_EFFICIENTNET_B2_320/train_exp15.py

# Evaluate
python ai-engine/experiments/classification/EXP15_EFFICIENTNET_B2_320/evaluate_exp15.py
```
