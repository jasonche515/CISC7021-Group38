"""Shared experiment configuration for CISC7021 Group 38.

All three members must keep these values identical so that results are
directly comparable.
"""

from pathlib import Path

# --- Paths -----------------------------------------------------------------
SHARED_DIR = Path(__file__).resolve().parent
REPO_ROOT = SHARED_DIR.parent
DATA_DIR = SHARED_DIR / "data"
SAMPLES_PATH = SHARED_DIR / "samples.json"

# --- Dataset ---------------------------------------------------------------
DATASET_NAME = "multifieldqa_en"
LONGBENCH_URL = (
    "https://huggingface.co/datasets/THUDM/LongBench/resolve/main/data.zip"
)
NUM_SAMPLES = 150  # full multifieldqa_en test split (LongBench v1 has 150)
SEED = 42

# --- Model / generation ----------------------------------------------------
# Canonical model id. ``meta-llama/Llama-3.2-3B-Instruct`` is licence-gated on
# the Hugging Face Hub; the identical ungated mirror
# ``unsloth/Llama-3.2-3B-Instruct`` can be passed with ``--model`` instead.
MODEL_ID = "meta-llama/Llama-3.2-3B-Instruct"
MIRROR_MODEL_ID = "unsloth/Llama-3.2-3B-Instruct"
TEMPERATURE = 0.0
MAX_NEW_TOKENS = 64

# Llama-3.2-3B-Instruct is trained with a 131072 token context window
# (``rope_scaling.type = llama3``, factor 32), so the raw contexts in
# multifieldqa_en (max 15026 tokens) all fit and the baseline needs no
# truncation. The prompt budget is capped at 32768 to bound the fp16 KV cache
# on a 12 GB GPU; no sample in the shared index reaches it.
MODEL_CONTEXT_WINDOW = 131072
MAX_CONTEXT_TOKENS = 32768
MAX_PROMPT_TOKENS = MAX_CONTEXT_TOKENS - MAX_NEW_TOKENS - 32
