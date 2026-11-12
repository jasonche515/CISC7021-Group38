import json, sys
from pathlib import Path
import pandas as pd
from transformers import AutoTokenizer

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from shared.config import MODEL_ID, SAMPLES_PATH
from part2_truncation.run_truncation import locate_answer 

tok = AutoTokenizer.from_pretrained(MODEL_ID)
samples = {s["id"]: s for s in json.load(open(SAMPLES_PATH, encoding="utf-8"))}

rows = []
for ratio in (2, 4):
    data = json.load(open(Path(__file__).parent / f"results_member2_{ratio}x.json", encoding="utf-8"))
    for r in data["results"]:
        s = samples[r["id"]]
        info = locate_answer(tok, s["docs"], s["answers"],
                             r["orig_docs_tokens"], ratio, r["head_frac"])
        rows.append({"ratio": ratio, "id": r["id"], "f1": r["f1"], "em": r["em"], **info})

df = pd.DataFrame(rows)
df.to_csv(Path(__file__).parent / "answer_position_analysis.csv", index=False)
print(df.groupby(["ratio", "answer_zone"]).agg(n=("f1", "size"), mean_f1=("f1", "mean"), mean_em=("em", "mean")))