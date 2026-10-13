"""Shared data loading and scoring for the sentiment model test."""
import json
import sys
from pathlib import Path

import pandas as pd
from sklearn.metrics import accuracy_score, f1_score

LABELS = ["negative", "neutral", "positive"]
ORACLE = {-1: "negative", 0: "neutral", 1: "positive"}
DATASETS = {"github": "GitHub", "jira": "Jira", "so": "Stack Overflow"}


def load(data_dir):
    """Return (train, test): fold 0 of each dataset is the test set, folds 1-9 are train."""
    frames = []
    for key, name in DATASETS.items():
        df = pd.read_csv(Path(data_dir) / f"{key}.csv")
        df["source"] = name
        df["fold"] = df["dataset"].str.rsplit("_", n=1).str[-1].astype(int)
        df["label"] = df["oracle"].map(ORACLE)
        df["text"] = df["text"].astype(str)
        frames.append(df[["id", "source", "fold", "text", "label"]])
    full = pd.concat(frames, ignore_index=True)
    return full[full.fold != 0].reset_index(drop=True), full[full.fold == 0].reset_index(drop=True)


def score(y_true, y_pred, labels=LABELS):
    return {
        "n": len(y_true),
        "accuracy": round(accuracy_score(y_true, y_pred), 4),
        "macro_f1": round(f1_score(y_true, y_pred, labels=labels, average="macro", zero_division=0), 4),
    }


def score_by_source(test, preds, labels=LABELS):
    out = {"All": score(test["label"], preds, labels)}
    for name in DATASETS.values():
        m = (test["source"] == name).values
        out[name] = score(test["label"][m], pd.Series(preds)[m], labels)
    return out


def save(results_path, model_name, result):
    p = Path(results_path)
    data = json.loads(p.read_text()) if p.exists() else {}
    data[model_name] = result
    p.write_text(json.dumps(data, indent=2))
    print(model_name, json.dumps(result), file=sys.stderr)
