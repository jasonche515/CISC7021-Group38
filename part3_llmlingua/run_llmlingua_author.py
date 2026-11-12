"""Run the author's published LLMLingua inference recipe on the course QA task.

Uses the Alpaca checkpoint named in Microsoft's demonstration and the
iterative_size=100/context_budget=*2 recipe in the official reproduction FAQ.
This is a transfer evaluation, not a recreation of every paper experiment.
"""
from __future__ import annotations
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from part3_llmlingua.run_llmlingua_paper import build_parser, run
PART = Path(__file__).resolve().parent
COMPRESSOR = "vicgalle/alpaca-7b"
REVISION = "c98caccd9a60bc04b92c07e93966a72ee5173a95"
def main() -> int:
    parser = build_parser()
    parser.description = __doc__
    parser.set_defaults(recipe="author_release", compressor_model=COMPRESSOR, revision=REVISION, iterative_size=100, context_budget="*2", sample_indices=[17, 75, 130], jsonl=PART / "author_pilot3_compressed.jsonl", output=PART / "author_pilot3_compressed.json")
    args = parser.parse_args()
    if args.compressor_model != COMPRESSOR or args.revision != REVISION or args.iterative_size != 100 or args.context_budget != "*2":
        parser.error("This runner fixes the checkpoint and author recipe; use a separate experiment for variants")
    return run(args)
if __name__ == "__main__":
    raise SystemExit(main())
