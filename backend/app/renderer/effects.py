from PIL import Image, ImageDraw, ImageFilter

from .config import enabled, get
from .glass import add_glass_effect
from .lighting import add_global_lighting
from .mat import draw_image_window_depth, draw_inner_reveal_depth, draw_mat_window_bevel
from .postprocess import add_chromatic_aberration, add_film_grain, add_vignette, color_grade
from .utils import mm_to_px


def apply_renderer_effects(canvas, layout, effects_config):
    canvas = apply_mat_effects(canvas, layout, effects_config)
    canvas = apply_frame_effects(canvas, layout, effects_config)
    canvas = apply_glass_effects(canvas, layout, effects_config)
    return apply_postprocess_effects(canvas, effects_config)


def apply_mat_effects(canvas, layout, effects_config):
    if not layout["has_mat"]:
        return canvas

    mat_config = get(effects_config, "mat", default={}) or {}
    window_bevel = mat_config.get("window_bevel", {})
    if window_bevel.get("enabled"):
        bevel_width = max(1, mm_to_px(window_bevel.get("width_mm", 1.5)))
        bevel_kwargs = {
            "width_px": bevel_width,
            "highlight_opacity": int(window_bevel.get("highlight_opacity", 210)),
            "edge_opacity": int(window_bevel.get("edge_opacity", 52)),
            "shadow_opacity": int(window_bevel.get("shadow_opacity", 0)),
        }
        if layout.get("top_aperture_rect"):
            canvas = draw_mat_window_bevel(canvas, layout["top_aperture_rect"], **bevel_kwargs)
        canvas = draw_mat_window_bevel(canvas, layout["window_rect"], **bevel_kwargs)

    if enabled(effects_config, "mat", "inner_reveal_depth_shadow") and layout["has_inner_reveal"]:
        shadow_config = get(effects_config, "mat", "inner_reveal_depth_shadow", default={}) or {}
        canvas = draw_inner_reveal_depth(
            canvas,
            layout["window_rect"],
            layout["inner_reveal_px"],
            strength=float(shadow_config.get("strength", 0.18)),
        )

    if enabled(effects_config, "mat", "image_window_depth_shadow"):
        shadow_config = get(effects_config, "mat", "image_window_depth_shadow", default={}) or {}
        canvas = draw_image_window_depth(
            canvas,
            layout["window_rect"],
            layout["mat_px"],
            strength=float(shadow_config.get("strength", 0.18)),
        )

    return canvas


def apply_frame_effects(canvas, layout, effects_config):
    if not enabled(effects_config, "frame", "cast_shadow"):
        return canvas

    shadow_config = get(effects_config, "frame", "cast_shadow", default={}) or {}
    return add_frame_cast_shadow(
        canvas,
        layout["frame_inner_rect"],
        layout["frame_px"],
        opacity=int(shadow_config.get("opacity", 42)),
        blur_px=int(shadow_config.get("blur_px", 10)),
    )


def add_frame_cast_shadow(canvas, inner_rect, frame_px, opacity=42, blur_px=10):
    left, top, right, bottom = inner_rect
    shadow_width = max(2, min(frame_px // 6, 16))
    blur_radius = max(2, min(blur_px, 18))

    mask = Image.new("L", canvas.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rectangle([left, top, right, bottom], outline=opacity, width=shadow_width)
    mask = mask.filter(ImageFilter.GaussianBlur(blur_radius))

    clip = Image.new("L", canvas.size, 0)
    clip_draw = ImageDraw.Draw(clip)
    clip_draw.rectangle([left, top, right, bottom], fill=255)
    clipped_mask = Image.new("L", canvas.size, 0)
    clipped_mask.paste(mask, mask=clip)

    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, opacity))
    shadow.putalpha(clipped_mask)
    return Image.alpha_composite(canvas.convert("RGBA"), shadow).convert("RGB")


def apply_glass_effects(canvas, layout, effects_config):
    if layout["glass_type"] == "none" or not enabled(effects_config, "glass"):
        return canvas

    glass_config = get(effects_config, "glass", default={}) or {}
    return add_glass_effect(canvas, layout["window_rect"], opacity=int(glass_config.get("opacity", 12)))


def apply_postprocess_effects(canvas, effects_config):
    if enabled(effects_config, "postprocess", "global_lighting"):
        config = get(effects_config, "postprocess", "global_lighting", default={}) or {}
        canvas = add_global_lighting(canvas, strength=float(config.get("strength", 0.04)))
    if enabled(effects_config, "postprocess", "vignette"):
        config = get(effects_config, "postprocess", "vignette", default={}) or {}
        canvas = add_vignette(canvas, strength=float(config.get("strength", 0.08)))
    if enabled(effects_config, "postprocess", "film_grain"):
        config = get(effects_config, "postprocess", "film_grain", default={}) or {}
        canvas = add_film_grain(canvas, sigma=float(config.get("sigma", 1.2)))
    if enabled(effects_config, "postprocess", "color_grade"):
        canvas = color_grade(canvas)
    if enabled(effects_config, "postprocess", "chromatic_aberration"):
        config = get(effects_config, "postprocess", "chromatic_aberration", default={}) or {}
        canvas = add_chromatic_aberration(canvas, offset=int(config.get("offset_px", 1)))
    return canvas
