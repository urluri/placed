import math
from dataclasses import asdict, dataclass
from enum import Enum

import numpy as np
from PIL import Image, ImageFilter


class ArtworkType(str, Enum):
    watercolor = "watercolor"
    photo = "photo"
    poster = "poster"
    canvas = "canvas"
    volumetric = "volumetric"


class InteriorStyle(str, Enum):
    minimal = "minimal"
    scandi = "scandi"
    japandi = "japandi"
    contemporary = "contemporary"
    loft = "loft"
    modern_vintage = "modern_vintage"
    neoclassic = "neoclassic"
    universal = "universal"


class DecorStyle(str, Enum):
    standard = "standard"
    modern = "modern"
    signature = "signature"


class SizeProfile(str, Enum):
    small = "small"
    medium = "medium"
    large = "large"
    extra_large = "extra_large"


class Tonality(str, Enum):
    light = "light"
    medium = "medium"
    dark = "dark"


class Temperature(str, Enum):
    warm = "warm"
    neutral = "neutral"
    cool = "cool"


class ChromaLevel(str, Enum):
    muted = "muted"
    medium = "medium"
    vivid = "vivid"


class Occupancy(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


@dataclass
class ColorSample:
    hex: str
    rgb: tuple[int, int, int]
    lab: tuple[float, float, float]
    family: str
    temperature: str
    lightness: str
    chroma_level: str
    chroma: float
    share: float


@dataclass
class ImagePalette:
    primary: ColorSample
    secondary: ColorSample | None
    accent: ColorSample | None
    is_monochrome: bool
    temperature: str
    lightness: str
    chroma_level: str
    frame_occupancy: str


@dataclass
class MatColor:
    id: str
    name: str
    hex: str
    rgb: tuple[int, int, int]
    lab: tuple[float, float, float]
    family: str
    temperature: str
    lightness: str
    chroma_level: str
    available: bool = True


@dataclass
class FrameOption:
    id: str
    name: str
    material: str
    color_family: str
    width_mm: int
    depth_mm: int | None
    profile: str
    hex: str
    available: bool = True


@dataclass
class MatSpec:
    enabled: bool
    outer_color: MatColor | None
    inner_color: MatColor | None
    left_mm: int
    right_mm: int
    top_mm: int
    bottom_mm: int
    overlap_mm: int
    inner_reveal_mm: int = 0


@dataclass
class GlassSpec:
    type: str
    required: bool


@dataclass
class GeometrySpec:
    size_profile: str
    aspect: str
    window_width_mm: int
    window_height_mm: int
    mat_outer_width_mm: int
    mat_outer_height_mm: int
    outer_width_mm: int
    outer_height_mm: int


@dataclass
class DecorationSpec:
    decor_style: str
    title: str
    artwork_type: str
    frame: FrameOption
    mat: MatSpec | None
    glass: GlassSpec | None
    shadow_box: bool
    geometry: GeometrySpec
    reasons: list[str]
    warnings: list[str]
    decision_tree: list[dict]


def rgb_array_to_lab(rgb):
    rgb = rgb.astype(np.float32) / 255.0
    rgb = np.where(rgb > 0.04045, ((rgb + 0.055) / 1.055) ** 2.4, rgb / 12.92)
    xyz = rgb @ np.array(
        [
            [0.4124564, 0.2126729, 0.0193339],
            [0.3575761, 0.7151522, 0.1191920],
            [0.1804375, 0.0721750, 0.9503041],
        ],
        dtype=np.float32,
    )
    xyz /= np.array([0.95047, 1.0, 1.08883], dtype=np.float32)
    f = np.where(xyz > 0.008856, np.cbrt(xyz), (7.787 * xyz) + (16 / 116))
    l = (116 * f[:, 1]) - 16
    a = 500 * (f[:, 0] - f[:, 1])
    b = 200 * (f[:, 1] - f[:, 2])
    return np.stack([l, a, b], axis=1)


def rgb_to_lab(rgb):
    return tuple(float(x) for x in rgb_array_to_lab(np.array([rgb], dtype=np.float32))[0])


def hex_to_rgb(value):
    value = value.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


def catalog_temperature_from_lab(lab):
    b = lab[2]
    if b >= 7:
        return Temperature.warm.value
    if b <= -7:
        return Temperature.cool.value
    return Temperature.neutral.value


def catalog_lightness_from_l(l_value):
    if l_value >= 68:
        return Tonality.light.value
    if l_value <= 38:
        return Tonality.dark.value
    return Tonality.medium.value


def catalog_chroma_level(chroma):
    if chroma < 14:
        return ChromaLevel.muted.value
    if chroma > 34:
        return ChromaLevel.vivid.value
    return ChromaLevel.medium.value


def mat_color(color_id, name, hex_value, family, temperature=None):
    rgb = hex_to_rgb(hex_value)
    lab = rgb_to_lab(rgb)
    chroma = math.sqrt(lab[1] * lab[1] + lab[2] * lab[2])
    return MatColor(
        color_id,
        name,
        hex_value,
        rgb,
        lab,
        family,
        temperature or catalog_temperature_from_lab(lab),
        catalog_lightness_from_l(lab[0]),
        catalog_chroma_level(chroma),
    )


MAT_CATALOG = [
    mat_color("PW001", "Museum White", "#F7F6F2", "white", "cool"),
    mat_color("PW002", "Gallery White", "#F3F2ED", "white", "neutral"),
    mat_color("PW003", "Warm White", "#F5F1E8", "white", "warm"),
    mat_color("PW004", "Ivory", "#EEE6D5", "white", "warm"),
    mat_color("PW005", "Antique White", "#E8DFCF", "white", "warm"),
    mat_color("PW006", "Linen", "#DDD4C4", "white", "warm"),
    mat_color("PW007", "Natural Cotton", "#E6DFD2", "white", "neutral"),
    mat_color("PW008", "Cream", "#F2E7D3", "white", "warm"),
    mat_color("PG101", "Soft Grey", "#E5E4E0", "light_grey"),
    mat_color("PG102", "Gallery Grey", "#DBD9D5", "light_grey"),
    mat_color("PG103", "Stone Grey", "#CFCBC5", "light_grey"),
    mat_color("PG104", "Silver Grey", "#C8C8C6", "light_grey"),
    mat_color("PG105", "Ash Grey", "#B8B8B5", "light_grey"),
    mat_color("PG106", "Mist Grey", "#D7D6D2", "light_grey"),
    mat_color("PG107", "Pearl Grey", "#D0D0CC", "light_grey"),
    mat_color("PG108", "Dove Grey", "#C5C2BB", "light_grey"),
    mat_color("PG201", "Graphite", "#55575B", "dark_grey"),
    mat_color("PG202", "Charcoal", "#4A4A4C", "dark_grey"),
    mat_color("PG203", "Slate", "#666A73", "dark_grey"),
    mat_color("PG204", "Basalt", "#5F625D", "dark_grey"),
    mat_color("PG205", "Iron Grey", "#707070", "dark_grey"),
    mat_color("PG206", "Anthracite", "#383A3D", "dark_grey"),
    mat_color("PB301", "Sand", "#D6C3A5", "beige"),
    mat_color("PB302", "Desert Sand", "#CDB59A", "beige"),
    mat_color("PB303", "Beige", "#D9C6AE", "beige"),
    mat_color("PB304", "Taupe", "#B7A79A", "beige"),
    mat_color("PB305", "Clay", "#B79B84", "beige"),
    mat_color("PB306", "Oatmeal", "#D8CBB8", "beige"),
    mat_color("PB307", "Mushroom", "#B8AA9C", "beige"),
    mat_color("PB308", "Camel", "#B6946A", "beige"),
    mat_color("PE401", "Terracotta", "#B76545", "earth"),
    mat_color("PE402", "Burnt Clay", "#A75A40", "earth"),
    mat_color("PE403", "Rust", "#964B35", "earth"),
    mat_color("PE404", "Cinnamon", "#A26A4A", "earth"),
    mat_color("PE405", "Umber", "#7C5A46", "earth"),
    mat_color("PE406", "Cocoa", "#6B4E3D", "earth"),
    mat_color("PE407", "Mocha", "#7A6756", "earth"),
    mat_color("PE408", "Chestnut", "#77523D", "earth"),
    mat_color("PG501", "Sage", "#A7B39C", "green"),
    mat_color("PG502", "Olive Grey", "#8E9378", "green"),
    mat_color("PG503", "Moss", "#707A58", "green"),
    mat_color("PG504", "Eucalyptus", "#8FA89B", "green"),
    mat_color("PG505", "Forest Mist", "#6E7C6A", "green"),
    mat_color("PG506", "Khaki", "#8C8762", "green"),
    mat_color("PG507", "Lichen", "#B2B59A", "green"),
    mat_color("PG508", "Dusty Olive", "#7A785C", "green"),
    mat_color("PB601", "Dusty Blue", "#8FA7B5", "light_blue"),
    mat_color("PB602", "Mist Blue", "#B5C2C9", "light_blue"),
    mat_color("PB603", "Steel Blue", "#758A98", "light_blue"),
    mat_color("PB604", "Blue Grey", "#8B99A3", "light_blue"),
    mat_color("PB605", "Smoke Blue", "#6D7D89", "light_blue"),
    mat_color("PB606", "Slate Blue", "#667789", "light_blue"),
    mat_color("PB607", "Ocean Mist", "#A8BCC3", "light_blue"),
    mat_color("PB608", "Ice Blue", "#D7E2E7", "light_blue"),
    mat_color("PN701", "Navy Grey", "#45556A", "blue"),
    mat_color("PN702", "Deep Indigo", "#3E4A63", "blue"),
    mat_color("PN703", "Midnight Blue", "#2F3A4A", "blue"),
    mat_color("PN704", "Denim", "#5C718A", "blue"),
    mat_color("PN705", "Petrol Blue", "#4A6672", "blue"),
    mat_color("PN706", "Ink Blue", "#35485A", "blue"),
    mat_color("PR801", "Dusty Rose", "#C49A96", "pink"),
    mat_color("PR802", "Blush", "#D9BBB3", "pink"),
    mat_color("PR803", "Nude Pink", "#D8B3A5", "pink"),
    mat_color("PR804", "Mauve", "#B799A6", "pink"),
    mat_color("PR805", "Old Rose", "#A97E7A", "pink"),
    mat_color("PR806", "Rose Clay", "#B98D82", "pink"),
    mat_color("PV901", "Lavender Grey", "#B4A9B9", "purple"),
    mat_color("PV902", "Heather", "#A58FA5", "purple"),
    mat_color("PV903", "Dusty Lilac", "#9D8BA7", "purple"),
    mat_color("PV904", "Plum Grey", "#746675", "purple"),
    mat_color("PV905", "Aubergine", "#5E4A57", "purple"),
    mat_color("PY1001", "Sand Yellow", "#D6BE78", "yellow"),
    mat_color("PY1002", "Wheat", "#D3B57C", "yellow"),
    mat_color("PY1003", "Ochre", "#C39A49", "yellow"),
    mat_color("PY1004", "Honey", "#C28B3A", "yellow"),
    mat_color("PY1005", "Mustard Grey", "#9F8A4C", "yellow"),
]


FRAME_FAMILIES = {
    "black_wood": ("чёрное дерево", "wood", "black", "#22211F", "flat", 24),
    "white_oak": ("белёный дуб", "wood", "white_oak", "#D5C5A8", "flat", 24),
    "light_oak": ("светлый дуб", "wood", "light_oak", "#B69B73", "flat", 24),
    "natural_oak": ("натуральный дуб", "wood", "natural_oak", "#A98252", "flat", 25),
    "walnut": ("орех", "wood", "walnut", "#6E4A2D", "flat", 26),
    "canvas_float_oak": ("плавающая дубовая рама", "wood", "natural_oak", "#A98252", "float", 40),
    "canvas_float_black": ("чёрная плавающая рама", "wood", "black", "#22211F", "float", 40),
    "graphite_aluminum": ("графитовый алюминий", "aluminum", "graphite", "#4C4D4A", "flat", 18),
    "black_aluminum": ("чёрный алюминий", "aluminum", "black", "#202020", "flat", 18),
    "champagne_aluminum": ("алюминий шампань", "aluminum", "champagne", "#B8A47D", "flat", 18),
    "matte_gold": ("матовое золото", "wood", "gold", "#A88645", "ornate", 24),
    "matte_silver": ("матовое серебро", "wood", "silver", "#BFC0BA", "ornate", 24),
    "deep_shadow_box_black": ("глубокая чёрная коробка", "wood", "black", "#1D1C1A", "gallery_box", 50),
    "deep_shadow_box_oak": ("глубокая дубовая коробка", "wood", "natural_oak", "#967048", "gallery_box", 50),
}


STYLE_FRAME_CANDIDATES = {
    "minimal": ["black_wood", "white_oak", "natural_oak", "graphite_aluminum"],
    "scandi": ["light_oak", "white_oak", "natural_oak"],
    "japandi": ["natural_oak", "walnut", "black_wood"],
    "contemporary": ["black_aluminum", "graphite_aluminum", "white_oak"],
    "loft": ["black_aluminum", "graphite_aluminum", "champagne_aluminum"],
    "modern_vintage": ["walnut", "champagne_aluminum", "black_wood"],
    "neoclassic": ["walnut", "matte_gold", "matte_silver"],
    "universal": ["natural_oak", "black_wood", "graphite_aluminum"],
}


MAT_PERCENT = {
    "small": {"standard": 0.35, "modern": 0.45, "signature": 0.55},
    "medium": {"standard": 0.30, "modern": 0.40, "signature": 0.50},
    "large": {"standard": 0.25, "modern": 0.35, "signature": 0.45},
    "extra_large": {"standard": 0.15, "modern": 0.18, "signature": 0.20},
}


FRAME_WIDTHS = {
    "small": {"low": (15, 10), "medium": (15, 10), "high": (20, 12)},
    "medium": {"low": (20, 12), "medium": (20, 12), "high": (30, 15)},
    "large": {"low": (30, 15), "medium": (35, 18), "high": (40, 20)},
    "extra_large": {"low": (40, 20), "medium": (50, 22), "high": (50, 25)},
}


def build_decoration_set(image_path, artwork_width_mm, artwork_height_mm, artwork_type, interior_style):
    artwork_type = normalize_artwork_type(artwork_type)
    interior_style = normalize_interior_style(interior_style)
    width = clamp_int(artwork_width_mm, 50, 3000)
    height = clamp_int(artwork_height_mm, 50, 3000)

    palette = analyze_image(image_path)
    size_profile = classify_size(width, height)
    aspect = classify_aspect(width, height)

    variants = [
        build_variant(DecorStyle.standard.value, width, height, artwork_type, interior_style, palette, size_profile, aspect),
        build_variant(DecorStyle.modern.value, width, height, artwork_type, interior_style, palette, size_profile, aspect),
        build_variant(DecorStyle.signature.value, width, height, artwork_type, interior_style, palette, size_profile, aspect),
    ]

    return {
        "image_analysis": image_analysis_payload(palette),
        "variants": [serialize_dataclass(variant) for variant in variants],
    }


def image_analysis_payload(palette):
    data = serialize_dataclass(palette)
    return {
        "palette": {
            "primary": data["primary"],
            "secondary": data["secondary"],
            "accent": data["accent"],
        },
        "temperature": data["temperature"],
        "lightness": data["lightness"],
        "chroma_level": data["chroma_level"],
        "frame_occupancy": data["frame_occupancy"],
        "is_monochrome": data["is_monochrome"],
    }


def build_variant(decor_style, width, height, artwork_type, interior_style, palette, size_profile, aspect):
    mat_enabled = decide_mat(artwork_type, decor_style, palette.frame_occupancy)
    shadow_box = artwork_type == ArtworkType.volumetric.value
    frame = choose_frame(decor_style, interior_style, artwork_type, size_profile, palette.frame_occupancy)
    mat = build_mat_spec(decor_style, width, height, artwork_type, palette, size_profile, aspect, mat_enabled, frame)
    glass = choose_glass(decor_style, artwork_type)
    geometry = build_geometry(width, height, frame.width_mm, mat, size_profile, aspect)

    reasons = build_reasons(decor_style, frame, mat, glass, palette, interior_style)
    warnings = []
    if shadow_box:
        warnings.append("Для объёмной работы нужна глубокая коробочная рама и дистанция до стекла.")
    if artwork_type == ArtworkType.canvas.value:
        warnings.append("Холст оформляется без стекла и без паспарту.")
    decision_tree = build_decision_tree(
        decor_style=decor_style,
        width=width,
        height=height,
        artwork_type=artwork_type,
        interior_style=interior_style,
        palette=palette,
        size_profile=size_profile,
        aspect=aspect,
        mat_enabled=mat_enabled,
        mat=mat,
        frame=frame,
        glass=glass,
        shadow_box=shadow_box,
        geometry=geometry,
    )

    return DecorationSpec(
        decor_style=decor_style,
        title=variant_title(decor_style),
        artwork_type=artwork_type,
        frame=frame,
        mat=mat,
        glass=glass,
        shadow_box=shadow_box,
        geometry=geometry,
        reasons=reasons,
        warnings=warnings,
        decision_tree=decision_tree,
    )


def analyze_image(image_path):
    img = Image.open(image_path).convert("RGB")
    img.thumbnail((512, 512), Image.Resampling.LANCZOS)
    arr = np.asarray(img).reshape(-1, 3)

    if len(arr) > 5000:
        idx = np.linspace(0, len(arr) - 1, 5000).astype(int)
        arr = arr[idx]

    lab = rgb_array_to_lab(arr)
    labels, centers, counts = kmeans(lab, k=6)
    order = np.argsort(counts)[::-1]
    clusters = []
    total = counts.sum()

    for idx in order:
        center_lab = centers[idx]
        rgb = lab_to_rgb(center_lab)
        chroma = float(math.sqrt(center_lab[1] ** 2 + center_lab[2] ** 2))
        share = float(counts[idx] / total)
        clusters.append(
            ColorSample(
                hex=rgb_to_hex(rgb),
                rgb=rgb,
                lab=tuple(float(round(x, 2)) for x in center_lab),
                family=color_family(center_lab),
                temperature=temperature_from_lab(center_lab),
                lightness=lightness_from_l(center_lab[0]),
                chroma_level=chroma_level(chroma),
                chroma=round(chroma, 2),
                share=round(share, 3),
            )
        )

    primary = first_meaningful_color(clusters)
    secondary = next_distinct_color(clusters, primary, min_share=0.08)
    accent = find_accent_color(clusters, primary, secondary)

    avg_lab = lab.mean(axis=0)
    avg_chroma = float(np.sqrt(lab[:, 1] ** 2 + lab[:, 2] ** 2).mean())
    monochrome = avg_chroma < 8 and max(c.chroma for c in clusters[:4]) < 14

    return ImagePalette(
        primary=primary,
        secondary=secondary,
        accent=accent,
        is_monochrome=monochrome,
        temperature=temperature_from_lab(avg_lab),
        lightness=lightness_from_l(avg_lab[0]),
        chroma_level=chroma_level(avg_chroma),
        frame_occupancy=frame_occupancy(img),
    )


def kmeans(points, k=6, iterations=8):
    if len(points) < k:
        k = len(points)
    seed_positions = np.linspace(0, len(points) - 1, k).astype(int)
    centers = points[seed_positions].astype(np.float32)

    for _ in range(iterations):
        distances = ((points[:, None, :] - centers[None, :, :]) ** 2).sum(axis=2)
        labels = distances.argmin(axis=1)
        for i in range(k):
            members = points[labels == i]
            if len(members):
                centers[i] = members.mean(axis=0)

    counts = np.bincount(labels, minlength=k)
    return labels, centers, counts


def frame_occupancy(img):
    grey = img.convert("L").filter(ImageFilter.FIND_EDGES)
    arr = np.asarray(grey).astype(np.float32)
    height, width = arr.shape
    border = max(4, int(min(width, height) * 0.15))
    mask = np.zeros_like(arr, dtype=bool)
    mask[:border, :] = True
    mask[-border:, :] = True
    mask[:, :border] = True
    mask[:, -border:] = True

    border_complexity = arr[mask].mean()
    total_complexity = arr.mean() + 1e-6
    score = border_complexity / total_complexity
    if score < 0.28:
        return Occupancy.low.value
    if score < 0.52:
        return Occupancy.medium.value
    return Occupancy.high.value


def decide_mat(artwork_type, decor_style, occupancy):
    if artwork_type == ArtworkType.canvas.value:
        return False
    if artwork_type == ArtworkType.volumetric.value:
        return False
    if artwork_type in {ArtworkType.watercolor.value, ArtworkType.photo.value}:
        return True
    if artwork_type == ArtworkType.poster.value:
        return not (occupancy == Occupancy.high.value and decor_style in {DecorStyle.modern.value, DecorStyle.signature.value})
    return True


def build_mat_spec(decor_style, width, height, artwork_type, palette, size_profile, aspect, enabled, frame):
    if not enabled:
        return MatSpec(False, None, None, 0, 0, 0, 0, 0, 0)

    short_side = min(width, height)
    percent = MAT_PERCENT[size_profile][decor_style]
    if size_profile == SizeProfile.extra_large.value:
        base = clamp_int(short_side * percent, 50, 160)
    else:
        base = clamp_int(short_side * percent, 35, 140)

    top = base
    bottom = base if aspect == "square" else int(round(base * (1.20 if decor_style == DecorStyle.signature.value else 1.15)))

    outer_color = choose_mat_color(decor_style, palette, frame)
    inner_color = None
    reveal = 0
    if decor_style == DecorStyle.signature.value:
        inner_color = choose_signature_inner_color(palette)
        reveal = 6

    return MatSpec(True, outer_color, inner_color, base, base, top, bottom, 4, reveal)


def choose_mat_color(decor_style, palette, frame=None):
    if decor_style == DecorStyle.modern.value:
        source = modern_source_color(palette)
        if source is None:
            return neutral_mat_by_temperature(palette.temperature)
        target = shift_lab_for_colored_mat(source.lab, palette.lightness, source.family, mode="modern")
        return nearest_mat_color(
            target,
            allowed_chroma={"muted", "medium"},
            exclude_too_close_to=palette.primary.lab,
            avoid_frame_lab=rgb_to_lab(hex_to_rgb(frame.hex)) if frame else None,
        )

    if decor_style == DecorStyle.signature.value:
        return choose_signature_outer_color(palette)

    preferred = standard_mat_families(palette.temperature, palette.lightness)
    candidates = sorted(
        MAT_CATALOG,
        key=lambda color: (
            0 if color.id in preferred else 8,
            0 if color.temperature == palette.temperature else 3,
            delta_e(color.lab, palette.primary.lab) * 0.04,
        ),
    )
    return candidates[0]


def choose_signature_inner_color(palette):
    if palette.is_monochrome:
        return find_mat("PG201")
    if is_minimal_image(palette):
        return find_mat("PB304")
    if palette.accent is None:
        return find_mat("PG201") if palette.temperature == Temperature.cool.value else find_mat("PB304")
    target = shift_lab_for_colored_mat(palette.accent.lab, palette.lightness, palette.accent.family, mode="signature")
    return nearest_mat_color(target, allowed_chroma={"muted", "medium"}, exclude_too_close_to=palette.primary.lab)


def choose_signature_outer_color(palette):
    if palette.is_monochrome:
        return find_mat("PW001")
    if is_minimal_image(palette):
        return find_mat("PW002")
    return choose_mat_color(DecorStyle.standard.value, palette, None)


def choose_frame(decor_style, interior_style, artwork_type, size_profile, occupancy):
    if artwork_type == ArtworkType.volumetric.value:
        family = "deep_shadow_box_oak" if interior_style in {"minimal", "scandi", "japandi"} else "deep_shadow_box_black"
    elif artwork_type == ArtworkType.canvas.value:
        family = "canvas_float_oak" if interior_style in {"scandi", "japandi", "minimal"} else "canvas_float_black"
    else:
        candidates = STYLE_FRAME_CANDIDATES.get(interior_style, STYLE_FRAME_CANDIDATES["universal"])
        family = candidates[0]
        if decor_style == DecorStyle.modern.value and len(candidates) > 1:
            family = candidates[1]
        if decor_style == DecorStyle.signature.value and len(candidates) > 2:
            family = candidates[2]

    name, material, color_family_value, hex_color, profile, depth = FRAME_FAMILIES[family]
    wood_width, aluminum_width = FRAME_WIDTHS[size_profile][occupancy]
    width = wood_width if material == "wood" else aluminum_width
    if decor_style == DecorStyle.signature.value:
        width += 5 if material == "wood" else 2

    return FrameOption(
        id=f"{family}-{width}",
        name=name,
        material=material,
        color_family=color_family_value,
        width_mm=width,
        depth_mm=depth,
        profile=profile,
        hex=hex_color,
    )


def choose_glass(decor_style, artwork_type):
    if artwork_type == ArtworkType.canvas.value:
        return GlassSpec("none", False)
    if artwork_type in {ArtworkType.watercolor.value, ArtworkType.photo.value}:
        return GlassSpec("museum", True)
    if artwork_type == ArtworkType.poster.value:
        return GlassSpec("museum" if decor_style == DecorStyle.signature.value else "ordinary", True)
    if artwork_type == ArtworkType.volumetric.value:
        return GlassSpec("museum" if decor_style == DecorStyle.signature.value else "ordinary", True)
    return GlassSpec("museum", True)


def build_geometry(width, height, frame_width, mat, size_profile, aspect):
    if mat and mat.enabled:
        window_width = width - 2 * mat.overlap_mm
        window_height = height - 2 * mat.overlap_mm
        mat_outer_width = width + mat.left_mm + mat.right_mm
        mat_outer_height = height + mat.top_mm + mat.bottom_mm
    else:
        window_width = width
        window_height = height
        mat_outer_width = width
        mat_outer_height = height

    return GeometrySpec(
        size_profile=size_profile,
        aspect=aspect,
        window_width_mm=window_width,
        window_height_mm=window_height,
        mat_outer_width_mm=mat_outer_width,
        mat_outer_height_mm=mat_outer_height,
        outer_width_mm=mat_outer_width + 2 * frame_width,
        outer_height_mm=mat_outer_height + 2 * frame_width,
    )


def renderer_geometry(spec):
    mat = spec["mat"]
    frame = spec["frame"]
    geometry = {
        "frame": frame["width_mm"],
        "passepartout": mat["left_mm"] if mat and mat["enabled"] else 0,
        "mat_left": mat["left_mm"] if mat and mat["enabled"] else 0,
        "mat_right": mat["right_mm"] if mat and mat["enabled"] else 0,
        "mat_top": mat["top_mm"] if mat and mat["enabled"] else 0,
        "mat_bottom": mat["bottom_mm"] if mat and mat["enabled"] else 0,
        "inner_reveal": mat["inner_reveal_mm"] if mat and mat["enabled"] else 0,
        "glass": "forbidden" if spec["glass"]["type"] == "none" else "required",
        "frame_color": hex_to_rgb(frame["hex"]),
    }
    if mat and mat["enabled"] and mat["outer_color"]:
        geometry["mat_color"] = hex_to_rgb(mat["outer_color"]["hex"])
    if mat and mat["enabled"] and mat["inner_color"]:
        geometry["inner_mat_color"] = hex_to_rgb(mat["inner_color"]["hex"])
    return geometry


def build_reasons(decor_style, frame, mat, glass, palette, interior_style):
    reasons = [
        f"Основа изображения: {ru_temperature(palette.temperature)}, {ru_lightness(palette.lightness)}, {ru_chroma(palette.chroma_level)}.",
        f"Рама «{frame.name}» подходит под стиль «{ru_interior_style(interior_style)}» и дает ширину {frame.width_mm} мм.",
    ]

    if mat and mat.enabled:
        reasons.append(f"Паспарту «{mat.outer_color.name}» отделяет изображение от стекла и сохраняет спокойное поле вокруг работы.")
        if mat.inner_color:
            reasons.append(f"Внутренний кант «{mat.inner_color.name}» добавляет акцент без большой цветной площади.")
    else:
        reasons.append("Паспарту не используется, потому что материал или композиция требуют более прямого оформления.")

    if glass and glass.type != "none":
        reasons.append(f"Стекло: {ru_glass_type(glass.type)}.")
    return reasons


def build_decision_tree(
    decor_style,
    width,
    height,
    artwork_type,
    interior_style,
    palette,
    size_profile,
    aspect,
    mat_enabled,
    mat,
    frame,
    glass,
    shadow_box,
    geometry,
):
    primary = palette.primary
    secondary = palette.secondary
    accent = palette.accent

    tree = [
        decision_node(
            "Входные данные",
            "Пользовательские параметры нормализованы перед расчётом.",
            [
                f"Тип работы: {ru_artwork_type(artwork_type)} (`{artwork_type}`).",
                f"Физический размер: {width} x {height} мм.",
                f"Стиль интерьера: {ru_interior_style(interior_style)} (`{interior_style}`).",
                f"Вариант оформления: {decor_style}.",
            ],
        ),
        decision_node(
            "Анализ изображения",
            "Загруженное изображение уменьшено для анализа, пиксели переведены в Lab и сгруппированы в цветовые кластеры.",
            [
                f"Основной цвет: {primary.hex}, доля {percent(primary.share)}, {ru_temperature(primary.temperature)}, {ru_lightness(primary.lightness)}, {ru_chroma(primary.chroma_level)}.",
                color_line("Второй цвет", secondary),
                color_line("Акцентный цвет", accent),
                f"Итоговая температура изображения: {ru_temperature(palette.temperature)}.",
                f"Итоговая светлота: {ru_lightness(palette.lightness)}.",
                f"Насыщенность: {ru_chroma(palette.chroma_level)}.",
                f"Занятость краёв: {ru_occupancy(palette.frame_occupancy)}.",
                f"Монохромность: {'да' if palette.is_monochrome else 'нет'}.",
            ],
        ),
        decision_node(
            "Размер и пропорции",
            "Размерный профиль определяет базовые проценты паспарту и ширину рамы.",
            [
                f"Длинная сторона {max(width, height)} мм -> профиль `{size_profile}`.",
                f"Аспект: `{aspect}`.",
                f"Для `{decor_style}` базовое паспарту = {int(MAT_PERCENT[size_profile][decor_style] * 100)}% от короткой стороны.",
            ],
        ),
        decision_node(
            "Жёсткие правила типа работы",
            artwork_rule_summary(artwork_type, decor_style, palette.frame_occupancy),
            [
                f"Паспарту: {'включено' if mat_enabled else 'выключено'}.",
                f"Стекло: {ru_glass_type(glass.type)}.",
                f"Shadow box: {'да' if shadow_box else 'нет'}.",
            ],
        ),
        decision_node(
            "Паспарту",
            mat_decision_summary(decor_style, mat, palette),
            mat_details(decor_style, mat, palette, aspect),
        ),
        decision_node(
            "Рама",
            frame_decision_summary(frame, decor_style, interior_style, artwork_type),
            [
                f"Кандидаты стиля: {', '.join(STYLE_FRAME_CANDIDATES.get(interior_style, STYLE_FRAME_CANDIDATES['universal']))}.",
                f"Выбранная рама: {frame.name}.",
                f"Материал: {material_ru(frame.material)}.",
                f"Цвет/семейство: {frame.color_family}.",
                f"Ширина: {frame.width_mm} мм.",
                f"Профиль: {frame.profile}.",
                f"Глубина: {frame.depth_mm or 'не задана'} мм.",
            ],
        ),
        decision_node(
            "Геометрия результата",
            "Все физические размеры считаются в миллиметрах; пиксели появляются только на этапе рендера.",
            [
                f"Окно: {geometry.window_width_mm} x {geometry.window_height_mm} мм.",
                f"Размер с паспарту без рамы: {geometry.mat_outer_width_mm} x {geometry.mat_outer_height_mm} мм.",
                f"Итоговый внешний размер: {geometry.outer_width_mm} x {geometry.outer_height_mm} мм.",
            ],
        ),
    ]

    return tree


def decision_node(title, result, facts):
    return {
        "title": title,
        "result": result,
        "facts": [fact for fact in facts if fact],
    }


def color_line(label, color):
    if color is None:
        return f"{label}: не найден устойчивый отдельный кластер."
    return f"{label}: {color.hex}, доля {percent(color.share)}, {ru_temperature(color.temperature)}, {ru_lightness(color.lightness)}, {ru_chroma(color.chroma_level)}."


def artwork_rule_summary(artwork_type, decor_style, occupancy):
    if artwork_type == ArtworkType.canvas.value:
        return "Холст оформляется без стекла и без паспарту; нужна рама с достаточной глубиной."
    if artwork_type == ArtworkType.volumetric.value:
        return "Объёмная работа требует стекло, глубокую коробочную раму и дистанцию до стекла; паспарту по умолчанию не используется."
    if artwork_type == ArtworkType.watercolor.value:
        return "Акварель требует паспарту и защитное стекло, лучше музейное."
    if artwork_type == ArtworkType.photo.value:
        return "Фотография получает паспарту и музейное стекло как безопасный fine-art вариант."
    if artwork_type == ArtworkType.poster.value and occupancy == Occupancy.high.value and decor_style in {DecorStyle.modern.value, DecorStyle.signature.value}:
        return "Постер с высокой занятостью краёв в modern/signature может идти без паспарту, чтобы не перегружать оформление."
    return "Постер получает паспарту и стекло как базовый безопасный вариант."


def mat_decision_summary(decor_style, mat, palette):
    if not mat or not mat.enabled:
        return "Паспарту отключено жёстким правилом или композиционной эвристикой."
    if decor_style == DecorStyle.standard.value:
        return "Standard выбирает спокойный нейтральный цвет паспарту по температуре и светлоте изображения."
    if decor_style == DecorStyle.modern.value:
        return "Modern берёт второй цвет изображения как источник, приглушает его в Lab и ищет ближайший каталоговый цвет."
    return "Signature использует нейтральное внешнее паспарту и тонкий внутренний кант по акцентному цвету."


def mat_details(decor_style, mat, palette, aspect):
    if not mat or not mat.enabled:
        return ["Поля паспарту равны 0 мм.", "Окно совпадает с физическим размером работы."]

    facts = [
        f"Внешний цвет: {mat.outer_color.name} ({mat.outer_color.hex}).",
        f"Поля: left={mat.left_mm}, right={mat.right_mm}, top={mat.top_mm}, bottom={mat.bottom_mm} мм.",
        f"Нижнее поле {'равно верхнему' if aspect == 'square' else 'увеличено относительно верхнего'}; aspect=`{aspect}`.",
        f"Перекрытие окна: {mat.overlap_mm} мм.",
    ]

    if decor_style == DecorStyle.modern.value:
        source = palette.secondary or palette.primary
        facts.append(f"Источник цвета для Modern: {'secondary' if palette.secondary else 'primary'} {source.hex}.")
        facts.append("Цвет приглушён перед поиском ближайшего цвета в MVP-каталоге паспарту.")
    if decor_style == DecorStyle.signature.value:
        if mat.inner_color:
            facts.append(f"Внутренний кант: {mat.inner_color.name} ({mat.inner_color.hex}), reveal={mat.inner_reveal_mm} мм.")
        if palette.is_monochrome:
            facts.append("Изображение монохромное, поэтому кант уходит в графит.")
        elif palette.accent:
            facts.append(f"Кант выбран от акцентного цвета {palette.accent.hex}.")
        else:
            facts.append("Акцентный цвет не найден, поэтому используется запасной нейтральный кант.")
    return facts


def frame_decision_summary(frame, decor_style, interior_style, artwork_type):
    if artwork_type == ArtworkType.volumetric.value:
        return "Рама выбрана из deep shadow-box семейства из-за объёмного типа работы."
    if artwork_type == ArtworkType.canvas.value:
        return "Рама выбрана как подходящая для холста без стекла и паспарту."
    return f"Рама выбрана из набора кандидатов для стиля «{ru_interior_style(interior_style)}»; `{decor_style}` берёт свою позицию в списке."


def ru_temperature(value):
    return {"warm": "тёплая палитра", "neutral": "нейтральная палитра", "cool": "холодная палитра"}.get(value, value)


def ru_lightness(value):
    return {"light": "светлое изображение", "medium": "средняя светлота", "dark": "тёмное изображение"}.get(value, value)


def ru_chroma(value):
    return {"muted": "приглушённые цвета", "medium": "умеренная насыщенность", "vivid": "яркие цвета"}.get(value, value)


def ru_interior_style(value):
    return {
        "minimal": "минимализм",
        "scandi": "сканди",
        "japandi": "джапанди",
        "contemporary": "contemporary",
        "loft": "лофт",
        "modern_vintage": "modern vintage",
        "neoclassic": "неоклассика",
        "universal": "универсальный",
    }.get(value, value)


def ru_glass_type(value):
    return {"ordinary": "обычное", "museum": "музейное", "uv": "UV", "none": "нет"}.get(value, value)


def ru_artwork_type(value):
    return {
        "poster": "постер",
        "photo": "фото",
        "watercolor": "акварель",
        "canvas": "холст",
        "volumetric": "объёмная работа",
    }.get(value, value)


def ru_occupancy(value):
    return {"low": "низкая", "medium": "средняя", "high": "высокая"}.get(value, value)


def material_ru(value):
    return {"wood": "дерево", "aluminum": "алюминий"}.get(value, value)


def percent(value):
    return f"{round(value * 100, 1)}%"


def variant_title(decor_style):
    return {
        "standard": "Standard: спокойная мастерская база",
        "modern": "Modern: современный цветовой ответ",
        "signature": "Signature: акцентное оформление",
    }[decor_style]


def classify_size(width, height):
    longer = max(width, height)
    if longer <= 420:
        return SizeProfile.small.value
    if longer <= 700:
        return SizeProfile.medium.value
    if longer <= 1000:
        return SizeProfile.large.value
    return SizeProfile.extra_large.value


def classify_aspect(width, height):
    ratio = width / height
    if 0.92 <= ratio <= 1.08:
        return "square"
    if ratio > 1.8 or ratio < 0.55:
        return "panoramic"
    if ratio < 0.92:
        return "portrait"
    return "landscape"


def standard_mat_families(temperature, lightness):
    if temperature == Temperature.warm.value:
        if lightness == Tonality.light.value:
            return ["PW004", "PW003"]
        if lightness == Tonality.medium.value:
            return ["PW003", "PW004"]
        return ["PW003", "PW001"]
    if temperature == Temperature.cool.value:
        return ["PW001", "PW002"] if lightness != Tonality.medium.value else ["PW002", "PG101"]
    return ["PW002", "PW001"]


def neutral_mat_by_temperature(temperature):
    if temperature == Temperature.warm.value:
        return find_mat("PW003")
    if temperature == Temperature.cool.value:
        return find_mat("PW001")
    return find_mat("PW002")


def modern_source_color(palette):
    if is_expressive_mat_source(palette.secondary):
        return palette.secondary
    if palette.accent is not None:
        return palette.accent
    return None


def is_expressive_mat_source(color):
    if color is None:
        return False
    if color.family in {"white", "black", "grey", "light_grey", "dark_grey"}:
        return False
    if color.chroma <= 10:
        return False
    return color.lab[0] >= 32


def is_minimal_image(palette):
    return palette.primary.share > 0.70


def shift_lab_for_colored_mat(lab, image_lightness, family, mode):
    l, a, b = lab
    if image_lightness == Tonality.light.value:
        l -= 15
    elif image_lightness == Tonality.dark.value:
        l += 15

    factor = chroma_factor_for_mat(family, mode)
    return (clamp_float(l, 18, 90), a * factor, b * factor)


def chroma_factor_for_mat(family, mode):
    if mode == "signature":
        return 0.40
    if family in {"red", "brown", "earth", "yellow", "pink"}:
        return 0.25
    if family in {"green", "blue", "light_blue", "grey", "light_grey", "dark_grey"}:
        return 0.45
    return 0.35


def nearest_mat_color(target_lab, allowed_chroma=None, exclude_too_close_to=None, avoid_frame_lab=None):
    candidates = [color for color in MAT_CATALOG if color.available]
    if allowed_chroma:
        candidates = [color for color in candidates if color.chroma_level in allowed_chroma]

    def score(color):
        distance = delta_e(color.lab, target_lab)
        if exclude_too_close_to:
            image_distance = delta_e(color.lab, exclude_too_close_to)
            if image_distance < 6:
                distance += 80
            elif image_distance < 10:
                distance += 35
        if avoid_frame_lab:
            frame_distance = delta_e(color.lab, avoid_frame_lab)
            if frame_distance < 8:
                distance += 55
            elif frame_distance < 12:
                distance += 25
        return distance

    return min(candidates, key=score)


def find_mat(color_id):
    return next(color for color in MAT_CATALOG if color.id == color_id)


def first_meaningful_color(clusters):
    for color in clusters:
        l = color.lab[0]
        if color.share > 0.12 and not (l > 94 or l < 6):
            return color
    return clusters[0]


def next_distinct_color(clusters, primary, min_share):
    for color in clusters:
        if color.share >= min_share and delta_e(color.lab, primary.lab) >= 12:
            return color
    return None


def find_accent_color(clusters, primary, secondary):
    if primary.share > 0.70:
        return None

    scored = []
    for color in clusters:
        if color is primary or color is secondary:
            continue
        if color.share < 0.02 or color.share > 0.15:
            continue
        if color.chroma_level == ChromaLevel.muted.value:
            continue
        distance = delta_e(color.lab, primary.lab)
        if distance < 18:
            continue
        scored.append((color.chroma, color))
    if not scored:
        return None
    return max(scored, key=lambda item: item[0])[1]


def temperature_from_lab(lab):
    b = lab[2]
    if b >= 7:
        return Temperature.warm.value
    if b <= -7:
        return Temperature.cool.value
    return Temperature.neutral.value


def lightness_from_l(l_value):
    if l_value >= 68:
        return Tonality.light.value
    if l_value <= 38:
        return Tonality.dark.value
    return Tonality.medium.value


def chroma_level(chroma):
    if chroma < 14:
        return ChromaLevel.muted.value
    if chroma > 34:
        return ChromaLevel.vivid.value
    return ChromaLevel.medium.value


def color_family(lab):
    l, a, b = lab
    chroma = math.sqrt(a * a + b * b)
    hue = math.degrees(math.atan2(b, a))
    if l > 88 and chroma < 12:
        return "white"
    if l < 22 and chroma < 16:
        return "black"
    if chroma < 12:
        return "grey"
    if -35 <= hue < 30:
        return "red"
    if 30 <= hue < 75:
        return "brown"
    if 75 <= hue < 125:
        return "yellow"
    if 125 <= hue < 190:
        return "green"
    if -160 <= hue < -35:
        return "blue"
    return "purple"


def delta_e(a, b):
    return float(np.linalg.norm(np.asarray(a, dtype=np.float32) - np.asarray(b, dtype=np.float32)))


def rgb_to_hex(rgb):
    return "#{:02X}{:02X}{:02X}".format(*rgb)


def lab_to_rgb(lab):
    l, a, b = lab
    fy = (l + 16) / 116
    fx = a / 500 + fy
    fz = fy - b / 200
    xyz = np.array([fx, fy, fz], dtype=np.float32)
    xyz = np.where(xyz ** 3 > 0.008856, xyz ** 3, (xyz - 16 / 116) / 7.787)
    xyz *= np.array([0.95047, 1.0, 1.08883], dtype=np.float32)
    rgb = xyz @ np.array(
        [
            [3.2404542, -1.5371385, -0.4985314],
            [-0.9692660, 1.8760108, 0.0415560],
            [0.0556434, -0.2040259, 1.0572252],
        ],
        dtype=np.float32,
    )
    rgb = np.clip(rgb, 0, 1)
    rgb = np.where(rgb > 0.0031308, 1.055 * (rgb ** (1 / 2.4)) - 0.055, 12.92 * rgb)
    rgb = np.clip(np.round(rgb * 255), 0, 255).astype(int)
    return tuple(int(x) for x in rgb)


def serialize_dataclass(value):
    if isinstance(value, Enum):
        return value.value
    if hasattr(value, "__dataclass_fields__"):
        return {key: serialize_dataclass(item) for key, item in asdict(value).items()}
    if isinstance(value, list):
        return [serialize_dataclass(item) for item in value]
    if isinstance(value, dict):
        return {key: serialize_dataclass(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return list(value)
    return value


def normalize_artwork_type(value):
    value = str(value or "").strip()
    if value not in {item.value for item in ArtworkType}:
        return ArtworkType.poster.value
    return value


def normalize_interior_style(value):
    aliases = {
        "minimalism": "minimal",
        "scandic": "scandi",
        "ModernVintage": "modern_vintage",
        "classic": "neoclassic",
    }
    value = aliases.get(str(value), str(value))
    if value not in {item.value for item in InteriorStyle}:
        return InteriorStyle.universal.value
    return value


def clamp_int(value, low, high):
    return max(low, min(high, int(round(float(value)))))


def clamp_float(value, low, high):
    return max(low, min(high, float(value)))
