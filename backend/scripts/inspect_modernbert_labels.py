import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer


MODEL_ID = "aieng-lab/ModernBERT-base_sentiment"

examples = [
    ("positive", "Thank you so much! This solution works perfectly."),
    ("negative", "This is terrible. I'm very frustrated with these failures."),
    ("neutral", "The meeting is scheduled for Tuesday at 10 AM."),
    ("positive", "Excellent work! The team did a fantastic job."),
    ("negative", "I'm disappointed that the bug still isn't fixed."),
    ("neutral", "The pull request contains three updated files."),
]

tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
model = AutoModelForSequenceClassification.from_pretrained(
    MODEL_ID,
    attn_implementation="sdpa",
)

model.eval()

for expected, text in examples:
    inputs = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        max_length=128,
    )

    with torch.inference_mode():
        probabilities = torch.softmax(
            model(**inputs).logits,
            dim=-1,
        )[0]

    print(f"\nExpected: {expected}")
    print(f"Text: {text}")

    for index, probability in enumerate(probabilities.tolist()):
        print(f"LABEL_{index}: {probability:.2%}")

    print(f"Predicted index: {probabilities.argmax().item()}")
