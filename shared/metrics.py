"""Answer metrics (Exact Match / token-level F1) shared by all members.

Implements the standard SQuAD/LongBench normalisation so that the numbers are
comparable with the published LongBench ``multifieldqa_en`` results.
"""

import re
import string
from collections import Counter
from typing import Dict, Iterable, List


def normalize_answer(text: str) -> str:
    """Lowercase, strip punctuation/articles and collapse whitespace."""
    text = text.lower()

    def remove_articles(s: str) -> str:
        return re.sub(r"\b(a|an|the)\b", " ", s)

    def remove_punc(s: str) -> str:
        return "".join(ch for ch in s if ch not in set(string.punctuation))

    def white_space_fix(s: str) -> str:
        return " ".join(s.split())

    return white_space_fix(remove_articles(remove_punc(text)))


def exact_match(prediction: str, ground_truth: str) -> float:
    return float(normalize_answer(prediction) == normalize_answer(ground_truth))


def f1(prediction: str, ground_truth: str) -> float:
    pred_tokens = normalize_answer(prediction).split()
    gold_tokens = normalize_answer(ground_truth).split()
    if not pred_tokens or not gold_tokens:
        # Both empty counts as a perfect match, otherwise no overlap.
        return float(pred_tokens == gold_tokens)
    common = Counter(pred_tokens) & Counter(gold_tokens)
    num_same = sum(common.values())
    if num_same == 0:
        return 0.0
    precision = num_same / len(pred_tokens)
    recall = num_same / len(gold_tokens)
    return 2 * precision * recall / (precision + recall)


def score(prediction: str, answers: Iterable[str]) -> Dict[str, float]:
    """Return the best EM/F1 over all reference answers."""
    answers: List[str] = list(answers)
    if not answers:
        return {"em": 0.0, "f1": 0.0}
    return {
        "em": max(exact_match(prediction, gold) for gold in answers),
        "f1": max(f1(prediction, gold) for gold in answers),
    }


def mean_metrics(rows: Iterable[Dict[str, object]]) -> Dict[str, float]:
    rows = list(rows)
    if not rows:
        return {}
    keys = ["em", "f1", "prompt_tokens", "generation_latency", "total_latency"]
    out = {}
    for key in keys:
        values = [float(row[key]) for row in rows if row.get(key) is not None]
        if values:
            out[f"mean_{key}"] = sum(values) / len(values)
    out["num_samples"] = len(rows)
    return out
