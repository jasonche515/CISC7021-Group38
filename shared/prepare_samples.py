"""Download LongBench ``multifieldqa_en`` and build the shared sample index.

Run once (Member 1's responsibility):

    python shared/prepare_samples.py

The output ``shared/samples.json`` is the single source of truth for all three
members: a fixed, seed-controlled list of samples with stable ids, so every
method is evaluated on exactly the same questions and contexts.
"""

import argparse
import json
import random
import sys
import zipfile
from pathlib import Path

import requests
from tqdm import tqdm

try:  # run as a script (python shared/prepare_samples.py)
    from config import (
        DATA_DIR,
        DATASET_NAME,
        LONGBENCH_URL,
        NUM_SAMPLES,
        SAMPLES_PATH,
        SEED,
    )
except ImportError:  # imported from the repo root
    from shared.config import (
        DATA_DIR,
        DATASET_NAME,
        LONGBENCH_URL,
        NUM_SAMPLES,
        SAMPLES_PATH,
        SEED,
    )


def download(url: str, dest: Path) -> None:
    if dest.exists() and dest.stat().st_size > 0:
        print(f"[skip] {dest} already exists")
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    with requests.get(url, stream=True, timeout=120) as response:
        response.raise_for_status()
        total = int(response.headers.get("content-length", 0))
        with open(tmp, "wb") as handle, tqdm(
            total=total, unit="B", unit_scale=True, desc=dest.name
        ) as bar:
            for chunk in response.iter_content(chunk_size=1 << 20):
                if chunk:
                    handle.write(chunk)
                    bar.update(len(chunk))
    tmp.replace(dest)


def load_jsonl(path: Path) -> list:
    with open(path, encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--num-samples", type=int, default=NUM_SAMPLES)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--output", type=Path, default=SAMPLES_PATH)
    parser.add_argument("--force", action="store_true", help="rebuild samples.json")
    args = parser.parse_args()

    if args.output.exists() and not args.force:
        print(f"[skip] {args.output} already exists (use --force to rebuild)")
        return 0

    archive = DATA_DIR / "data.zip"
    download(LONGBENCH_URL, archive)

    jsonl_path = DATA_DIR / f"{DATASET_NAME}.jsonl"
    if not jsonl_path.exists():
        with zipfile.ZipFile(archive) as zf:
            member = f"data/{DATASET_NAME}.jsonl"
            zf.extract(member, DATA_DIR)
            (DATA_DIR / member).replace(jsonl_path)

    records = load_jsonl(jsonl_path)
    records.sort(key=lambda row: str(row["_id"]))

    num = min(args.num_samples, len(records))
    rng = random.Random(args.seed)
    picked = rng.sample(records, num)
    picked.sort(key=lambda row: str(row["_id"]))

    samples = []
    for row in picked:
        answers = row.get("answers") or []
        if isinstance(answers, str):
            answers = [answers]
        samples.append(
            {
                "id": str(row["_id"]),
                "question": row["input"],
                "docs": row["context"],
                "answers": answers,
                "length": row.get("length"),
            }
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(
            {
                "dataset": DATASET_NAME,
                "seed": args.seed,
                "num_samples": len(samples),
                "samples": samples,
            },
            handle,
            ensure_ascii=False,
            indent=2,
        )
    print(f"[ok] wrote {len(samples)} samples to {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
