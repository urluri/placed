from __future__ import annotations

from dataclasses import dataclass
from math import sqrt

import numpy as np
from PIL import Image, ImageOps


@dataclass
class ColorCluster:
    rgb: tuple[int, int, int]
    lab: tuple[float, float, float]
    share: float
    chroma: float


def analyze_image(image_path: str):
    rgb = load_rgb(image_path)
    lab = rgb_to_lab(rgb)
    clusters = extract_color_clusters(rgb, lab)

    lightness_value = float(np.percentile(lab[:, :, 0], 50))
    chroma_values = np.sqrt(lab[:, :, 1] ** 2 + lab[:, :, 2] ** 2)
    chroma_value = weighted_mean_chroma(chroma_values)
    contrast_value = image_contrast(lab[:, :, 0])
    occupancy_value = frame_occupancy(lab)
    temperature_score = image_temperature(clusters)

    primary = choose_primary(clusters)
    secondary = choose_secondary(clusters, primary)
    accent = choose_accent(clusters, primary, secondary, temperature_score)

    return {
        "palette": {
            "primary": serialize_color(primary),
            "secondary": serialize_color(secondary),
            "accent": serialize_color(accent),
        },
        "temperature": classify_temperature(temperature_score),
        "lightness": classify_lightness(lightness_value),
        "chroma_level": classify_chroma(chroma_value),
        "frame_occupancy": classify_level(occupancy_value, low=0.22, high=0.45),
        "contrast": classify_contrast(contrast_value),
        "metrics": {
            "lightness": round(lightness_value, 2),
            "chroma": round(chroma_value, 2),
            "contrast": round(contrast_value, 2),
            "frame_occupancy": round(occupancy_value, 3),
            "temperature_score": round(temperature_score, 2),
        },
    }


def load_rgb(image_path: str):
    image = ImageOps.exif_transpose(Image.open(image_path))
    if image.mode == "RGBA":
        background = Image.new("RGBA", image.size, (255, 255, 255, 255))
        image = Image.alpha_composite(background, image)
    image = image.convert("RGB")
    image.thumbnail((360, 360), Image.Resampling.LANCZOS)
    return np.asarray(image, dtype=np.float32)


def extract_color_clusters(rgb, lab, k=10):
    flat_rgb = rgb.reshape(-1, 3)
    flat_lab = lab.reshape(-1, 3)

    if len(flat_lab) == 0:
        return []

    sample_size = min(18000, len(flat_lab))
    rng = np.random.default_rng(19)
    sample_idx = rng.choice(len(flat_lab), sample_size, replace=False)
    sample_lab = flat_lab[sample_idx]

    centers = initialize_centers(sample_lab, min(k, len(sample_lab)))
    for _ in range(18):
        distances = ((sample_lab[:, None, :] - centers[None, :, :]) ** 2).sum(axis=2)
        labels = distances.argmin(axis=1)
        next_centers = centers.copy()
        for idx in range(len(centers)):
            points = sample_lab[labels == idx]
            if len(points):
                next_centers[idx] = points.mean(axis=0)
        if np.allclose(centers, next_centers, atol=0.08):
            break
        centers = next_centers

    all_distances = ((flat_lab[:, None, :] - centers[None, :, :]) ** 2).sum(axis=2)
    all_labels = all_distances.argmin(axis=1)
    clusters: list[ColorCluster] = []
    total = len(flat_lab)
    for idx in range(len(centers)):
        mask = all_labels == idx
        count = int(mask.sum())
        if count == 0:
            continue
        mean_lab = flat_lab[mask].mean(axis=0)
        mean_rgb = flat_rgb[mask].mean(axis=0)
        chroma = float(sqrt(mean_lab[1] ** 2 + mean_lab[2] ** 2))
        clusters.append(
            ColorCluster(
                rgb=tuple(int(round(channel)) for channel in mean_rgb),
                lab=(float(mean_lab[0]), float(mean_lab[1]), float(mean_lab[2])),
                share=count / total,
                chroma=chroma,
            )
        )

    return sorted(clusters, key=lambda cluster: cluster.share, reverse=True)


def initialize_centers(sample_lab, k):
    lightness = sample_lab[:, 0]
    chroma = np.sqrt(sample_lab[:, 1] ** 2 + sample_lab[:, 2] ** 2)
    seed_scores = [
        lightness,
        -lightness,
        chroma,
        -chroma,
        sample_lab[:, 1],
        -sample_lab[:, 1],
        sample_lab[:, 2],
        -sample_lab[:, 2],
    ]

    indices = []
    for score in seed_scores:
        idx = int(np.argmax(score))
        if idx not in indices:
            indices.append(idx)
        if len(indices) == k:
            break

    if len(indices) < k:
        step = max(1, len(sample_lab) // k)
        for idx in range(0, len(sample_lab), step):
            if idx not in indices:
                indices.append(idx)
            if len(indices) == k:
                break

    return sample_lab[indices[:k]].copy()


def choose_primary(clusters):
    if not clusters:
        return None
    return max(clusters, key=lambda cluster: cluster.share * (0.72 + min(cluster.chroma, 70) / 250))


def choose_secondary(clusters, primary):
    if not primary:
        return None
    candidates = [
        cluster
        for cluster in clusters
        if cluster is not primary and cluster.share >= 0.035 and delta_e(cluster, primary) >= 14
    ]
    if not candidates:
        candidates = [cluster for cluster in clusters if cluster is not primary]
    if not candidates:
        return None
    return max(candidates, key=lambda cluster: cluster.share * (0.5 + min(cluster.chroma, 70) / 140))


def choose_accent(clusters, primary, secondary, scene_temperature):
    anchors = [cluster for cluster in (primary, secondary) if cluster]
    candidates = [cluster for cluster in clusters if cluster not in anchors and cluster.share >= 0.006]
    if not candidates:
        return None

    def score(cluster):
        distance = min(delta_e(cluster, anchor) for anchor in anchors) if anchors else 25
        lightness = cluster.lab[0]
        temp_score = color_temperature_score(cluster)
        anchor_lightness = np.mean([anchor.lab[0] for anchor in anchors]) if anchors else lightness
        lightness_pop = 1 + max(0, lightness - anchor_lightness) / 45
        share_weight = np.sqrt(min(cluster.share / 0.035, 2.2))
        chroma_weight = 0.45 + min(cluster.chroma / 34, 1.8)
        distance_weight = 0.55 + min(distance / 38, 1.7)
        temperature_weight = 1.0
        if scene_temperature <= -5 and temp_score >= 10:
            temperature_weight += 1.15
        elif scene_temperature >= 7 and temp_score <= -8:
            temperature_weight += 0.85
        elif abs(temp_score - scene_temperature) >= 24:
            temperature_weight += 0.35
        highlight_weight = 1.25 if lightness >= 58 and cluster.chroma >= 16 else 1.0
        dark_penalty = 0.45 if lightness < 20 and cluster.chroma < 16 else 1.0
        return share_weight * chroma_weight * distance_weight * lightness_pop * temperature_weight * highlight_weight * dark_penalty

    accent = max(candidates, key=score)
    return accent if score(accent) >= 0.35 else None


def image_temperature(clusters):
    meaningful = [cluster for cluster in clusters if cluster.share >= 0.02]
    if not meaningful:
        return 0.0
    numerator = 0.0
    denominator = 0.0
    for cluster in meaningful:
        l_value, a_value, b_value = cluster.lab
        chroma_weight = min(cluster.chroma / 35, 1.6)
        neutral_penalty = 0.35 if cluster.chroma < 8 and l_value > 78 else 1.0
        weight = cluster.share * (0.4 + chroma_weight) * neutral_penalty
        numerator += (b_value + a_value * 0.22) * weight
        denominator += weight
    return numerator / denominator if denominator else 0.0


def color_temperature_score(cluster):
    return cluster.lab[2] + cluster.lab[1] * 0.22


def weighted_mean_chroma(chroma_values):
    flattened = chroma_values.reshape(-1)
    weights = np.clip(flattened / 35, 0.35, 1.8)
    return float(np.average(flattened, weights=weights))


def image_contrast(lightness):
    p5, p95 = np.percentile(lightness, [5, 95])
    p20, p80 = np.percentile(lightness, [20, 80])
    return float((p95 - p5) * 0.65 + (p80 - p20) * 0.35)


def frame_occupancy(lab):
    height, width, _ = lab.shape
    band = max(4, int(min(width, height) * 0.08))
    border_mask = np.zeros((height, width), dtype=bool)
    border_mask[:band, :] = True
    border_mask[-band:, :] = True
    border_mask[:, :band] = True
    border_mask[:, -band:] = True

    lightness = lab[:, :, 0]
    chroma = np.sqrt(lab[:, :, 1] ** 2 + lab[:, :, 2] ** 2)
    grad_y = np.abs(np.diff(lightness, axis=0, prepend=lightness[:1, :]))
    grad_x = np.abs(np.diff(lightness, axis=1, prepend=lightness[:, :1]))
    edge_activity = grad_x + grad_y

    occupied = (chroma > 12) | (lightness < 86) | (edge_activity > 7)
    return float(occupied[border_mask].mean())


def serialize_color(cluster):
    if not cluster:
        return None
    rgb = tuple(max(0, min(255, value)) for value in cluster.rgb)
    lab = cluster.lab
    return {
        "hex": rgb_to_hex(rgb),
        "rgb": list(rgb),
        "lab": [round(value, 2) for value in lab],
        "family": color_family(rgb, cluster.chroma, lab[0]),
        "temperature": classify_temperature(cluster.lab[2] + cluster.lab[1] * 0.22),
        "lightness": classify_lightness(lab[0]),
        "chroma_level": classify_chroma(cluster.chroma),
        "chroma": round(cluster.chroma, 2),
        "share": round(cluster.share, 3),
    }


def rgb_to_hex(rgb):
    return "#" + "".join(f"{channel:02X}" for channel in rgb)


def color_family(rgb, chroma, lightness):
    red, green, blue = [channel / 255 for channel in rgb]
    max_channel = max(red, green, blue)
    min_channel = min(red, green, blue)
    delta = max_channel - min_channel
    if lightness < 18:
        return "black"
    if lightness > 88 and chroma < 10:
        return "white"
    if chroma < 9 or delta < 0.05:
        return "grey"

    if max_channel == red:
        hue = (60 * ((green - blue) / delta) + 360) % 360
    elif max_channel == green:
        hue = 60 * ((blue - red) / delta + 2)
    else:
        hue = 60 * ((red - green) / delta + 4)

    if hue < 18 or hue >= 345:
        return "red"
    if hue < 45:
        return "orange"
    if hue < 72:
        return "yellow"
    if hue < 155:
        return "green"
    if hue < 195:
        return "cyan"
    if hue < 255:
        return "blue"
    if hue < 292:
        return "violet"
    if hue < 345:
        return "magenta"
    return "grey"


def classify_temperature(score):
    if score >= 7:
        return "теплый"
    if score <= -5:
        return "холодный"
    return "нейтральный"


def classify_lightness(value):
    if value >= 68:
        return "светлый"
    if value <= 42:
        return "темный"
    return "средний"


def classify_chroma(value):
    if value >= 34:
        return "высокая"
    if value <= 16:
        return "низкая"
    return "средняя"


def classify_contrast(value):
    if value >= 58:
        return "высокий"
    if value <= 30:
        return "низкий"
    return "средний"


def classify_level(value, low, high):
    if value >= high:
        return "высокая"
    if value <= low:
        return "низкая"
    return "средняя"


def delta_e(first: ColorCluster, second: ColorCluster):
    return sqrt(sum((a - b) ** 2 for a, b in zip(first.lab, second.lab)))


def rgb_to_lab(rgb):
    srgb = rgb / 255.0
    linear = np.where(srgb <= 0.04045, srgb / 12.92, ((srgb + 0.055) / 1.055) ** 2.4)
    matrix = np.array(
        [
            [0.4124564, 0.3575761, 0.1804375],
            [0.2126729, 0.7151522, 0.0721750],
            [0.0193339, 0.1191920, 0.9503041],
        ],
        dtype=np.float32,
    )
    xyz = linear @ matrix.T
    xyz = xyz / np.array([0.95047, 1.00000, 1.08883], dtype=np.float32)
    epsilon = 216 / 24389
    kappa = 24389 / 27
    f_xyz = np.where(xyz > epsilon, np.cbrt(xyz), (kappa * xyz + 16) / 116)
    l_value = 116 * f_xyz[:, :, 1] - 16
    a_value = 500 * (f_xyz[:, :, 0] - f_xyz[:, :, 1])
    b_value = 200 * (f_xyz[:, :, 1] - f_xyz[:, :, 2])
    return np.stack([l_value, a_value, b_value], axis=2).astype(np.float32)
