from PIL import Image, ImageDraw, ImageFilter


def composite_shadow(canvas, rect, offset=(18, 22), blur=24, opacity=78):
    left, top, right, bottom = rect
    dx, dy = offset

    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(shadow)
    draw.rectangle(
        [left + dx, top + dy, right + dx, bottom + dy],
        fill=(0, 0, 0, opacity),
    )

    shadow = shadow.filter(ImageFilter.GaussianBlur(blur))
    return Image.alpha_composite(canvas.convert("RGBA"), shadow).convert("RGB")


def add_inner_occlusion(canvas, rect, blur=7, opacity=55, spread=8):
    left, top, right, bottom = rect
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)

    draw.rectangle(
        [left - spread, top - spread, right + spread, bottom + spread],
        outline=(0, 0, 0, opacity),
        width=spread,
    )

    layer = layer.filter(ImageFilter.GaussianBlur(blur))
    return Image.alpha_composite(canvas.convert("RGBA"), layer).convert("RGB")


def add_contact_shadow(canvas, rect, blur=5, opacity=34):
    left, top, right, bottom = rect
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    draw.rectangle([left + 2, top + 2, right + 2, bottom + 2], outline=(0, 0, 0, opacity), width=4)
    layer = layer.filter(ImageFilter.GaussianBlur(blur))
    return Image.alpha_composite(canvas.convert("RGBA"), layer).convert("RGB")
