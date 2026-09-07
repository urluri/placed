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


def draw_aperture_depth(canvas, aperture_rect, mat_px, strength=0.26):
    left, top, right, bottom = aperture_rect
    if right <= left or bottom <= top:
        return canvas

    depth = max(2, min(mat_px // 18, 8))
    blur = max(1, min(depth, 5))
    line_alpha = int(42 * strength)
    shadow_alpha = int(92 * strength)
    highlight_alpha = int(48 * strength)

    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # The bevel is intentionally quiet: mat board has thickness, but it should not look like a heavy frame.
    draw.line([(left, top), (right, top)], fill=(255, 255, 255, highlight_alpha), width=1)
    draw.line([(left, top), (left, bottom)], fill=(255, 255, 255, highlight_alpha), width=1)
    draw.line([(left, bottom), (right, bottom)], fill=(0, 0, 0, line_alpha), width=1)
    draw.line([(right, top), (right, bottom)], fill=(0, 0, 0, line_alpha), width=1)

    shadow_mask = Image.new("L", canvas.size, 0)
    shadow_draw = ImageDraw.Draw(shadow_mask)
    shadow_draw.rectangle([left, top, right, bottom], outline=shadow_alpha, width=depth)
    shadow_mask = shadow_mask.filter(ImageFilter.GaussianBlur(blur))

    aperture_clip = Image.new("L", canvas.size, 0)
    clip_draw = ImageDraw.Draw(aperture_clip)
    clip_draw.rectangle([left, top, right, bottom], fill=255)
    clipped_shadow = Image.new("L", canvas.size, 0)
    clipped_shadow.paste(shadow_mask, mask=aperture_clip)

    shadow_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 46))
    shadow_layer.putalpha(clipped_shadow)
    overlay = Image.alpha_composite(overlay, shadow_layer)

    return Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB")


def draw_image_window_depth(canvas, aperture_rect, mat_px, strength=0.34):
    left, top, right, bottom = aperture_rect
    if right <= left or bottom <= top:
        return canvas

    depth = max(3, min(mat_px // 14, 11))
    blur = max(2, min(depth, 6))
    shadow_alpha = int(120 * strength)
    line_alpha = int(56 * strength)
    highlight_alpha = int(64 * strength)

    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    edge_draw = ImageDraw.Draw(overlay)
    edge_draw.line([(left, top), (right, top)], fill=(255, 255, 255, highlight_alpha), width=1)
    edge_draw.line([(left, top), (left, bottom)], fill=(255, 255, 255, highlight_alpha), width=1)
    edge_draw.line([(left, bottom), (right, bottom)], fill=(0, 0, 0, line_alpha), width=1)
    edge_draw.line([(right, top), (right, bottom)], fill=(0, 0, 0, line_alpha), width=1)

    shadow_mask = Image.new("L", canvas.size, 0)
    shadow_draw = ImageDraw.Draw(shadow_mask)
    shadow_draw.rectangle([left, top, right, bottom], outline=shadow_alpha, width=depth)
    shadow_mask = shadow_mask.filter(ImageFilter.GaussianBlur(blur))

    image_clip = Image.new("L", canvas.size, 0)
    clip_draw = ImageDraw.Draw(image_clip)
    clip_draw.rectangle([left, top, right, bottom], fill=255)
    clipped_shadow = Image.new("L", canvas.size, 0)
    clipped_shadow.paste(shadow_mask, mask=image_clip)

    shadow_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 58))
    shadow_layer.putalpha(clipped_shadow)
    overlay = Image.alpha_composite(overlay, shadow_layer)
    return Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB")


def draw_inner_reveal_depth(canvas, aperture_rect, reveal_px, strength=0.24):
    if isinstance(reveal_px, (tuple, list)):
        left_reveal, top_reveal, right_reveal, bottom_reveal = [max(0, int(value)) for value in reveal_px]
    else:
        reveal = max(0, int(reveal_px))
        left_reveal = top_reveal = right_reveal = bottom_reveal = reveal

    if max(left_reveal, top_reveal, right_reveal, bottom_reveal) <= 0:
        return canvas

    left, top, right, bottom = aperture_rect
    reveal_left = left - left_reveal
    reveal_top = top - top_reveal
    reveal_right = right + right_reveal
    reveal_bottom = bottom + bottom_reveal

    depth = max(2, min(max(left_reveal, top_reveal, right_reveal, bottom_reveal) // 3, 9))
    blur = max(1, min(depth, 5))
    shadow_alpha = int(115 * strength)

    shadow_mask = Image.new("L", canvas.size, 0)
    shadow_draw = ImageDraw.Draw(shadow_mask)
    shadow_draw.rectangle([reveal_left, reveal_top, reveal_right, reveal_bottom], outline=shadow_alpha, width=depth)
    shadow_mask = shadow_mask.filter(ImageFilter.GaussianBlur(blur))

    reveal_clip = Image.new("L", canvas.size, 0)
    clip_draw = ImageDraw.Draw(reveal_clip)
    clip_draw.rectangle([reveal_left, reveal_top, reveal_right, reveal_bottom], fill=255)
    clip_draw.rectangle([left, top, right, bottom], fill=0)

    clipped_shadow = Image.new("L", canvas.size, 0)
    clipped_shadow.paste(shadow_mask, mask=reveal_clip)
    shadow_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 56))
    shadow_layer.putalpha(clipped_shadow)
    return Image.alpha_composite(canvas.convert("RGBA"), shadow_layer).convert("RGB")


def draw_mat_window_bevel(canvas, aperture_rect, width_px=4, highlight_opacity=210, edge_opacity=52, shadow_opacity=26):
    left, top, right, bottom = [int(value) for value in aperture_rect]
    if right <= left or bottom <= top:
        return canvas

    width_px = max(1, int(width_px))
    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # A real mat bevel is a 45-degree cut. For this preview it must read as a
    # consistent paper edge, so all four sides use the same light treatment.
    _ = shadow_opacity
    for offset in range(width_px):
        fade = 1 - offset / max(1, width_px)
        highlight = int(highlight_opacity * fade)
        edge = int(edge_opacity * fade)

        x0 = left - offset
        y0 = top - offset
        x1 = right + offset
        y1 = bottom + offset

        draw.rectangle([x0, y0, x1, y1], outline=(255, 255, 255, highlight), width=1)

        if offset == 0 and edge > 0:
            draw.rectangle([left, top, right, bottom], outline=(255, 255, 255, min(255, highlight + edge)))

    return Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB")


def draw_inner_reveal(canvas, aperture_rect, reveal_px, color):
    if isinstance(reveal_px, (tuple, list)):
        left_reveal, top_reveal, right_reveal, bottom_reveal = [max(0, int(value)) for value in reveal_px]
    else:
        reveal = max(0, int(reveal_px))
        left_reveal = top_reveal = right_reveal = bottom_reveal = reveal

    if max(left_reveal, top_reveal, right_reveal, bottom_reveal) <= 0:
        return canvas

    left, top, right, bottom = aperture_rect
    reveal_left = left - left_reveal
    reveal_top = top - top_reveal
    reveal_right = right + right_reveal
    reveal_bottom = bottom + bottom_reveal
    width = max(1, reveal_right - reveal_left)
    height = max(1, reveal_bottom - reveal_top)

    reveal_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    texture = mat_board_texture(width, height, color).convert("RGBA")
    mask = Image.new("L", (width, height), 0)
    draw_mask = ImageDraw.Draw(mask)
    if left_reveal > 0:
        draw_mask.rectangle([0, 0, left - reveal_left, height], fill=255)
    if top_reveal > 0:
        draw_mask.rectangle([left - reveal_left, 0, right - reveal_left, top - reveal_top], fill=255)
    if right_reveal > 0:
        draw_mask.rectangle([right - reveal_left, 0, width, height], fill=255)
    if bottom_reveal > 0:
        draw_mask.rectangle([left - reveal_left, bottom - reveal_top, right - reveal_left, height], fill=255)

    texture.putalpha(mask)
    reveal_layer.alpha_composite(texture, (reveal_left, reveal_top))
    return Image.alpha_composite(canvas.convert("RGBA"), reveal_layer).convert("RGB")
