import copy
import json
from pathlib import Path


CONFIG_PATH = Path(__file__).with_name("effects.json")

DEFAULT_EFFECTS = {
    "frame": {
        "triangular_slope": {
            "enabled": True,
            "angle_degrees": 30,
        },
        "cast_shadow": {
            "enabled": False,
            "opacity": 42,
            "blur_px": 10,
        },
    },
    "mat": {
        "window_bevel": {
            "enabled": True,
            "width_mm": 1.5,
            "highlight_opacity": 210,
            "edge_opacity": 52,
            "shadow_opacity": 0,
        },
        "inner_reveal_depth_shadow": {
            "enabled": False,
            "strength": 0.18,
        },
        "image_window_depth_shadow": {
            "enabled": False,
            "strength": 0.18,
        },
    },
    "glass": {
        "enabled": False,
        "opacity": 12,
    },
    "postprocess": {
        "global_lighting": {
            "enabled": False,
            "strength": 0.04,
        },
        "vignette": {
            "enabled": False,
            "strength": 0.08,
        },
        "film_grain": {
            "enabled": False,
            "sigma": 1.2,
        },
        "color_grade": {
            "enabled": False,
        },
        "chromatic_aberration": {
            "enabled": False,
            "offset_px": 1,
        },
    },
}


def load_effects_config(path=None, overrides=None):
    config = copy.deepcopy(DEFAULT_EFFECTS)
    config_path = Path(path) if path else CONFIG_PATH

    if config_path.exists():
        with config_path.open("r", encoding="utf-8") as file:
            merge_dict(config, json.load(file))

    if overrides:
        merge_dict(config, overrides)

    return config


def merge_dict(base, patch):
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            merge_dict(base[key], value)
        else:
            base[key] = value
    return base


def enabled(config, *path):
    node = get(config, *path)
    return isinstance(node, dict) and bool(node.get("enabled"))


def get(config, *path, default=None):
    node = config
    for key in path:
        if not isinstance(node, dict) or key not in node:
            return default
        node = node[key]
    return node
