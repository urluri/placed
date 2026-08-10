from PIL import Image

from .frame import draw_frame
from .glass import add_glass_effect
from .lighting import add_global_lighting
from .mat import draw_inner_reveal, draw_mat
from .postprocess import add_chromatic_aberration, add_film_grain, add_vignette, color_grade
from .utils import mm_to_px

TECHNICAL_FRAME_COLOR = (0, 0, 0)
DEFAULT_MAT_COLOR = (255, 255, 240)


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
    canvas = draw_frame(canvas, outer_rect, frame, frame_color, material=frame_material)
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
        else:
            canvas = draw_mat(canvas, mat_rect, window_rect, mat_px, mat_color)

    if glass_type and glass_type != "none":
        opacity = 12 if glass_type == "museum" else 16
        canvas = add_glass_effect(canvas, window_rect, opacity=opacity)

    canvas = add_global_lighting(canvas, strength=0.045)
    canvas = add_vignette(canvas, strength=0.045)
    canvas = add_film_grain(canvas, sigma=0.9)
    canvas = add_chromatic_aberration(canvas, offset=1)
    canvas = color_grade(canvas)

    canvas.save(output_path, quality=95)
    return canvas
