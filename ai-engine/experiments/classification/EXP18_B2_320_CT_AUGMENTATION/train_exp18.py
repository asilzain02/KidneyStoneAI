"""
train_exp18.py — EXP18_B2_320_CT_AUGMENTATION training entry point.
DO NOT execute automatically.

Usage:
    python ai-engine/experiments/classification/EXP18_B2_320_CT_AUGMENTATION/train_exp18.py
    python ai-engine/experiments/classification/EXP18_B2_320_CT_AUGMENTATION/train_exp18.py --smoke-test
"""
from __future__ import annotations
import argparse, datetime, json, sys, time
from pathlib import Path
_EXP_DIR      = Path(__file__).parent
_ENGINE_ROOT  = _EXP_DIR.parent.parent.parent
_PROJECT_ROOT = _ENGINE_ROOT.parent
sys.path.insert(0, str(_ENGINE_ROOT))

import torch, torch.nn as nn
from torch.utils.data import DataLoader
from tqdm import tqdm
import yaml

from utils.seed_utils import set_seed
from utils.logger import get_logger
from dataset import CTKidneyDataset18
from model import build_exp18_model, count_parameters
from transforms import get_exp18_transforms

log = get_logger("EXP18")
_OUT_DIR     = _EXP_DIR / "outputs"
_CKPT_DIR    = _OUT_DIR / "checkpoints"
_LOG_DIR     = _OUT_DIR / "logs"
_METRICS_DIR = _OUT_DIR / "metrics"

def _compute_stats(logits, labels):
    p = torch.tensor(logits).argmax(1); l = torch.tensor(labels)
    acc = (p == l).sum().item() / len(l)
    f1s = []
    for c in range(4):
        tp = ((p==c)&(l==c)).sum().item()
        fp = ((p==c)&(l!=c)).sum().item()
        fn = ((p!=c)&(l==c)).sum().item()
        pr = tp/(tp+fp) if tp+fp>0 else 0
        re = tp/(tp+fn) if tp+fn>0 else 0
        f1s.append(2*pr*re/(pr+re) if pr+re>0 else 0)
    return {"accuracy": round(acc,6), "macro_f1": round(sum(f1s)/4,6)}

def run_epoch(m, ld, c, o, dev, tr: bool, desc: str):
    m.train() if tr else m.eval()
    t_loss, lgs, lbl = 0.0, [], []
    with torch.enable_grad() if tr else torch.no_grad():
        pb = tqdm(ld, desc=desc, leave=False, dynamic_ncols=True)
        for im, lb in pb:
            im, lb = im.to(dev), lb.to(dev)
            lg = m(im); lo = c(lg, lb)
            if tr: o.zero_grad(); lo.backward(); o.step()
            t_loss += lo.item() * im.size(0)
            lgs.extend(lg.detach().cpu().tolist()); lbl.extend(lb.cpu().tolist())
            pb.set_postfix(loss=f"{lo.item():.4f}")
    return t_loss / len(lbl), lgs, lbl

def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--smoke-test", action="store_true")
    args = parser.parse_args(); smoke = args.smoke_test
    
    with open(_EXP_DIR / "config.yaml", "r", encoding="utf-8") as f: cfg = yaml.safe_load(f)
    t = cfg["training"]; seed = cfg["experiment"]["seed"]
    set_seed(seed, deterministic=bool(cfg["experiment"]["deterministic"]))
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    print("\n" + "="*66)
    print("  EXPERIMENT: EXP18_B2_320_CT_AUGMENTATION")
    print("="*66 + "\n")
    
    sz = int(t["input_size"])
    tf_tr = get_exp18_transforms("train", sz, cfg)
    tf_vl = get_exp18_transforms("val", sz, cfg)
    
    tr_ds = CTKidneyDataset18(_PROJECT_ROOT/cfg["data"]["train_csv"], tf_tr, smoke, smoke_n=10)
    vl_ds = CTKidneyDataset18(_PROJECT_ROOT/cfg["data"]["val_csv"], tf_vl)
    te_ds = CTKidneyDataset18(_PROJECT_ROOT/cfg["data"]["test_csv"], tf_vl)
    
    bs = int(t["batch_size"])
    tr_ld = DataLoader(tr_ds, batch_size=bs, shuffle=True,  num_workers=0, pin_memory=True)
    vl_ld = DataLoader(vl_ds, batch_size=bs, shuffle=False, num_workers=0, pin_memory=True)
    te_ld = DataLoader(te_ds, batch_size=bs, shuffle=False, num_workers=0, pin_memory=True)

    m = build_exp18_model(cfg).to(device)
    print(f"  Params: {count_parameters(m):,}")
    
    opt = torch.optim.AdamW(m.parameters(), lr=float(t["learning_rate"]), weight_decay=float(t["weight_decay"]))
    sch = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=int(t["scheduler_T_max"]))
    cri = nn.CrossEntropyLoss()

    ckpt_dir = _CKPT_DIR / "smoke" if smoke else _CKPT_DIR
    ckpt_dir.mkdir(parents=True, exist_ok=True); _LOG_DIR.mkdir(parents=True, exist_ok=True); _METRICS_DIR.mkdir(parents=True, exist_ok=True)
    b_ckpt = ckpt_dir / cfg["output"]["checkpoint_name"]; l_ckpt = ckpt_dir / cfg["output"]["latest_name"]
    
    b_f1, no_imp, hist, ep_c, pat = 0.0, 0, [], (2 if smoke else int(t["num_epochs"])), int(t["early_stopping_patience"])
    t0 = time.time()
    
    for ep in range(ep_c):
        et0 = time.time()
        tr_L, tr_lg, tr_lb = run_epoch(m, tr_ld, cri, opt, device, True,  f"Ep {ep+1} T")
        vl_L, vl_lg, vl_lb = run_epoch(m, vl_ld, cri, opt, device, False, f"Ep {ep+1} V")
        sch.step()
        
        tr_S, vl_S = _compute_stats(tr_lg, tr_lb), _compute_stats(vl_lg, vl_lb)
        hist.append({"epoch": ep+1, "train_loss": round(tr_L,6), "val_loss": round(vl_L,6), "val_macro_f1": vl_S["macro_f1"], "elapsed": round(time.time()-et0, 2)})
        
        is_best = vl_S["macro_f1"] > b_f1
        if is_best:
            b_f1, no_imp = vl_S["macro_f1"], 0
            st = {"epoch": ep+1, "model_state_dict": m.state_dict(), "optimizer_state_dict": opt.state_dict(), "best_val_macro_f1": b_f1, "class_names": cfg["classes"]["names"], "experiment_name": cfg["experiment"]["id"], "config": cfg, "seed": seed}
            torch.save(st, b_ckpt)
        else: no_imp += 1

        torch.save({**st, "epoch": ep+1}, l_ckpt)  # type: ignore
        log.info(f"Ep {ep+1}", tr_L=f"{tr_L:.4f}", tr_f1=f"{tr_S['macro_f1']:.4f}", vl_L=f"{vl_L:.4f}", vl_f1=f"{vl_S['macro_f1']:.4f}", best_f1=f"{b_f1:.4f}")
        
        if not smoke and no_imp >= pat: break

    with open(_LOG_DIR / ("hist_smoke.json" if smoke else "training_history.json"), "w", encoding="utf-8") as f: json.dump(hist, f, indent=2)

    if not smoke:
        te_L, te_lg, te_lb = run_epoch(m, te_ld, cri, opt, device, False, "Test")
        with open(_METRICS_DIR/"test_results.json", "w", encoding="utf-8") as f: json.dump({"split": "test", "loss": round(te_L,6), **_compute_stats(te_lg, te_lb)}, f, indent=2)
        with open(_LOG_DIR/"experiment_metadata.json", "w", encoding="utf-8") as f: json.dump({"experiment_id": cfg["experiment"]["id"], "seed": seed}, f, indent=2)

    print("\n" + "="*66); print("  SMOKE TEST PASSED" if smoke else "  TRAINING COMPLETE"); print("="*66 + "\n")

if __name__ == "__main__": main()
