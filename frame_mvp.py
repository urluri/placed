import yaml
from PIL import Image, ImageOps, ImageDraw, ImageFilter
from dataclasses import dataclass
from enum import Enum
import os

DPI = 300

def mm_to_px(mm):
    return int(mm * DPI / 25.4)

# =======================================================
# INPUT MODEL
# =======================================================

class ArtworkType(str, Enum):
    poster = "poster"
    canvas = "canvas"
    photo = "photo"
    volumetric = "volumetric"


@dataclass
class InputData:
    width_mm: int
    height_mm: int
    artwork_type: ArtworkType


# =======================================================
# SIZE OUTPUTS
# =======================================================

def compute_final_dimensions(w_mm, h_mm, geometry):
    frame = geometry["frame"]
    mat = geometry["passepartout"]

    total_w = w_mm + 2 * (frame + mat)
    total_h = h_mm + 2 * (frame + mat)

    return {
        "canvas_width_mm": w_mm,
        "canvas_height_mm": h_mm,
        "frame_mm": frame,
        "passepartout_mm": mat,
        "final_width_mm": total_w,
        "final_height_mm": total_h
    }


# =======================================================
# LOAD RULES
# =======================================================

def load_rules():
    with open("rules.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# =======================================================
# SIZE CATEGORY
# =======================================================

def get_size_category(short_side, rules):
    for name, profile in rules["size_profiles"].items():
        cond = profile.get("short_side_mm", {})
        min_v = cond.get("min", -10**9)
        max_v = cond.get("max", 10**9)

        if min_v <= short_side <= max_v:
            return name

    return "large"


# =======================================================
# GEOMETRY ENGINE
# =======================================================

def compute_geometry(size_category, artwork_type, rules):
    base = rules["size_profiles"][size_category]["geometry"].copy()
    art = rules["artwork_types"][artwork_type]

    frame = base["frame_width_mm"]
    passepartout = base["passepartout_mm"]

    notes = []

    # --- FRAME ADJUSTMENT
    adj = art.get("frame", {}).get("width_adjustment", {})
    if adj:
        frame += (adj["min"] + adj["max"]) / 2
        notes.append(f"Frame adjusted by {(adj['min'] + adj['max']) / 2} mm")

    # --- PASSPARTOUT
    if art.get("passepartout", {}).get("enabled") is False:
        passepartout = 0
        notes.append("Passepartout disabled for this type")
    else:
        padj = art.get("passepartout", {}).get("adjustment", {})
        if padj:
            passepartout += (padj["min"] + padj["max"]) / 2
            notes.append(f"Passepartout adjusted by {(padj['min'] + padj['max']) / 2} mm")

    return {
        "frame": max(10, frame),
        "passepartout": max(0, passepartout),
        "notes": notes
    }


# =======================================================
# RENDER ENGINE
# =======================================================

def render(image_path, img_w_mm, img_h_mm, geometry, output_path="output.jpg"):

    img = Image.open(image_path).convert("RGB")

    img_w = mm_to_px(img_w_mm)
    img_h = mm_to_px(img_h_mm)

    img = img.resize((img_w, img_h), Image.LANCZOS)

    frame = mm_to_px(geometry["frame"])
    mat = mm_to_px(geometry["passepartout"])

    FRAME = (112, 98, 82)
    FRAME_LIGHT = (155, 140, 122)
    FRAME_DARK = (72, 60, 48)

    MAT = (236, 228, 214)

    WALL = (236, 234, 230)

    # ------------------------------------------------
    # Размеры итоговой композиции
    # ------------------------------------------------

    picture_w = img_w + mat * 2 + frame * 2
    picture_h = img_h + mat * 2 + frame * 2

    margin = 220

    canvas = Image.new(
        "RGB",
        (picture_w + margin * 2, picture_h + margin * 2),
        WALL
    )

    # ------------------------------------------------
    # Большая тень
    # ------------------------------------------------

    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))

    d = ImageDraw.Draw(shadow)

    x = margin + 18
    y = margin + 20

    d.rectangle(
        [x, y, x + picture_w, y + picture_h],
        fill=(0, 0, 0, 80)
    )

    shadow = shadow.filter(ImageFilter.GaussianBlur(22))

    canvas = Image.alpha_composite(
        canvas.convert("RGBA"),
        shadow
    ).convert("RGB")

    # ------------------------------------------------
    # Рама
    # ------------------------------------------------

    draw = ImageDraw.Draw(canvas)

    left = margin
    top = margin

    right = left + picture_w
    bottom = top + picture_h

    draw.rectangle(
        [left, top, right, bottom],
        fill=FRAME
    )

    # ------------------------------------------------
    # Внешний bevel
    # ------------------------------------------------

    for i in range(6):

        draw.line(
            [(left+i, top+i), (right-i, top+i)],
            fill=FRAME_LIGHT
        )

        draw.line(
            [(left+i, top+i), (left+i, bottom-i)],
            fill=FRAME_LIGHT
        )

        draw.line(
            [(left+i, bottom-i), (right-i, bottom-i)],
            fill=FRAME_DARK
        )

        draw.line(
            [(right-i, top+i), (right-i, bottom-i)],
            fill=FRAME_DARK
        )

    # ------------------------------------------------
    # Паспарту
    # ------------------------------------------------

    mat_left = left + frame
    mat_top = top + frame

    mat_right = right - frame
    mat_bottom = bottom - frame

    draw.rectangle(
        [mat_left, mat_top, mat_right, mat_bottom],
        fill=MAT
    )

    # ------------------------------------------------
    # Внутренний bevel паспарту
    # ------------------------------------------------

    for i in range(4):

        draw.line(
            [(mat_left+i, mat_top+i), (mat_right-i, mat_top+i)],
            fill=(250, 248, 244)
        )

        draw.line(
            [(mat_left+i, mat_top+i), (mat_left+i, mat_bottom-i)],
            fill=(250, 248, 244)
        )

        draw.line(
            [(mat_left+i, mat_bottom-i), (mat_right-i, mat_bottom-i)],
            fill=(195, 188, 175)
        )

        draw.line(
            [(mat_right-i, mat_top+i), (mat_right-i, mat_bottom-i)],
            fill=(195, 188, 175)
        )

    # ------------------------------------------------
    # Тень от окна паспарту
    # ------------------------------------------------

    aperture_left = mat_left + mat
    aperture_top = mat_top + mat

    aperture_right = mat_right - mat
    aperture_bottom = mat_bottom - mat

    shadow2 = Image.new("RGBA", canvas.size, (0, 0, 0, 0))

    ds = ImageDraw.Draw(shadow2)

    ds.rectangle(
        [
            aperture_left+4,
            aperture_top+4,
            aperture_right+4,
            aperture_bottom+4
        ],
        fill=(0,0,0,50)
    )

    shadow2 = shadow2.filter(ImageFilter.GaussianBlur(6))

    canvas = Image.alpha_composite(
        canvas.convert("RGBA"),
        shadow2
    ).convert("RGB")

    # ------------------------------------------------
    # Изображение
    # ------------------------------------------------

    canvas.paste(
        img,
        (
            aperture_left,
            aperture_top
        )
    )

    canvas.save(output_path, quality=95)

# =======================================================
# MAIN FLOW
# =======================================================

def run():
    rules = load_rules()

    print("Enter artwork width (mm): ")
    w = int(input())

    print("Enter artwork height (mm): ")
    h = int(input())

    print("Type (poster/canvas/photo/volumetric): ")
    t = ArtworkType(input().strip())

    img_path = os.path.join("test_images", "test.jpg")

    if not os.path.exists(img_path):
        raise FileNotFoundError("test_images/test.jpg not found")

    short_side = min(w, h)

    size_category = get_size_category(short_side, rules)

    geometry = compute_geometry(size_category, t.value, rules)

    result = compute_final_dimensions(w, h, geometry)

    print("\n================ RESULT ================\n")

    print("Size category:", size_category)
    print("Artwork type:", t.value)

    print("\n--- GEOMETRY ---")
    print(f"Frame width: {result['frame_mm']} mm")
    print(f"Passepartout: {result['passepartout_mm']} mm")

    print("\n--- FINAL SIZE (WITH FRAME) ---")
    print(f"Width: {result['final_width_mm']} mm")
    print(f"Height: {result['final_height_mm']} mm")

    print("\n--- BREAKDOWN ---")
    print(f"Artwork: {result['canvas_width_mm']} x {result['canvas_height_mm']} mm")
    print(f"Frame adds: {result['frame_mm']} mm each side")
    print(f"Passepartout adds: {result['passepartout_mm']} mm each side")

    print("\nNotes:")
    for n in geometry["notes"]:
        print("-", n)

    render(img_path, w, h, geometry)

    print("\nSaved to output.jpg")


if __name__ == "__main__":
    run()