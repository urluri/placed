from PIL import Image, ImageDraw, ImageFilter


def add_glass_effect(canvas, rect, opacity=16):
    left, top, right, bottom = rect
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)

    draw.rectangle(rect, fill=(255, 255, 255, opacity))

    highlight = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    hd = ImageDraw.Draw(highlight)
    width = right - left
    hd.polygon(
        [
            (left + width * 0.06, top),
            (left + width * 0.28, top),
            (left + width * 0.78, bottom),
            (left + width * 0.54, bottom),
        ],
        fill=(255, 255, 255, 28),
    )
    highlight = highlight.filter(ImageFilter.GaussianBlur(12))

    layer = Image.alpha_composite(layer, highlight)

    for offset in range(-160, int(right - left), 170):
        draw.line(
            [(left + offset, bottom), (left + offset + 220, top)],
            fill=(255, 255, 255, 12),
            width=2,
        )

    return Image.alpha_composite(canvas.convert("RGBA"), layer).convert("RGB")
