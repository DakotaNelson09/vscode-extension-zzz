"""
Diagnostic companion to evaluate.py: finds the specific secret rows the
baseline missed (predicted not_secret when the true label is secret) and
prints the backend's full response for each, so you can see WHY it missed
each one before picking a 3.4 mitigation.

Run this the same way as evaluate.py: same folder, same venv, backend
from Step 1.1 running.
"""

import json

import pandas as pd
import requests

BACKEND_URL = "http://localhost:8000/detect"


def diagnose(csv_path):
    df = pd.read_csv(csv_path).dropna(subset=["label"])
    secret_rows = df[df["label"].str.strip().str.lower() == "secret"].reset_index(drop=True)

    print(f"Checking {len(secret_rows)} labeled-secret rows in {csv_path}...\n")

    misses = []
    for i, row in secret_rows.iterrows():
        print(f"{i + 1}/{len(secret_rows)}", end="\r")
        resp = requests.post(
            BACKEND_URL,
            json={"text": row["text"], "max_results": 10, "batch_size": 1},
        )
        result = resp.json()
        detected = result.get("secrets_detected", 0) > 0

        if not detected:
            misses.append({"source": row["source"], "text": row["text"], "response": result})

    print()  # move off the \r line

    if not misses:
        print("No misses — every labeled secret in this file was detected. Nothing to diagnose.")
        return misses

    print(f"--- {len(misses)} missed secret(s) out of {len(secret_rows)} ---\n")
    for m in misses:
        print("=" * 70)
        print(f"source: {m['source']}")
        print("-" * 70)
        print("text:")
        print(m["text"])
        print("-" * 70)
        print("backend response:")
        print(json.dumps(m["response"], indent=2))
        print()

    return misses


if __name__ == "__main__":
    diagnose("test_set.csv")
