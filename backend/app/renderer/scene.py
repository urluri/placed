from PIL import Image

from .frame import draw_frame
from .glass import add_glass_effect
from .lighting import add_global_lighting
from .mat import draw_inner_reveal, draw_mat
from .postprocess import (
    add_chromatic_aberration,
    add_film_grain,
    add_vignette,
    color_grade,
)
from .shadows import add_contact_shadow, add_inner_occlusion, composite_shadow
from .utils import mm_to_px
from .wall import create_wall


def render(image_path, img_w_mm, img_h_mm, geometry, output_path="output.jpg", rotate_image=False):
    artwork = Image.open(image_path).convert("RGB")
    if rotate_image:
        artwork = artwork.rotate(90, expand=True)

    art_w = mm_to_px(img_w_mm)
    art_h = mm_to_px(img_h_mm)
    artwork = artwork.resize((art_w, art_h), Image.LANCZOS)

    frame = mm_to_px(geometry["frame"])
    mat_left = mm_to_px(geometry.get("mat_left", geometry.get("passepartout", 0)))
    mat_right = mm_to_px(geometry.get("mat_right", geometry.get("passepartout", 0)))
    mat_top = mm_to_px(geometry.get("mat_top", geometry.get("passepartout", 0)))
    mat_bottom = mm_to_px(geometry.get("mat_bottom", geometry.get("passepartout", 0)))
    inner_reveal = mm_to_px(geometry.get("inner_reveal", 0))
    frame_color = geometry.get("frame_color", (112, 98, 82))
    mat_color = geometry.get("mat_color", (236, 228, 214))
    inner_mat_color = geometry.get("inner_mat_color", (85, 86, 83))

    picture_w = art_w + mat_left + mat_right + frame * 2
    picture_h = art_h + mat_top + mat_bottom + frame * 2
    margin = max(180, int(min(picture_w, picture_h) * 0.14))

    canvas_w = picture_w + margin * 2
    canvas_h = picture_h + margin * 2
    canvas = create_wall(canvas_w, canvas_h, style="gallery")

    left = margin
    top = margin
    right = left + picture_w
    bottom = top + picture_h
    frame_rect = (left, top, right, bottom)

    canvas = composite_shadow(
        canvas,
        frame_rect,
        offset=(max(12, frame // 6), max(16, frame // 5)),
        blur=max(18, frame // 4),
        opacity=76,
    )

    canvas = draw_frame(canvas, frame_rect, frame, base=frame_color)

    mat_rect = (
        left + frame,
        top + frame,
        right - frame,
        bottom - frame,
    )

    aperture_rect = (
        mat_rect[0] + mat_left,
        mat_rect[1] + mat_top,
        mat_rect[2] - mat_right,
        mat_rect[3] - mat_bottom,
    )

    mat_for_bevel = max(mat_left, mat_right, mat_top, mat_bottom)
    if mat_for_bevel > 0:
        canvas = draw_mat(canvas, mat_rect, aperture_rect, mat_for_bevel, base=mat_color)
        canvas = draw_inner_reveal(canvas, aperture_rect, inner_reveal, inner_mat_color)
        canvas = add_inner_occlusion(
            canvas,
            aperture_rect,
            blur=max(5, mat_for_bevel // 18),
            opacity=42,
            spread=max(5, mat_for_bevel // 18),
        )

    canvas.paste(artwork, (aperture_rect[0], aperture_rect[1]))
    canvas = add_contact_shadow(canvas, aperture_rect, blur=4, opacity=28)

    if geometry.get("glass") not in {"none", "forbidden"}:
        canvas = add_glass_effect(canvas, aperture_rect)

    canvas = add_global_lighting(canvas)
    canvas = add_vignette(canvas)
    canvas = add_film_grain(canvas)
    canvas = add_chromatic_aberration(canvas, offset=1)
    canvas = color_grade(canvas)

    canvas.save(output_path, quality=95)
    return canvas
