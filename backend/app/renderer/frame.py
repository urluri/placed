import numpy as np
from PIL import Image, ImageDraw

from .utils import adjust_color

FRAME_BASE = (112, 98, 82)


def wood_texture(width, height, base=FRAME_BASE):
    y, x = np.mgrid[0:height, 0:width]
    grain = np.sin((x + np.sin(y / 37) * 18) / 24) * 5
    fine = np.random.normal(0, 2.0, (height, width))
    long_wave = np.sin((x + y * 0.25) / 90) * 3
    noise = grain + fine + long_wave

    arr = np.zeros((height, width, 3), dtype=np.float32)
    arr[:] = base
    arr[:, :, 0] += noise * 1.25
    arr[:, :, 1] += noise * 0.85
    arr[:, :, 2] += noise * 0.45
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def draw_frame(canvas, outer_rect, frame_px, base=FRAME_BASE):
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
    texture = wood_texture(width, height, base).convert("RGBA")

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

    bevel_layers = max(8, min(26, frame_px // 8))
    for i in range(bevel_layers):
        t = i / max(1, bevel_layers - 1)
        light = 1.42 - t * 0.38
        dark = 0.58 + t * 0.20

        current_bottom = bottom - i
        draw.line([(left + i, top + i), (right - i, top + i)], fill=adjust_color(base, light))
        draw.line([(left + i, top + i), (left + i, current_bottom)], fill=adjust_color(base, light))
        draw.line([(left + i, current_bottom), (right - i, current_bottom)], fill=adjust_color(base, dark))
        draw.line([(right - i, top + i), (right - i, current_bottom)], fill=adjust_color(base, dark))

    inner_left, inner_top, inner_right, inner_bottom = inner_rect
    inner_layers = max(5, min(18, frame_px // 10))
    for i in range(inner_layers):
        t = i / max(1, inner_layers - 1)
        light = 1.16 - t * 0.13
        dark = 0.66 + t * 0.18
        draw.line([(inner_left - i, inner_top - i), (inner_right + i, inner_top - i)], fill=adjust_color(base, dark))
        draw.line([(inner_left - i, inner_top - i), (inner_left - i, inner_bottom + i)], fill=adjust_color(base, dark))
        draw.line([(inner_left - i, inner_bottom + i), (inner_right + i, inner_bottom + i)], fill=adjust_color(base, light))
        draw.line([(inner_right + i, inner_top - i), (inner_right + i, inner_bottom + i)], fill=adjust_color(base, light))

    return canvas
