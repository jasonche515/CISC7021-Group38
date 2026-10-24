"""Unified prompt formatting shared by all three members.

Every member must build prompts through these helpers so that the prompt
wording, chat template and token counting are identical across methods.
The wording follows the official LongBench ``multifieldqa_en`` template.
"""

from typing import Dict, List, Tuple

SYSTEM_PROMPT = (
    "You are a helpful assistant that answers questions based only on the "
    "provided text."
)

USER_TEMPLATE = (
    "Read the following text and answer the question briefly.\n\n"
    "Text: {docs}\n\n"
    "Question: {question}\n\n"
    "Answer:"
)


def build_prompt(docs: str, question: str) -> str:
    """Return the plain-text user prompt for one sample."""
    return USER_TEMPLATE.format(docs=docs.strip(), question=question.strip())


def build_messages(docs: str, question: str) -> List[Dict[str, str]]:
    """Return chat messages (system + user) for one sample."""
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": build_prompt(docs, question)},
    ]


def render_input_ids(tokenizer, docs: str, question: str) -> List[int]:
    """Apply the model chat template and return the prompt token ids."""
    # Render to text first, then tokenize with ``add_special_tokens=False``:
    # the template already contains the BOS/special tokens, and this avoids
    # the ``tokenize=True`` return type differences across transformers
    # versions (list[int] vs tokenizers.Encoding).
    text = tokenizer.apply_chat_template(
        build_messages(docs, question),
        add_generation_prompt=True,
        tokenize=False,
    )
    return tokenizer(text, add_special_tokens=False, verbose=False)["input_ids"]


def build_with_budget(
    tokenizer,
    docs: str,
    question: str,
    max_prompt_tokens: int,
) -> Tuple[str, List[int], Dict[str, object]]:
    """Build the prompt, shrinking ``docs`` if it exceeds the token budget.

    The docs are truncated from the tail (head is kept) because this is the
    uncompressed baseline: the raw context is used whenever it fits, and the
    fallback is recorded explicitly so the truncation is transparent.

    Returns ``(docs_used, input_ids, info)`` where ``info`` contains
    ``original_prompt_tokens`` and ``truncated``.
    """
    input_ids = render_input_ids(tokenizer, docs, question)
    original_tokens = len(input_ids)
    info: Dict[str, object] = {
        "original_prompt_tokens": original_tokens,
        "truncated": False,
        "docs_chars_used": len(docs),
    }
    if original_tokens <= max_prompt_tokens:
        info["prompt_tokens"] = original_tokens
        return docs, input_ids, info

    docs_ids = tokenizer(docs, add_special_tokens=False, verbose=False)["input_ids"]

    # Binary search the largest docs prefix that still fits the budget.
    lo, hi = 0, len(docs_ids)
    best_docs, best_ids = "", render_input_ids(tokenizer, "", question)
    while lo <= hi:
        mid = (lo + hi) // 2
        candidate = tokenizer.decode(docs_ids[:mid], skip_special_tokens=True)
        candidate_ids = render_input_ids(tokenizer, candidate, question)
        if len(candidate_ids) <= max_prompt_tokens:
            best_docs, best_ids = candidate, candidate_ids
            lo = mid + 1
        else:
            hi = mid - 1

    if len(best_ids) > max_prompt_tokens:  # pathological template overhead
        best_ids = best_ids[:max_prompt_tokens]
        best_docs = ""

    info.update(
        truncated=True,
        prompt_tokens=len(best_ids),
        docs_chars_used=len(best_docs),
    )
    return best_docs, best_ids, info
