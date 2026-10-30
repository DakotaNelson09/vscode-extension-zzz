import pandas as pd
import requests
from sklearn.metrics import classification_report
import re

PEM_HEADER_RE = re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----")

def has_pem_private_key_header(text):
    return bool(PEM_HEADER_RE.search(text))

def evaluate(csv_path, use_pem_override=False):
    df = pd.read_csv(csv_path).dropna(subset=["label"])
    y_true, y_pred = [], []
    for i, (_, row) in enumerate(df.iterrows()):
        print(f"{i+1}/{len(df)}", end="\r")
        resp = requests.post(
            "http://localhost:8000/detect",
            json={"text": row["text"], "max_results": 10, "batch_size": 1},
        )
        result = resp.json()
        flagged = result.get("secrets_detected", 0) > 0
        if use_pem_override:
            flagged = flagged or has_pem_private_key_header(row["text"])
        y_pred.append(flagged)
        y_true.append(row["label"].strip().lower() == "secret")
    print()
    print(classification_report(y_true, y_pred, target_names=["not_secret", "secret"]))
    return y_true, y_pred

if __name__ == "__main__":
    print("--- Baseline on test_set.csv ---")
    evaluate("test_set.csv")
    print("\n--- With PEM-header override on test_set.csv ---")
    evaluate("test_set.csv", use_pem_override=True)