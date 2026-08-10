import numpy as np
from PIL import Image, ImageDraw, ImageFilter

MAT_BASE = (236, 228, 214)


def mat_board_texture(width, height, base=MAT_BASE):
    y, x = np.mgrid[0:height, 0:width]
    cloud = np.random.normal(0, 2.8, (height, width))
    cloud = np.asarray(
        Image.fromarray(np.clip(128 + cloud * 10, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2.1))
    ).astype(np.float32)
    cloud = (cloud - 128) * 0.18

    horizontal_fibers = np.sin((x + np.sin(y / 29) * 12) / 8.5) * 0.75
    vertical_fibers = np.sin((y + np.sin(x / 41) * 9) / 17) * 0.35
    fine = np.random.normal(0, 0.9, (height, width))
    speckles = (np.random.random((height, width)) > 0.996).astype(np.float32) * np.random.normal(-10, 3, (height, width))
    texture_value = cloud + horizontal_fibers + vertical_fibers + fine + speckles

    arr = np.zeros((height, width, 3), dtype=np.float32)
    arr[:] = base
    arr += texture_value[:, :, None]
    arr[:, :, 0] += horizontal_fibers * 0.35
    arr[:, :, 2] -= horizontal_fibers * 0.18
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.18))


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
    if left_reveal > 0:
        draw.rectangle([left - left_reveal, top - top_reveal, left, bottom + bottom_reveal], fill=color)
    if top_reveal > 0:
        draw.rectangle([left, top - top_reveal, right, top], fill=color)
    if right_reveal > 0:
        draw.rectangle([right, top - top_reveal, right + right_reveal, bottom + bottom_reveal], fill=color)
    if bottom_reveal > 0:
        draw.rectangle([left, bottom, right, bottom + bottom_reveal], fill=color)
    return canvas
