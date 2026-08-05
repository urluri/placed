from PIL import Image

from .frame import draw_frame
from .glass import add_glass_effect
from .lighting import add_global_lighting
from .mat import draw_mat
from .postprocess import add_chromatic_aberration, add_film_grain, add_vignette, color_grade
from .shadows import add_contact_shadow, add_inner_occlusion
from .utils import mm_to_px

TECHNICAL_FRAME_COLOR = (0, 0, 0)
DEFAULT_MAT_COLOR = (255, 255, 240)


def render(image_path, img_w_mm, img_h_mm, geometry, output_path="output.jpg", rotate_image=False):
    artwork = Image.open(image_path).convert("RGB")
    if rotate_image:
        artwork = artwork.rotate(90, expand=True)

    art_w = mm_to_px(img_w_mm)
    art_h = mm_to_px(img_h_mm)
    frame = mm_to_px(geometry.get("frame", 20))
    mat_left = mm_to_px(geometry.get("mat_left", 0))
    mat_right = mm_to_px(geometry.get("mat_right", 0))
    mat_top = mm_to_px(geometry.get("mat_top", 0))
    mat_bottom = mm_to_px(geometry.get("mat_bottom", 0))
    frame_color = tuple(geometry.get("frame_color", TECHNICAL_FRAME_COLOR))
    mat_color = tuple(geometry.get("mat_color", DEFAULT_MAT_COLOR))
    glass_type = geometry.get("glass", "none")
    has_mat = any((mat_left, mat_right, mat_top, mat_bottom))

    artwork = artwork.resize((art_w, art_h), Image.LANCZOS)

    mat_outer_w = art_w + mat_left + mat_right
    mat_outer_h = art_h + mat_top + mat_bottom
    picture_w = mat_outer_w + frame * 2
    picture_h = mat_outer_h + frame * 2

    outer_rect = (0, 0, picture_w - 1, picture_h - 1)
    mat_rect = (frame, frame, frame + mat_outer_w, frame + mat_outer_h)
    art_rect = (
        frame + mat_left,
        frame + mat_top,
        frame + mat_left + art_w,
        frame + mat_top + art_h,
    )

    canvas = Image.new("RGB", (picture_w, picture_h), frame_color)
    canvas = draw_frame(canvas, outer_rect, frame, frame_color)

    if has_mat:
        mat_px = max(1, min(mat_left, mat_right, mat_top, mat_bottom))
        canvas = draw_mat(canvas, mat_rect, art_rect, mat_px, mat_color)
        canvas = add_inner_occlusion(canvas, art_rect, blur=7, opacity=44, spread=max(4, mat_px // 14))
    else:
        canvas = add_inner_occlusion(canvas, art_rect, blur=5, opacity=32, spread=max(3, frame // 8))

    canvas.paste(artwork, (art_rect[0], art_rect[1]))
    canvas = add_contact_shadow(canvas, art_rect, blur=4, opacity=24)

    if glass_type and glass_type != "none":
        opacity = 12 if glass_type == "museum" else 16
        canvas = add_glass_effect(canvas, art_rect, opacity=opacity)

    canvas = add_global_lighting(canvas, strength=0.045)
    canvas = add_vignette(canvas, strength=0.045)
    canvas = add_film_grain(canvas, sigma=0.9)
    canvas = add_chromatic_aberration(canvas, offset=1)
    canvas = color_grade(canvas)

    canvas.save(output_path, quality=95)
    return canvas
