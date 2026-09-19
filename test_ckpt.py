import torch
import sys

def inspect(path):
    print(f"\n--- {path} ---")
    ckpt = torch.load(path, map_location="cpu")
    print("Keys:", list(ckpt.keys()))
    sd = ckpt.get("model_state_dict", ckpt.get("state_dict", ckpt))
    keys = list(sd.keys())
    print("SD len:", len(keys))
    for k, v in sd.items():
        if "conv_head.weight" in k:
            print("conv_head shape:", list(v.shape))
        if "head.1.weight" in k or "head.1.bias" in k:
            print(k, list(v.shape))
    print("metadata:", {k:v for k,v in ckpt.items() if k not in ["model_state_dict", "optimizer_state_dict"]})

inspect("ai-engine/weights/classification/final_candidate_exp02a.pth")
inspect("ai-engine/experiments/classification/EXP15_EFFICIENTNET_B2_320/outputs/checkpoints/best_model_exp15_b2_320.pth")
