from __future__ import annotations

import json
import os
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime, timezone
from math import sqrt
from pathlib import Path


APP_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = APP_ROOT.parents[1]
MODEL_PATH = APP_ROOT / "models" / "mat_color_knn.json"
LABELER_DB_PATH = Path(os.getenv("PLACED_LABELER_DB_PATH", PROJECT_ROOT / "runtime" / "labeler" / "labeler.db"))

LEVEL_VALUES = {
    "low": 0.0,
    "низкая": 0.0,
    "низкий": 0.0,
    "низкое": 0.0,
    "medium": 0.5,
    "средняя": 0.5,
    "средний": 0.5,
    "среднее": 0.5,
    "high": 1.0,
    "высокая": 1.0,
    "высокий": 1.0,
    "высокое": 1.0,
}
LIGHTNESS_VALUES = {
    "dark": 0.0,
    "темный": 0.0,
    "тёмный": 0.0,
    "темная": 0.0,
    "тёмная": 0.0,
    "темное": 0.0,
    "тёмное": 0.0,
    "medium": 0.5,
    "средний": 0.5,
    "средняя": 0.5,
    "среднее": 0.5,
    "light": 1.0,
    "светлый": 1.0,
    "светлая": 1.0,
    "светлое": 1.0,
}
TEMPERATURE_VALUES = {
    "cold": 0.0,
    "холодный": 0.0,
    "холодная": 0.0,
    "холодное": 0.0,
    "neutral": 0.5,
    "нейтральный": 0.5,
    "нейтральная": 0.5,
    "нейтральное": 0.5,
    "warm": 1.0,
    "теплый": 1.0,
    "тёплый": 1.0,
    "теплая": 1.0,
    "тёплая": 1.0,
    "теплое": 1.0,
    "тёплое": 1.0,
}
MONOCHROME_VALUES = {
    "color": 0.0,
    "цветное": 0.0,
    "false": 0.0,
    "monochrome": 1.0,
    "монохромное": 1.0,
    "монохромная": 1.0,
    "ч/б": 1.0,
    "true": 1.0,
}
COLOR_FAMILIES = [
    "black",
    "white",
    "grey",
    "red",
    "orange",
    "yellow",
    "green",
    "cyan",
    "blue",
    "violet",
    "magenta",
]
ACCENT_SOURCES = ["pop", "temperature", "light", "area"]
TARGETS = ["outer_mat_color_id", "inner_mat_color_id"]


def train_model_from_labeler(db_path=LABELER_DB_PATH, model_path=MODEL_PATH, palette=None):
    db_path = Path(db_path)
    if not db_path.exists():
        raise FileNotFoundError(f"Labeler database not found: {db_path}")

    rows = load_training_rows(db_path)
    if not rows:
        raise ValueError("No annotations found for training")

    feature_rows = []
    for row in rows:
        image_features = json.loads(row["image_features_json"])
        label = json.loads(row["label_json"])
        features = extract_features(image_features)
        feature_rows.append(
            {
                "id": row["id"],
                "image_id": row["image_id"],
                "features": features,
                "labels": {
                    target: label.get(target)
                    for target in TARGETS
                    if label.get(target)
                },
            }
        )

    feature_names = feature_rows[0]["features"].keys()
    vectors = [[sample["features"][name] for name in feature_names] for sample in feature_rows]
    scaler = fit_scaler(vectors)
    samples = []
    for sample, vector in zip(feature_rows, vectors):
        normalized = normalize_vector(vector, scaler)
        samples.append(
            {
                "id": sample["id"],
                "image_id": sample["image_id"],
                "x": [round(value, 6) for value in normalized],
                "labels": sample["labels"],
            }
        )

    target_counts = {
        target: dict(Counter(sample["labels"].get(target) for sample in samples if sample["labels"].get(target)))
        for target in TARGETS
    }
    model = {
        "type": "placed_mat_color_knn",
        "version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "feature_names": list(feature_names),
        "scaler": scaler,
        "samples": samples,
        "targets": TARGETS,
        "target_counts": target_counts,
        "palette_ids": sorted((palette or {}).keys()),
    }

    model_path = Path(model_path)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    model_path.write_text(json.dumps(model, ensure_ascii=False, indent=2), encoding="utf-8")
    return model


def load_training_rows(db_path):
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    try:
        return connection.execute(
            """
            SELECT id, image_id, image_features_json, label_json
            FROM annotations
            ORDER BY updated_at ASC
            """
        ).fetchall()
    finally:
        connection.close()


def predict_mat_colors(image_analysis, decor_style, palette, model_path=MODEL_PATH, k=9):
    model = load_model(model_path)
    if not model:
        return unavailable_prediction("ML-модель еще не обучена.")

    features = extract_features(image_analysis)
    vector = [features.get(name, 0.0) for name in model["feature_names"]]
    normalized = normalize_vector(vector, model["scaler"])
    neighbors = nearest_neighbors(normalized, model["samples"], k=k)

    predictions = {}
    for target in TARGETS:
        if target == "inner_mat_color_id" and decor_style != "signature":
            continue
        predictions[target] = vote_color(target, neighbors, palette)

    return {
        "available": True,
        "model_version": model.get("version"),
        "trained_at": model.get("created_at"),
        "sample_count": len(model.get("samples", [])),
        "neighbors": [
            {
                "id": neighbor["sample"]["id"],
                "image_id": neighbor["sample"]["image_id"],
                "distance": round(neighbor["distance"], 4),
                "labels": neighbor["sample"].get("labels", {}),
            }
            for neighbor in neighbors[:5]
        ],
        "predictions": predictions,
    }


def load_model(model_path=MODEL_PATH):
    path = Path(model_path)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def model_metadata(model_path=MODEL_PATH):
    model = load_model(model_path)
    if not model:
        return {
            "available": False,
            "reason": "ML-модель еще не обучена.",
            "model_version": None,
            "trained_at": None,
            "sample_count": 0,
        }

    samples = model.get("samples", [])
    return {
        "available": True,
        "type": model.get("type"),
        "model_version": model.get("version"),
        "trained_at": model.get("created_at"),
        "sample_count": len(samples),
        "target_counts": model.get("target_counts", {}),
        "palette_size": len(model.get("palette_ids", [])),
    }


def unavailable_prediction(reason):
    return {
        "available": False,
        "reason": reason,
        "predictions": {},
        "neighbors": [],
        "sample_count": 0,
    }


def extract_features(image_analysis):
    palette = image_analysis.get("palette", {}) if isinstance(image_analysis, dict) else {}
    accent = palette.get("accent", {}) if isinstance(palette.get("accent"), dict) else {}
    metrics = image_analysis.get("metrics", {}) if isinstance(image_analysis.get("metrics"), dict) else {}

    features = {
        "metric_lightness": numeric(metrics.get("lightness"), 50.0) / 100,
        "metric_chroma": numeric(metrics.get("chroma"), 0.0) / 100,
        "metric_monochrome": numeric(metrics.get("monochrome_score"), level(image_analysis.get("monochrome"), MONOCHROME_VALUES)),
        "metric_contrast": numeric(metrics.get("contrast"), 0.0) / 100,
        "metric_occupancy": numeric(metrics.get("frame_occupancy"), 0.0),
        "metric_temperature": (numeric(metrics.get("temperature_score"), 0.0) + 1) / 2,
        "level_temperature": level(image_analysis.get("temperature"), TEMPERATURE_VALUES, 0.5),
        "level_lightness": level(image_analysis.get("lightness"), LIGHTNESS_VALUES, 0.5),
        "level_chroma": level(image_analysis.get("chroma_level"), LEVEL_VALUES, 0.5),
        "level_occupancy": level(image_analysis.get("frame_occupancy"), LEVEL_VALUES, 0.5),
        "level_contrast": level(image_analysis.get("contrast"), LEVEL_VALUES, 0.5),
        "level_monochrome": level(image_analysis.get("monochrome"), MONOCHROME_VALUES, 0.0),
    }

    for prefix, color in (
        ("primary", palette.get("primary")),
        ("secondary", palette.get("secondary")),
        ("accent", accent.get("selected")),
    ):
        features.update(color_features(prefix, color))

    candidates = accent.get("candidates") if isinstance(accent.get("candidates"), dict) else {}
    scores = accent.get("scores") if isinstance(accent.get("scores"), dict) else {}
    for source in ACCENT_SOURCES:
        features.update(color_features(f"candidate_{source}", candidates.get(source)))
        features[f"candidate_{source}_score"] = numeric(scores.get(source), 0.0) / 100

    return features


def color_features(prefix, color):
    lab = color.get("lab") if isinstance(color, dict) else None
    if not isinstance(lab, list) or len(lab) != 3:
        lab = [50.0, 0.0, 0.0]

    family = str((color or {}).get("family") or "").strip().lower() if isinstance(color, dict) else ""
    features = {
        f"{prefix}_l": numeric(lab[0], 50.0) / 100,
        f"{prefix}_a": (numeric(lab[1], 0.0) + 128) / 255,
        f"{prefix}_b": (numeric(lab[2], 0.0) + 128) / 255,
        f"{prefix}_share": numeric((color or {}).get("share"), 0.0) if isinstance(color, dict) else 0.0,
        f"{prefix}_chroma": numeric((color or {}).get("chroma"), 0.0) / 100 if isinstance(color, dict) else 0.0,
        f"{prefix}_exists": 1.0 if isinstance(color, dict) else 0.0,
    }
    for known_family in COLOR_FAMILIES:
        features[f"{prefix}_family_{known_family}"] = 1.0 if family == known_family else 0.0
    return features


def fit_scaler(vectors):
    columns = list(zip(*vectors))
    mean = [sum(column) / len(column) for column in columns]
    std = []
    for column, column_mean in zip(columns, mean):
        variance = sum((value - column_mean) ** 2 for value in column) / len(column)
        std.append(sqrt(variance) or 1.0)
    return {"mean": mean, "std": std}


def normalize_vector(vector, scaler):
    return [
        (float(value) - float(mean)) / float(std or 1.0)
        for value, mean, std in zip(vector, scaler["mean"], scaler["std"])
    ]


def nearest_neighbors(vector, samples, k):
    neighbors = []
    for sample in samples:
        distance = euclidean(vector, sample["x"])
        neighbors.append({"sample": sample, "distance": distance})
    neighbors.sort(key=lambda item: item["distance"])
    return neighbors[: max(1, min(k, len(neighbors)))]


def vote_color(target, neighbors, palette):
    weights = defaultdict(float)
    evidence = defaultdict(list)
    for neighbor in neighbors:
        color_id = neighbor["sample"].get("labels", {}).get(target)
        if not color_id or color_id not in palette:
            continue
        weight = 1 / (neighbor["distance"] + 0.08)
        weights[color_id] += weight
        evidence[color_id].append(round(neighbor["distance"], 4))

    if not weights:
        return {"color_id": None, "confidence": "low", "weight": 0.0, "evidence": []}

    ranked = sorted(weights.items(), key=lambda item: item[1], reverse=True)
    best_id, best_weight = ranked[0]
    total_weight = sum(weights.values())
    share = best_weight / total_weight if total_weight else 0.0
    confidence = "high" if share >= 0.62 and len(evidence[best_id]) >= 3 else "medium" if share >= 0.42 else "low"
    return {
        "color_id": best_id,
        "color": palette_color_summary(palette.get(best_id)),
        "confidence": confidence,
        "weight": round(best_weight, 4),
        "vote_share": round(share, 3),
        "evidence": evidence[best_id][:5],
        "top": [
            {
                "color_id": color_id,
                "color": palette_color_summary(palette.get(color_id)),
                "vote_share": round(weight / total_weight, 3),
            }
            for color_id, weight in ranked[:5]
        ],
    }


def palette_color_summary(color):
    if not isinstance(color, dict):
        return None
    return {
        "id": color.get("id"),
        "name": color.get("name"),
        "hex": color.get("hex"),
    }


def euclidean(first, second):
    return sqrt(sum((a - b) ** 2 for a, b in zip(first, second)))


def numeric(value, fallback=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(fallback)


def level(value, mapping, fallback=0.5):
    return mapping.get(str(value or "").strip().lower(), fallback)
