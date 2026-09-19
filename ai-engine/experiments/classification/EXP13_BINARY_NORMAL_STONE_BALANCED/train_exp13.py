"""
train_exp13.py — EXP13 Training Entry Point

EXP13: Binary Normal-vs-Stone + Balanced Training
Experiment ID: EXP13_BINARY_NORMAL_STONE_BALANCED

Intentional changes vs. 4-class baseline:
  1. num_classes = 2 (Normal, Stone only)
  2. WeightedRandomSampler on training set for balance

Everything else is IDENTICAL to the baseline:
  - EfficientNet-B0 backbone
  - AdamW optimizer
  - CosineAnnealing scheduler
  - Same LR, WD, dropout, batch size, input size, seed

DO NOT RUN AUTOMATICALLY.
I will start training manually:

    cd "D:\\Final Sem Project\\KidneyStoneAI"
    .\.venv-ai\Scripts\Activate.ps1
    python "ai-engine/experiments/classification/EXP13_BINARY_NORMAL_STONE_BALANCED/train_exp13.py"

    # Smoke test (2 epochs, 30 samples/class):
    python "ai-engine/experiments/classification/EXP13_BINARY_NORMAL_STONE_BALANCED/train_exp13.py" --smoke
"""

from __future__ import annotations

import argparse
import datetime
import json
import sys
import time
from pathlib import Path

# ── Path setup ────────────────────────────────────────────────
_EXP_DIR = Path(__file__).parent
_ENGINE_ROOT = _EXP_DIR.parent.parent.parent  # ai-engine/
_PROJECT_ROOT = _ENGINE_ROOT.parent

sys.path.insert(0, str(_ENGINE_ROOT))

import torch
import torch.nn as nn
from torch.utils.data import DataLoader

# ── Project shared imports (READ ONLY — not modified) ─────────
from preprocessing.classification_transforms import get_classification_transforms
from utils.logger import get_logger
from utils.seed_utils import set_seed

# ── EXP13 local imports ───────────────────────────────────────
from dataset import BinaryNormalStoneDataset
from sampler import make_balanced_sampler, summarise_balance

import yaml

log = get_logger("EXP13")

# ── Config ────────────────────────────────────────────────────
_CFG_PATH = _EXP_DIR / "config.yaml"
_OUT_DIR  = _EXP_DIR / "outputs"
_CKPT_DIR = _OUT_DIR / "checkpoints"
_LOG_DIR  = _OUT_DIR / "logs"
_METRICS_DIR = _OUT_DIR / "metrics"


def load_cfg() -> dict:
    # with open(_CFG_PATH, "r") as f:
    #     return yaml.safe_load(f)
    with open(_CFG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_binary_efficientnet(dropout: float, pretrained: bool) -> nn.Module:
    """
    Build EfficientNet-B0 with a 2-class head.
    Uses the same KidneyClassifier pattern as the production model
    but with num_classes=2.
    """
    try:
        import timm
    except ImportError:
        raise ImportError("timm is required: pip install timm")

    backbone = timm.create_model(
        "efficientnet_b0",
        pretrained=pretrained,
        num_classes=0,   # remove default head
    )
    in_features = backbone.num_features

    head = nn.Sequential(
        nn.Dropout(p=dropout),
        nn.Linear(in_features, 2),   # 2 outputs: Normal, Stone
    )

    class BinaryEfficientNetB0(nn.Module):
        def __init__(self):
            super().__init__()
            self.backbone = backbone
            self.head = head
            self.num_classes = 2

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            return self.head(self.backbone(x))

    return BinaryEfficientNetB0()


def count_parameters(model: nn.Module) -> int:
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


def _binary_epoch_metrics(logits, labels) -> dict:
    """Compute per-batch binary metrics from logits."""
    probs = torch.softmax(logits, dim=1)
    preds = probs.argmax(dim=1)
    tp = ((preds == 1) & (labels == 1)).sum().item()
    tn = ((preds == 0) & (labels == 0)).sum().item()
    fp = ((preds == 1) & (labels == 0)).sum().item()
    fn = ((preds == 0) & (labels == 1)).sum().item()
    return {"tp": tp, "tn": tn, "fp": fp, "fn": fn}


def _aggregate_metrics(tp, tn, fp, fn, total_loss, total_samples) -> dict:
    loss = total_loss / total_samples if total_samples else 0.0
    acc = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) else 0.0
    prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    rec  = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1   = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
    return {
        "loss": round(loss, 6),
        "accuracy": round(acc, 6),
        "precision": round(prec, 6),
        "recall": round(rec, 6),
        "f1": round(f1, 6),
    }


def parse_args():
    p = argparse.ArgumentParser(description="EXP13 — Binary Normal-Stone Balanced Training")
    p.add_argument("--smoke", action="store_true",
                   help="Smoke test: 2 epochs, 30 samples/class. Does NOT overwrite full checkpoints.")
    return p.parse_args()


def main():
    args = parse_args()
    cfg = load_cfg()

    t_cfg = cfg["training"]
    seed  = int(t_cfg["seed"])
    set_seed(seed, deterministic=bool(t_cfg["deterministic"]))

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # ── Print safety header ────────────────────────────────────────────────────
    print("\n" + "=" * 64)
    print("  EXPERIMENT: EXP13_BINARY_NORMAL_STONE_BALANCED")
    print("=" * 64)
    print(f"  Training:      ENABLED (binary Normal vs Stone)")
    print(f"  Fine-tuning:   FROM SCRATCH (ImageNet pretrained init)")
    print(f"  External data: NOT USED FOR TRAINING")
    print(f"  Augmented:     EXCLUDED")
    print(f"  Device:        {device}")
    if device.type == "cuda":
        print(f"  GPU:           {torch.cuda.get_device_name(0)}")
        mem = torch.cuda.get_device_properties(0).total_memory / 1e9
        print(f"  GPU Memory:    {mem:.1f} GB")
    print("=" * 64 + "\n")

    # ── Resolve paths ─────────────────────────────────────────────────────────
    train_csv = _PROJECT_ROOT / cfg["data"]["train_csv"]
    val_csv   = _PROJECT_ROOT / cfg["data"]["val_csv"]
    test_csv  = _PROJECT_ROOT / cfg["data"]["test_csv"]

    input_size = int(t_cfg["input_size"])
    aug_strategy = str(t_cfg["augmentation_strategy"])  # "baseline"

    # ── Datasets ──────────────────────────────────────────────────────────────
    smoke_n = 30 if args.smoke else 0

    train_tf = get_classification_transforms("train", input_size, strategy=aug_strategy)
    val_tf   = get_classification_transforms("val",   input_size)
    test_tf  = get_classification_transforms("test",  input_size)

    train_ds = BinaryNormalStoneDataset(train_csv, transform=train_tf,
                                        smoke=args.smoke, smoke_n=smoke_n)
    val_ds   = BinaryNormalStoneDataset(val_csv,   transform=val_tf)
    test_ds  = BinaryNormalStoneDataset(test_csv,  transform=test_tf)

    # ── Print counts ──────────────────────────────────────────────────────────
    print("  Classes:")
    print("    Normal (0)")
    print("    Stone  (1)\n")
    print("  Training:")
    print(f"    Normal: {train_ds.normal_count}")
    print(f"    Stone:  {train_ds.stone_count}")
    print(f"    Total:  {len(train_ds)}\n")
    print("  Validation (natural, NOT oversampled):")
    print(f"    Normal: {val_ds.normal_count}")
    print(f"    Stone:  {val_ds.stone_count}")
    print(f"    Total:  {len(val_ds)}\n")
    print("  Test (natural, NOT oversampled):")
    print(f"    Normal: {test_ds.normal_count}")
    print(f"    Stone:  {test_ds.stone_count}")
    print(f"    Total:  {len(test_ds)}\n")
    print("  Oversampling: TRAIN ONLY (WeightedRandomSampler)\n")
    print("  External evaluation:")
    print("    3364 images — NOT USED FOR TRAINING\n")
    print("  Backbone: EfficientNet-B0\n")
    print(f"  Checkpoint dir: {_CKPT_DIR}\n")

    # ── Save manifest ─────────────────────────────────────────────────────────
    if not args.smoke:
        manifest_path = _EXP_DIR / "dataset" / "generated_manifest.csv"
        train_ds.save_manifest(manifest_path)
        log.info(f"Training manifest saved: {manifest_path}")

    # ── Sampler (train only) ──────────────────────────────────────────────────
    summarise_balance(train_ds.get_labels(), ["Normal", "Stone"])
    sampler = make_balanced_sampler(train_ds.get_labels(), num_classes=2)

    batch_size = int(t_cfg["batch_size"])
    num_epochs = 2 if args.smoke else int(t_cfg["num_epochs"])

    # shuffle=False because WeightedRandomSampler handles ordering
    train_loader = DataLoader(train_ds, batch_size=batch_size, sampler=sampler,
                              num_workers=0, pin_memory=True)
    val_loader   = DataLoader(val_ds, batch_size=batch_size, shuffle=False,
                              num_workers=0, pin_memory=True)
    test_loader  = DataLoader(test_ds, batch_size=batch_size, shuffle=False,
                              num_workers=0, pin_memory=True)

    # ── Model ─────────────────────────────────────────────────────────────────
    model = build_binary_efficientnet(
        dropout=float(cfg["model"]["dropout"]),
        pretrained=bool(cfg["model"]["pretrained"]),
    )
    model.to(device)
    n_params = count_parameters(model)
    print(f"  Model: EfficientNet-B0 (binary head, 2 outputs)")
    print(f"  Trainable parameters: {n_params:,}\n")

    # ── Optimizer / Scheduler / Loss ─────────────────────────────────────────
    lr = float(t_cfg["learning_rate"])
    wd = float(t_cfg["weight_decay"])
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=wd)

    t_max = int(t_cfg["scheduler_T_max"])
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=t_max)

    criterion = nn.CrossEntropyLoss()

    patience  = int(t_cfg["early_stopping_patience"])
    min_delta = float(t_cfg["early_stopping_min_delta"])

    # ── Checkpoint paths ──────────────────────────────────────────────────────
    if args.smoke:
        ckpt_dir = _CKPT_DIR / "smoke"
    else:
        ckpt_dir = _CKPT_DIR
    ckpt_dir.mkdir(parents=True, exist_ok=True)

    best_ckpt    = ckpt_dir / "best_model_exp13_binary_normal_stone_balanced.pth"
    latest_ckpt  = ckpt_dir / "latest_checkpoint_exp13.pth"
    history_path = (_OUT_DIR / "logs" / "training_history_smoke.json"
                    if args.smoke else
                    _OUT_DIR / "logs" / "training_history.json")
    history_path.parent.mkdir(parents=True, exist_ok=True)

    # ── Training loop ─────────────────────────────────────────────────────────
    best_val_acc      = 0.0
    epochs_no_improve = 0
    history = []
    start_time = time.time()

    print("=" * 64)
    print(f"  Starting{'  SMOKE TEST' if args.smoke else ''} training "
          f"for {num_epochs} epoch(s)…")
    print("=" * 64 + "\n")

    for epoch in range(num_epochs):
        ep_start = time.time()
        current_lr = optimizer.param_groups[0]["lr"]

        # ── Train epoch ───────────────────────────────────────────────────────
        model.train()
        tr_loss = tr_tp = tr_tn = tr_fp = tr_fn = 0
        tr_total = 0
        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad()
            logits = model(images)
            loss = criterion(logits, labels)
            loss.backward()
            optimizer.step()
            tr_loss  += loss.item() * images.size(0)
            m = _binary_epoch_metrics(logits.detach(), labels)
            tr_tp += m["tp"]; tr_tn += m["tn"]
            tr_fp += m["fp"]; tr_fn += m["fn"]
            tr_total += images.size(0)

        train_metrics = _aggregate_metrics(tr_tp, tr_tn, tr_fp, tr_fn,
                                           tr_loss, tr_total)

        # ── Val epoch ─────────────────────────────────────────────────────────
        model.eval()
        vl_loss = vl_tp = vl_tn = vl_fp = vl_fn = 0
        vl_total = 0
        with torch.no_grad():
            for images, labels in val_loader:
                images, labels = images.to(device), labels.to(device)
                logits = model(images)
                loss = criterion(logits, labels)
                vl_loss  += loss.item() * images.size(0)
                m = _binary_epoch_metrics(logits, labels)
                vl_tp += m["tp"]; vl_tn += m["tn"]
                vl_fp += m["fp"]; vl_fn += m["fn"]
                vl_total += images.size(0)

        val_metrics = _aggregate_metrics(vl_tp, vl_tn, vl_fp, vl_fn,
                                         vl_loss, vl_total)
        scheduler.step()

        ep_time = time.time() - ep_start
        hist_entry = {
            "epoch": epoch + 1,
            "train_loss": train_metrics["loss"],
            "train_accuracy": train_metrics["accuracy"],
            "train_precision": train_metrics["precision"],
            "train_recall": train_metrics["recall"],
            "train_f1": train_metrics["f1"],
            "validation_loss": val_metrics["loss"],
            "validation_accuracy": val_metrics["accuracy"],
            "validation_precision": val_metrics["precision"],
            "validation_recall": val_metrics["recall"],
            "validation_f1": val_metrics["f1"],
            "learning_rate": current_lr,
            "elapsed_time_s": round(ep_time, 2),
        }
        history.append(hist_entry)

        # ── Save best ─────────────────────────────────────────────────────────
        val_acc = val_metrics["accuracy"]
        is_best = val_acc > best_val_acc + min_delta
        if is_best:
            best_val_acc = val_acc
            epochs_no_improve = 0
            state = {
                "epoch": epoch + 1,
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "best_val_acc": best_val_acc,
                "experiment": "EXP13_BINARY_NORMAL_STONE_BALANCED",
                "num_classes": 2,
                "class_names": ["Normal", "Stone"],
            }
            torch.save(state, best_ckpt)

        state = {
            "epoch": epoch + 1,
            "model_state_dict": model.state_dict(),
            "optimizer_state_dict": optimizer.state_dict(),
            "best_val_acc": best_val_acc,
            "experiment": "EXP13_BINARY_NORMAL_STONE_BALANCED",
            "num_classes": 2,
            "class_names": ["Normal", "Stone"],
        }
        torch.save(state, latest_ckpt)

        log.info(
            f"Epoch {epoch+1}/{num_epochs}",
            tr_loss=f"{train_metrics['loss']:.4f}",
            tr_acc=f"{train_metrics['accuracy']:.4f}",
            tr_f1=f"{train_metrics['f1']:.4f}",
            vl_loss=f"{val_metrics['loss']:.4f}",
            vl_acc=f"{val_metrics['accuracy']:.4f}",
            vl_f1=f"{val_metrics['f1']:.4f}",
            best_val_acc=f"{best_val_acc:.4f}",
            new_best=is_best,
        )

        if not is_best:
            epochs_no_improve += 1
        if epochs_no_improve >= patience and not args.smoke:
            log.info(f"Early stopping at epoch {epoch+1}", patience=patience)
            break

    elapsed = time.time() - start_time

    # ── Save history ──────────────────────────────────────────────────────────
    with open(history_path, "w") as f:
        json.dump(history, f, indent=2)

    # ── Run test evaluation ───────────────────────────────────────────────────
    if not args.smoke:
        _evaluate_split(model, test_loader, device, criterion,
                        _METRICS_DIR / "test_results.json",
                        split="test")

    # ── Save experiment metadata ──────────────────────────────────────────────
    if not args.smoke:
        meta = {
            "experiment_id": "EXP13_BINARY_NORMAL_STONE_BALANCED",
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "backbone": "efficientnet_b0",
            "num_classes": 2,
            "class_names": ["Normal", "Stone"],
            "class_to_index": {"Normal": 0, "Stone": 1},
            "input_size": input_size,
            "batch_size": batch_size,
            "learning_rate": lr,
            "weight_decay": wd,
            "optimizer": "AdamW",
            "scheduler": "CosineAnnealingLR",
            "dropout": float(cfg["model"]["dropout"]),
            "augmentation_strategy": aug_strategy,
            "balancing_method": "WeightedRandomSampler (train only)",
            "seed": seed,
            "num_epochs_trained": len(history),
            "best_val_acc": best_val_acc,
            "training_duration_s": round(elapsed, 1),
            "device": str(device),
            "pytorch_version": torch.__version__,
            "cuda_available": torch.cuda.is_available(),
            "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU",
            "train_normal": train_ds.normal_count,
            "train_stone": train_ds.stone_count,
            "val_normal": val_ds.normal_count,
            "val_stone": val_ds.stone_count,
            "test_normal": test_ds.normal_count,
            "test_stone": test_ds.stone_count,
            "trainable_params": n_params,
            "intentional_changes": [
                "binary_classification (Normal vs Stone only)",
                "training_set_balancing (WeightedRandomSampler)",
            ],
            "inherited_from_baseline": [
                "EfficientNet-B0 architecture",
                "AdamW optimizer",
                "LR=0.001, WD=0.0001",
                "CosineAnnealing scheduler",
                "Dropout=0.3",
                "Batch size=32",
                "Input size=224",
                "Seed=42",
                "Baseline augmentation strategy",
            ],
        }
        meta_path = _OUT_DIR / "logs" / "experiment_metadata.json"
        with open(meta_path, "w") as f:
            json.dump(meta, f, indent=2)
        log.info(f"Metadata saved: {meta_path}")

    print("\n" + "=" * 64)
    if args.smoke:
        print("  SMOKE TEST PASSED — Full training NOT started")
        print(f"  Smoke checkpoint: {best_ckpt}")
    else:
        print("  TRAINING COMPLETE")
        print(f"  Best val accuracy: {best_val_acc:.4f}")
        print(f"  Best checkpoint: {best_ckpt}")
        print(f"  Run external evaluation:")
        print(f"    python ai-engine/experiments/classification/"
              f"EXP13_BINARY_NORMAL_STONE_BALANCED/evaluate_exp13.py")
    print("=" * 64 + "\n")


@torch.no_grad()
def _evaluate_split(model, loader, device, criterion, out_path: Path,
                    split: str = "val") -> dict:
    """Evaluate a DataLoader and save metrics JSON."""
    model.eval()
    loss_total = tp = tn = fp = fn = 0
    n_total = 0
    all_probs = []
    all_labels = []

    for images, labels in loader:
        images, labels = images.to(device), labels.to(device)
        logits = model(images)
        loss = criterion(logits, labels)
        loss_total += loss.item() * images.size(0)
        m = _binary_epoch_metrics(logits, labels)
        tp += m["tp"]; tn += m["tn"]; fp += m["fp"]; fn += m["fn"]
        n_total += images.size(0)
        probs = torch.softmax(logits, dim=1)[:, 1].cpu().tolist()
        all_probs.extend(probs)
        all_labels.extend(labels.cpu().tolist())

    metrics = _aggregate_metrics(tp, tn, fp, fn, loss_total, n_total)

    # Add extra metrics
    spec = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    try:
        from sklearn.metrics import roc_auc_score, matthews_corrcoef, balanced_accuracy_score
        roc_auc = float(roc_auc_score(all_labels, all_probs))
        mcc     = float(matthews_corrcoef(all_labels,
                         [1 if p >= 0.5 else 0 for p in all_probs]))
        bal_acc = float(balanced_accuracy_score(all_labels,
                         [1 if p >= 0.5 else 0 for p in all_probs]))
    except Exception:
        roc_auc = bal_acc = mcc = None

    result = {
        "split": split,
        **metrics,
        "specificity": round(spec, 6),
        "roc_auc": round(roc_auc, 6) if roc_auc is not None else None,
        "balanced_accuracy": round(bal_acc, 6) if bal_acc is not None else None,
        "mcc": round(mcc, 6) if mcc is not None else None,
        "TP": tp, "TN": tn, "FP": fp, "FN": fn,
        "confusion_matrix": [[tn, fp], [fn, tp]],
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    import json
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    log.info(f"{split} metrics saved: {out_path}")
    return result


if __name__ == "__main__":
    main()
