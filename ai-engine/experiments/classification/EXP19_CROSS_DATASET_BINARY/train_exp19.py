"""
EXP19 Binary Training Script.
DO NOT AUTOMATICALLY EXECUTE IN BACKGROUND.
Usage: python train_exp19.py [--smoke-test]
"""
from __future__ import annotations
import argparse, json, sys, time
from pathlib import Path
_EXP_DIR      = Path(__file__).parent
_ENGINE_ROOT  = _EXP_DIR.parent.parent.parent
sys.path.insert(0, str(_ENGINE_ROOT))

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from tqdm import tqdm
import yaml

from dataset import Exp19Dataset
from transforms import get_exp19_transforms
from model import build_exp19_model, count_parameters
from metrics import compute_binary_metrics
from utils.seed_utils import set_seed
from utils.logger import get_logger

log = get_logger("EXP19")

def _compute_stats(logits, labels):
    p = torch.tensor(logits).argmax(1).tolist()
    l = torch.tensor(labels).tolist()
    return compute_binary_metrics(l, p)

def run_epoch(m, ld, c, o, dev, tr: bool, desc: str):
    m.train() if tr else m.eval()
    t_loss, lgs, lbl = 0.0, [], []
    with torch.enable_grad() if tr else torch.no_grad():
        pb = tqdm(ld, desc=desc, leave=False, dynamic_ncols=True)
        for im, lb in pb:
            im, lb = im.to(dev), lb.to(dev)
            lg = m(im)
            lo = c(lg, lb)
            if tr:
                o.zero_grad()
                lo.backward()
                o.step()
            t_loss += lo.item() * im.size(0)
            lgs.extend(lg.detach().cpu().tolist())
            lbl.extend(lb.cpu().tolist())
            pb.set_postfix(loss=f"{lo.item():.4f}")
    return t_loss / len(lbl), lgs, lbl

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke-test", action="store_true")
    args = parser.parse_args()
    smoke = args.smoke_test
    
    with open(_EXP_DIR / "config.yaml", "r", encoding="utf-8") as f: cfg = yaml.safe_load(f)
    set_seed(cfg["split"]["seed"])
    device = torch.device(cfg["hardware"]["device"] if torch.cuda.is_available() else "cpu")
    
    print("\n" + "="*66)
    print("  EXPERIMENT: EXP19_CROSS_DATASET_BINARY")
    print("  DATASET A : " + cfg["dataset"]["root"])
    print("="*66 + "\n")
    
    tf_tr = get_exp19_transforms("train", cfg)
    tf_vl = get_exp19_transforms("val", cfg)
    
    manifest = Path(cfg["dataset"]["manifest"])
    if not manifest.exists():
        sys.exit(f"ERROR: Dataset A manifest not found: {manifest}")
        
    root_dir = cfg["dataset"]["root"]
    tr_ds = Exp19Dataset(manifest, "train", root_dir, transform=tf_tr)
    vl_ds = Exp19Dataset(manifest, "val", root_dir, transform=tf_vl)
    te_ds = Exp19Dataset(manifest, "test", root_dir, transform=tf_vl)
    
    if smoke:
        tr_ds.samples = tr_ds.samples[:16]
        vl_ds.samples = vl_ds.samples[:16]
        te_ds.samples = te_ds.samples[:16]
        
    bs = int(cfg["training"]["batch_size"])
    tr_ld = DataLoader(tr_ds, batch_size=bs, shuffle=True,  num_workers=0, pin_memory=True)
    vl_ld = DataLoader(vl_ds, batch_size=bs, shuffle=False, num_workers=0, pin_memory=True)
    
    m = build_exp19_model(cfg).to(device)
    print(f"  Params: {count_parameters(m):,}")
    
    opt = torch.optim.AdamW(m.parameters(), lr=float(cfg["training"]["learning_rate"]), weight_decay=float(cfg["training"]["weight_decay"]))
    cri = nn.CrossEntropyLoss()

    out_dir = Path(cfg["output"]["dir"])
    ckpt_dir = out_dir / "checkpoints"
    rep_dir = out_dir / "reports"
    log_dir = out_dir / "logs"
    
    for d in [ckpt_dir, rep_dir, log_dir]: d.mkdir(parents=True, exist_ok=True)
    
    b_ckpt = ckpt_dir / cfg["output"]["best_checkpoint"]
    l_ckpt = ckpt_dir / cfg["output"]["last_checkpoint"]
    
    b_f1, no_imp, hist, ep_c = 0.0, 0, [], (1 if smoke else int(cfg["training"]["epochs"]))
    pat = int(cfg["training"]["patience"])
    t0 = time.time()
    
    for ep in range(ep_c):
        et0 = time.time()
        tr_L, tr_lg, tr_lb = run_epoch(m, tr_ld, cri, opt, device, True,  f"Ep {ep+1} T")
        vl_L, vl_lg, vl_lb = run_epoch(m, vl_ld, cri, opt, device, False, f"Ep {ep+1} V")
        
        tr_S, vl_S = _compute_stats(tr_lg, tr_lb), _compute_stats(vl_lg, vl_lb)
        hist.append({"epoch": ep+1, "train_loss": round(tr_L,6), "val_loss": round(vl_L,6), "val_f1": vl_S["f1"], "elapsed": round(time.time()-et0, 2)})
        
        is_best = vl_S["f1"] > b_f1
        if is_best:
            b_f1, no_imp = vl_S["f1"], 0
            st = {"epoch": ep+1, "model_state_dict": m.state_dict(), "optimizer_state_dict": opt.state_dict(), "best_val_f1": b_f1, "config": cfg, "seed": cfg["split"]["seed"]}
            torch.save(st, b_ckpt)
            with open(rep_dir/"best_validation_metrics.json", "w") as f:
                json.dump(vl_S, f, indent=2)
        else: no_imp += 1

        torch.save({**st, "epoch": ep+1}, l_ckpt) # type: ignore
        log.info(f"Ep {ep+1}", tr_L=f"{tr_L:.4f}", tr_f1=f"{tr_S['f1']:.4f}", vl_L=f"{vl_L:.4f}", vl_f1=f"{vl_S['f1']:.4f}", best_f1=f"{b_f1:.4f}")
        
        if not smoke and no_imp >= pat: 
            print("  EARLY STOPPING.")
            break

    import csv
    with open(log_dir / ("training_history_smoke.csv" if smoke else "training_history.csv"), "w", newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["epoch", "train_loss", "val_loss", "val_f1", "elapsed"])
        writer.writeheader(); writer.writerows(hist)
        
    with open(rep_dir/"training_summary.json", "w") as f:
        json.dump({"total_time": round(time.time()-t0, 2), "best_epoch": ep+1-no_imp, "best_val_f1": b_f1}, f, indent=2)

    print("\n" + "="*66); print("  SMOKE TEST PASSED" if smoke else "  TRAINING COMPLETE"); print("="*66 + "\n")

if __name__ == "__main__": main()
