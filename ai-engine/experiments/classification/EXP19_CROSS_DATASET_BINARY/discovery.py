"""
Script to discover Dataset A (Kidney Stone Dataset / Original), generate the report, and create the train/val/test split.
DO NOT RUN IN AUTOMATED TRAINING.
"""
from __future__ import annotations
import os, sys, glob, hashlib, json, csv, random
from pathlib import Path
from collections import defaultdict
import yaml

def md5(fname):
    h = hashlib.md5()
    try:
        with open(fname, "rb") as f:
            for c in iter(lambda: f.read(4096), b""): h.update(c)
        return h.hexdigest()
    except BaseException:
        return None

def main():
    cfg_path = Path("ai-engine/experiments/classification/EXP19_CROSS_DATASET_BINARY/config.yaml")
    with open(cfg_path, "r", encoding="utf-8") as f: cfg = yaml.safe_load(f)
    
    root_val = Path(cfg["dataset"]["root"])
    if not root_val.exists():
        sys.exit(f"ERROR: Dataset A root {root_val} not found.")

    class_mapping = cfg["dataset"]["class_mapping"]
    
    report = {
        "dataset_name": cfg["dataset"]["name"],
        "dataset_root": str(root_val),
        "discovered_classes": [],
        "class_mapping": class_mapping,
        "images_per_class": defaultdict(int),
        "total_images": 0,
        "supported_extensions": set(),
        "invalid_unreadable": 0,
        "duplicate_filename_count": 0,
        "duplicate_hash_count": 0,
        "available_patient_study_identifiers": False,
        "split_strategy": "deterministic_random (no patient identifiers found)"
    }
    
    all_files = []
    filenames = set()
    hashes = set()
    dup_names = 0
    dup_hashes = 0
    
    valid_exts = {".jpg", ".jpeg", ".png", ".bmp"}
    
    # Exclude Augmented explicitly (though root_val directs exactly to /Original, this guarantees safety)
    if "Augmented" in str(root_val):
        sys.exit("ERROR: Dataset A root contains 'Augmented'. It must use exactly the 'Original' directory.")
        
    for cls_name in sorted(os.listdir(root_val)):
        cls_dir = root_val / cls_name
        if not cls_dir.is_dir(): continue
        
        report["discovered_classes"].append(cls_name)
        
        if cls_name not in class_mapping:
            sys.exit(f"ERROR: Ambiguous class '{cls_name}' found. Expected {list(class_mapping.keys())}. STOPPING.")
            
        mapped_label = class_mapping[cls_name]
        
        for fpath in cls_dir.rglob("*"):
            if not fpath.is_file(): continue
            ext = fpath.suffix.lower()
            if ext not in valid_exts:
                report["invalid_unreadable"] += 1
                continue
                
            report["supported_extensions"].add(ext)
            report["images_per_class"][cls_name] += 1
            report["total_images"] += 1
            
            fname = fpath.name
            if fname in filenames: dup_names += 1
            else: filenames.add(fname)
            
            all_files.append({
                "path": str(fpath.relative_to(root_val)),
                "raw_label": cls_name,
                "class_name": mapped_label,
                "label": 1 if mapped_label == "STONE" else 0
            })
            
    report["duplicate_filename_count"] = dup_names
    
    print("Hashing all images in Dataset A to test for duplicates...")
    for item in all_files:
        h = md5(str(root_val / item["path"]))
        if h in hashes: dup_hashes += 1
        elif h: hashes.add(h)
    
    report["duplicate_hash_count"] = dup_hashes
    report["supported_extensions"] = list(report["supported_extensions"])
    
    # Stratified Split
    stone_files = [f for f in all_files if f["class_name"] == "STONE"]
    non_stone_files = [f for f in all_files if f["class_name"] == "NON_STONE"]
    
    random.seed(cfg["split"]["seed"])
    stone_files.sort(key=lambda x: x["path"]); random.shuffle(stone_files)
    non_stone_files.sort(key=lambda x: x["path"]); random.shuffle(non_stone_files)
    
    tr_ratio, val_ratio = cfg["split"]["train"], cfg["split"]["validation"]
    
    def get_splits(arr):
        tr_end = int(len(arr) * tr_ratio)
        val_end = tr_end + int(len(arr) * val_ratio)
        for i, item in enumerate(arr):
            if i < tr_end: item["split"] = "train"
            elif i < val_end: item["split"] = "val"
            else: item["split"] = "test"
            
    get_splits(stone_files)
    get_splits(non_stone_files)
    
    manifest_data = stone_files + non_stone_files
    random.shuffle(manifest_data)
    
    manifest_path = Path(cfg["dataset"]["manifest"])
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(manifest_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["path", "raw_label", "class_name", "label", "split"])
        writer.writeheader()
        writer.writerows(manifest_data)
        
    rep_path = manifest_path.parent / "dataset_discovery_report.json"
    with open(rep_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
        
    print(f"Dataset A discovery and split generated:\n{manifest_path}")

if __name__ == "__main__": main()
