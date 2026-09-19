"""
EXP19 Internal Evaluation (Dataset A - Test Split)
"""
from __future__ import annotations
import argparse, json, sys, csv
from pathlib import Path
_EXP_DIR      = Path(__file__).parent
_ENGINE_ROOT  = _EXP_DIR.parent.parent.parent
sys.path.insert(0, str(_ENGINE_ROOT))

import torch
from torch.utils.data import DataLoader
from tqdm import tqdm
import yaml

from dataset import Exp19Dataset
from transforms import get_exp19_transforms
from model import build_exp19_model
from metrics import compute_binary_metrics

def main():
    parser = argparse.ArgumentParser()
    args = parser.parse_args()
    
    with open(_EXP_DIR / "config.yaml", "r", encoding="utf-8") as f: cfg = yaml.safe_load(f)
    out_dir = Path(cfg["output"]["dir"])
    ckpt_path = out_dir / "checkpoints" / cfg["output"]["best_checkpoint"]
    
    if not ckpt_path.exists(): sys.exit("ERROR: Checkpoint not found.")
    
    device = torch.device(cfg["hardware"]["device"] if torch.cuda.is_available() else "cpu")
    model = build_exp19_model(cfg)
    model.load_state_dict(torch.load(ckpt_path, map_location=device)["model_state_dict"])
    model.to(device).eval()

    tf = get_exp19_transforms("test", cfg)
    manifest = Path(cfg["dataset"]["manifest"])
    root_dir = cfg["dataset"]["root"]
    ds = Exp19Dataset(manifest, "test", root_dir, transform=tf)
    loader = DataLoader(ds, batch_size=32, shuffle=False, num_workers=0)
    
    y_true, y_pred, y_prob, rows = [], [], [], []
    with torch.no_grad():
        for imgs, lbls in tqdm(loader, desc="Internal Evaluator (Dataset A)"):
            logits = model(imgs.to(device))
            probs = torch.softmax(logits, dim=1).cpu()
            for i in range(len(lbls)):
                gt = int(lbls[i])
                ps = float(probs[i, 1]) # P(STONE)
                pd_ = 1 if ps >= 0.5 else 0
                y_true.append(gt); y_pred.append(pd_); y_prob.append(ps)
                rows.append({
                    "image_path": ds.samples[i+len(rows)-(len(lbls))][0],
                    "ground_truth": gt, "predicted_class": pd_, "stone_probability": round(ps,6)
                })

    metrics = compute_binary_metrics(y_true, y_pred, y_prob)
    
    print("\n  INTERNAL TEST RESULTS (Dataset A):")
    for k,v in metrics.items(): print(f"    {k:20s}: {v}")
    
    rep_dir = out_dir / "reports"
    pred_dir = out_dir / "predictions"
    rep_dir.mkdir(exist_ok=True); pred_dir.mkdir(exist_ok=True)
    
    with open(rep_dir/"exp19_internal_test_metrics.json", "w", encoding="utf-8") as f:
        json.dump({"split": "test", "metrics": metrics}, f, indent=2)
    
    with open(pred_dir/"exp19_internal_test_predictions.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["image_path","ground_truth","predicted_class","stone_probability"])
        w.writeheader(); w.writerows(rows)
        
    print("\n  INTERNAL EVALUATION COMPLETE\n")

if __name__ == "__main__": main()
