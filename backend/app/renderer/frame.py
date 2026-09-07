from functools import lru_cache
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from .utils import adjust_color

FRAME_BASE = (112, 98, 82)
WOOD_TEXTURE_FILES = {
    "white_wood": "white_wood.jpg",
    "light_oak": "oak_light.jpg",
    "oak": "oak.jpg",
    "walnut": "wenge.jpg",
    "dark_walnut": "wenge_dark.jpg",
}
REPO_ROOT = Path(__file__).resolve().parents[3]
TEXTURE_ROOT = REPO_ROOT / "textures"


def stable_seed(width, height, base, salt=0):
    return (
        int(width) * 73856093
        ^ int(height) * 19349663
        ^ int(base[0]) * 83492791
        ^ int(base[1]) * 2654435761
        ^ int(base[2]) * 97531
        ^ int(salt)
    ) & 0xFFFFFFFF


def wood_material_params(base):
    r_value, g_value, b_value = base
    lightness = (max(base) + min(base)) / 2
    warmth = r_value - b_value

    if lightness > 220:
        return {"kind": "painted_light", "contrast": 1.6, "pore": 0.4, "ring": 0.0, "ray": 0.0, "grain": 1.2}
    if lightness < 45:
        return {"kind": "painted_dark", "contrast": 3.0, "pore": 1.3, "ring": 2.0, "ray": 0.5, "grain": 2.3}
    if warmth > 70 and lightness > 155:
        return {"kind": "light_oak", "contrast": 12.0, "pore": 5.4, "ring": 8.8, "ray": 5.2, "grain": 9.5}
    if warmth > 55 and lightness > 95:
        return {"kind": "oak", "contrast": 13.5, "pore": 5.8, "ring": 9.6, "ray": 4.2, "grain": 10.5}
    if warmth > 35 and lightness > 55:
        return {"kind": "walnut", "contrast": 14.2, "pore": 4.6, "ring": 10.6, "ray": 1.1, "grain": 11.4}
    return {"kind": "dark_walnut", "contrast": 12.2, "pore": 4.0, "ring": 9.2, "ray": 0.7, "grain": 9.6}


def blurred_noise(width, height, rng, blur_radius, scale=1.0):
    raw = rng.normal(127, 46, (height, width)).astype(np.uint8)
    img = Image.fromarray(raw, "L").filter(ImageFilter.GaussianBlur(blur_radius))
    arr = np.asarray(img).astype(np.float32) - 127
    return arr * scale / 48


@lru_cache(maxsize=8)
def load_wood_texture_asset(texture_name):
    path = TEXTURE_ROOT / texture_name
    if not path.exists():
        return None
    image = Image.open(path).convert("RGB")
    max_side = max(image.size)
    if max_side > 2400:
        scale = 2400 / max_side
        image = image.resize(
            (max(1, int(image.width * scale)), max(1, int(image.height * scale))),
            Image.Resampling.LANCZOS,
        )
    return image


def texture_key_for_frame(frame_id, base):
    if frame_id in WOOD_TEXTURE_FILES:
        return frame_id
    return None


def crop_resized_texture(source, width, height, rng, rotate=False):
    if rotate:
        source = source.transpose(Image.Transpose.ROTATE_90)

    src_w, src_h = source.size
    crop_w = min(src_w, max(width * 4, 900))
    crop_h = min(src_h, max(height * 10, 420))
    max_x = max(0, src_w - crop_w)
    max_y = max(0, src_h - crop_h)
    left = int(rng.integers(0, max_x + 1)) if max_x else 0
    top = int(rng.integers(0, max_y + 1)) if max_y else 0
    crop = source.crop((left, top, left + crop_w, top + crop_h))
    return crop.resize((max(1, width), max(1, height)), Image.Resampling.LANCZOS)


def tint_texture_to_frame(texture, base, texture_key=None):
    arr = np.asarray(texture).astype(np.float32)
    mean = arr.reshape(-1, 3).mean(axis=0)
    detail = arr - mean
    if texture_key == "white_wood":
        detail *= 2.85
        target = np.array(base, dtype=np.float32) + detail
        blended = arr * 0.18 + target * 0.82

        # White painted wood sits close to clipping after relief and global lighting.
        # Compress only the brightest paint so grain and profile remain visible.
        luminance = blended.mean(axis=2, keepdims=True)
        highlight = np.clip((luminance - 231) / 24, 0, 1)
        blended -= highlight * (luminance - 231) * 0.88
        blended = np.minimum(blended, 238)
    else:
        target = np.array(base, dtype=np.float32) + detail * 0.92
        blended = arr * 0.68 + target * 0.32
    return Image.fromarray(np.clip(blended, 0, 255).astype(np.uint8))


def real_wood_texture(width, height, base, frame_px, frame_id):
    texture_key = texture_key_for_frame(frame_id, base)
    texture_name = WOOD_TEXTURE_FILES.get(texture_key)
    source = load_wood_texture_asset(texture_name) if texture_name else None
    if source is None:
        return None

    rng = np.random.default_rng(stable_seed(width, height, base, frame_px + 271))
    rail = max(1, frame_px)
    result = Image.new("RGB", (width, height), base)

    top = crop_resized_texture(source, width, rail, rng, rotate=True)
    bottom = crop_resized_texture(source, width, rail, rng, rotate=True)
    left = crop_resized_texture(source, rail, height, rng, rotate=False)
    right = crop_resized_texture(source, rail, height, rng, rotate=False)

    top_layer = Image.new("RGB", (width, height), base)
    bottom_layer = Image.new("RGB", (width, height), base)
    left_layer = Image.new("RGB", (width, height), base)
    right_layer = Image.new("RGB", (width, height), base)
    top_layer.paste(tint_texture_to_frame(top, base, texture_key), (0, 0))
    bottom_layer.paste(tint_texture_to_frame(bottom, base, texture_key), (0, max(0, height - rail)))
    left_layer.paste(tint_texture_to_frame(left, base, texture_key), (0, 0))
    right_layer.paste(tint_texture_to_frame(right, base, texture_key), (max(0, width - rail), 0))

    masks = wood_rail_masks(width, height, rail)
    for layer, mask in (
        (top_layer, masks["top"]),
        (bottom_layer, masks["bottom"]),
        (left_layer, masks["left"]),
        (right_layer, masks["right"]),
    ):
        result.paste(layer, (0, 0), mask)

    return result.filter(ImageFilter.UnsharpMask(radius=0.9, percent=85, threshold=2))


def wood_rail_masks(width, height, rail):
    rail = max(1, min(rail, width // 2, height // 2))
    masks = {}
    specs = {
        "top": [(0, 0), (width, 0), (width - rail, rail), (rail, rail)],
        "bottom": [(0, height), (rail, height - rail), (width - rail, height - rail), (width, height)],
        "left": [(0, 0), (rail, rail), (rail, height - rail), (0, height)],
        "right": [(width, 0), (width, height), (width - rail, height - rail), (width - rail, rail)],
    }
    for name, polygon in specs.items():
        mask = Image.new("L", (width, height), 0)
        ImageDraw.Draw(mask).polygon(polygon, fill=255)
        masks[name] = mask
    return masks


def draw_wood_outer_contour(canvas, outer_rect, base, frame_px):
    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    left, top, right, bottom = outer_rect
    layers = max(1, min(3, frame_px // 18))
    shadow = (*adjust_color(base, 0.62), 46)
    highlight = (*bevel_color(base, 1.10), 24)
    for i in range(layers):
        alpha_factor = 1 - i / max(1, layers)
        draw.line([(left + i, bottom - i), (right - i, bottom - i)], fill=(*shadow[:3], int(shadow[3] * alpha_factor)))
        draw.line([(right - i, top + i), (right - i, bottom - i)], fill=(*shadow[:3], int(shadow[3] * alpha_factor)))
        draw.line([(left + i, top + i), (right - i, top + i)], fill=(*highlight[:3], int(highlight[3] * alpha_factor)))
        draw.line([(left + i, top + i), (left + i, bottom - i)], fill=(*highlight[:3], int(highlight[3] * alpha_factor)))
    return Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB")


def rail_coordinates(width, height, frame_px):
    y, x = np.mgrid[0:height, 0:width]
    dist_outer = np.minimum.reduce([x, y, width - 1 - x, height - 1 - y])
    inner_left = frame_px
    inner_top = frame_px
    inner_right = max(frame_px + 1, width - frame_px)
    inner_bottom = max(frame_px + 1, height - frame_px)
    dist_inner = np.minimum.reduce(
        [
            np.abs(x - inner_left),
            np.abs(x - (inner_right - 1)),
            np.abs(y - inner_top),
            np.abs(y - (inner_bottom - 1)),
        ]
    )
    top_or_bottom = np.minimum(y, height - 1 - y) <= np.minimum(x, width - 1 - x)
    u = np.where(top_or_bottom, x, y).astype(np.float32)
    v = np.where(top_or_bottom, y, x).astype(np.float32)
    return x.astype(np.float32), y.astype(np.float32), u, v, dist_outer.astype(np.float32), dist_inner.astype(np.float32)


def wood_texture(width, height, base=FRAME_BASE, frame_px=1, profile="natural_wood", frame_id=None):
    real_texture = real_wood_texture(width, height, base, frame_px, frame_id)
    if real_texture is not None:
        return real_texture

    rng = np.random.default_rng(stable_seed(width, height, base, frame_px))
    params = wood_material_params(base)
    x, y, u, v, dist_outer, dist_inner = rail_coordinates(width, height, frame_px)
    if params["kind"] == "painted_light":
        return painted_light_wood_texture(width, height, base, frame_px, rng, u, v, dist_outer, dist_inner)

    rail_width = max(8, frame_px)
    u_warp = (
        np.sin(u / (44 + rail_width * 0.22) + np.sin(v / 37) * 0.5) * (7.5 + rail_width * 0.04)
        + blurred_noise(width, height, rng, max(5, rail_width // 7), 7.5)
        + blurred_noise(width, height, rng, max(12, rail_width // 3), 13.0)
    )
    v_warp = (
        np.sin(u / 115 + v / 21) * 2.2
        + blurred_noise(width, height, rng, max(2, rail_width // 14), 1.8)
    )
    grain_u = u + u_warp
    grain_v = v + v_warp

    annual = np.sin(grain_u / (16 + rail_width * 0.07) + np.sin(grain_u / 82) * 1.1)
    secondary = np.sin(grain_u / (6.8 + rail_width * 0.016) + grain_v / 24) * 0.58
    broad = np.sin(grain_u / (68 + rail_width * 0.16) + np.sin(grain_v / 29) * 0.9) * 0.72
    fine = rng.normal(0, 0.62, (height, width))

    long_grain = np.zeros((height, width), dtype=np.float32)
    for period in (21, 34, 55, 89):
        phase = rng.uniform(0, np.pi * 2)
        drift = np.sin(grain_v / (period * 1.35) + phase) * rng.uniform(0.55, 1.35)
        long_grain += np.sin(grain_u / period + drift + phase) * rng.uniform(0.55, 1.15)
    long_grain /= 4
    long_grain = np.sign(long_grain) * np.abs(long_grain) ** 1.28

    dark_grain = np.clip(np.sin(grain_u / 3.25 + np.sin(grain_v / 11) * 1.25) - 0.72, 0, 1)
    dark_grain += np.clip(np.sin(grain_u / 6.6 + np.sin(grain_v / 17) * 1.1) - 0.84, 0, 1) * 1.35
    dark_grain *= np.clip(blurred_noise(width, height, rng, 0.9, 1.8) + 0.8, 0, 1.25)

    crisp_lines = np.zeros((height, width), dtype=np.float32)
    max_axis = max(width, height)
    line_count = max(10, min(46, int(max_axis / 17)))
    for _ in range(line_count):
        center = rng.uniform(-max_axis * 0.12, max_axis * 1.12)
        line_width = rng.uniform(1.0, 3.4)
        wobble = np.sin(grain_v / rng.uniform(18, 58) + rng.uniform(0, np.pi * 2)) * rng.uniform(2.0, 8.0)
        line = np.exp(-((grain_u + wobble - center) ** 2) / (2 * line_width * line_width))
        crisp_lines += line * rng.uniform(0.45, 1.0)
    crisp_lines = np.clip(crisp_lines, 0, 1.35)

    pores = np.sin(grain_u / 4.7 + np.sin(grain_v / 9) * 0.9)
    pore_mask = np.clip((pores - 0.72) * 3.3, 0, 1)
    pore_breakup = np.clip(blurred_noise(width, height, rng, 1.4, 1.5) + 0.55, 0, 1)
    pore_value = -pore_mask * pore_breakup * params["pore"]

    ray_value = 0
    if params["ray"] > 0.55:
        ray_lines = np.clip(np.sin((grain_u + grain_v * 0.36) / 13.5) - 0.86, 0, 1) * 6
        ray_value = ray_lines * params["ray"] * (0.35 + np.clip(np.sin(grain_u / 140) * 0.5 + 0.5, 0, 1))

    edge_age = np.clip(1 - np.minimum(dist_outer, dist_inner) / max(1, rail_width * 0.28), 0, 1)
    profile_shadow = np.sin(np.clip(dist_outer / max(1, rail_width), 0, 1) * np.pi) * 0.8

    if profile == "classic":
        cove = np.sin(np.clip(dist_outer / max(1, rail_width * 0.72), 0, 1) * np.pi * 2.0) * 0.65
    else:
        cove = np.sin(np.clip((dist_outer + dist_inner) / max(1, rail_width * 1.8), 0, 1) * np.pi) * 0.35

    value = (
        annual * params["ring"]
        + secondary * params["contrast"]
        + broad * params["contrast"] * 0.55
        + long_grain * params["grain"]
        + fine
        + pore_value
        - dark_grain * params["pore"] * 1.9
        - crisp_lines * params["grain"] * 0.85
        + ray_value
        + profile_shadow * 0.9
        + cove
        - edge_age * 1.15
    )

    arr = np.zeros((height, width, 3), dtype=np.float32)
    arr[:] = base
    if params["kind"] in {"painted_light", "painted_dark"}:
        arr[:, :, 0] += value * 0.58
        arr[:, :, 1] += value * 0.56
        arr[:, :, 2] += value * 0.52
    elif params["kind"] in {"light_oak", "oak"}:
        arr[:, :, 0] += value * 1.12
        arr[:, :, 1] += value * 0.78
        arr[:, :, 2] += value * 0.42
    else:
        arr[:, :, 0] += value * 1.02
        arr[:, :, 1] += value * 0.62
        arr[:, :, 2] += value * 0.34

    if params["kind"] in {"light_oak", "oak"}:
        arr[:, :, 0] += long_grain * params["grain"] * 0.28
        arr[:, :, 1] += long_grain * params["grain"] * 0.12
        arr[:, :, 2] -= crisp_lines * params["grain"] * 0.18
    elif params["kind"] in {"walnut", "dark_walnut"}:
        arr[:, :, 0] += long_grain * params["grain"] * 0.18
        arr[:, :, 1] -= crisp_lines * params["grain"] * 0.24
        arr[:, :, 2] -= crisp_lines * params["grain"] * 0.16

    corner_softening = np.clip(((x / max(1, width - 1)) * (y / max(1, height - 1))), 0, 1)
    corner_softening *= np.clip(((1 - x / max(1, width - 1)) * (1 - y / max(1, height - 1))), 0, 1)
    arr += corner_softening[:, :, None] * 3.0

    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    return img.filter(ImageFilter.UnsharpMask(radius=1.2, percent=135, threshold=1))


def painted_light_wood_texture(width, height, base, frame_px, rng, u, v, dist_outer, dist_inner):
    cloud = blurred_noise(width, height, rng, max(8, frame_px // 3), 1.15)
    soft_cloud = blurred_noise(width, height, rng, max(18, frame_px), 0.9)
    fine = rng.normal(0, 0.22, (height, width))
    quiet_grain = np.sin((u + np.sin(v / 47) * 3.5) / 72) * 0.36
    edge_tone = np.clip(1 - np.minimum(dist_outer, dist_inner) / max(1, frame_px * 0.35), 0, 1) * -0.42
    value = cloud + soft_cloud + fine + quiet_grain + edge_tone

    arr = np.zeros((height, width, 3), dtype=np.float32)
    arr[:] = base
    arr[:, :, 0] += value * 0.86
    arr[:, :, 1] += value * 0.90
    arr[:, :, 2] += value * 0.94
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.12))


def aluminum_texture(width, height, base):
    y, x = np.mgrid[0:height, 0:width]
    brushed = np.sin((x + y * 0.04) / 18) * 0.65
    fine = np.random.normal(0, 0.45, (height, width))
    highlight = np.sin((x - y * 0.12) / 150) * 1.5
    noise = brushed + fine + highlight

    arr = np.zeros((height, width, 3), dtype=np.float32)
    arr[:] = base
    arr[:, :, 0] += noise
    arr[:, :, 1] += noise
    arr[:, :, 2] += noise
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def profile_curve(position, material, profile):
    def bump(center, width, amplitude):
        return amplitude * np.exp(-((position - center) ** 2) / max(0.001, 2 * width * width))

    if material == "aluminum":
        return bump(0.52, 0.28, 0.16) - bump(0.94, 0.045, 0.08)
    if profile == "classic":
        return (
            bump(0.20, 0.08, 0.14)
            - bump(0.34, 0.045, 0.09)
            + bump(0.52, 0.13, 0.22)
            - bump(0.76, 0.055, 0.10)
            + bump(0.88, 0.06, 0.09)
        )
    return (
        bump(0.24, 0.10, 0.12)
        - bump(0.42, 0.055, 0.06)
        + bump(0.62, 0.16, 0.18)
        - bump(0.88, 0.045, 0.08)
    )


def apply_frame_relief(texture, frame_px, material, profile="flat"):
    arr = np.asarray(texture).astype(np.float32)
    height, width = arr.shape[:2]
    y, x = np.mgrid[0:height, 0:width]
    inner_left = frame_px
    inner_top = frame_px
    inner_right = max(frame_px + 1, width - frame_px)
    inner_bottom = max(frame_px + 1, height - frame_px)

    ring = (x < inner_left) | (x >= inner_right) | (y < inner_top) | (y >= inner_bottom)
    dist_outer = np.minimum.reduce([x, y, width - 1 - x, height - 1 - y]).astype(np.float32)
    dist_inner = np.minimum.reduce(
        [
            np.abs(x - inner_left),
            np.abs(x - (inner_right - 1)),
            np.abs(y - inner_top),
            np.abs(y - (inner_bottom - 1)),
        ]
    ).astype(np.float32)
    rail_position = np.clip(dist_outer / np.maximum(1, dist_outer + dist_inner), 0, 1)
    moulding = profile_curve(rail_position, material, profile)
    soft_rounding = np.sin(np.clip(np.minimum(dist_outer, dist_inner) / max(1, frame_px * 0.45), 0, 1) * np.pi)

    diagonal_light = ((1 - x / max(1, width)) * 0.62 + (1 - y / max(1, height)) * 0.38)
    inner_lip = np.clip(1 - dist_inner / max(1, frame_px * 0.16), 0, 1)
    outer_lip = np.clip(1 - dist_outer / max(1, frame_px * 0.18), 0, 1)

    if material == "aluminum":
        relief = 0.96 + moulding * 0.72 + soft_rounding * 0.07 + diagonal_light * 0.07 - inner_lip * 0.12 - outer_lip * 0.03
    else:
        wood_profile = np.maximum(moulding, 0)
        wood_inner_edge = np.clip(1 - dist_inner / max(1, frame_px * 0.08), 0, 1)
        wood_outer_edge = np.clip(1 - dist_outer / max(1, frame_px * 0.08), 0, 1)
        relief = (
            1.0
            + wood_profile * 0.12
            + soft_rounding * 0.026
            - wood_inner_edge * 0.025
            - wood_outer_edge * 0.012
        )

    arr[ring] *= relief[ring, None]
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def bevel_color(color, factor):
    if factor <= 1:
        return adjust_color(color, factor)

    amount = min(1.0, (factor - 1) * 0.72)
    return tuple(int(channel + (255 - channel) * amount) for channel in color)


def apply_triangular_frame_slope(texture, frame_px, material, frame_id=None, angle_degrees=30):
    """Apply one clean bevel: outer frame edge is higher than the inner edge."""
    if frame_px <= 1:
        return texture

    arr = np.asarray(texture).astype(np.float32)
    height, width = arr.shape[:2]
    rail = max(1, min(frame_px, width // 2, height // 2))
    if rail <= 1:
        return texture

    slope = math.tan(math.radians(angle_degrees))
    strength = min(0.36, max(0.12, slope * 0.62))
    if frame_id == "white_wood":
        outer_lift = strength * 0.26
        inner_drop = strength * 0.78
    elif material == "aluminum":
        outer_lift = strength * 0.42
        inner_drop = strength * 0.82
    else:
        outer_lift = strength * 0.42
        inner_drop = strength * 0.92

    y, x = np.mgrid[0:height, 0:width]
    masks = {name: np.asarray(mask) > 0 for name, mask in wood_rail_masks(width, height, rail).items()}
    positions = {
        "top": np.clip(y / rail, 0, 1),
        "bottom": np.clip((height - 1 - y) / rail, 0, 1),
        "left": np.clip(x / rail, 0, 1),
        "right": np.clip((width - 1 - x) / rail, 0, 1),
    }

    relief = np.ones((height, width), dtype=np.float32)
    for name, mask in masks.items():
        t = positions[name].astype(np.float32)
        t = t * t * (3 - 2 * t)
        relief[mask] = 1 + outer_lift * (1 - t[mask]) - inner_drop * t[mask]

    arr *= relief[:, :, None]
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def draw_frame(canvas, outer_rect, frame_px, base=FRAME_BASE, material="wood", profile="flat", frame_id=None, effects_config=None):
    left, top, right, bottom = outer_rect
    width = right - left
    height = bottom - top

    frame_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    if material == "aluminum":
        texture = aluminum_texture(width, height, base).convert("RGBA")
    else:
        texture = wood_texture(width, height, base, frame_px=frame_px, profile=profile, frame_id=frame_id).convert("RGBA")
    slope_config = (effects_config or {}).get("triangular_slope", {"enabled": True, "angle_degrees": 30})
    if slope_config.get("enabled", True):
        texture = apply_triangular_frame_slope(
            texture.convert("RGB"),
            frame_px,
            material,
            frame_id=frame_id,
            angle_degrees=float(slope_config.get("angle_degrees", 30)),
        ).convert("RGBA")

    mask = Image.new("L", (width, height), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rectangle([0, 0, width, height], fill=255)
    mask_draw.rectangle(
        [
            frame_px,
            frame_px,
            max(frame_px, width - frame_px),
            max(frame_px, height - frame_px),
        ],
        fill=0,
    )
    texture.putalpha(mask)
    frame_layer.alpha_composite(texture, (left, top))

    canvas = Image.alpha_composite(canvas.convert("RGBA"), frame_layer).convert("RGB")
    return canvas
