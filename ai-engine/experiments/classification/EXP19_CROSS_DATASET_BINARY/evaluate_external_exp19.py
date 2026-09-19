"""
EXP19 External Evaluation (Dataset B)
"""
from __future__ import annotations
import argparse, json, sys, csv, hashlib
from pathlib import Path
_EXP_DIR      = Path(__file__).parent
_ENGINE_ROOT  = _EXP_DIR.parent.parent.parent
sys.path.insert(0, str(_ENGINE_ROOT))

import torch
from torch.utils.data import DataLoader, Dataset
from tqdm import tqdm
import yaml
from PIL import Image

from transforms import get_exp19_transforms
from model import build_exp19_model
from metrics import compute_binary_metrics

def md5(fname):
    h = hashlib.md5()
    try:
        with open(fname, "rb") as f:
            for c in iter(lambda: f.read(8192), b""): h.update(c)
        return h.hexdigest()
    except BaseException: return None

class ExternalDataset(Dataset):
    def __init__(self, root: Path, mapping: dict, transform=None):
        self.transform = transform
        self.samples = []
        for d in sorted(root.iterdir()):
            if not d.is_dir(): continue
            if d.name not in mapping: continue
            lbl = 1 if mapping[d.name] == "STONE" else 0
            for p in sorted(d.iterdir()):
                if p.suffix.lower() in {".jpg",".jpeg",".png",".bmp"}:
                    self.samples.append((str(p), lbl))

    def __len__(self): return len(self.samples)
    def __getitem__(self, i):
        path, label = self.samples[i]
        img = Image.open(path).convert("RGB")
        if self.transform: img = self.transform(img)
        return img, label, path

def check_overlap(root_a: Path, root_b: Path, rep_dir: Path):
    print("Checking dataset overlap across A and B...")
    a_files, b_files = [], []
    for ext in {".jpg",".jpeg",".png",".bmp"}:
        a_files.extend(list(root_a.rglob(f"*{ext}")))
        b_files.extend(list(root_b.rglob(f"*{ext}")))
        
    a_hashes = {md5(f): str(f) for f in a_files}
    b_hashes = {md5(f): str(f) for f in b_files}
    
    # Remove None if standard failure occurred
    a_hashes.pop(None, None); b_hashes.pop(None, None)
    
    overlap = set(a_hashes.keys()).intersection(set(b_hashes.keys()))
    dup_examples = [{ "dataset_a_path": a_hashes[h], "dataset_b_path": b_hashes[h] } for h in overlap]
    
    rep = {
        "dataset_a_count": len(a_files),
        "dataset_b_count": len(b_files),
        "duplicate_hash_count": len(overlap),
        "duplicate_examples": dup_examples[:50] # save top 50 examples
    }
    with open(rep_dir/"exp19_cross_dataset_overlap_report.json", "w", encoding="utf-8") as f:
        json.dump(rep, f, indent=2)
    print(f"Overlap check complete. Duplicates found: {len(overlap)}")

def main():
    parser = argparse.ArgumentParser()
    args = parser.parse_args()
    
    with open(_EXP_DIR / "config.yaml", "r", encoding="utf-8") as f: cfg = yaml.safe_load(f)
    out_dir = Path(cfg["output"]["dir"])
    rep_dir = out_dir / "reports"
    pred_dir = out_dir / "predictions"
    rep_dir.mkdir(exist_ok=True); pred_dir.mkdir(exist_ok=True)
    
    ckpt_path = out_dir / "checkpoints" / cfg["output"]["best_checkpoint"]
    
    if not ckpt_path.exists(): sys.exit("ERROR: Checkpoint not found.")
    
    device = torch.device(cfg["hardware"]["device"] if torch.cuda.is_available() else "cpu")
    model = build_exp19_model(cfg)
    model.load_state_dict(torch.load(ckpt_path, map_location=device)["model_state_dict"])
    model.to(device).eval()

    ext_root = Path(cfg["external_test"]["root"])
    if not ext_root.exists(): sys.exit("ERROR: Dataset B not found.")
    
    check_overlap(Path(cfg["dataset"]["root"]), ext_root, rep_dir)
    
    tf = get_exp19_transforms("test", cfg)
    mapping = cfg["external_test"]["class_mapping"]
    ds = ExternalDataset(ext_root, mapping, transform=tf)
    loader = DataLoader(ds, batch_size=32, shuffle=False, num_workers=0)
    
    y_true, y_pred, y_prob, rows = [], [], [], []
    with torch.no_grad():
        for imgs, lbls, paths in tqdm(loader, desc="External Evaluator (Dataset B)"):
            logits = model(imgs.to(device))
            probs = torch.softmax(logits, dim=1).cpu()
            for i in range(len(lbls)):
                gt = int(lbls[i])
                ps = float(probs[i, 1])
                pd_ = 1 if ps >= 0.5 else 0
                y_true.append(gt); y_pred.append(pd_); y_prob.append(ps)
                rows.append({
                    "image_path": paths[i],
                    "ground_truth": gt, "predicted_class": pd_, "stone_probability": round(ps,6)
                })

    metrics = compute_binary_metrics(y_true, y_pred, y_prob)
    
    print("\n  EXTERNAL TEST RESULTS (Dataset B):")
    for k,v in metrics.items(): print(f"    {k:20s}: {v}")
    
    BASE = {"accuracy": 0.6064, "f1": 0.6126, "roc_auc": 0.6981}
    EXP15 = {"accuracy": 0.6293, "f1": 0.6938, "roc_auc": 0.8532}

    print("\n  CROSS-DATASET GENERALIZATION COMPARISON:")
    print(f"  {'Metric':15s} | {'Baseline':10s} | {'EXP15 Base':10s} | {'EXP19 Cross':10s}")
    print("  " + "-"*55)
    for k in ["accuracy", "f1", "roc_auc"]:
        b, e, v = BASE.get(k,0), EXP15.get(k,0), metrics.get(k,0)
        print(f"  {k:15s} | {b:10.4f} | {e:10.4f} | {v:10.4f}")

    report = {
        "dataset_name": cfg["external_test"]["name"],
        "total_evaluated": len(rows),
        "failed_images": 0,
        "class_counts": {"Stone": sum(1 for y in y_true if y == 1), "Non-Stone": sum(1 for y in y_true if y == 0)},
        "checkpoint": str(ckpt_path),
        "device": str(device),
        "class_mapping": mapping,
        "threshold": 0.50,
        "metrics": metrics
    }
    
    with open(rep_dir/"exp19_external_metrics.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
        
    with open(rep_dir/"exp19_comparison_with_existing_models.json", "w", encoding="utf-8") as f:
        json.dump({
            "experiment": "EXP19_CROSS_DATASET_BINARY",
            "metrics": metrics,
            "comparison_exp15": EXP15,
            "comparison_baseline": BASE
        }, f, indent=2)
    
    with open(pred_dir/"exp19_external_predictions.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["image_path","ground_truth","predicted_class","stone_probability"])
        w.writeheader(); w.writerows(rows)
        
    print("\n  EXTERNAL EVALUATION COMPLETE\n")

if __name__ == "__main__": main()
