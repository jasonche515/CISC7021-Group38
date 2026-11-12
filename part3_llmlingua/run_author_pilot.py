"""Run a fixed sample list through the pinned author recipe and matched baseline."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone
PART = Path(__file__).resolve().parent
ROOT = PART.parent
COMPRESSOR = "vicgalle/alpaca-7b"
REVISION = "c98caccd9a60bc04b92c07e93966a72ee5173a95"
def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample-indices", nargs="+", type=int, default=None)
    parser.add_argument("--all-samples", action="store_true")
    parser.add_argument("--seed-prefixes", nargs="*", default=[])
    parser.add_argument("--prefix", default="author_pilot3")
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()
    samples = json.loads((ROOT / "shared/samples.json").read_text())["samples"]
    if args.all_samples and args.sample_indices is not None:
        parser.error("Choose --all-samples or --sample-indices")
    if args.all_samples and len(samples) != 150:
        parser.error("The frozen full experiment requires the shared 150-sample split")
    args.sample_indices = list(range(len(samples))) if args.all_samples else (args.sample_indices or [17, 75, 130])
    if any(not name.replace("_", "").isalnum() for name in [args.prefix] + args.seed_prefixes) or len(set(args.sample_indices)) != len(args.sample_indices):
        parser.error("Use a simple filename prefix and distinct source indices")
    if any(index < 0 or index >= len(samples) for index in args.sample_indices):
        parser.error("Source index is outside the shared split")
    def artifact(suffix):
        return PART / f"{args.prefix}_{suffix}"
    expected_ids = {samples[index]["id"] for index in args.sample_indices}
    seeded = {}
    for suffix in ("compressed.jsonl", "results.jsonl", "matched_headtail.jsonl"):
        destination = artifact(suffix)
        existing = [json.loads(line) for line in destination.read_text().splitlines() if line.strip()] if destination.exists() else []
        done = {(row["id"], int(row["target_compression_ratio"])) for row in existing}
        additions = []
        for prefix in args.seed_prefixes:
            source_path = PART / f"{prefix}_{suffix}"
            for line in source_path.read_text().splitlines():
                if not line.strip():
                    continue
                row = json.loads(line)
                if row["id"] not in expected_ids or int(row["target_compression_ratio"]) not in (2, 4):
                    raise ValueError("Seed row is outside the fixed experiment")
                if suffix == "compressed.jsonl":
                    required = {"recipe": "author_release", "compressor_model": COMPRESSOR, "compressor_revision": REVISION, "iterative_size": 100, "context_budget": "*2", "preprocessing_version": "preserve_source_v2", "compressor_loading_verified": True, "compressor_lm_head_key_remapped": True, "source_text_preserved": True}
                    if any(row.get(key) != value for key, value in required.items()):
                        raise ValueError("Seed compression settings do not match the frozen recipe")
                elif suffix == "results.jsonl":
                    settings = row.get("compression_settings", {})
                    if settings.get("compressor_loading_verified") is not True or settings.get("compressor_revision") != REVISION or row.get("method") != "llmlingua_author_recipe_alpaca":
                        raise ValueError("Seed evaluation lacks frozen-recipe provenance")
                elif row.get("method") != "head_tail_matched_author_budget" or not 0 <= row.get("budget_gap_tokens", -1) <= 2:
                    raise ValueError("Invalid matched-baseline seed")
                key = (row["id"], int(row["target_compression_ratio"]))
                if key not in done:
                    additions.append(row)
                    done.add(key)
        if additions:
            with destination.open("a", encoding="utf-8") as handle:
                for row in additions:
                    handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        seeded[suffix] = len(additions)
    environment = os.environ.copy()
    environment.update({"HF_HOME": str(ROOT / ".cache/huggingface"), "TRANSFORMERS_CACHE": str(ROOT / ".cache/huggingface/transformers"), "PYTHONUNBUFFERED": "1"})
    environment.pop("HF_HUB_OFFLINE", None)
    os.environ.update({k: environment[k] for k in ("HF_HOME", "TRANSFORMERS_CACHE", "PYTHONUNBUFFERED")})
    os.environ.pop("HF_HUB_OFFLINE", None)
    from huggingface_hub import snapshot_download
    status_path = artifact("status.json")
    frozen_paths = ["part3_llmlingua/run_llmlingua_paper.py", "part3_llmlingua/run_llmlingua_author.py", "part3_llmlingua/run_llmlingua.py", "part3_llmlingua/run_author_matched_baseline.py", "shared/config.py", "shared/metrics.py", "shared/prompt_template.py", "shared/samples.json"]
    frozen_hashes = {path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in frozen_paths}
    status = {"state": "running", "stage": "download", "started_at": datetime.now(timezone.utc).isoformat(), "sample_indices": args.sample_indices, "num_source_samples": len(args.sample_indices), "num_jobs_per_stage": 2 * len(args.sample_indices), "seed_prefixes": args.seed_prefixes, "new_seed_rows": seeded, "compressor_model": COMPRESSOR, "compressor_revision": REVISION, "frozen_code_sha256": frozen_hashes}
    def save():
        temporary = status_path.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(status, indent=2), encoding="utf-8")
        temporary.replace(status_path)
    save()
    try:
        snapshot = snapshot_download(COMPRESSOR, revision=REVISION, cache_dir=environment["TRANSFORMERS_CACHE"], allow_patterns=["config.json", "generation_config.json", "*.safetensors", "model.safetensors.index.json", "tokenizer.model", "tokenizer_config.*", "special_tokens_map.json"], max_workers=3, local_files_only=args.offline)
        status["snapshot_path"] = snapshot
        environment["HF_HUB_OFFLINE"] = "1"
        stages = [
            ("compression", [str(PART / "run_llmlingua_author.py"), "--device", "mps", "--sample-indices", *map(str, args.sample_indices), "--jsonl", str(artifact("compressed.jsonl")), "--output", str(artifact("compressed.json"))]),
            ("evaluation", [str(PART / "run_llmlingua.py"), "evaluate", "--input", str(artifact("compressed.jsonl")), "--device", "mps", "--dtype", "float16", "--jsonl", str(artifact("results.jsonl")), "--output", str(artifact("results.json")), "--save-context"]),
            ("matched_baseline", [str(PART / "run_author_matched_baseline.py"), "--input", str(artifact("results.json")), "--jsonl", str(artifact("matched_headtail.jsonl")), "--output", str(artifact("matched_headtail.json"))]),
            ("analysis", [str(PART / "analyze_paper_pilot.py"), *( ["--all-samples"] if args.all_samples else ["--sample-indices", *map(str, args.sample_indices)] ), "--compressed", str(artifact("compressed.json")), "--results", str(artifact("results.json")), "--matched-baseline", str(artifact("matched_headtail.json")), "--out-dir", str(artifact("analysis"))]),
        ]
        if args.all_samples:
            stages.append(("report_contribution", [str(PART / "build_author_full_contribution.py"), "--prefix", args.prefix]))
        for stage, arguments in stages:
            status.update(stage=stage, state="running")
            save()
            print(f"[author-pilot] {stage}", flush=True)
            with (PART / f"_{args.prefix}.log").open("a", encoding="utf-8") as log:
                with subprocess.Popen([sys.executable] + arguments, cwd=ROOT, env=environment, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1) as process:
                    for line in process.stdout:
                        log.write(line)
                        log.flush()
                        print(line, end="", flush=True)
                    code = process.wait()
            if code:
                status.update(state="failed", exit_code=code, finished_at=datetime.now(timezone.utc).isoformat())
                save()
                return code
    except BaseException as error:
        status.update(state="interrupted" if isinstance(error, KeyboardInterrupt) else "failed", error=str(error), finished_at=datetime.now(timezone.utc).isoformat())
        save()
        raise
    if any(hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != digest for path, digest in frozen_hashes.items()):
        status.update(state="failed", stage="freeze_check", error="Frozen experiment source changed during execution", finished_at=datetime.now(timezone.utc).isoformat())
        save()
        return 1
    status.update(state="complete", stage="complete", exit_code=0, finished_at=datetime.now(timezone.utc).isoformat())
    save()
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
