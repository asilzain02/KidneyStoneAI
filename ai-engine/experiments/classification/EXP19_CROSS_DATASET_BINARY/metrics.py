"""
EXP19 Shared Classification Metrics.
"""

def compute_binary_metrics(y_true: list[int], y_pred: list[int], y_prob: list[float] | None = None) -> dict:
    tp=tn=fp=fn=0
    for gt, pd_ in zip(y_true, y_pred):
        if gt == 1 and pd_ == 1: tp+=1
        elif gt == 0 and pd_ == 0: tn+=1
        elif gt == 0 and pd_ == 1: fp+=1
        else: fn+=1
        
    tot = tp+tn+fp+fn
    acc = (tp+tn)/tot if tot > 0 else 0.
    prec = tp/(tp+fp) if (tp+fp) > 0 else 0.
    rec = tp/(tp+fn) if (tp+fn) > 0 else 0.
    spec = tn/(tn+fp) if (tn+fp) > 0 else 0.
    f1 = 2*prec*rec/(prec+rec) if (prec+rec) > 0 else 0.
    bal = (rec + spec) / 2
    
    try:
        if y_prob is not None:
            from sklearn.metrics import roc_auc_score, matthews_corrcoef
            roc = float(roc_auc_score(y_true, y_prob))
            mcc = float(matthews_corrcoef(y_true, y_pred))
        else:
            roc, mcc = None, None
    except:
        roc, mcc = None, None
        
    return {
        "accuracy": round(acc, 6),
        "precision": round(prec, 6),
        "recall": round(rec, 6),
        "specificity": round(spec, 6),
        "f1": round(f1, 6),
        "balanced_accuracy": round(bal, 6),
        "roc_auc": round(roc, 6) if roc else None,
        "mcc": round(mcc, 6) if mcc else None,
        "confusion_matrix": [[tn, fp], [fn, tp]],
        "TP": tp, "TN": tn, "FP": fp, "FN": fn
    }
