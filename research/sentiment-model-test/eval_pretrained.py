"""Score the ready-made models, untuned, on fold 0 of the GitHub, Jira and Stack Overflow sets."""

import sys
from pathlib import Path

import pandas as pd
import torch
from common import LABELS, load, save, score, score_by_source
from transformers import pipeline

data_dir, out_dir = sys.argv[1], Path(sys.argv[2])
out_dir.mkdir(parents=True, exist_ok=True)
results = out_dir / "results.json"
device = 0 if torch.cuda.is_available() else -1
_, test = load(data_dir)
texts = test["text"].tolist()
preds = test[["id", "source", "text", "label"]].copy()

# GoEmotions' own grouping of its 28 labels; "ambiguous" emotions count as neutral here.
GO_POS = {
    "amusement",
    "excitement",
    "joy",
    "love",
    "desire",
    "optimism",
    "caring",
    "pride",
    "admiration",
    "gratitude",
    "relief",
    "approval",
}
GO_NEG = {
    "fear",
    "nervousness",
    "remorse",
    "embarrassment",
    "disappointment",
    "sadness",
    "grief",
    "disgust",
    "anger",
    "annoyance",
    "disapproval",
}
EKMAN = {
    "joy": "positive",
    "anger": "negative",
    "disgust": "negative",
    "fear": "negative",
    "sadness": "negative",
    "neutral": "neutral",
    "surprise": "neutral",
}


def classify(model, mapper):
    pipe = pipeline("text-classification", model=model, device=device)
    out = pipe(texts, batch_size=32, truncation=True, max_length=256)
    del pipe
    torch.cuda.empty_cache()
    return [mapper(o["label"]) for o in out]


def go_map(label):
    return (
        "positive" if label in GO_POS else "negative" if label in GO_NEG else "neutral"
    )


# 1) Cardiff: three classes, used as is.
p = classify("cardiffnlp/twitter-roberta-base-sentiment-latest", str.lower)
preds["cardiff"] = p
save(
    results,
    "cardiffnlp/twitter-roberta-base-sentiment-latest",
    score_by_source(test, p),
)

# 2) SamLowe: top emotion mapped to polarity.
p = classify("SamLowe/roberta-base-go_emotions", go_map)
preds["samlowe"] = p
save(
    results,
    "SamLowe/roberta-base-go_emotions (emotions mapped to polarity)",
    score_by_source(test, p),
)

# 3) j-hartmann: top emotion mapped to polarity.
p = classify(
    "j-hartmann/emotion-english-distilroberta-base", lambda l: EKMAN[l.lower()]
)
preds["jhartmann"] = p
save(
    results,
    "j-hartmann/emotion-english-distilroberta-base (emotions mapped to polarity)",
    score_by_source(test, p),
)

# 4) Zero-shot: the three labels are given as plain words, no training.
zs = pipeline(
    "zero-shot-classification",
    model="MoritzLaurer/deberta-v3-large-zeroshot-v2.0",
    device=device,
)
out = zs(
    texts,
    candidate_labels=LABELS,
    hypothesis_template="The sentiment of this text is {}.",
    multi_label=False,
    batch_size=16,
    truncation=True,
    max_length=256,
)
del zs
torch.cuda.empty_cache()
p = [o["labels"][0] for o in out]
preds["zeroshot"] = p
save(
    results,
    "MoritzLaurer/deberta-v3-large-zeroshot-v2.0 (zero-shot)",
    score_by_source(test, p),
)

# 5) SiEBERT has no neutral class, so it is scored only on the non-neutral messages.
p = classify("siebert/sentiment-roberta-large-english", str.lower)
preds["siebert"] = p
m = (test["label"] != "neutral").values
two = ["negative", "positive"]
save(
    results,
    "siebert/sentiment-roberta-large-english (non-neutral messages only)",
    {"All": score(test["label"][m], pd.Series(p)[m], two)},
)

preds.to_csv(out_dir / "predictions_pretrained.csv", index=False)
