from PIL import Image, ImageDraw

from .utils import mm_to_px

TECHNICAL_FRAME_COLOR = (0, 0, 0)


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
    mat_color = tuple(geometry.get("mat_color", (241, 238, 232)))
    has_mat = any((mat_left, mat_right, mat_top, mat_bottom))

    artwork = artwork.resize((art_w, art_h), Image.LANCZOS)

    mat_outer_w = art_w + mat_left + mat_right
    mat_outer_h = art_h + mat_top + mat_bottom
    picture_w = mat_outer_w + frame * 2
    picture_h = mat_outer_h + frame * 2

    canvas = Image.new("RGB", (picture_w, picture_h), frame_color)
    if has_mat:
        draw = ImageDraw.Draw(canvas)
        draw.rectangle(
            [frame, frame, frame + mat_outer_w, frame + mat_outer_h],
            fill=mat_color,
        )

    canvas.paste(artwork, (frame + mat_left, frame + mat_top))

    canvas.save(output_path, quality=95)
    return canvas
