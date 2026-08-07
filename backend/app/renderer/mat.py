import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from .utils import adjust_color
from .utils import mm_to_px

MAT_BASE = (236, 228, 214)
MAT_BEVEL_MM = 1.5


def mat_board_texture(width, height, base=MAT_BASE):
    large = np.random.normal(0, 2.2, (height, width))
    fibers = np.sin(np.mgrid[0:height, 0:width][1] / 11) * 0.8
    arr = np.zeros((height, width, 3), dtype=np.float32)
    arr[:] = base
    arr += (large + fibers)[:, :, None]
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.35))


def draw_mat(canvas, mat_rect, aperture_rect, mat_px, base=MAT_BASE):
    if mat_px <= 0:
        return canvas

    left, top, right, bottom = mat_rect
    width = right - left
    height = bottom - top
    a_left, a_top, a_right, a_bottom = aperture_rect

    mat_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    texture = mat_board_texture(width, height, base).convert("RGBA")
    mask = Image.new("L", (width, height), 0)
    draw_mask = ImageDraw.Draw(mask)
    draw_mask.rectangle([0, 0, width, height], fill=255)
    draw_mask.rectangle(
        [a_left - left, a_top - top, a_right - left, a_bottom - top],
        fill=0,
    )
    texture.putalpha(mask)
    mat_layer.alpha_composite(texture, (left, top))

    canvas = Image.alpha_composite(canvas.convert("RGBA"), mat_layer).convert("RGB")
    draw = ImageDraw.Draw(canvas)

    bevel = max(1, mm_to_px(MAT_BEVEL_MM))
    for i in range(bevel):
        t = i / max(1, bevel - 1)
        high = adjust_color(base, 1.10 - t * 0.04)
        low = adjust_color(base, 0.82 + t * 0.06)

        draw.line([(a_left - i, a_top - i), (a_right + i, a_top - i)], fill=low)
        draw.line([(a_left - i, a_top - i), (a_left - i, a_bottom + i)], fill=low)
        draw.line([(a_left - i, a_bottom + i), (a_right + i, a_bottom + i)], fill=high)
        draw.line([(a_right + i, a_top - i), (a_right + i, a_bottom + i)], fill=high)

    return canvas


def draw_inner_reveal(canvas, aperture_rect, reveal_px, color):
    if isinstance(reveal_px, (tuple, list)):
        left_reveal, top_reveal, right_reveal, bottom_reveal = [max(0, int(value)) for value in reveal_px]
    else:
        reveal = max(0, int(reveal_px))
        left_reveal = top_reveal = right_reveal = bottom_reveal = reveal

    if max(left_reveal, top_reveal, right_reveal, bottom_reveal) <= 0:
        return canvas

    left, top, right, bottom = aperture_rect
    draw = ImageDraw.Draw(canvas)
    draw.rectangle(
        [left - left_reveal, top - top_reveal, right + right_reveal, bottom + bottom_reveal],
        fill=color,
    )
    draw.rectangle([left, top, right, bottom], fill=color)

    bevel = min(max(1, mm_to_px(0.6)), max(left_reveal, top_reveal, right_reveal, bottom_reveal))
    for i in range(bevel):
        low = adjust_color(color, 0.78 + i * 0.04)
        high = adjust_color(color, 1.08 - i * 0.03)
        draw.line([(left - i - 1, top - i - 1), (right + i, top - i - 1)], fill=low)
        draw.line([(left - i - 1, top - i - 1), (left - i - 1, bottom + i)], fill=low)
        draw.line([(left - i - 1, bottom + i), (right + i, bottom + i)], fill=high)
        draw.line([(right + i, top - i - 1), (right + i, bottom + i)], fill=high)
    return canvas
