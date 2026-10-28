"""Fine-tune roberta-base on folds 1-9 of the three sets and score it on fold 0."""

import sys
from pathlib import Path

import torch
from common import LABELS, load, save, score_by_source
from torch.utils.data import DataLoader
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    get_linear_schedule_with_warmup,
)

data_dir, out_dir = sys.argv[1], Path(sys.argv[2])
out_dir.mkdir(parents=True, exist_ok=True)
torch.manual_seed(42)
device = "cuda" if torch.cuda.is_available() else "cpu"
EPOCHS, BATCH, LR, MAX_LEN = 3, 32, 2e-5, 128

train, test = load(data_dir)
tok = AutoTokenizer.from_pretrained("roberta-base")
model = AutoModelForSequenceClassification.from_pretrained(
    "roberta-base", num_labels=len(LABELS)
).to(device)


def batches(df, shuffle):
    rows = list(zip(df["text"].tolist(), df["label"].map(LABELS.index).tolist()))

    def collate(items):
        enc = tok(
            [t for t, _ in items],
            truncation=True,
            max_length=MAX_LEN,
            padding=True,
            return_tensors="pt",
        )
        enc["labels"] = torch.tensor([y for _, y in items])
        return enc

    return DataLoader(rows, batch_size=BATCH, shuffle=shuffle, collate_fn=collate)


train_dl = batches(train, True)
opt = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=0.01)
steps = EPOCHS * len(train_dl)
sched = get_linear_schedule_with_warmup(opt, int(0.06 * steps), steps)
scaler = torch.amp.GradScaler(enabled=device == "cuda")

for epoch in range(EPOCHS):
    model.train()
    total = 0.0
    for b in train_dl:
        b = {k: v.to(device) for k, v in b.items()}
        with torch.autocast(device_type=device, enabled=device == "cuda"):
            loss = model(**b).loss
        opt.zero_grad()
        scaler.scale(loss).backward()
        scaler.step(opt)
        scaler.update()
        sched.step()
        total += loss.item()
    print(f"epoch {epoch + 1} mean loss {total / len(train_dl):.4f}", file=sys.stderr)

model.eval()
preds = []
with torch.no_grad():
    for b in batches(test, False):
        b = {k: v.to(device) for k, v in b.items() if k != "labels"}
        preds += [LABELS[i] for i in model(**b).logits.argmax(-1).tolist()]

out = test[["id", "source", "text", "label"]].copy()
out["roberta_finetuned"] = preds
out.to_csv(out_dir / "predictions_finetuned.csv", index=False)
result = score_by_source(test, preds)
result["train_n"] = len(train)
save(out_dir / "results.json", "roberta-base fine-tuned on folds 1-9 (ours)", result)
