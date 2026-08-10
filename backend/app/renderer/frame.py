import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from .utils import adjust_color

FRAME_BASE = (112, 98, 82)


def wood_texture(width, height, base=FRAME_BASE):
    y, x = np.mgrid[0:height, 0:width]
    grain = np.sin((x + np.sin(y / 31) * 22) / 19) * 7
    secondary = np.sin((x + y * 0.18) / 47) * 3.5
    long_wave = np.sin((x + y * 0.22) / 108) * 4
    fine = np.random.normal(0, 1.7, (height, width))
    pores = (np.random.random((height, width)) > 0.992).astype(np.float32) * -22
    pores = Image.fromarray(np.clip(128 + pores, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.45))
    pores = np.asarray(pores).astype(np.float32) - 128
    noise = grain + secondary + long_wave + fine + pores

    arr = np.zeros((height, width, 3), dtype=np.float32)
    arr[:] = base
    arr[:, :, 0] += noise * 1.35
    arr[:, :, 1] += noise * 0.92
    arr[:, :, 2] += noise * 0.52
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def aluminum_texture(width, height, base):
    y, x = np.mgrid[0:height, 0:width]
    brushed = np.sin((x + y * 0.06) / 9) * 1.4
    fine = np.random.normal(0, 0.65, (height, width))
    highlight = np.sin((x - y * 0.16) / 120) * 2.7
    noise = brushed + fine + highlight

    arr = np.zeros((height, width, 3), dtype=np.float32)
    arr[:] = base
    arr[:, :, 0] += noise
    arr[:, :, 1] += noise
    arr[:, :, 2] += noise
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def apply_frame_relief(texture, frame_px, material):
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
    rail_center = np.minimum(dist_outer, dist_inner) / max(1, frame_px * 0.5)
    convex = np.sin(np.clip(rail_center, 0, 1) * np.pi)

    diagonal_light = ((1 - x / max(1, width)) * 0.62 + (1 - y / max(1, height)) * 0.38)
    inner_lip = np.clip(1 - dist_inner / max(1, frame_px * 0.18), 0, 1)
    outer_lip = np.clip(1 - dist_outer / max(1, frame_px * 0.20), 0, 1)

    if material == "aluminum":
        relief = 0.92 + convex * 0.18 + diagonal_light * 0.11 - inner_lip * 0.18 - outer_lip * 0.04
    else:
        relief = 0.88 + convex * 0.28 + diagonal_light * 0.12 - inner_lip * 0.24 - outer_lip * 0.06

    arr[ring] *= relief[ring, None]
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def bevel_color(color, factor):
    if factor <= 1:
        return adjust_color(color, factor)

    amount = min(1.0, (factor - 1) * 0.72)
    return tuple(int(channel + (255 - channel) * amount) for channel in color)


def draw_frame(canvas, outer_rect, frame_px, base=FRAME_BASE, material="wood"):
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
        texture = wood_texture(width, height, base).convert("RGBA")
    texture = apply_frame_relief(texture.convert("RGB"), frame_px, material).convert("RGBA")

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

    outer_glow = max(1, frame_px // 16)
    for i in range(outer_glow):
        factor = 1.18 - i * 0.035
        draw.rectangle([left + i, top + i, right - i, bottom - i], outline=bevel_color(base, factor))

    bevel_layers = max(8, min(24 if material == "aluminum" else 34, frame_px // 6))
    for i in range(bevel_layers):
        t = i / max(1, bevel_layers - 1)
        if material == "aluminum":
            light = 1.34 - t * 0.22
            dark = 0.64 + t * 0.18
        else:
            light = 1.52 - t * 0.44
            dark = 0.50 + t * 0.24

        current_bottom = bottom - i
        draw.line([(left + i, top + i), (right - i, top + i)], fill=bevel_color(base, light))
        draw.line([(left + i, top + i), (left + i, current_bottom)], fill=bevel_color(base, light))
        draw.line([(left + i, current_bottom), (right - i, current_bottom)], fill=bevel_color(base, dark))
        draw.line([(right - i, top + i), (right - i, current_bottom)], fill=bevel_color(base, dark))

    inner_left, inner_top, inner_right, inner_bottom = inner_rect
    inner_layers = max(6, min(18 if material == "aluminum" else 24, frame_px // 7))
    for i in range(inner_layers):
        t = i / max(1, inner_layers - 1)
        if material == "aluminum":
            light = 1.18 - t * 0.10
            dark = 0.58 + t * 0.22
        else:
            light = 1.25 - t * 0.16
            dark = 0.46 + t * 0.25
        draw.line([(inner_left - i, inner_top - i), (inner_right + i, inner_top - i)], fill=bevel_color(base, dark))
        draw.line([(inner_left - i, inner_top - i), (inner_left - i, inner_bottom + i)], fill=bevel_color(base, dark))
        draw.line([(inner_left - i, inner_bottom + i), (inner_right + i, inner_bottom + i)], fill=bevel_color(base, light))
        draw.line([(inner_right + i, inner_top - i), (inner_right + i, inner_bottom + i)], fill=bevel_color(base, light))

    rabbet = max(2, min(frame_px // 9, 14))
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
