from PIL import Image, ImageDraw

from .utils import mm_to_px

TECHNICAL_FRAME_COLOR = (0, 0, 0)
TECHNICAL_BACKGROUND = (236, 234, 230)


def render(image_path, img_w_mm, img_h_mm, geometry, output_path="output.jpg", rotate_image=False):
    artwork = Image.open(image_path).convert("RGB")
    if rotate_image:
        artwork = artwork.rotate(90, expand=True)

    art_w = mm_to_px(img_w_mm)
    art_h = mm_to_px(img_h_mm)
    frame = mm_to_px(geometry.get("frame", 20))
    margin = max(80, int(min(art_w, art_h) * 0.1))

    artwork = artwork.resize((art_w, art_h), Image.LANCZOS)

    picture_w = art_w + frame * 2
    picture_h = art_h + frame * 2
    canvas_w = picture_w + margin * 2
    canvas_h = picture_h + margin * 2

    canvas = Image.new("RGB", (canvas_w, canvas_h), TECHNICAL_BACKGROUND)
    draw = ImageDraw.Draw(canvas)

    frame_left = margin
    frame_top = margin
    frame_right = frame_left + picture_w
    frame_bottom = frame_top + picture_h
    draw.rectangle(
        [frame_left, frame_top, frame_right, frame_bottom],
        fill=TECHNICAL_FRAME_COLOR,
    )

    canvas.paste(artwork, (frame_left + frame, frame_top + frame))
    canvas.save(output_path, quality=95)
    return canvas
