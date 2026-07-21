"""
build_dataset.py

Validates dataset/seed_dataset.csv and splits it into
train / val / test CSVs for later use in BERT fine-tuning
and LSTM/CNN training.

Usage:
    python scripts/build_dataset.py
"""

import csv
import random
import os

SEED = 42
INPUT_PATH = os.path.join("dataset", "seed_dataset.csv")
OUTPUT_DIR = "dataset"

VALID_LABELS = {"sensitive", "non-sensitive"}
VALID_CATEGORIES = {"PII", "financial", "credentials", "health", "none"}

TRAIN_RATIO = 0.7
VAL_RATIO = 0.15
# remaining ~0.15 goes to test


def load_and_validate(path):
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required_cols = {"text", "label", "category"}
        if not required_cols.issubset(reader.fieldnames or []):
            raise ValueError(
                f"CSV must have columns {required_cols}, found {reader.fieldnames}"
            )

        for i, row in enumerate(reader, start=2):  # start=2 accounts for header row
            text = row["text"].strip()
            label = row["label"].strip()
            category = row["category"].strip()

            if not text:
                raise ValueError(f"Row {i}: empty text field")
            if label not in VALID_LABELS:
                raise ValueError(
                    f"Row {i}: invalid label '{label}', must be one of {VALID_LABELS}"
                )
            if category not in VALID_CATEGORIES:
                raise ValueError(
                    f"Row {i}: invalid category '{category}', must be one of {VALID_CATEGORIES}"
                )
            if label == "non-sensitive" and category != "none":
                raise ValueError(
                    f"Row {i}: non-sensitive rows must have category 'none'"
                )
            if label == "sensitive" and category == "none":
                raise ValueError(
                    f"Row {i}: sensitive rows must have a real category, not 'none'"
                )

            rows.append({"text": text, "label": label, "category": category})

    return rows


def split_rows(rows, train_ratio, val_ratio, seed):
    random.seed(seed)
    shuffled = rows[:]
    random.shuffle(shuffled)

    n = len(shuffled)
    n_train = int(n * train_ratio)
    n_val = int(n * val_ratio)

    train = shuffled[:n_train]
    val = shuffled[n_train:n_train + n_val]
    test = shuffled[n_train + n_val:]

    return train, val, test


def write_csv(rows, path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["text", "label", "category"])
        writer.writeheader()
        writer.writerows(rows)


def print_summary(name, rows):
    sensitive = sum(1 for r in rows if r["label"] == "sensitive")
    non_sensitive = len(rows) - sensitive
    print(f"{name}: {len(rows)} rows "
          f"({sensitive} sensitive, {non_sensitive} non-sensitive)")


def main():
    rows = load_and_validate(INPUT_PATH)
    print(f"Loaded {len(rows)} valid rows from {INPUT_PATH}")

    train, val, test = split_rows(rows, TRAIN_RATIO, VAL_RATIO, SEED)

    write_csv(train, os.path.join(OUTPUT_DIR, "train.csv"))
    write_csv(val, os.path.join(OUTPUT_DIR, "val.csv"))
    write_csv(test, os.path.join(OUTPUT_DIR, "test.csv"))

    print_summary("Train", train)
    print_summary("Val", val)
    print_summary("Test", test)
    print(f"\nFiles written to {OUTPUT_DIR}/train.csv, val.csv, test.csv")


if __name__ == "__main__":
    main()
