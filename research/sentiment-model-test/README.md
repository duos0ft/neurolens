# Sentiment model test

A first test of pre-trained transformer models for sentiment analysis on work-related text conversations.
Five ready-made Hugging Face models were scored untuned, and one RoBERTa model was fine-tuned by us,
all on the same held-out messages.

## Result

Fine-tuning wins clearly: RoBERTa fine-tuned on developer conversations reached 87.1% accuracy,
against 78.3% for the best ready-made model.

| Model | Accuracy | Macro F1 | GitHub acc. | Jira acc. | Stack Overflow acc. |
| --- | --- | --- | --- | --- | --- |
| `roberta-base`, fine-tuned by us | 87.1% | 0.866 | 86.1% | 88.8% | 86.5% |
| `SamLowe/roberta-base-go_emotions` (emotions mapped to polarity) | 78.3% | 0.760 | 65.9% | 90.3% | 82.4% |
| `cardiffnlp/twitter-roberta-base-sentiment-latest` | 74.7% | 0.745 | 71.3% | 77.2% | 77.0% |
| `MoritzLaurer/deberta-v3-large-zeroshot-v2.0` (zero-shot) | 72.1% | 0.716 | 72.2% | 72.3% | 71.6% |
| `j-hartmann/emotion-english-distilroberta-base` (emotions mapped to polarity) | 69.5% | 0.642 | 61.3% | 79.8% | 68.9% |
| Always answer "neutral" (baseline) | 49.8% | 0.222 | 42.5% | 67.3% | 38.3% |

`siebert/sentiment-roberta-large-english` has no neutral class, so it was scored only on the 876
non-neutral test messages: 86.2% accuracy, 0.862 macro F1. That number is not comparable with the table.

## Test data

Three public, human-labeled datasets of developer conversation, labeled negative, neutral or positive,
from [disa-lab/DeepSentimentSECrossPlatform](https://github.com/disa-lab/DeepSentimentSECrossPlatform) (CC0 licence):

| File | Source | Messages |
| --- | --- | --- |
| `data/github.csv` | GitHub pull request and commit comments | 7,122 |
| `data/jira.csv` | Jira issue comments | 5,869 |
| `data/so.csv` | Stack Overflow posts | 4,423 |

Each file comes with 10 stratified folds. Fold 0 of each file is the test set (1,745 messages);
folds 1 to 9 are the training set for the fine-tune (15,669 messages).

## Limits

- **Not workplace chat.** This is developer conversation, the closest public labeled data we found. Scores on our own messages will differ.
- **One fold, one seed.** The fine-tune was run once; no confidence interval.
- **Emotion mapping is ours.** The SamLowe and j-hartmann models predict emotions; the mapping to polarity is in `eval_pretrained.py`. The Jira and Stack Overflow labels were themselves derived from emotions, which may favour these models there.
- **Small overlap.** 70 test messages also appear in the training folds. Without them the fine-tuned model scores 87.0%.
- **Zero-shot prompt.** One hypothesis template was tried ("The sentiment of this text is {}."); others may score differently.

## Files

- `common.py`: data loading and scoring.
- `eval_pretrained.py`: scores the five ready-made models.
- `finetune_roberta.py`: fine-tunes `roberta-base` (3 epochs, batch 32, learning rate 2e-5, max length 128, seed 42) and scores it. The trained weights are not saved.
- `results/results.json`: all scores, overall and per dataset.
- `results/predictions_pretrained.csv`, `results/predictions_finetuned.csv`: the prediction for every test message.

## Rerun

Run with Python 3.14, torch 2.11.0 (CUDA 12.8), transformers 5.19.0 on an RTX 3070 Ti.
The first run downloads about 4 GB of models.

```
python -m venv venv
venv\Scripts\python -m pip install torch --index-url https://download.pytorch.org/whl/cu128
venv\Scripts\python -m pip install transformers scikit-learn pandas sentencepiece protobuf
venv\Scripts\python eval_pretrained.py data results
venv\Scripts\python finetune_roberta.py data results
```
