from __future__ import annotations

import argparse

from .algorithm import PLACED_PALETTE
from .mat_ml import LABELER_DB_PATH, MODEL_PATH, train_model_from_labeler


def main():
    parser = argparse.ArgumentParser(description="Train placed mat color model from labeler annotations.")
    parser.add_argument("--db", default=str(LABELER_DB_PATH), help="Path to labeler SQLite database.")
    parser.add_argument("--out", default=str(MODEL_PATH), help="Path to output model JSON.")
    args = parser.parse_args()

    model = train_model_from_labeler(args.db, args.out, palette=PLACED_PALETTE)
    print(f"trained_samples={len(model['samples'])}")
    print(f"model={args.out}")
    for target, counts in model["target_counts"].items():
        print(f"{target}={len(counts)} classes")


if __name__ == "__main__":
    main()
