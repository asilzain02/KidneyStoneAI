# External Dataset Evaluation

This document outlines the independent testing pipeline for measuring the `EfficientNet-B0` classification weights generalizing capability completely externally via the **Axial CT Kidney Stone Dataset**.

## Dataset Mapping Constraints

1. **Dataset Purpose:** Measure generalization capacity externally without utilizing the target dataset for retraining.
2. **Dataset Location:** Standardized natively to:
   `datasets/raw/classification/additional_dataset/Kidney Stone Dataset/`
3. **Original vs Augmented:** The provided subset structures itself via two folders (`Original` & `Augmented`). 
4. **Why ONLY Original:** Augmented derivatives are intrinsically chained dependent variants of the original samples. If included in generalized accuracy assessments it inflates measurements artificially creating heavy bias. Thus `Augmented/` is algorithmically locked out and refused natively by the Pipeline.

## Model Cross-Mapping (4-Class to Binary)

The base architecture leverages four classes (`Normal`, `Cyst`, `Stone`, `Tumor`). The external validation holds solely binary subsets mapping Kidney Stones presence via `Stone` & `Non-Stone`.

**Exact Transformation Binding Strategy:**

- `Stone` logits mapping -> **STONE**
- `Normal` logits mapping -> **NON_STONE**
- `Cyst` logits mapping -> **NON_STONE**
- `Tumor` logits mapping -> **NON_STONE**

## Evaluation Metrics Output

Inference logs resolve the standard properties natively bound: 
- Accuracy
- Precision
- Recall (Sensitivity)
- Specificity
- F1-Score
- ROC-AUC
- Detailed Confusion Matrices separating precisely `TN`, `TP`, `FN`, `FP`.

## Execution Semantics

This CLI script restricts training logic natively via constraints. It only opens inference mapping blocks. It absolutely does **NOT** rewrite PyTorch Weights under any circumstances. 

To run evaluations explicitly:

```bash
python ai-engine/evaluation/external_evaluator.py
```

### Outputs Generate Here:

- `outputs/evaluation/external/external_results.json` (Structured JSON outputs mapping logic).
- `outputs/evaluation/external/external_predictions.csv` (Fully recorded raw logic probabilities/confidence per item).
