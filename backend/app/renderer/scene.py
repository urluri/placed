from PIL import Image, ImageDraw, ImageFilter

from .frame import draw_frame
from .mat import draw_inner_reveal, draw_inner_reveal_depth, draw_mat
from .utils import mm_to_px

TECHNICAL_FRAME_COLOR = (0, 0, 0)
DEFAULT_MAT_COLOR = (245, 241, 232)


def add_frame_cast_shadow(canvas, inner_rect, frame_px):
    left, top, right, bottom = inner_rect
    shadow_width = max(3, min(frame_px // 5, 22))
    blur_radius = max(4, min(frame_px // 6, 20))

    mask = Image.new("L", canvas.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rectangle([left, top, right, bottom], outline=170, width=shadow_width)
    mask = mask.filter(ImageFilter.GaussianBlur(blur_radius))

    clip = Image.new("L", canvas.size, 0)
    clip_draw = ImageDraw.Draw(clip)
    clip_draw.rectangle([left, top, right, bottom], fill=255)
    clipped_mask = Image.new("L", canvas.size, 0)
    clipped_mask.paste(mask, mask=clip)

    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 72))
    shadow.putalpha(clipped_mask)
    return Image.alpha_composite(canvas.convert("RGBA"), shadow).convert("RGB")


def render(image_path, img_w_mm, img_h_mm, geometry, output_path="output.jpg", rotation_degrees=0):
    artwork = Image.open(image_path).convert("RGB")
    if rotation_degrees:
        artwork = artwork.rotate(rotation_degrees, expand=True)

    art_w = mm_to_px(img_w_mm)
    art_h = mm_to_px(img_h_mm)
    frame = mm_to_px(geometry.get("frame", 20))
    mat_left = mm_to_px(geometry.get("mat_left", 0))
    mat_right = mm_to_px(geometry.get("mat_right", 0))
    mat_top = mm_to_px(geometry.get("mat_top", 0))
    mat_bottom = mm_to_px(geometry.get("mat_bottom", 0))
    overlap = mm_to_px(geometry.get("overlap", 0))
    inner_reveal_left = mm_to_px(geometry.get("inner_reveal_left", geometry.get("inner_reveal", 0)))
    inner_reveal_right = mm_to_px(geometry.get("inner_reveal_right", geometry.get("inner_reveal", 0)))
    inner_reveal_top = mm_to_px(geometry.get("inner_reveal_top", geometry.get("inner_reveal", 0)))
    inner_reveal_bottom = mm_to_px(geometry.get("inner_reveal_bottom", geometry.get("inner_reveal", 0)))
    frame_color = tuple(geometry.get("frame_color", TECHNICAL_FRAME_COLOR))
    frame_material = geometry.get("frame_material", "wood")
    frame_profile = geometry.get("frame_profile", "flat")
    frame_id = geometry.get("frame_id")
    mat_color = tuple(geometry.get("mat_color", DEFAULT_MAT_COLOR))
    inner_mat_color = tuple(geometry.get("inner_mat_color", mat_color))
    glass_type = geometry.get("glass", "none")
    has_mat = any((mat_left, mat_right, mat_top, mat_bottom))
    has_inner_reveal = any((inner_reveal_left, inner_reveal_right, inner_reveal_top, inner_reveal_bottom))

    artwork = artwork.resize((art_w, art_h), Image.LANCZOS)

    window_w = art_w - 2 * overlap if has_mat else art_w
    window_h = art_h - 2 * overlap if has_mat else art_h
    mat_outer_w = window_w + mat_left + mat_right
    mat_outer_h = window_h + mat_top + mat_bottom
    picture_w = mat_outer_w + frame * 2
    picture_h = mat_outer_h + frame * 2

    outer_rect = (0, 0, picture_w - 1, picture_h - 1)
    mat_rect = (frame, frame, frame + mat_outer_w, frame + mat_outer_h)
    window_rect = (
        frame + mat_left,
        frame + mat_top,
        frame + mat_left + window_w,
        frame + mat_top + window_h,
    )
    art_rect = (
        window_rect[0] - overlap,
        window_rect[1] - overlap,
        window_rect[0] - overlap + art_w,
        window_rect[1] - overlap + art_h,
    )

    canvas = Image.new("RGB", (picture_w, picture_h), frame_color)
    canvas = draw_frame(canvas, outer_rect, frame, frame_color, material=frame_material, profile=frame_profile, frame_id=frame_id)
    canvas.paste(artwork, (art_rect[0], art_rect[1]))

    if has_mat:
        mat_px = max(1, min(mat_left, mat_right, mat_top, mat_bottom))
        if has_inner_reveal:
            top_aperture_rect = (
                window_rect[0] - inner_reveal_left,
                window_rect[1] - inner_reveal_top,
                window_rect[2] + inner_reveal_right,
                window_rect[3] + inner_reveal_bottom,
            )
            canvas = draw_mat(canvas, mat_rect, top_aperture_rect, mat_px, mat_color)
            canvas = draw_inner_reveal(
                canvas,
                window_rect,
                (inner_reveal_left, inner_reveal_top, inner_reveal_right, inner_reveal_bottom),
                inner_mat_color,
            )
            canvas = draw_inner_reveal_depth(
                canvas,
                window_rect,
                (inner_reveal_left, inner_reveal_top, inner_reveal_right, inner_reveal_bottom),
                strength=0.24,
            )
        else:
            canvas = draw_mat(canvas, mat_rect, window_rect, mat_px, mat_color)

    # Realism effects are disabled temporarily while we isolate frame-corner shadows.
    # Keep geometry, colors, artwork, and textures only. Re-enable effects step by step.
    _ = (glass_type, frame, mat_px if has_mat else 0, window_rect)

    if output_path:
        canvas.save(output_path, quality=96, subsampling=0)
    return canvas
