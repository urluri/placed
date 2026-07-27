import os

from backend.app.algorithm import build_decoration_set, renderer_geometry
from backend.app.renderer.scene import render


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_IMAGE = os.path.join(BASE_DIR, "test_images", "test.jpg")


def ask_int(prompt, default):
    raw = input(f"{prompt} [{default}]: ").strip()
    return int(raw) if raw else default


def ask_choice(prompt, choices, default):
    raw = input(f"{prompt} ({'/'.join(choices)}) [{default}]: ").strip()
    return raw if raw in choices else default


def run():
    width_mm = ask_int("Artwork width, mm", 300)
    height_mm = ask_int("Artwork height, mm", 400)
    artwork_type = ask_choice(
        "Artwork type",
        ["poster", "photo", "watercolor", "canvas", "volumetric"],
        "poster",
    )
    interior_style = ask_choice(
        "Interior style",
        ["minimal", "scandi", "japandi", "contemporary", "loft", "modern_vintage", "neoclassic", "universal"],
        "minimal",
    )

    if not os.path.exists(DEFAULT_IMAGE):
        raise FileNotFoundError("test_images/test.jpg not found")

    result = build_decoration_set(
        image_path=DEFAULT_IMAGE,
        artwork_width_mm=width_mm,
        artwork_height_mm=height_mm,
        artwork_type=artwork_type,
        interior_style=interior_style,
    )

    print("\n================ VARIANTS ================\n")
    for variant in result["variants"]:
        frame = variant["frame"]
        mat = variant["mat"]
        glass = variant["glass"]
        print(variant["title"])
        print(f"- frame: {frame['name']}, {frame['width_mm']} mm")
        print(f"- mat: {mat['outer_color']['name'] if mat and mat['enabled'] else 'none'}")
        print(f"- glass: {glass['type']}")
        print(f"- outer size: {variant['geometry']['outer_width_mm']} x {variant['geometry']['outer_height_mm']} mm")
        for warning in variant["warnings"]:
            print(f"- warning: {warning}")
        print()

    standard = result["variants"][0]
    rendered = render(
        DEFAULT_IMAGE,
        width_mm,
        height_mm,
        renderer_geometry(standard),
        output_path=os.path.join(BASE_DIR, "output.jpg"),
    )
    rendered.save(os.path.join(BASE_DIR, "output.jpg"))
    print("Saved to output.jpg")


if __name__ == "__main__":
    run()
