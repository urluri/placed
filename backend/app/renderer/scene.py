from PIL import Image

from .utils import mm_to_px

TECHNICAL_FRAME_COLOR = (0, 0, 0)


def render(image_path, img_w_mm, img_h_mm, geometry, output_path="output.jpg", rotate_image=False):
    artwork = Image.open(image_path).convert("RGB")
    if rotate_image:
        artwork = artwork.rotate(90, expand=True)

    art_w = mm_to_px(img_w_mm)
    art_h = mm_to_px(img_h_mm)
    frame = mm_to_px(geometry.get("frame", 20))

    artwork = artwork.resize((art_w, art_h), Image.LANCZOS)

    picture_w = art_w + frame * 2
    picture_h = art_h + frame * 2

    canvas = Image.new("RGB", (picture_w, picture_h), TECHNICAL_FRAME_COLOR)
    canvas.paste(artwork, (frame, frame))

    canvas.save(output_path, quality=95)
    return canvas
