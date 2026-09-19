# EXP19 CROSS-DATASET BINARY (Cross-dataset Generalization)

## 1. Research Objective
Can a binary kidney-stone classifier trained on one CT dataset (Dataset A, Kidney Stone Dataset) generalize to a separate, independent CT dataset (Dataset B, CT-Kidney)?
This evaluates pure generalized transfer of CT calculus morphological features across acquisition domains.

## 2. Dataset A (Internal Training Dataset)
**Path:** `datasets/raw/classification/additional_dataset/Kidney Stone Dataset/Original`
*   **Split Classes:** Only the "Original" collection is selected. "Augmented" subsets are actively ignored programmatically.
*   **Binary Scope:** 
    *   `Stone` -> maps inherently to `STONE` (1)
    *   `Non-Stone` -> maps inherently to `NON_STONE` (0)
*   **Architecture Flow:** Entirely handled via explicit manifest splitting to ensure exact replicability, stratified cleanly 70/15/15. Patient/study metadata is missing in the source structure, thus deterministic mapping with collision detection protects the boundary.

## 3. Dataset B (Final EXTERNAL Test Dataset)
**Path:** `datasets/raw/classification/ct-kidney`
*   Independent, evaluation-only pool.
*   **Class Mapping:**
    *   `Stone` -> `STONE` (1)
    *   `Normal` -> `NON_STONE` (0) 
*   **Absolute Rule Constraints:** CT-Kidney is explicitly forbidden from informing epochs, loss gradients, class sampling distributions, training augmentations, threshold selection boundaries, or any forms of fine-tuning calibrations.

## 4. Methodology & Models
*   **Architecture:** ImageNet pretrained `EfficientNet-B0`
*   **Resolution Configuration:** `224x224` Input Target.
*   **Augmentation Policy:** Moderate anatomic bounds (5° bounds rot, 5% shift, slight lumance jitter).

## 5. Execution Pipeline
1. Dataset split mapping (Manifest Builder):
```powershell
python ai-engine/experiments/classification/EXP19_CROSS_DATASET_BINARY/discovery.py
```
2. Primary Model Fitting (Not auto-invoked):
```powershell
python ai-engine/experiments/classification/EXP19_CROSS_DATASET_BINARY/train_exp19.py
```
3. Test Base Extraction (Dataset A):
```powershell
python ai-engine/experiments/classification/EXP19_CROSS_DATASET_BINARY/evaluate_exp19.py
```
4. Final Unseen Verification (Dataset B, CT-Kidney):
```powershell
python ai-engine/experiments/classification/EXP19_CROSS_DATASET_BINARY/evaluate_external_exp19.py
```

## 6. Interpretation Overview
*   **Internal Dataset A Metrics** measure performance within the exact training dataset domain geometry. High rates specify successful visual extraction.
*   **External Dataset B Metrics** independently measure cross-dataset generalization. High internal performance *does not* formally constitute broad translation; the cross-metric drop represents pure dataset/domain shift originating from institutional or algorithmic scanner boundaries. Compare holistic metric behaviors instead of targeting isolated thresholds.
