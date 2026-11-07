"""Run Part 1-3 in one environment with chunked prefill. Original files untouched.

    python run_all.py --limit 3            # smoke test
    python run_all.py                      # full run (resumable)
    python run_all.py --only evaluate      # re-run one stage
    python run_all.py --out /content/drive/MyDrive/cisc7021/results_same_env
"""
import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STAGES = ["baseline", "trunc2", "trunc4", "compress", "evaluate"]

def patch_llmlingua_cache():
    import llmlingua
    from transformers import DynamicCache

    def is_cache_obj(x):
        return hasattr(x, "get_seq_length")

    def to_legacy(cache):
        if not is_cache_obj(cache):
            return cache
        if hasattr(cache, "layers"):
            return [[l.keys, l.values] for l in cache.layers]
        if hasattr(cache, "to_legacy_cache"):
            return [[x[0], x[1]] for x in cache.to_legacy_cache()]
        return [[k, v] for k, v in zip(cache.key_cache, cache.value_cache)]

    def from_legacy(legacy):
        if is_cache_obj(legacy):
            return legacy
        cache = DynamicCache()
        for i, layer in enumerate(legacy):
            cache.update(layer[0], layer[1], i)
        return cache

    orig_init = llmlingua.PromptCompressor.__init__

    def init(self, *a, **k):
        orig_init(self, *a, **k)

        # 1) model.forward: legacy in -> Cache, Cache out -> legacy
        orig_forward = self.model.forward

        def forward(*fa, past_key_values=None, **fk):
            if past_key_values is not None:
                past_key_values = from_legacy(past_key_values)
            out = orig_forward(*fa, past_key_values=past_key_values, **fk)
            if getattr(out, "past_key_values", None) is not None:
                out.past_key_values = to_legacy(out.past_key_values)
            return out

        self.model.forward = forward

        # 2) get_ppl: whatever it returns with return_kv, make it legacy
        orig_get_ppl = self.get_ppl

        def get_ppl(*ga, **gk):
            res = orig_get_ppl(*ga, **gk)
            if gk.get("return_kv") and isinstance(res, tuple) and len(res) == 2:
                return res[0], to_legacy(res[1])
            return res

        self.get_ppl = get_ppl

    llmlingua.PromptCompressor.__init__ = init

def patch_chunked(threshold, chunk, model_id):
    sys.path.insert(0, str(ROOT))
    import transformers

    # Llama-2 tokenizer has no chat_template in recent transformers
    _orig_from_pretrained = transformers.AutoTokenizer.from_pretrained

    def _from_pretrained(cls, name, *a, **k):
        tok = _orig_from_pretrained(name, *a, **k)
        if getattr(tok, "chat_template", None) is None:
            tok.chat_template = _orig_from_pretrained(model_id).chat_template
        return tok

    transformers.AutoTokenizer.from_pretrained = classmethod(_from_pretrained)

    from part1_uncompressed import run_baseline as rb
    from part2_truncation import run_truncation as rt
    from part3_llmlingua import run_llmlingua as rl
    # ...(以下的 orig_hf、hf_generate 等維持原樣)
    orig_hf = rb.HFBackend.generate

    def hf_generate(self, input_ids, max_new_tokens):
        if len(input_ids) > threshold:
            return rt.generate_chunked(self, input_ids, max_new_tokens, chunk)
        return orig_hf(self, input_ids, max_new_tokens)

    rb.HFBackend.generate = hf_generate  # Part 2 imports this same class

    orig_target = rl.TargetModel.generate

    def target_generate(self, docs, question, max_new_tokens):
        input_ids = rl.render_input_ids(self.tokenizer, docs, question)
        if len(input_ids) > threshold:
            answer, latency = rt.generate_chunked(self, input_ids, max_new_tokens, chunk)
            return answer, latency, len(input_ids)
        return orig_target(self, docs, question, max_new_tokens)

    rl.TargetModel.generate = target_generate
    return rb, rt, rl


def worker(args):
    rb, rt, rl = patch_chunked(args.chunk_threshold, args.chunk_size, args.model)
    if args.worker == "compress":
        patch_llmlingua_cache()
    out = Path(args.out)
    lim = ["--limit", str(args.limit)] if args.limit else []
    ctx = ["--save-context"] if args.save_context else []
    hf_dev = "cpu" if args.device == "mps" else args.device
    stage = args.worker

    if stage == "baseline":
        code = rb.run(rb.parse_args([
            "--model", args.model, "--device", hf_dev, "--dtype", args.dtype,
            "--output", str(out / "results_member1.json"),
            "--jsonl", str(out / "results_member1.jsonl"), *lim, *ctx]))
    elif stage in ("trunc2", "trunc4"):
        code = rt.run(rt.parse_args([
            "--ratio", stage[-1], "--model", args.model, "--device", hf_dev,
            "--dtype", args.dtype, "--out-dir", str(out),
            "--chunk-threshold", str(args.chunk_threshold),
            "--chunk-size", str(args.chunk_size), *lim, *ctx]))
    elif stage == "compress":
        code = rl.main([
            "compress", "--ratios", "2", "4", "--device", args.device,
            "--jsonl", str(out / "compressed_member3.jsonl"),
            "--output", str(out / "compressed_member3.json"), *lim])
    elif stage == "evaluate":
        code = rl.main([
            "evaluate", "--model", args.model, "--device", args.device,
            "--dtype", args.dtype,
            "--input", str(out / "compressed_member3.jsonl"),
            "--jsonl", str(out / "results_member3.jsonl"),
            "--output", str(out / "results_member3.json"), *lim, *ctx])
    sys.exit(int(code or 0))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", default=str(ROOT / "rerun_same_machine"))
    p.add_argument("--only", nargs="+", choices=STAGES, default=STAGES)
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--model", default="unsloth/Llama-3.2-3B-Instruct")
    p.add_argument("--device", default="auto", choices=["auto", "cpu", "cuda", "mps"])
    p.add_argument("--dtype", default="float16", choices=["float32", "float16", "bfloat16"])
    p.add_argument("--chunk-threshold", type=int, default=4096)
    p.add_argument("--chunk-size", type=int, default=2048)
    p.add_argument("--save-context", action="store_true")
    p.add_argument("--worker", choices=STAGES, help=argparse.SUPPRESS)
    args = p.parse_args()

    Path(args.out).mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")

    if args.worker:
        worker(args)
        return

    passthrough = [a for a in sys.argv[1:] if a not in ("--only", *STAGES)]
    # rebuild clean arg list (drop --only values)
    base = ["--out", args.out, "--model", args.model, "--device", args.device,
            "--dtype", args.dtype, "--chunk-threshold", str(args.chunk_threshold),
            "--chunk-size", str(args.chunk_size)]
    if args.limit:
        base += ["--limit", str(args.limit)]
    if args.save_context:
        base += ["--save-context"]

    for stage in [s for s in STAGES if s in args.only]:
        print(f"\n{'=' * 70}\n[stage] {stage}\n{'=' * 70}", flush=True)
        t0 = time.perf_counter()
        rc = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "--worker", stage, *base],
            cwd=ROOT).returncode
        if rc != 0:
            print(f"[FAILED] {stage} (exit {rc}). Re-run the same command to resume.")
            sys.exit(rc)
        print(f"[ok] {stage} in {(time.perf_counter() - t0) / 60:.1f} min", flush=True)
    print(f"\nAll done. Results in: {args.out}")


if __name__ == "__main__":
    main()