import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from .utils import adjust_color

FRAME_BASE = (112, 98, 82)


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
        return {"kind": "painted_light", "contrast": 1.7, "pore": 0.9, "ring": 1.2, "ray": 0.9}
    if lightness < 45:
        return {"kind": "painted_dark", "contrast": 1.4, "pore": 0.8, "ring": 1.1, "ray": 0.45}
    if warmth > 70 and lightness > 155:
        return {"kind": "light_oak", "contrast": 5.8, "pore": 2.4, "ring": 4.6, "ray": 2.7}
    if warmth > 55 and lightness > 95:
        return {"kind": "oak", "contrast": 7.2, "pore": 2.8, "ring": 5.4, "ray": 2.0}
    if warmth > 35 and lightness > 55:
        return {"kind": "walnut", "contrast": 8.4, "pore": 2.1, "ring": 6.6, "ray": 0.7}
    return {"kind": "dark_walnut", "contrast": 7.4, "pore": 1.8, "ring": 5.7, "ray": 0.45}


def blurred_noise(width, height, rng, blur_radius, scale=1.0):
    raw = rng.normal(127, 46, (height, width)).astype(np.uint8)
    img = Image.fromarray(raw, "L").filter(ImageFilter.GaussianBlur(blur_radius))
    arr = np.asarray(img).astype(np.float32) - 127
    return arr * scale / 48


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


def wood_texture(width, height, base=FRAME_BASE, frame_px=1, profile="natural_wood"):
    rng = np.random.default_rng(stable_seed(width, height, base, frame_px))
    params = wood_material_params(base)
    x, y, u, v, dist_outer, dist_inner = rail_coordinates(width, height, frame_px)

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

    annual = np.sin(grain_u / (18 + rail_width * 0.08) + np.sin(grain_u / 87) * 0.9)
    secondary = np.sin(grain_u / (7.5 + rail_width * 0.018) + grain_v / 24) * 0.48
    broad = np.sin(grain_u / (78 + rail_width * 0.18) + np.sin(grain_v / 31) * 0.8) * 0.62
    fine = rng.normal(0, 0.42, (height, width))

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
        + fine
        + pore_value
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

    corner_softening = np.clip(((x / max(1, width - 1)) * (y / max(1, height - 1))), 0, 1)
    corner_softening *= np.clip(((1 - x / max(1, width - 1)) * (1 - y / max(1, height - 1))), 0, 1)
    arr += corner_softening[:, :, None] * 3.0

    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


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
        relief = 0.93 + moulding * 0.88 + soft_rounding * 0.10 + diagonal_light * 0.08 - inner_lip * 0.16 - outer_lip * 0.04

    arr[ring] *= relief[ring, None]
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def bevel_color(color, factor):
    if factor <= 1:
        return adjust_color(color, factor)

    amount = min(1.0, (factor - 1) * 0.72)
    return tuple(int(channel + (255 - channel) * amount) for channel in color)


def draw_frame(canvas, outer_rect, frame_px, base=FRAME_BASE, material="wood", profile="flat"):
    left, top, right, bottom = outer_rect
    width = right - left
    height = bottom - top
    inner_rect = (
        left + frame_px,
        top + frame_px,
        right - frame_px,
        bottom - frame_px,
    )

    frame_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    if material == "aluminum":
        texture = aluminum_texture(width, height, base).convert("RGBA")
    else:
        texture = wood_texture(width, height, base, frame_px=frame_px, profile=profile).convert("RGBA")
    texture = apply_frame_relief(texture.convert("RGB"), frame_px, material, profile).convert("RGBA")

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
    draw = ImageDraw.Draw(canvas)

    bevel_layers = max(5, min(14 if material == "aluminum" else 18, frame_px // 8))
    for i in range(bevel_layers):
        t = i / max(1, bevel_layers - 1)
        if material == "aluminum":
            light = 1.18 - t * 0.12
            dark = 0.76 + t * 0.12
        else:
            light = 1.26 - t * 0.18
            dark = 0.68 + t * 0.18

        current_bottom = bottom - i
        draw.line([(left + i, top + i), (right - i, top + i)], fill=bevel_color(base, light))
        draw.line([(left + i, top + i), (left + i, current_bottom)], fill=bevel_color(base, light))
        draw.line([(left + i, current_bottom), (right - i, current_bottom)], fill=bevel_color(base, dark))
        draw.line([(right - i, top + i), (right - i, current_bottom)], fill=bevel_color(base, dark))

    inner_left, inner_top, inner_right, inner_bottom = inner_rect
    inner_layers = max(5, min(12 if material == "aluminum" else 16, frame_px // 9))
    for i in range(inner_layers):
        t = i / max(1, inner_layers - 1)
        if material == "aluminum":
            light = 1.10 - t * 0.06
            dark = 0.70 + t * 0.12
        else:
            light = 1.13 - t * 0.08
            dark = 0.62 + t * 0.14
        draw.line([(inner_left - i, inner_top - i), (inner_right + i, inner_top - i)], fill=bevel_color(base, dark))
        draw.line([(inner_left - i, inner_top - i), (inner_left - i, inner_bottom + i)], fill=bevel_color(base, dark))
        draw.line([(inner_left - i, inner_bottom + i), (inner_right + i, inner_bottom + i)], fill=bevel_color(base, light))
        draw.line([(inner_right + i, inner_top - i), (inner_right + i, inner_bottom + i)], fill=bevel_color(base, light))

    rabbet = max(2, min(frame_px // 10, 10))
    for i in range(rabbet):
        t = i / max(1, rabbet - 1)
        color = bevel_color(base, 0.42 + t * 0.18)
        draw.rectangle(
            [
                inner_left - i,
                inner_top - i,
                inner_right + i,
                inner_bottom + i,
            ],
            outline=color,
        )

    return canvas
