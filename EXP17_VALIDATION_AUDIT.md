# EXP17/EXP15 VALIDATION INTEGRITY AUDIT

## Overview
This read-only audit investigates why the EXP15 model achieves 100% precision, recall, and F1 on the validation set across entirely different thresholds (0.22 through 0.66) during EXP17 threshold optimization, despite lower external performance.

## 1-3. Manifest and Dataset Baseline
* **Manifest Path:** `datasets/splits/classification/val.csv`
* **Total Images:** 1789
  * Normal: 750
  * Cyst: 492
  * Stone: 204
  * Tumor: 343
* **Mapping Verified:** Stone isolated as Positive (1). All other conditions (Normal/Cyst/Tumor) mapped to Negative (0).
* **Dataset Size Validated:** 1789 matches expectation; this is the entire internal validation split.

## 4-9. Leakage & Overlap Analysis
Exact filename, path, and file hash overlaps were explicitly computed across train, validation, and test splits:

| Overlap Type | Train ∩ Val | Train ∩ Test | Val ∩ Test |
| -- | -- | -- | -- |
| Absolute Paths | 0 | 0 | 0 |
| Filenames | 0 | 0 | 0 |
| MD5 Hashes (Image Content) | 0 | 0 | 0 |

**Conclusion (Direct Leakage):** Clean. There are no perfectly identical image files or structurally accidental overlap errors bridging the validation set and the training set.

## 10. Patient / Study Identifiers
* **Existence:** Evaluated columns (`image_path`, `class_name`, `class_id`, `dataset_name`, `image_hash`, `width`, `height`).
* **Conclusion (Patient Leakage):** `patient_id` and `study_id` **DO NOT EXIST** in the manifest trackings. Therefore, it is impossible to rule out Patient/Study Leakage programmatically.

## 16-20. Checkpoint & Transformation Integrity
* **Checkpoint Used:** `ai-engine/experiments/classification/EXP15_EFFICIENTNET_B2_320/outputs/checkpoints/best_model_exp15_b2_320.pth` (Confirmed).
* **Selection Metric Checked:** Selected by `best_val_macro_f1`. Inside the checkpoint, the recorded metric is exactly `1.0`. 
* **Validation Transforms (Preprocessing):** Unaltered. Validated identically to EXP15 design: `Resize(320)->ToTensor()->Normalize(ImageNet)`.
* **Random Training Augmentation:** None present in the validation loader configuration.

## 11-15. Probability Distribution Analysis [P(Stone)]
Inference generated entirely untouched (uncached) logic against all 1789 images precisely extracting `P(Stone)`. 

* **Overall Minimum:** 0.000000
* **Overall Maximum:** 1.000000
* **Overall Mean:** 0.114080

**Decoupled Ground-Truth Statistics:**
* **Stone Group:** (Min = `0.672600`, Max = `1.000000`, Mean = `0.997836`)
* **Non-Stone Group:** (Min = `0.000000`, Max = `0.219415`, Mean = `0.000334`)

### The Probability Gap
* Lowest `P(Stone)` prediction on a real Stone image: **0.672600**
* Highest `P(Stone)` prediction on a real Non-Stone image: **0.219415**
* **Absolute Empty Gap:** **0.453185**

## Final Conclusion
There is **NO measurable evidence** of preprocessing mismatch, label mapping errors, checkpoint mismatch, direct file duplication leakage, or cached training overlap. 

The anomalous 100% metrics between thresholds 0.22 and 0.66 are caused entirely by an **unusually strong validation separation phase (empty gap of 0.453)** inherently coupled with **implied patient/slice leakage**. Because there is no patient filtering tracked across the manifest file, the training and validation images are highly likely drawn from nearly identical CT slice layers of the same internal patients. EfficientNet-B2 (320px) learned to perfectly distinguish these tightly clustered specific slices, generating an artificial `1.0` macro-F1 internal score that fails to generalize purely onto the external dataset.
