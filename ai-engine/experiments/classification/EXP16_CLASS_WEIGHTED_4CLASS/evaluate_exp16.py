"""
evaluate_exp16.py — EXP16 external evaluation.
INFERENCE ONLY.
"""
from __future__ import annotations
import argparse, csv, json, sys
from pathlib import Path
_EXP_DIR      = Path(__file__).parent
_ENGINE_ROOT  = _EXP_DIR.parent.parent.parent
_PROJECT_ROOT = _ENGINE_ROOT.parent
sys.path.insert(0, str(_ENGINE_ROOT))

import torch
from torch.utils.data import DataLoader
from tqdm import tqdm
import yaml

from preprocessing.classification_transforms import get_classification_transforms
from model import build_exp16_model

_OUT_DIR     = _EXP_DIR / "outputs"
_METRICS_DIR = _OUT_DIR / "metrics"
_PRED_DIR    = _OUT_DIR / "predictions"
EXPECTED_TOTAL = 3364

class _ExternalDS(torch.utils.data.Dataset):
    def __init__(self, root, transform):
        self.root, self.transform = root, transform
        self._paths, self._labels = [], []
        for d in sorted(root.iterdir()):
            if not d.is_dir(): continue
            lbl = 1 if d.name == "Stone" else 0
            for p in sorted(d.iterdir()):
                if p.suffix.lower() in {".jpg",".jpeg",".png",".bmp"}:
                    self._paths.append(p); self._labels.append(lbl)
    def __len__(self): return len(self._paths)
    def __getitem__(self, i):
        from PIL import Image
        img = Image.open(self._paths[i]).convert("RGB")
        return self.transform(img) if self.transform else img, self._labels[i], str(self._paths[i])

def _full_metrics(y_true, y_pred, y_prob):
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
        roc = float(roc_auc_score(y_true, y_prob))
        mcc = float(matthews_corrcoef(y_true, y_pred))
        bal = float(balanced_accuracy_score(y_true, y_pred))
    except Exception: roc=mcc=bal=None
    return dict(accuracy=round(acc,6), precision=round(prec,6), recall=round(rec,6),
                specificity=round(spec,6), f1=round(f1,6), roc_auc=round(roc,6) if roc else None,
                balanced_accuracy=round(bal,6) if bal else None, mcc=round(mcc,6) if mcc else None,
                TP=tp, TN=tn, FP=fp, FN=fn, confusion_matrix=[[tn,fp],[fn,tp]])

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=str, default=str(_OUT_DIR/"checkpoints"/"best_model_exp16_class_weighted.pth"))
    args = parser.parse_args()
    ckpt_path = Path(args.checkpoint)
    with open(_EXP_DIR / "config.yaml", "r", encoding="utf-8") as f: cfg = yaml.safe_load(f)
    ext_root = Path(_PROJECT_ROOT/cfg["external"]["root"])
    
    if not ckpt_path.exists(): sys.exit("ERROR: Checkpoint not found.")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = build_exp16_model(cfg); model.load_state_dict(torch.load(ckpt_path, map_location=device)["model_state_dict"])
    model.to(device).eval()

    tf = get_classification_transforms("test", int(cfg["training"]["input_size"]))
    ds = _ExternalDS(ext_root, tf)
    if len(ds) != EXPECTED_TOTAL: sys.exit(f"ERROR: Expected {EXPECTED_TOTAL} images, found {len(ds)}.")

    loader = DataLoader(ds, batch_size=32, shuffle=False, num_workers=0)
    y_true, y_pred, y_prob, rows = [], [], [], []
    with torch.no_grad():
        for imgs, lbls, paths in tqdm(loader, desc="Inference"):
            logits = model(imgs.to(device)); probs = torch.softmax(logits, dim=1).cpu()
            for i in range(len(lbls)):
                gt = int(lbls[i]); ps = float(probs[i, 2])
                pd_ = 1 if ps >= 0.5 else 0
                y_true.append(gt); y_pred.append(pd_); y_prob.append(ps)
                rows.append({"image_path": paths[i], "ground_truth": "Stone" if gt==1 else "Non-Stone",
                             "predicted_class": "Stone" if pd_==1 else "Non-Stone", "stone_probability": round(ps,6),
                             "correct": pd_==gt})

    metrics = _full_metrics(y_true, y_pred, y_prob)
    print("\n  External Results:"); [print(f"    {k:20s}: {v}") for k,v in metrics.items() if k not in ("confusion_matrix","TP","TN","FP","FN")]
    BASE = dict(accuracy=0.6064, precision=0.5687, recall=0.6639, specificity=0.5557, f1=0.6126, roc_auc=0.6981)
    print("\n  vs Baseline:"); [print(f"    {k:20s}  base={bv:.4f}  exp={metrics.get(k,0):.4f}  diff={metrics.get(k,bv)-bv:+.4f}") for k,bv in BASE.items() if metrics.get(k) is not None]

    _METRICS_DIR.mkdir(parents=True, exist_ok=True); _PRED_DIR.mkdir(parents=True, exist_ok=True)
    with open(_METRICS_DIR/"external_results.json","w",encoding="utf-8") as f: json.dump({"experiment":"EXP16","metrics":metrics,"baseline":BASE}, f, indent=2)
    with open(_PRED_DIR/"external_predictions.csv","w",newline="",encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["image_path","ground_truth","predicted_class","stone_probability","correct"])
        w.writeheader(); w.writerows(rows)
    print("  EVALUATION COMPLETE\n")

if __name__ == "__main__": main()
