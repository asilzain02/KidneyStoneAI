"""
evaluate_exp14.py — EXP14 external evaluation.
INFERENCE ONLY. Training/fine-tuning is DISABLED.

Usage:
    python ai-engine/experiments/classification/EXP14_CT_MULTIVIEW_AUGMENTATION/evaluate_exp14.py
    python .../evaluate_exp14.py --checkpoint path/to/ckpt.pth
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

_EXP_DIR      = Path(__file__).parent
_ENGINE_ROOT  = _EXP_DIR.parent.parent.parent
_PROJECT_ROOT = _ENGINE_ROOT.parent
sys.path.insert(0, str(_ENGINE_ROOT))

import torch
from torch.utils.data import DataLoader
from tqdm import tqdm
import yaml

from utils.logger import get_logger
from transforms import get_exp14_transforms
from model      import build_exp14_model

log = get_logger("EXP14_eval")

_OUT_DIR     = _EXP_DIR / "outputs"
_CKPT_DIR    = _OUT_DIR / "checkpoints"
_METRICS_DIR = _OUT_DIR / "metrics"
_PRED_DIR    = _OUT_DIR / "predictions"

CLASS_NAMES = ["Normal", "Cyst", "Stone", "Tumor"]
STONE_IDX   = CLASS_NAMES.index("Stone")       # 2
EXPECTED_TOTAL = 3364


class _ExternalDS(torch.utils.data.Dataset):
    """External Axial CT Kidney Stone dataset — inference-only."""
    def __init__(self, root: Path, transform):
        self.root      = root
        self.transform = transform
        self._paths, self._labels, self._dirs = [], [], []
        for cls_dir in sorted(root.iterdir()):
            if not cls_dir.is_dir():
                continue
            lbl = 1 if cls_dir.name == "Stone" else 0
            for p in sorted(cls_dir.iterdir()):
                if p.suffix.lower() in {".jpg",".jpeg",".png",".bmp"}:
                    self._paths.append(p)
                    self._labels.append(lbl)
                    self._dirs.append(cls_dir.name)

    def __len__(self): return len(self._paths)

    def __getitem__(self, i):
        from PIL import Image
        img = Image.open(self._paths[i]).convert("RGB")
        if self.transform:
            img = self.transform(img)
        return img, self._labels[i], str(self._paths[i])


def _full_metrics(y_true, y_pred, y_prob_stone):
    tp=tn=fp=fn=0
    for g,p in zip(y_true,y_pred):
        if g==1 and p==1: tp+=1
        elif g==0 and p==0: tn+=1
        elif g==0 and p==1: fp+=1
        else: fn+=1
    tot = tp+tn+fp+fn
    acc  = (tp+tn)/tot if tot>0 else 0.
    prec = tp/(tp+fp)  if (tp+fp)>0 else 0.
    rec  = tp/(tp+fn)  if (tp+fn)>0 else 0.
    spec = tn/(tn+fp)  if (tn+fp)>0 else 0.
    f1   = 2*prec*rec/(prec+rec) if (prec+rec)>0 else 0.
    try:
        from sklearn.metrics import roc_auc_score, matthews_corrcoef, balanced_accuracy_score
        roc = float(roc_auc_score(y_true, y_prob_stone))
        mcc = float(matthews_corrcoef(y_true, y_pred))
        bal = float(balanced_accuracy_score(y_true, y_pred))
    except Exception:
        roc=mcc=bal=None
    return dict(accuracy=round(acc,6), precision=round(prec,6),
                recall=round(rec,6), specificity=round(spec,6), f1=round(f1,6),
                roc_auc=round(roc,6) if roc is not None else None,
                balanced_accuracy=round(bal,6) if bal is not None else None,
                mcc=round(mcc,6) if mcc is not None else None,
                TP=tp, TN=tn, FP=fp, FN=fn,
                confusion_matrix=[[tn,fp],[fn,tp]])


def main():
    parser = argparse.ArgumentParser(description="EXP14 External Evaluation")
    parser.add_argument("--checkpoint", type=str,
                        default=str(_CKPT_DIR/"best_model_exp14_multiview.pth"))
    args = parser.parse_args()

    ckpt_path = Path(args.checkpoint).resolve()
    cfg_path  = _EXP_DIR / "config.yaml"
    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    ext_root = Path(_PROJECT_ROOT / cfg["external"]["root"]).resolve()

    print("\n" + "="*66)
    print("  EXP14 — EXTERNAL EVALUATION  (TRAIN DISABLED)")
    print("="*66)
    print(f"  Checkpoint : {ckpt_path}")
    print(f"  External   : {ext_root}")
    print("="*66+"\n")

    if not ckpt_path.exists():
        sys.exit(f"ERROR: Checkpoint not found: {ckpt_path}\nRun train_exp14.py first.")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    ckpt   = torch.load(ckpt_path, map_location=device)
    model  = build_exp14_model(cfg)
    model.load_state_dict(ckpt["model_state_dict"])
    model.to(device).eval()

    transform = get_exp14_transforms("test", cfg)
    ext_ds    = _ExternalDS(ext_root, transform)
    discovered = len(ext_ds)
    if discovered != EXPECTED_TOTAL:
        sys.exit(f"ERROR: Expected {EXPECTED_TOTAL} images, found {discovered}. STOPPING.")
    print(f"  External images discovered: {discovered}  ✓\n")

    loader = DataLoader(ext_ds, batch_size=32, shuffle=False, num_workers=0)
    y_true, y_pred, y_prob, rows = [], [], [], []

    with torch.no_grad():
        for imgs, lbls, paths in tqdm(loader, desc="Inference"):
            imgs  = imgs.to(device)
            logits = model(imgs)
            probs  = torch.softmax(logits, dim=1).cpu()
            for i in range(len(lbls)):
                gt = int(lbls[i])
                ps = float(probs[i, STONE_IDX])   # P(Stone) — continuous
                pd_ = 1 if ps >= 0.5 else 0
                y_true.append(gt); y_pred.append(pd_); y_prob.append(ps)
                rows.append({"image_path": paths[i],
                             "ground_truth": "Stone" if gt==1 else "Non-Stone",
                             "predicted_class": "Stone" if pd_==1 else "Non-Stone",
                             "stone_probability": round(ps,6),
                             "correct": pd_==gt})

    metrics = _full_metrics(y_true, y_pred, y_prob)

    print("\n  External Results:")
    for k,v in metrics.items():
        if k not in ("confusion_matrix","TP","TN","FP","FN"):
            print(f"    {k:20s}: {v}")
    print(f"\n  Confusion: TN={metrics['TN']} FP={metrics['FP']} FN={metrics['FN']} TP={metrics['TP']}")

    BASE = dict(accuracy=0.6064,precision=0.5687,recall=0.6639,
                specificity=0.5557,f1=0.6126,roc_auc=0.6981)
    print("\n  vs Baseline (final_candidate_exp02a.pth):")
    for k,bv in BASE.items():
        ev = metrics.get(k)
        if ev is not None:
            delta = ev - bv
            print(f"    {k:20s}  base={bv:.4f}  exp14={ev:.4f}  Δ={delta:+.4f}")

    _METRICS_DIR.mkdir(parents=True, exist_ok=True)
    _PRED_DIR.mkdir(parents=True, exist_ok=True)
    with open(_METRICS_DIR/"external_results.json","w",encoding="utf-8") as f:
        json.dump({"experiment":"EXP14","metrics":metrics,"baseline":BASE}, f, indent=2)
    with open(_PRED_DIR/"external_predictions.csv","w",newline="",encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["image_path","ground_truth",
                           "predicted_class","stone_probability","correct"])
        w.writeheader(); w.writerows(rows)
    print(f"\n  Saved: {_METRICS_DIR/'external_results.json'}")
    print("  EXTERNAL EVALUATION COMPLETE\n")


if __name__ == "__main__":
    main()
