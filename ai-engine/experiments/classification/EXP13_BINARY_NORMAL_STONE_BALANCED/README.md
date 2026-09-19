# EXP13 — Binary Normal-vs-Stone + Balanced Training

**Experiment ID:** `EXP13_BINARY_NORMAL_STONE_BALANCED`

---

## Hypothesis

Changing the 4-class kidney CT classification problem to a binary
Normal-vs-Stone task, and balancing training data to have equal
Normal and Stone representation, will improve external generalisation
on the Axial CT Kidney Stone dataset.

---

## Isolation Guarantee

| Rule | Status |
|------|--------|
| Existing 4-class model untouched | ✅ |
| Existing weights directory untouched | ✅ |
| Existing split CSV files untouched | ✅ |
| Existing dataset images untouched | ✅ |
| External dataset untouched | ✅ |
| Production inference pipeline untouched | ✅ |
| No image files copied | ✅ |

---

## Intentional Changes vs. Baseline

| Change | Description |
|--------|-------------|
| Binary classification | Only Normal (0) and Stone (1) — Cyst and Tumor excluded |
| Balanced training | WeightedRandomSampler on TRAIN ONLY |

Everything else is **identical to baseline**:
- EfficientNet-B0 backbone
- AdamW, LR=0.001, WD=0.0001
- CosineAnnealing scheduler
- Dropout=0.3, BatchSize=32, InputSize=224, Seed=42
- Baseline augmentation strategy

---

## Files

```
EXP13_BINARY_NORMAL_STONE_BALANCED/
├── config.yaml          — Full configuration (inherited + changes documented)
├── train_exp13.py       — Training entry point
├── evaluate_exp13.py    — External evaluation (inference-only)
├── dataset.py           — Binary dataset + external dataset classes
├── sampler.py           — WeightedRandomSampler builder
├── README.md            — This file
├── dataset/
│   └── generated_manifest.csv  (created after training)
└── outputs/
    ├── checkpoints/
    │   └── best_model_exp13_binary_normal_stone_balanced.pth
    ├── logs/
    │   ├── training_history.json
    │   └── experiment_metadata.json
    ├── metrics/
    │   ├── test_results.json
    │   └── external_results.json
    └── predictions/
        └── external_predictions.csv
```

---

## Data Split Details

Source: `datasets/splits/classification/train.csv / val.csv / test.csv`
(existing project files, not modified)

Filtering: only rows where `class_name` is `Normal` or `Stone` are used.

| Split | Normal | Stone | Oversampled? |
|-------|--------|-------|--------------|
| Train | ~3501  | ~952  | YES (WeightedRandomSampler) |
| Val   | ~750   | ~204  | NO — natural distribution |
| Test  | ~751   | ~204  | NO — natural distribution |

> Exact counts printed at runtime.

---

## Commands

### Smoke test (always run first)
```powershell
cd "D:\Final Sem Project\KidneyStoneAI"
.\.venv-ai\Scripts\Activate.ps1
python "ai-engine/experiments/classification/EXP13_BINARY_NORMAL_STONE_BALANCED/train_exp13.py" --smoke
```

### Full training
```powershell
cd "D:\Final Sem Project\KidneyStoneAI"
.\.venv-ai\Scripts\Activate.ps1
python "ai-engine/experiments/classification/EXP13_BINARY_NORMAL_STONE_BALANCED/train_exp13.py"
```

### External evaluation (after training)
```powershell
python "ai-engine/experiments/classification/EXP13_BINARY_NORMAL_STONE_BALANCED/evaluate_exp13.py"
```

---

## Baseline Reference

Baseline external metrics (recorded, 4-class model):

| Metric | Value |
|--------|-------|
| Accuracy | 60.64% |
| Precision | 56.87% |
| Recall | 66.39% |
| Specificity | 55.57% |
| F1 | 61.26% |
| ROC-AUC | 69.81% |

**Important:** These numbers correspond to the existing 4-class model
checkpoint. The exact file must be identified by the user before claiming
the comparison is valid.

---

## External Evaluation Protocol

- Dataset: `Kidney Stone Dataset/Original` — NEVER modified
- Augmented subset: EXCLUDED entirely
- External dataset: NEVER used for training or fine-tuning
- Threshold: 0.5 (fixed, not tuned on external data)
- Evaluation: model.eval() + torch.no_grad()

---

## Success Criteria (engineering)

- [x] Isolated from all existing experiments
- [x] Existing code unmodified
- [x] Existing datasets unmodified
- [x] Existing weights unmodified
- [x] Binary output (2 logits)
- [x] Training balanced via WeightedRandomSampler (train only)
- [x] Val/test use natural distribution
- [x] External dataset untouched
- [x] Reproducible (seed=42, deterministic=True)
- [ ] External evaluation complete (run after training)

Research success determined after external evaluation.
