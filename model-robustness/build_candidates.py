import json
import re
import random
import pandas as pd

patterns_df = pd.read_excel("../IssueGuard/Secret-Regular-Expression.xlsx")
pattern_list = patterns_df["Regular Expression"].dropna().tolist()
compiled_patterns = []
skipped = []
for p in pattern_list:
    try:
        compiled_patterns.append(re.compile(p))
    except re.error as e:
        skipped.append((p, str(e)))

print(f"Compiled {len(compiled_patterns)} of {len(pattern_list)} patterns ({len(skipped)} skipped — incompatible with Python's re module)")

with open("raw_samples.json", encoding="utf-8") as f:
    samples = json.load(f)

hits, non_hits = [], []
for sample in samples:
    matched = any(p.search(sample["text"]) for p in compiled_patterns)
    (hits if matched else non_hits).append(sample)

print(f"{len(hits)} regex hits, {len(non_hits)} non-hits out of {len(samples)} total")

random.seed(42)
sampled_non_hits = random.sample(non_hits, min(len(hits) * 2, len(non_hits)))

rows = []
for s in hits:
    rows.append({"source": s["source"], "text": s["text"], "regex_flagged": True, "label": ""})
for s in sampled_non_hits:
    rows.append({"source": s["source"], "text": s["text"], "regex_flagged": False, "label": ""})

pd.DataFrame(rows).to_csv("to_label.csv", index=False)
print(f"Wrote {len(rows)} rows to to_label.csv")