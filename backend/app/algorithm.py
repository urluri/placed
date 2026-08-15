from dataclasses import asdict, dataclass
from enum import Enum
from math import sqrt

from .image_analysis import analyze_image


class DecorStyle(str, Enum):
    standard = "standard"
    signature = "signature"


SIZE_PROFILE_LABELS = {
    "small": "малый",
    "medium": "средний",
    "large": "большой",
    "extra_large": "очень большой",
}

ARTWORK_TYPE_LABELS = {
    "poster": "постер",
    "photo": "фото",
    "watercolor": "акварель",
    "engraving": "гравюра",
    "botanical": "ботаническая иллюстрация",
    "canvas": "холст",
    "volumetric": "объемная работа",
}

CONSTRUCTIVE_RULES = {
    "watercolor": {"glass_required": True, "glass_type": "museum", "mat": "always", "shadow_box": False},
    "photo": {"glass_required": True, "glass_type": "museum", "mat": "always", "shadow_box": False},
    "engraving": {"glass_required": True, "glass_type": "museum", "mat": "always", "shadow_box": False},
    "botanical": {"glass_required": True, "glass_type": "museum", "mat": "always", "shadow_box": False},
    "poster": {"glass_required": True, "glass_type": "regular", "mat": "vote", "shadow_box": False},
    "canvas": {"glass_required": False, "glass_type": "none", "mat": "never", "shadow_box": False},
    "volumetric": {"glass_required": True, "glass_type": "museum", "mat": "always", "shadow_box": True},
}

POSTER_OCCUPANCY_VOTES = {
    "low": 2,
    "medium": 1,
    "high": -1,
}

POSTER_SIZE_PROFILE_VOTES = {
    "small": 2,
    "medium": 2,
    "large": 1,
    "extra_large": -1,
}

MAT_SIZE_PERCENTAGES = {
    "small": {"standard": 0.35, "signature": 0.35},
    "medium": {"standard": 0.25, "signature": 0.25},
    "large": {"standard": 0.15, "signature": 0.15},
    "extra_large": {"standard": 0.10, "signature": 0.10},
}

MAT_SIZE_MAX_MM = {
    "small": {"standard": None, "signature": None},
    "medium": {"standard": None, "signature": None},
    "large": {"standard": None, "signature": None},
    "extra_large": {"standard": 70, "signature": 70},
}

SIGNATURE_INNER_MAT_RATIO = 0.8
MAT_WINDOW_OVERLAP_MM = 5
ACCENT_SIMILAR_DELTA_E = 22
ACCENT_SAME_FAMILY_DELTA_E = 24
NEUTRAL_COLOR_FAMILIES = {"white", "grey", "black"}
INNER_MAT_MIN_L = 25
INNER_MAT_MAX_DARKER_THAN_IMAGE = 20
INNER_MAT_GRAPHITE_TARGET_L = 34

PLACED_PALETTE = {
    "PW001": {"id": "PW001", "name": "Museum White", "hex": "#F7F6F2", "family": "white", "role": "base_white"},
    "PW002": {"id": "PW002", "name": "Gallery White", "hex": "#F3F2ED", "family": "white", "role": "base_white"},
    "PW003": {"id": "PW003", "name": "Warm White", "hex": "#F5F1E8", "family": "white", "role": "base_white"},
    "PW004": {"id": "PW004", "name": "Ivory", "hex": "#EEE6D5", "family": "white", "role": "base_white"},
    "PW005": {"id": "PW005", "name": "Antique White", "hex": "#E8DFCF", "family": "white", "role": "base_white"},
    "PW006": {"id": "PW006", "name": "Linen", "hex": "#DDD4C4", "family": "beige", "role": "base_white"},
    "PW007": {"id": "PW007", "name": "Natural Cotton", "hex": "#E6DFD2", "family": "white", "role": "base_white"},
    "PW008": {"id": "PW008", "name": "Cream", "hex": "#F2E7D3", "family": "white", "role": "base_white"},
    "PG101": {"id": "PG101", "name": "Soft Grey", "hex": "#E5E4E0", "family": "grey", "role": "soft_neutral"},
    "PG102": {"id": "PG102", "name": "Gallery Grey", "hex": "#DBD9D5", "family": "grey", "role": "soft_neutral"},
    "PG103": {"id": "PG103", "name": "Stone Grey", "hex": "#CFCBC5", "family": "grey", "role": "soft_neutral"},
    "PG104": {"id": "PG104", "name": "Silver Grey", "hex": "#C8C8C6", "family": "grey", "role": "soft_neutral"},
    "PG105": {"id": "PG105", "name": "Ash Grey", "hex": "#B8B8B5", "family": "grey", "role": "soft_neutral"},
    "PG106": {"id": "PG106", "name": "Mist Grey", "hex": "#D7D6D2", "family": "grey", "role": "soft_neutral"},
    "PG107": {"id": "PG107", "name": "Pearl Grey", "hex": "#D0D0CC", "family": "grey", "role": "soft_neutral"},
    "PG108": {"id": "PG108", "name": "Dove Grey", "hex": "#C5C2BB", "family": "grey", "role": "soft_neutral"},
    "PG201": {"id": "PG201", "name": "Graphite", "hex": "#55575B", "family": "grey", "role": "deep_neutral"},
    "PG202": {"id": "PG202", "name": "Charcoal", "hex": "#4A4A4C", "family": "grey", "role": "deep_neutral"},
    "PG203": {"id": "PG203", "name": "Slate", "hex": "#666A73", "family": "grey", "role": "deep_neutral"},
    "PG204": {"id": "PG204", "name": "Basalt", "hex": "#5F625D", "family": "grey", "role": "deep_neutral"},
    "PG205": {"id": "PG205", "name": "Iron Grey", "hex": "#707070", "family": "grey", "role": "deep_neutral"},
    "PG206": {"id": "PG206", "name": "Anthracite", "hex": "#383A3D", "family": "grey", "role": "deep_neutral"},
    "PB301": {"id": "PB301", "name": "Sand", "hex": "#D6C3A5", "family": "beige", "role": "soft_neutral"},
    "PB302": {"id": "PB302", "name": "Desert Sand", "hex": "#CDB59A", "family": "beige", "role": "soft_neutral"},
    "PB303": {"id": "PB303", "name": "Beige", "hex": "#D9C6AE", "family": "beige", "role": "soft_neutral"},
    "PB304": {"id": "PB304", "name": "Taupe", "hex": "#B7A79A", "family": "beige", "role": "soft_neutral"},
    "PB305": {"id": "PB305", "name": "Clay", "hex": "#B79B84", "family": "beige", "role": "soft_neutral"},
    "PB306": {"id": "PB306", "name": "Oatmeal", "hex": "#D8CBB8", "family": "beige", "role": "soft_neutral"},
    "PB307": {"id": "PB307", "name": "Mushroom", "hex": "#B8AA9C", "family": "beige", "role": "soft_neutral"},
    "PB308": {"id": "PB308", "name": "Camel", "hex": "#B6946A", "family": "beige", "role": "soft_neutral"},
    "PE401": {"id": "PE401", "name": "Terracotta", "hex": "#B76545", "family": "earth", "role": "deep_color"},
    "PE402": {"id": "PE402", "name": "Burnt Clay", "hex": "#A75A40", "family": "earth", "role": "deep_color"},
    "PE403": {"id": "PE403", "name": "Rust", "hex": "#964B35", "family": "earth", "role": "deep_color"},
    "PE404": {"id": "PE404", "name": "Cinnamon", "hex": "#A26A4A", "family": "earth", "role": "deep_color"},
    "PE405": {"id": "PE405", "name": "Umber", "hex": "#7C5A46", "family": "earth", "role": "deep_color"},
    "PE406": {"id": "PE406", "name": "Cocoa", "hex": "#6B4E3D", "family": "earth", "role": "deep_color"},
    "PE407": {"id": "PE407", "name": "Mocha", "hex": "#7A6756", "family": "earth", "role": "deep_color"},
    "PE408": {"id": "PE408", "name": "Chestnut", "hex": "#77523D", "family": "earth", "role": "deep_color"},
    "PG501": {"id": "PG501", "name": "Sage", "hex": "#A7B39C", "family": "green", "role": "soft_color"},
    "PG502": {"id": "PG502", "name": "Olive Grey", "hex": "#8E9378", "family": "green", "role": "soft_color"},
    "PG503": {"id": "PG503", "name": "Moss", "hex": "#707A58", "family": "green", "role": "deep_color"},
    "PG504": {"id": "PG504", "name": "Eucalyptus", "hex": "#8FA89B", "family": "green", "role": "soft_color"},
    "PG505": {"id": "PG505", "name": "Forest Mist", "hex": "#6E7C6A", "family": "green", "role": "deep_color"},
    "PG506": {"id": "PG506", "name": "Khaki", "hex": "#8C8762", "family": "green", "role": "soft_color"},
    "PG507": {"id": "PG507", "name": "Lichen", "hex": "#B2B59A", "family": "green", "role": "soft_color"},
    "PG508": {"id": "PG508", "name": "Dusty Olive", "hex": "#7A785C", "family": "green", "role": "deep_color"},
    "PB601": {"id": "PB601", "name": "Dusty Blue", "hex": "#8FA7B5", "family": "blue", "role": "soft_color"},
    "PB602": {"id": "PB602", "name": "Mist Blue", "hex": "#B5C2C9", "family": "blue", "role": "soft_color"},
    "PB603": {"id": "PB603", "name": "Steel Blue", "hex": "#758A98", "family": "blue", "role": "soft_color"},
    "PB604": {"id": "PB604", "name": "Blue Grey", "hex": "#8B99A3", "family": "blue", "role": "soft_color"},
    "PB605": {"id": "PB605", "name": "Smoke Blue", "hex": "#6D7D89", "family": "blue", "role": "deep_color"},
    "PB606": {"id": "PB606", "name": "Slate Blue", "hex": "#667789", "family": "blue", "role": "deep_color"},
    "PB607": {"id": "PB607", "name": "Ocean Mist", "hex": "#A8BCC3", "family": "blue", "role": "soft_color"},
    "PB608": {"id": "PB608", "name": "Ice Blue", "hex": "#D7E2E7", "family": "blue", "role": "soft_color"},
    "PN701": {"id": "PN701", "name": "Navy Grey", "hex": "#45556A", "family": "navy", "role": "deep_color"},
    "PN702": {"id": "PN702", "name": "Deep Indigo", "hex": "#3E4A63", "family": "navy", "role": "deep_color"},
    "PN703": {"id": "PN703", "name": "Midnight Blue", "hex": "#2F3A4A", "family": "navy", "role": "deep_color"},
    "PN704": {"id": "PN704", "name": "Denim", "hex": "#5C718A", "family": "navy", "role": "deep_color"},
    "PN705": {"id": "PN705", "name": "Petrol Blue", "hex": "#4A6672", "family": "navy", "role": "deep_color"},
    "PN706": {"id": "PN706", "name": "Ink Blue", "hex": "#35485A", "family": "navy", "role": "deep_color"},
    "PR801": {"id": "PR801", "name": "Dusty Rose", "hex": "#C49A96", "family": "rose", "role": "soft_color"},
    "PR802": {"id": "PR802", "name": "Blush", "hex": "#D9BBB3", "family": "rose", "role": "soft_color"},
    "PR803": {"id": "PR803", "name": "Nude Pink", "hex": "#D8B3A5", "family": "rose", "role": "soft_color"},
    "PR804": {"id": "PR804", "name": "Mauve", "hex": "#B799A6", "family": "rose", "role": "soft_color"},
    "PR805": {"id": "PR805", "name": "Old Rose", "hex": "#A97E7A", "family": "rose", "role": "soft_color"},
    "PR806": {"id": "PR806", "name": "Rose Clay", "hex": "#B98D82", "family": "rose", "role": "soft_color"},
    "PV901": {"id": "PV901", "name": "Lavender Grey", "hex": "#B4A9B9", "family": "violet", "role": "soft_color"},
    "PV902": {"id": "PV902", "name": "Heather", "hex": "#A58FA5", "family": "violet", "role": "soft_color"},
    "PV903": {"id": "PV903", "name": "Dusty Lilac", "hex": "#9D8BA7", "family": "violet", "role": "soft_color"},
    "PV904": {"id": "PV904", "name": "Plum Grey", "hex": "#746675", "family": "violet", "role": "deep_color"},
    "PV905": {"id": "PV905", "name": "Aubergine", "hex": "#5E4A57", "family": "violet", "role": "deep_color"},
    "PY1001": {"id": "PY1001", "name": "Sand Yellow", "hex": "#D6BE78", "family": "yellow", "role": "accent"},
    "PY1002": {"id": "PY1002", "name": "Wheat", "hex": "#D3B57C", "family": "yellow", "role": "accent"},
    "PY1003": {"id": "PY1003", "name": "Ochre", "hex": "#C39A49", "family": "yellow", "role": "accent"},
    "PY1004": {"id": "PY1004", "name": "Honey", "hex": "#C28B3A", "family": "yellow", "role": "accent"},
    "PY1005": {"id": "PY1005", "name": "Mustard Grey", "hex": "#9F8A4C", "family": "yellow", "role": "accent"},
}

DEFAULT_MAT_COLOR = PLACED_PALETTE["PW003"]

MAT_COLOR_OPTIONS = {
    "warm_white": PLACED_PALETTE["PW003"],
    "museum_white": PLACED_PALETTE["PW001"],
}

FRAME_LIBRARY = {
    "black_aluminum": {
        "id": "black_aluminum",
        "name": "Черный алюминий",
        "material": "aluminum",
        "color_family": "black",
        "tone": "dark",
        "hex": "#111111",
    },
    "black_wood": {
        "id": "black_wood",
        "name": "Черное дерево",
        "material": "wood",
        "color_family": "black",
        "tone": "dark",
        "hex": "#111111",
    },
    "white_wood": {
        "id": "white_wood",
        "name": "Белое дерево",
        "material": "wood",
        "color_family": "white",
        "tone": "light",
        "hex": "#F4F1EA",
    },
    "champagne_aluminum": {
        "id": "champagne_aluminum",
        "name": "Шампань",
        "material": "aluminum",
        "color_family": "champagne",
        "tone": "light",
        "hex": "#D8B65C",
    },
    "silver_aluminum": {
        "id": "silver_aluminum",
        "name": "Серебро",
        "material": "aluminum",
        "color_family": "silver",
        "tone": "light",
        "hex": "#BFC3C7",
    },
    "light_oak": {
        "id": "light_oak",
        "name": "Светлый дуб",
        "material": "wood",
        "color_family": "oak",
        "tone": "light",
        "hex": "#D4B789",
    },
    "oak": {
        "id": "oak",
        "name": "Дуб",
        "material": "wood",
        "color_family": "oak",
        "tone": "medium",
        "hex": "#A6753F",
    },
    "walnut": {
        "id": "walnut",
        "name": "Орех",
        "material": "wood",
        "color_family": "walnut",
        "tone": "medium",
        "hex": "#6F4A2D",
    },
    "dark_walnut": {
        "id": "dark_walnut",
        "name": "Темный орех",
        "material": "wood",
        "color_family": "walnut",
        "tone": "dark",
        "hex": "#3B281D",
    },
    "gold": {
        "id": "gold",
        "name": "Золото",
        "material": "wood",
        "color_family": "gold",
        "tone": "medium",
        "hex": "#C3A15A",
    },
}

FRAME_STYLE_ORDER = {
    "minimal": ["black_aluminum", "white_wood", "champagne_aluminum", "silver_aluminum"],
    "contemporary": ["black_aluminum", "champagne_aluminum", "walnut", "oak", "white_wood", "light_oak", "silver_aluminum"],
    "scandi": ["light_oak", "white_wood", "oak", "champagne_aluminum", "black_wood"],
    "japandi": ["light_oak", "oak", "walnut"],
    "modern_vintage": ["walnut", "oak", "dark_walnut"],
    "loft": ["black_aluminum", "dark_walnut", "champagne_aluminum", "silver_aluminum"],
    "neoclassic": ["walnut", "dark_walnut", "gold"],
}

FRAME_MATERIAL_RULES = {
    "poster": ("aluminum", "wood"),
    "photo": ("aluminum", "wood"),
    "watercolor": ("wood", "aluminum"),
    "engraving": ("wood", "aluminum"),
    "botanical": ("wood", "aluminum"),
    "canvas": ("wood", None),
    "volumetric": ("wood", None),
}

FRAME_WIDTHS_MM = {
    "small": {
        "low": {"wood": 15, "aluminum": 10},
        "medium": {"wood": 15, "aluminum": 10},
        "high": {"wood": 20, "aluminum": 12},
    },
    "medium": {
        "low": {"wood": 15, "aluminum": 10},
        "medium": {"wood": 20, "aluminum": 12},
        "high": {"wood": 20, "aluminum": 12},
    },
    "large": {
        "low": {"wood": 20, "aluminum": 12},
        "medium": {"wood": 30, "aluminum": 15},
        "high": {"wood": 30, "aluminum": 15},
    },
    "extra_large": {
        "low": {"wood": 30, "aluminum": 15},
        "medium": {"wood": 40, "aluminum": 20},
        "high": {"wood": 50, "aluminum": 20},
    },
}

FRAME_LIGHTNESS_TONES = {
    "light": ["light"],
    "medium": ["medium"],
    "dark": ["dark", "medium"],
}

FRAME_MONOCHROME_IDS = {"black_aluminum", "black_wood", "white_wood", "silver_aluminum"}
FRAME_MONOCHROME_FALLBACK_ORDER = ["black_aluminum", "black_wood", "white_wood", "silver_aluminum"]
FRAME_NEOCLASSIC_MONOCHROME_FALLBACK_ORDER = ["black_wood", "white_wood"]
FRAME_HIGH_CHROMA_IDS = {"black_aluminum", "black_wood", "white_wood", "light_oak", "oak"}
FRAME_LOFT_LIGHT_WATERCOLOR_IDS = {"black_aluminum"}
BLACK_FRAME_IDS = {"black_aluminum", "black_wood"}
BLACK_FRAME_ALLOWED_STYLES = {"minimal", "loft", "contemporary"}
BLACK_FRAME_EXCLUDED_STYLES = {"scandi", "japandi", "modern_vintage", "neoclassic"}
WHITE_FRAME_ID = "white_wood"
SILVER_FRAME_ID = "silver_aluminum"
SILVER_FRAME_ALLOWED_STYLES = {"minimal", "contemporary"}
SILVER_FRAME_EXCLUDED_STYLES = {"japandi", "modern_vintage", "neoclassic"}
WALNUT_FRAME_ID = "walnut"
WALNUT_FRAME_ALLOWED_STYLES = {"modern_vintage", "neoclassic"}
WALNUT_FRAME_EXCLUDED_STYLES = {"scandi", "minimal"}
DARK_WALNUT_FRAME_ID = "dark_walnut"
DARK_WALNUT_FRAME_ALLOWED_STYLES = {"modern_vintage", "neoclassic"}
DARK_WALNUT_FRAME_EXCLUDED_STYLES = {"scandi", "japandi", "minimal"}
OAK_FRAME_ID = "oak"
OAK_FRAME_ALLOWED_STYLES = {"scandi", "japandi", "contemporary"}
OAK_FRAME_EXCLUDED_STYLES = {"loft", "neoclassic"}
LIGHT_OAK_FRAME_ID = "light_oak"
LIGHT_OAK_FRAME_ALLOWED_STYLES = {"scandi", "japandi"}
LIGHT_OAK_FRAME_EXCLUDED_STYLES = {"loft", "neoclassic"}
LIGHT_NEUTRAL_LOW_CONTRAST_FRAME_BY_STYLE = {
    "minimal": WHITE_FRAME_ID,
    "contemporary": WHITE_FRAME_ID,
    "loft": "black",
    "scandi": LIGHT_OAK_FRAME_ID,
    "japandi": LIGHT_OAK_FRAME_ID,
    "neoclassic": WALNUT_FRAME_ID,
    "modern_vintage": WALNUT_FRAME_ID,
}
BOTANICAL_WARM_FRAME_BY_STYLE = {
    "scandi": LIGHT_OAK_FRAME_ID,
    "minimal": WHITE_FRAME_ID,
    "contemporary": OAK_FRAME_ID,
    "japandi": OAK_FRAME_ID,
    "neoclassic": WALNUT_FRAME_ID,
    "modern_vintage": WALNUT_FRAME_ID,
    "loft": WALNUT_FRAME_ID,
}
BOTANICAL_COLD_FRAME_BY_STYLE = {
    "scandi": LIGHT_OAK_FRAME_ID,
    "japandi": LIGHT_OAK_FRAME_ID,
    "contemporary": LIGHT_OAK_FRAME_ID,
    "minimal": LIGHT_OAK_FRAME_ID,
    "neoclassic": DARK_WALNUT_FRAME_ID,
    "loft": DARK_WALNUT_FRAME_ID,
    "modern_vintage": DARK_WALNUT_FRAME_ID,
}


@dataclass
class FrameOption:
    id: str
    name: str
    material: str
    color_family: str
    tone: str
    width_mm: int
    depth_mm: int | None
    profile: str
    hex: str
    available: bool = True


@dataclass
class MatSpec:
    enabled: bool
    outer_color: dict | None
    inner_color: dict | None
    left_mm: int
    right_mm: int
    top_mm: int
    bottom_mm: int
    overlap_mm: int
    inner_reveal_mm: int = 0
    inner_reveal_left_mm: int = 0
    inner_reveal_right_mm: int = 0
    inner_reveal_top_mm: int = 0
    inner_reveal_bottom_mm: int = 0


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
    mat: MatSpec
    glass: GlassSpec
    shadow_box: bool
    geometry: GeometrySpec
    reasons: list[str]
    warnings: list[str]
    decision_tree: list[dict]


def build_decoration_set(
    image_path,
    artwork_width_mm,
    artwork_height_mm,
    artwork_type,
    interior_style,
    mat_size_config=None,
):
    width = clamp_int(artwork_width_mm, 50, 3000)
    height = clamp_int(artwork_height_mm, 50, 3000)
    image_analysis = analyze_image(image_path)
    mat_size_config = normalize_mat_size_config(mat_size_config)

    variants = [
        build_placeholder_variant(DecorStyle.standard.value, width, height, artwork_type, interior_style, image_analysis, mat_size_config),
        build_placeholder_variant(DecorStyle.signature.value, width, height, artwork_type, interior_style, image_analysis, mat_size_config),
    ]

    return {
        "image_analysis": image_analysis,
        "variants": [serialize_dataclass(variant) for variant in variants],
    }


def build_placeholder_variant(decor_style, width, height, artwork_type, interior_style, image_analysis, mat_size_config):
    normalized_type = normalize_artwork_type(artwork_type)
    size_profile = classify_size_profile(width, height)
    constructive = constructive_decision(normalized_type, size_profile, image_analysis)
    frame_decision = build_frame_decision(normalized_type, interior_style, size_profile, image_analysis)
    frame = frame_decision["frame"]
    mat = build_mat_spec(constructive["mat_enabled"], decor_style, size_profile, width, height, image_analysis, mat_size_config)
    glass = GlassSpec(type=constructive["glass_type"], required=constructive["glass_required"])
    geometry = build_geometry(width, height, frame.width_mm, mat, size_profile)

    return DecorationSpec(
        decor_style=decor_style,
        title=placeholder_title(decor_style),
        artwork_type=normalized_type,
        frame=frame,
        mat=mat,
        glass=glass,
        shadow_box=constructive["shadow_box"],
        geometry=geometry,
        reasons=[
            constructive["reason"],
            mat_reason(mat, decor_style, size_profile, mat_size_config) if mat.enabled else "Паспарту не используется.",
            frame_decision["reason"],
        ],
        warnings=[],
        decision_tree=[
            {
                "title": "Входные данные",
                "result": "Пользовательские параметры используются как физический размер работы.",
                "facts": [
                    f"Тип работы: {ARTWORK_TYPE_LABELS.get(normalized_type, normalized_type)}.",
                    f"Физический размер: {width} x {height} мм.",
                    f"Размерный профиль: {SIZE_PROFILE_LABELS[size_profile]}.",
                    f"Стиль интерьера: {interior_style}.",
                    f"Вариант оформления: {decor_style}.",
                ],
            },
            {
                "title": "Конструктив",
                "result": constructive["reason"],
                "facts": constructive["facts"],
            },
            {
                "title": "Размер паспарту",
                "result": mat_reason(mat, decor_style, size_profile, mat_size_config) if mat.enabled else "Расчет не требуется.",
                "facts": mat_facts(mat, decor_style, size_profile, width, height, mat_size_config),
            },
            {
                "title": "Расчеты изображения",
                "result": "Вычислены наблюдаемые характеристики изображения для выбора паспарту и рамы.",
                "facts": analysis_facts(image_analysis),
            },
            {
                "title": "Рама",
                "result": frame_decision["reason"],
                "facts": frame_decision["facts"],
            },
            {
                "title": "Цвета",
                "result": mat_color_reason(mat, decor_style, image_analysis) if mat.enabled else "Цвет паспарту не рассчитывается.",
                "facts": color_facts(mat, decor_style, image_analysis),
            }
        ],
    )


def build_frame_decision(artwork_type, interior_style, size_profile, image_analysis):
    normalized_style = normalize_frame_interior_style(interior_style)
    candidates = frame_candidates_for_style(normalized_style)
    facts = [
        f"Нормализованный стиль интерьера: {normalized_style}.",
        f"Базовый порядок: {frame_ids(candidates)}.",
    ]

    if normalized_style != "neoclassic":
        candidates = [candidate for candidate in candidates if candidate["id"] != "gold"]
        facts.append("Hard-фильтр: золото исключено вне неоклассики.")
    else:
        candidates = [candidate for candidate in candidates if candidate["material"] != "aluminum"]
        facts.append("Hard-фильтр: в неоклассике исключены алюминиевые рамы.")

    if artwork_type in {"canvas", "volumetric"}:
        candidates = [candidate for candidate in candidates if candidate["material"] == "wood"]
        facts.append(f"Hard-фильтр: для типа «{ARTWORK_TYPE_LABELS.get(artwork_type, artwork_type)}» оставлены только деревянные рамы.")

    if size_profile == "extra_large":
        candidates = [candidate for candidate in candidates if candidate["id"] != "white_wood"]
        facts.append("Hard-фильтр: для очень большого размера белая деревянная рама исключена.")

    if is_monochrome_image(image_analysis):
        candidates, used_fallback = monochrome_frame_candidates(candidates, normalized_style, size_profile)
        facts.append(
            "Hard-фильтр: монохромное изображение ограничено черными, белыми и серебристыми рамами."
            if not used_fallback
            else "Hard-фильтр: монохромное изображение ограничено черными, белыми и серебристыми рамами; базовый список заменен допустимым резервом."
        )

    lightness = normalize_visual_level(image_analysis.get("lightness"))
    temperature = normalize_temperature(image_analysis.get("temperature"))
    contrast_level = normalize_level(image_analysis.get("contrast"))
    occupancy_level = normalize_level(image_analysis.get("frame_occupancy"))

    targeted_frame_rule = targeted_frame_rule_for_image(
        artwork_type=artwork_type,
        normalized_style=normalized_style,
        lightness=lightness,
        temperature=temperature,
        contrast_level=contrast_level,
    )
    targeted_rule_selected = False
    if targeted_frame_rule:
        targeted_candidate = candidate_for_targeted_rule(
            targeted_frame_rule["frame_id"],
            artwork_type,
            candidates,
            normalized_style=normalized_style,
            size_profile=size_profile,
        )
        if targeted_candidate:
            candidates = [targeted_candidate]
            targeted_rule_selected = True
            facts.append(targeted_frame_rule["reason"])

    black_rule_active = black_frame_rule_applies(normalized_style=normalized_style)
    black_exclusion_reasons = black_frame_exclusion_reasons(normalized_style=normalized_style)
    if not targeted_rule_selected and not black_rule_active and any(candidate["id"] in BLACK_FRAME_IDS for candidate in candidates):
        candidates = [candidate for candidate in candidates if candidate["id"] not in BLACK_FRAME_IDS]
        if black_exclusion_reasons:
            facts.append(f"Hard-фильтр: черная рама исключена ({', '.join(black_exclusion_reasons)}).")
        else:
            facts.append("Hard-фильтр: условия правила черной рамы выполнены не полностью, черные рамы исключены.")

    black_rule_selected = False
    if not targeted_rule_selected and black_rule_active:
        black_candidate = black_frame_candidate(artwork_type, candidates)
        if black_candidate:
            candidates = [black_candidate]
            black_rule_selected = True
            facts.append(
                "Приоритетное правило черной рамы: стиль minimal/loft/contemporary. "
                "Выбрана черная рама."
            )

    silver_rule_active = silver_frame_rule_applies(
        normalized_style=normalized_style,
        temperature=temperature,
        image_analysis=image_analysis,
    )
    silver_exclusion_reasons = silver_frame_exclusion_reasons(
        normalized_style=normalized_style,
        temperature=temperature,
    )
    if not targeted_rule_selected and not silver_rule_active and any(candidate["id"] == SILVER_FRAME_ID for candidate in candidates):
        candidates = [candidate for candidate in candidates if candidate["id"] != SILVER_FRAME_ID]
        if silver_exclusion_reasons:
            facts.append(f"Hard-фильтр: серебряная рама исключена ({', '.join(silver_exclusion_reasons)}).")
        else:
            facts.append("Hard-фильтр: условия правила серебряной рамы выполнены не полностью, silver_aluminum исключена.")

    silver_rule_selected = False
    if not targeted_rule_selected and not black_rule_selected and silver_rule_active and any(candidate["id"] == SILVER_FRAME_ID for candidate in candidates):
        candidates = [FRAME_LIBRARY[SILVER_FRAME_ID]]
        silver_rule_selected = True
        facts.append(
            "Приоритетное правило серебряной рамы: монохромное изображение, температура cold/neutral "
            "и стиль minimal/contemporary. Выбрана silver_aluminum."
        )

    dark_walnut_rule_active = dark_walnut_frame_rule_applies(
        normalized_style=normalized_style,
        lightness=lightness,
        contrast_level=contrast_level,
        temperature=temperature,
    )
    dark_walnut_exclusion_reasons = dark_walnut_frame_exclusion_reasons(
        normalized_style=normalized_style,
        lightness=lightness,
        contrast_level=contrast_level,
        temperature=temperature,
    )
    if not targeted_rule_selected and not dark_walnut_rule_active and any(candidate["id"] == DARK_WALNUT_FRAME_ID for candidate in candidates):
        candidates = [candidate for candidate in candidates if candidate["id"] != DARK_WALNUT_FRAME_ID]
        if dark_walnut_exclusion_reasons:
            facts.append(f"Hard-фильтр: рама темный орех исключена ({', '.join(dark_walnut_exclusion_reasons)}).")
        else:
            facts.append("Hard-фильтр: условия правила темного ореха выполнены не полностью, dark_walnut исключена.")

    dark_walnut_rule_selected = False
    if (
        not targeted_rule_selected
        and not black_rule_selected
        and not silver_rule_selected
        and dark_walnut_rule_active
        and any(candidate["id"] == DARK_WALNUT_FRAME_ID for candidate in candidates)
    ):
        candidates = [FRAME_LIBRARY[DARK_WALNUT_FRAME_ID]]
        dark_walnut_rule_selected = True
        if normalized_style in {"modern_vintage", "neoclassic"} and temperature == "cold":
            facts.append(
                "Приоритетное правило темного ореха: стиль modern_vintage/neoclassic и холодная температура. "
                "Выбрана dark_walnut."
            )
        else:
            facts.append(
                "Приоритетное правило темного ореха: стиль modern_vintage/neoclassic, "
                "светлота dark и контраст high. Выбрана dark_walnut."
            )

    walnut_rule_active = walnut_frame_rule_applies(
        normalized_style=normalized_style,
        temperature=temperature,
        occupancy_level=occupancy_level,
    )
    walnut_exclusion_reasons = walnut_frame_exclusion_reasons(
        normalized_style=normalized_style,
        temperature=temperature,
        occupancy_level=occupancy_level,
    )
    if not targeted_rule_selected and not walnut_rule_active and any(candidate["id"] == WALNUT_FRAME_ID for candidate in candidates):
        candidates = [candidate for candidate in candidates if candidate["id"] != WALNUT_FRAME_ID]
        if walnut_exclusion_reasons:
            facts.append(f"Hard-фильтр: рама орех исключена ({', '.join(walnut_exclusion_reasons)}).")
        else:
            facts.append("Hard-фильтр: условия правила ореха выполнены не полностью, walnut исключена.")

    walnut_rule_selected = False
    if (
        not targeted_rule_selected
        and not black_rule_selected
        and not silver_rule_selected
        and not dark_walnut_rule_selected
        and walnut_rule_active
        and any(candidate["id"] == WALNUT_FRAME_ID for candidate in candidates)
    ):
        candidates = [FRAME_LIBRARY[WALNUT_FRAME_ID]]
        walnut_rule_selected = True
        facts.append(
            "Приоритетное правило ореха: стиль modern_vintage/neoclassic, теплая температура "
            "и заполненность не low. Выбрана walnut."
        )

    oak_rule_active = oak_frame_rule_applies(
        normalized_style=normalized_style,
        lightness=lightness,
        temperature=temperature,
        contrast_level=contrast_level,
    )
    oak_exclusion_reasons = oak_frame_exclusion_reasons(
        normalized_style=normalized_style,
        lightness=lightness,
        temperature=temperature,
        contrast_level=contrast_level,
    )
    if not targeted_rule_selected and not oak_rule_active and any(candidate["id"] == OAK_FRAME_ID for candidate in candidates):
        candidates = [candidate for candidate in candidates if candidate["id"] != OAK_FRAME_ID]
        if oak_exclusion_reasons:
            facts.append(f"Hard-фильтр: рама дуб исключена ({', '.join(oak_exclusion_reasons)}).")
        else:
            facts.append("Hard-фильтр: условия правила дуба выполнены не полностью, oak исключена.")

    oak_rule_selected = False
    if (
        not targeted_rule_selected
        and not black_rule_selected
        and not silver_rule_selected
        and not dark_walnut_rule_selected
        and not walnut_rule_selected
        and oak_rule_active
        and any(candidate["id"] == OAK_FRAME_ID for candidate in candidates)
    ):
        candidates = [FRAME_LIBRARY[OAK_FRAME_ID]]
        oak_rule_selected = True
        facts.append(
            "Приоритетное правило дуба: стиль scandi/japandi/contemporary, температура warm/neutral "
            "и светлота medium. Выбрана oak."
        )

    champagne_exclusion_reasons = []
    if normalized_style == "loft":
        champagne_exclusion_reasons.append("стиль loft")
    if lightness == "dark":
        champagne_exclusion_reasons.append("темная работа")
    if temperature == "cold":
        champagne_exclusion_reasons.append("холодная температура")
    if not targeted_rule_selected and champagne_exclusion_reasons:
        candidates = [candidate for candidate in candidates if candidate["id"] != "champagne_aluminum"]
        facts.append(f"Hard-фильтр: рама шампань исключена ({', '.join(champagne_exclusion_reasons)}).")

    champagne_rule_active = champagne_frame_rule_applies(
        normalized_style=normalized_style,
        lightness=lightness,
        temperature=temperature,
        contrast_level=contrast_level,
        image_analysis=image_analysis,
    )
    if not targeted_rule_selected and not champagne_rule_active and any(candidate["id"] == "champagne_aluminum" for candidate in candidates):
        candidates = [candidate for candidate in candidates if candidate["id"] != "champagne_aluminum"]
        facts.append("Hard-фильтр: условия правила шампани выполнены не полностью, champagne_aluminum исключена.")

    champagne_rule_selected = False
    if not targeted_rule_selected and not black_rule_selected and not dark_walnut_rule_selected and not walnut_rule_selected and not oak_rule_selected and champagne_rule_active and any(candidate["id"] == "champagne_aluminum" for candidate in candidates):
        candidates = [FRAME_LIBRARY["champagne_aluminum"]]
        champagne_rule_selected = True
        facts.append(
            "Приоритетное правило шампани: светлота light/medium, температура warm/neutral, "
            "стиль minimal/contemporary и контраст low/medium. Выбрана champagne_aluminum."
        )

    chroma_level = normalize_level(image_analysis.get("chroma_level"))

    light_oak_rule_active = light_oak_frame_rule_applies(
        normalized_style=normalized_style,
        lightness=lightness,
        contrast_level=contrast_level,
    )
    light_oak_exclusion_reasons = light_oak_frame_exclusion_reasons(
        normalized_style=normalized_style,
        lightness=lightness,
        contrast_level=contrast_level,
    )
    if not targeted_rule_selected and not light_oak_rule_active and any(candidate["id"] == LIGHT_OAK_FRAME_ID for candidate in candidates):
        candidates = [candidate for candidate in candidates if candidate["id"] != LIGHT_OAK_FRAME_ID]
        if light_oak_exclusion_reasons:
            facts.append(f"Hard-фильтр: рама светлый дуб исключена ({', '.join(light_oak_exclusion_reasons)}).")
        else:
            facts.append("Hard-фильтр: условия правила светлого дуба выполнены не полностью, light_oak исключена.")

    light_oak_rule_selected = False
    if not targeted_rule_selected and not dark_walnut_rule_selected and not walnut_rule_selected and not oak_rule_selected and not champagne_rule_selected and not silver_rule_selected and not black_rule_selected and light_oak_rule_active:
        light_oak_candidate = next((candidate for candidate in candidates if candidate["id"] == LIGHT_OAK_FRAME_ID), None)
        if light_oak_candidate:
            candidates = [light_oak_candidate]
            light_oak_rule_selected = True
            facts.append(
                "Приоритетное правило светлого дуба: стиль scandi/japandi, светлота light/medium "
                "и контраст low/medium. Выбрана light_oak."
            )

    white_rule_active = white_frame_rule_applies(
        normalized_style=normalized_style,
        lightness=lightness,
        contrast_level=contrast_level,
        chroma_level=chroma_level,
    )
    white_exclusion_reasons = white_frame_exclusion_reasons(
        normalized_style=normalized_style,
        lightness=lightness,
        contrast_level=contrast_level,
        chroma_level=chroma_level,
    )
    if not targeted_rule_selected and white_exclusion_reasons and any(candidate["id"] == WHITE_FRAME_ID for candidate in candidates):
        candidates = [candidate for candidate in candidates if candidate["id"] != WHITE_FRAME_ID]
        facts.append(f"Hard-фильтр: белая рама исключена ({', '.join(white_exclusion_reasons)}).")

    white_rule_selected = False
    if not targeted_rule_selected and not dark_walnut_rule_selected and not walnut_rule_selected and not oak_rule_selected and not champagne_rule_selected and not silver_rule_selected and not black_rule_selected and not light_oak_rule_selected and white_rule_active:
        white_candidate = next((candidate for candidate in candidates if candidate["id"] == WHITE_FRAME_ID), None)
        if white_candidate:
            candidates = [white_candidate]
            white_rule_selected = True
            facts.append(
                "Приоритетное правило белой рамы: светлота light, контраст low/medium и стиль scandi. "
                "Выбрана white_wood."
            )

    if chroma_level == "high" and not targeted_rule_selected and not dark_walnut_rule_selected and not walnut_rule_selected and not oak_rule_selected and not champagne_rule_selected and not silver_rule_selected and not black_rule_selected and not light_oak_rule_selected and not white_rule_selected:
        candidates, applied = optional_frame_filter(candidates, FRAME_HIGH_CHROMA_IDS)
        facts.append(
            "Hard-фильтр: высокая насыщенность изображения ограничила выбор нейтральными рамами."
            if applied
            else "Hard-фильтр высокой насыщенности пропущен: после предыдущих условий не осталось бы кандидатов."
        )
    elif chroma_level == "high" and targeted_rule_selected:
        facts.append("Hard-фильтр высокой насыщенности пропущен: активировано целевое правило выбора рамы.")
    elif chroma_level == "high" and dark_walnut_rule_selected:
        facts.append("Hard-фильтр высокой насыщенности пропущен: активировано приоритетное правило темного ореха.")
    elif chroma_level == "high" and walnut_rule_selected:
        facts.append("Hard-фильтр высокой насыщенности пропущен: активировано приоритетное правило ореха.")
    elif chroma_level == "high" and oak_rule_selected:
        facts.append("Hard-фильтр высокой насыщенности пропущен: активировано приоритетное правило дуба.")
    elif chroma_level == "high" and champagne_rule_selected:
        facts.append("Hard-фильтр высокой насыщенности пропущен: активировано приоритетное правило шампани.")
    elif chroma_level == "high" and silver_rule_selected:
        facts.append("Hard-фильтр высокой насыщенности пропущен: активировано приоритетное правило серебряной рамы.")
    elif chroma_level == "high" and black_rule_selected:
        facts.append("Hard-фильтр высокой насыщенности пропущен: активировано приоритетное правило черной рамы.")
    elif chroma_level == "high" and light_oak_rule_selected:
        facts.append("Hard-фильтр высокой насыщенности пропущен: активировано приоритетное правило светлого дуба.")
    elif chroma_level == "high":
        facts.append("Hard-фильтр высокой насыщенности пропущен: активировано приоритетное правило белой рамы.")

    if normalized_style == "loft" and artwork_type == "watercolor" and lightness == "light":
        candidates, applied = optional_frame_filter(candidates, FRAME_LOFT_LIGHT_WATERCOLOR_IDS)
        facts.append(
            "Hard-фильтр: светлая акварель в лофте ограничена черным алюминием и темным орехом."
            if applied
            else "Hard-фильтр светлой акварели в лофте пропущен: после предыдущих условий не осталось бы кандидатов."
        )

    if targeted_rule_selected:
        facts.append("Материал и светлота не меняют выбор: целевое правило уже зафиксировало раму.")
    elif dark_walnut_rule_selected:
        facts.append("Материал и светлота не меняют выбор: приоритетное правило уже зафиксировало раму темный орех.")
    elif walnut_rule_selected:
        facts.append("Материал и светлота не меняют выбор: приоритетное правило уже зафиксировало раму орех.")
    elif oak_rule_selected:
        facts.append("Материал и светлота не меняют выбор: приоритетное правило уже зафиксировало раму дуб.")
    elif champagne_rule_selected:
        facts.append("Материал и светлота не меняют выбор: приоритетное правило уже зафиксировало раму шампань.")
    elif silver_rule_selected:
        facts.append("Материал и светлота не меняют выбор: приоритетное правило уже зафиксировало серебряную раму.")
    elif black_rule_selected:
        facts.append("Материал и светлота не меняют выбор: приоритетное правило уже зафиксировало черную раму.")
    elif light_oak_rule_selected:
        facts.append("Материал и светлота не меняют выбор: приоритетное правило уже зафиксировало раму светлый дуб.")
    elif white_rule_selected:
        facts.append("Материал и светлота не меняют выбор: приоритетное правило уже зафиксировало белую раму.")
    else:
        material_preference, _material_fallback = FRAME_MATERIAL_RULES.get(artwork_type, FRAME_MATERIAL_RULES["poster"])
        preferred_material_candidates = [
            candidate for candidate in candidates if candidate["material"] == material_preference
        ]
        if preferred_material_candidates:
            candidates = preferred_material_candidates
            facts.append(f"Материал по типу работы: выбран приоритет {material_preference}.")
        else:
            facts.append(f"Материал по типу работы: приоритет {material_preference} недоступен, оставлен текущий список.")

        lightness_candidates = filter_by_frame_lightness(candidates, lightness)
        if lightness_candidates:
            candidates = lightness_candidates
            facts.append(f"Светлота изображения {lightness}: применен фильтр рамы {frame_ids(candidates)}.")
        else:
            facts.append(f"Светлота изображения {lightness}: фильтр отменен, потому что список стал бы пустым.")

    if candidates:
        selected = candidates[0]
    else:
        selected = fallback_frame_candidate(normalized_style, artwork_type, size_profile)
        facts.append(f"Резервный выбор: {selected['id']}.")

    width_mm = FRAME_WIDTHS_MM[size_profile][occupancy_level][selected["material"]]
    profile = frame_profile(selected)
    depth_mm = frame_depth(width_mm, selected["material"])
    frame = FrameOption(
        id=selected["id"],
        name=selected["name"],
        material=selected["material"],
        color_family=selected["color_family"],
        tone=selected["tone"],
        width_mm=width_mm,
        depth_mm=depth_mm,
        profile=profile,
        hex=selected["hex"],
    )
    facts.extend(
        [
            f"Итоговая рама: {frame.name} ({frame.id}), {frame.hex}.",
            f"Ширина профиля: {width_mm} мм по размерному профилю {size_profile}, заполненности {occupancy_level} и материалу {frame.material}.",
            f"Профиль: {profile}.",
        ]
    )

    return {
        "frame": frame,
        "reason": f"Рама выбрана по документу «Рама»: {frame.name}, {frame.width_mm} мм.",
        "facts": facts,
    }


def normalize_frame_interior_style(value):
    normalized = str(value or "").strip().lower()
    aliases = {
        "minimal": "minimal",
        "minimalism": "minimal",
        "минимализм": "minimal",
        "scandi": "scandi",
        "сканди": "scandi",
        "japandi": "japandi",
        "джапанди": "japandi",
        "contemporary": "contemporary",
        "современный": "contemporary",
        "loft": "loft",
        "лофт": "loft",
        "modern_vintage": "modern_vintage",
        "modern-vintage": "modern_vintage",
        "винтаж": "modern_vintage",
        "neoclassic": "neoclassic",
        "неоклассика": "neoclassic",
        "universal": "contemporary",
        "универсальный": "contemporary",
    }
    return aliases.get(normalized, "contemporary")


def frame_candidates_for_style(interior_style):
    frame_ids_for_style = FRAME_STYLE_ORDER.get(interior_style, FRAME_STYLE_ORDER["contemporary"])
    return [FRAME_LIBRARY[frame_id] for frame_id in frame_ids_for_style]


def fallback_frame_candidate(normalized_style, artwork_type, size_profile):
    candidates = frame_candidates_for_style(normalized_style)
    if normalized_style in BLACK_FRAME_EXCLUDED_STYLES:
        candidates = [candidate for candidate in candidates if candidate["id"] not in BLACK_FRAME_IDS]
    if normalized_style != "neoclassic":
        candidates = [candidate for candidate in candidates if candidate["id"] != "gold"]
    else:
        candidates = [candidate for candidate in candidates if candidate["material"] != "aluminum"]
    if artwork_type in {"canvas", "volumetric"}:
        candidates = [candidate for candidate in candidates if candidate["material"] == "wood"]
    if size_profile == "extra_large":
        candidates = [candidate for candidate in candidates if candidate["id"] != "white_wood"]
    if candidates:
        return candidates[0]
    if normalized_style in BLACK_FRAME_EXCLUDED_STYLES:
        return FRAME_LIBRARY["walnut"]
    return FRAME_LIBRARY["black_wood" if artwork_type in {"canvas", "volumetric"} else "black_aluminum"]


def frame_ids(candidates):
    return ", ".join(candidate["id"] for candidate in candidates) if candidates else "нет кандидатов"


def optional_frame_filter(candidates, allowed_ids):
    filtered = [candidate for candidate in candidates if candidate["id"] in allowed_ids]
    if not filtered:
        return candidates, False
    return filtered, True


def monochrome_frame_candidates(candidates, normalized_style, size_profile):
    filtered = [candidate for candidate in candidates if candidate["id"] in FRAME_MONOCHROME_IDS]
    if filtered:
        return filtered, False

    fallback_order = (
        FRAME_NEOCLASSIC_MONOCHROME_FALLBACK_ORDER
        if normalized_style == "neoclassic"
        else FRAME_MONOCHROME_FALLBACK_ORDER
    )
    fallback = [FRAME_LIBRARY[frame_id] for frame_id in fallback_order]
    if normalized_style == "neoclassic":
        fallback = [candidate for candidate in fallback if candidate["material"] != "aluminum"]
    if size_profile == "extra_large":
        fallback = [candidate for candidate in fallback if candidate["id"] != "white_wood"]
    if fallback:
        return fallback, True

    reserve_id = "black_wood" if normalized_style == "neoclassic" else "black_aluminum"
    return [FRAME_LIBRARY[reserve_id]], True


def filter_by_frame_lightness(candidates, lightness):
    for tone in FRAME_LIGHTNESS_TONES.get(lightness, FRAME_LIGHTNESS_TONES["medium"]):
        filtered = [candidate for candidate in candidates if candidate["tone"] == tone]
        if filtered:
            return filtered
    return []


def is_monochrome_image(image_analysis):
    raw_value = str(image_analysis.get("monochrome") or "").strip().lower()
    return raw_value in {"monochrome", "mono", "монохромное", "монохромный", "true", "yes"}


def normalize_temperature(value):
    normalized = str(value or "").strip().lower()
    if normalized in {"warm", "теплый", "тёплый", "teplyy"}:
        return "warm"
    if normalized in {"cold", "холодный", "holodnyy"}:
        return "cold"
    return "neutral"


def champagne_frame_rule_applies(normalized_style, lightness, temperature, contrast_level, image_analysis):
    if normalized_style not in {"minimal", "contemporary"}:
        return False
    if is_monochrome_image(image_analysis):
        return False
    return (
        lightness in {"light", "medium"}
        and temperature in {"warm", "neutral"}
        and contrast_level in {"low", "medium"}
    )


def silver_frame_exclusion_reasons(normalized_style, temperature):
    reasons = []
    if temperature == "warm":
        reasons.append("теплая температура")
    if normalized_style in SILVER_FRAME_EXCLUDED_STYLES:
        reasons.append(f"стиль {normalized_style}")
    return reasons


def silver_frame_rule_applies(normalized_style, temperature, image_analysis):
    if normalized_style not in SILVER_FRAME_ALLOWED_STYLES:
        return False
    if silver_frame_exclusion_reasons(normalized_style, temperature):
        return False
    return is_monochrome_image(image_analysis) and temperature in {"cold", "neutral"}


def dark_walnut_frame_exclusion_reasons(normalized_style, lightness, contrast_level, temperature=None):
    reasons = []
    if normalized_style in DARK_WALNUT_FRAME_EXCLUDED_STYLES:
        reasons.append(f"стиль {normalized_style}")
    if normalized_style in {"modern_vintage", "neoclassic"} and temperature == "cold":
        return reasons
    if contrast_level == "low":
        reasons.append("низкий контраст")
    if lightness == "light":
        reasons.append("высокая светлота")
    return reasons


def dark_walnut_frame_rule_applies(normalized_style, lightness, contrast_level, temperature=None):
    if normalized_style not in DARK_WALNUT_FRAME_ALLOWED_STYLES:
        return False
    if dark_walnut_frame_exclusion_reasons(normalized_style, lightness, contrast_level, temperature=temperature):
        return False
    if normalized_style in {"modern_vintage", "neoclassic"} and temperature == "cold":
        return True
    return lightness == "dark" and contrast_level == "high"


def walnut_frame_exclusion_reasons(normalized_style, temperature, occupancy_level):
    reasons = []
    if normalized_style in WALNUT_FRAME_EXCLUDED_STYLES:
        reasons.append(f"стиль {normalized_style}")
    if temperature == "cold":
        reasons.append("холодная температура")
    if occupancy_level == "low":
        reasons.append("низкая заполненность")
    return reasons


def walnut_frame_rule_applies(normalized_style, temperature, occupancy_level):
    if normalized_style not in WALNUT_FRAME_ALLOWED_STYLES:
        return False
    if walnut_frame_exclusion_reasons(normalized_style, temperature, occupancy_level):
        return False
    return temperature == "warm"


def oak_frame_exclusion_reasons(normalized_style, lightness, temperature, contrast_level):
    reasons = []
    if temperature == "cold":
        reasons.append("холодная температура")
    if normalized_style in OAK_FRAME_EXCLUDED_STYLES:
        reasons.append(f"стиль {normalized_style}")
    if contrast_level == "high":
        reasons.append("высокий контраст")
    return reasons


def oak_frame_rule_applies(normalized_style, lightness, temperature, contrast_level):
    if normalized_style not in OAK_FRAME_ALLOWED_STYLES:
        return False
    if oak_frame_exclusion_reasons(normalized_style, lightness, temperature, contrast_level):
        return False
    return temperature in {"warm", "neutral"} and lightness == "medium"


def targeted_frame_rule_for_image(artwork_type, normalized_style, lightness, temperature, contrast_level):
    if artwork_type == "botanical":
        if temperature == "warm":
            frame_id = BOTANICAL_WARM_FRAME_BY_STYLE.get(normalized_style)
            if frame_id:
                return {
                    "frame_id": frame_id,
                    "reason": (
                        "Целевое правило ботанической иллюстрации: температура warm; "
                        f"для стиля {normalized_style} выбрана рама {frame_id}."
                    ),
                }
        if temperature == "cold":
            frame_id = BOTANICAL_COLD_FRAME_BY_STYLE.get(normalized_style)
            if frame_id:
                return {
                    "frame_id": frame_id,
                    "reason": (
                        "Целевое правило ботанической иллюстрации: температура cold; "
                        f"для стиля {normalized_style} выбрана рама {frame_id}."
                    ),
                }

    if lightness in {"light", "medium"} and temperature == "neutral" and contrast_level in {"low", "medium"}:
        frame_id = LIGHT_NEUTRAL_LOW_CONTRAST_FRAME_BY_STYLE.get(normalized_style)
        if frame_id:
            return {
                "frame_id": frame_id,
                "reason": (
                    "Целевое правило светлой/средней нейтральной малоконтрастной работы: "
                    f"для стиля {normalized_style} выбрана рама {frame_id}."
                ),
            }

    return None


def candidate_for_targeted_rule(frame_id, artwork_type, candidates, normalized_style, size_profile):
    if frame_id == "black":
        return black_frame_candidate(artwork_type, candidates)

    candidate = next((candidate for candidate in candidates if candidate["id"] == frame_id), None)
    if candidate:
        return candidate

    if frame_id in FRAME_LIBRARY and frame_allowed_by_hard_constraints(
        FRAME_LIBRARY[frame_id],
        normalized_style=normalized_style,
        artwork_type=artwork_type,
        size_profile=size_profile,
    ):
        return FRAME_LIBRARY[frame_id]
    return None


def frame_allowed_by_hard_constraints(frame, normalized_style, artwork_type, size_profile):
    if normalized_style != "neoclassic" and frame["id"] == "gold":
        return False
    if normalized_style == "neoclassic" and frame["material"] == "aluminum":
        return False
    if artwork_type in {"canvas", "volumetric"} and frame["material"] != "wood":
        return False
    if size_profile == "extra_large" and frame["id"] == WHITE_FRAME_ID:
        return False
    return True


def black_frame_exclusion_reasons(normalized_style):
    reasons = []
    if normalized_style in BLACK_FRAME_EXCLUDED_STYLES:
        reasons.append(f"стиль {normalized_style}")
    return reasons


def black_frame_rule_applies(normalized_style):
    if normalized_style not in BLACK_FRAME_ALLOWED_STYLES:
        return False
    if black_frame_exclusion_reasons(normalized_style):
        return False
    return True


def black_frame_candidate(artwork_type, candidates):
    preferred_id = "black_wood" if artwork_type in {"canvas", "volumetric", "engraving"} else "black_aluminum"
    fallback_id = "black_aluminum" if preferred_id == "black_wood" else "black_wood"
    by_id = {candidate["id"]: candidate for candidate in candidates}
    if preferred_id in by_id:
        return by_id[preferred_id]
    if fallback_id in by_id and artwork_type not in {"canvas", "volumetric"}:
        return by_id[fallback_id]
    return FRAME_LIBRARY[preferred_id]


def light_oak_frame_exclusion_reasons(normalized_style, lightness, contrast_level):
    reasons = []
    if lightness == "dark":
        reasons.append("низкая светлота")
    if contrast_level == "high":
        reasons.append("высокий контраст")
    if normalized_style in LIGHT_OAK_FRAME_EXCLUDED_STYLES:
        reasons.append(f"стиль {normalized_style}")
    return reasons


def light_oak_frame_rule_applies(normalized_style, lightness, contrast_level):
    if normalized_style not in LIGHT_OAK_FRAME_ALLOWED_STYLES:
        return False
    if light_oak_frame_exclusion_reasons(normalized_style, lightness, contrast_level):
        return False
    return lightness in {"light", "medium"} and contrast_level in {"low", "medium"}


def white_frame_exclusion_reasons(normalized_style, lightness, contrast_level, chroma_level):
    reasons = []
    if lightness == "dark":
        reasons.append("низкая светлота")
    if chroma_level == "high":
        reasons.append("высокая насыщенность")
    if contrast_level == "high":
        reasons.append("высокий контраст")
    if normalized_style == "loft":
        reasons.append("стиль loft")
    return reasons


def white_frame_rule_applies(normalized_style, lightness, contrast_level, chroma_level):
    if normalized_style != "scandi":
        return False
    if white_frame_exclusion_reasons(normalized_style, lightness, contrast_level, chroma_level):
        return False
    return lightness == "light" and contrast_level in {"low", "medium"}


def frame_profile(frame):
    if frame["material"] == "aluminum":
        return "flat"
    if frame["id"] == "gold":
        return "classic"
    return "natural_wood"


def frame_depth(width_mm, material):
    if material == "aluminum":
        return max(12, width_mm + 4)
    return max(20, width_mm + 8)


def constructive_decision(artwork_type, size_profile, image_analysis):
    rule = CONSTRUCTIVE_RULES.get(artwork_type, CONSTRUCTIVE_RULES["poster"])
    mat_mode = rule["mat"]
    facts = [
        f"Стекло: {'да' if rule['glass_required'] else 'нет'}.",
        f"Тип стекла: {glass_type_label(rule['glass_type'])}.",
        f"Shadow box: {'да' if rule['shadow_box'] else 'нет'}.",
    ]

    if mat_mode == "always":
        facts.append("Паспарту: да, согласно правилу для типа работы.")
        return {
            "mat_enabled": True,
            "glass_required": rule["glass_required"],
            "glass_type": rule["glass_type"],
            "shadow_box": rule["shadow_box"],
            "reason": f"Для типа работы «{ARTWORK_TYPE_LABELS.get(artwork_type, artwork_type)}» паспарту используется согласно таблице конструктивных правил.",
            "facts": facts,
        }

    if mat_mode == "never":
        facts.append("Паспарту: нет, согласно правилу для типа работы.")
        return {
            "mat_enabled": False,
            "glass_required": rule["glass_required"],
            "glass_type": rule["glass_type"],
            "shadow_box": rule["shadow_box"],
            "reason": f"Для типа работы «{ARTWORK_TYPE_LABELS.get(artwork_type, artwork_type)}» паспарту не используется согласно таблице конструктивных правил.",
            "facts": facts,
        }

    occupancy_level = normalize_level(image_analysis.get("frame_occupancy"))
    occupancy_vote = POSTER_OCCUPANCY_VOTES[occupancy_level]
    size_vote = POSTER_SIZE_PROFILE_VOTES[size_profile]
    total_vote = occupancy_vote + size_vote
    mat_enabled = total_vote >= 1
    facts.extend(
        [
            f"Постер: решение по паспарту принимается голосованием.",
            f"Заполненность кадра: {occupancy_level}, голос {occupancy_vote}.",
            f"Размерный профиль: {SIZE_PROFILE_LABELS[size_profile]}, голос {size_vote}.",
            f"Сумма голосов: {total_vote}.",
            f"Итог: {'использовать паспарту' if mat_enabled else 'без паспарту'}.",
        ]
    )

    return {
        "mat_enabled": mat_enabled,
        "glass_required": rule["glass_required"],
        "glass_type": rule["glass_type"],
        "shadow_box": rule["shadow_box"],
        "reason": (
            f"Для постера сумма голосов за паспарту равна {total_vote}; порог включения - 1 и больше; "
            f"{'паспарту используется' if mat_enabled else 'паспарту не используется'}."
        ),
        "facts": facts,
    }


def build_mat_spec(enabled, decor_style, size_profile, width, height, image_analysis, mat_size_config=None):
    if not enabled:
        return MatSpec(
            enabled=False,
            outer_color=None,
            inner_color=None,
            left_mm=0,
            right_mm=0,
            top_mm=0,
            bottom_mm=0,
            overlap_mm=0,
            inner_reveal_mm=0,
            inner_reveal_left_mm=0,
            inner_reveal_right_mm=0,
            inner_reveal_top_mm=0,
            inner_reveal_bottom_mm=0,
        )

    mat_size_config = normalize_mat_size_config(mat_size_config)
    size_style = mat_size_style_for_geometry(decor_style)
    base_size = mat_base_size(width, height, size_style, size_profile, mat_size_config)
    bottom_size = int(round(base_size * 1.1))
    inner_color = signature_inner_mat_color(image_analysis) if decor_style == DecorStyle.signature.value else None
    inner_reveal_left = signature_inner_reveal(base_size) if inner_color else 0
    inner_reveal_right = signature_inner_reveal(base_size) if inner_color else 0
    inner_reveal_top = signature_inner_reveal(base_size) if inner_color else 0
    inner_reveal_bottom = signature_inner_reveal(bottom_size) if inner_color else 0

    return MatSpec(
        enabled=True,
        outer_color=mat_color_for_variant(decor_style, image_analysis),
        inner_color=inner_color,
        left_mm=base_size,
        right_mm=base_size,
        top_mm=base_size,
        bottom_mm=bottom_size,
        overlap_mm=MAT_WINDOW_OVERLAP_MM,
        inner_reveal_mm=inner_reveal_top,
        inner_reveal_left_mm=inner_reveal_left,
        inner_reveal_right_mm=inner_reveal_right,
        inner_reveal_top_mm=inner_reveal_top,
        inner_reveal_bottom_mm=inner_reveal_bottom,
    )


def signature_inner_reveal(outer_field_mm):
    reveal = int(round(outer_field_mm * (1 - SIGNATURE_INNER_MAT_RATIO)))
    return max(1, reveal)


def mat_size_style_for_geometry(decor_style):
    if decor_style == DecorStyle.signature.value:
        return DecorStyle.standard.value
    return decor_style


def mat_base_size(width, height, decor_style, size_profile, mat_size_config=None):
    mat_size_config = normalize_mat_size_config(mat_size_config)
    percentage = mat_size_config["percentages"][size_profile][decor_style]
    raw_size = int(round(min(width, height) * percentage))
    max_size = mat_size_config["max_mm"][size_profile][decor_style]
    if max_size is not None:
        return min(raw_size, max_size)
    return raw_size


def normalize_mat_size_config(config=None):
    percentages = {profile: values.copy() for profile, values in MAT_SIZE_PERCENTAGES.items()}
    max_mm = {profile: values.copy() for profile, values in MAT_SIZE_MAX_MM.items()}
    if not isinstance(config, dict):
        return {"percentages": percentages, "max_mm": max_mm}

    for profile in SIZE_PROFILE_LABELS:
        for decor_style in DecorStyle:
            style = decor_style.value
            raw_percentage = config.get("percentages", {}).get(profile, {}).get(style)
            percentage = normalize_percentage(raw_percentage)
            if percentage is not None:
                percentages[profile][style] = percentage

            raw_max = config.get("max_mm", {}).get(profile, {}).get(style)
            max_value = normalize_optional_mm(raw_max)
            if raw_max is not None:
                max_mm[profile][style] = max_value

    return {"percentages": percentages, "max_mm": max_mm}


def normalize_percentage(value):
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if not 0 < parsed <= 100:
        return None
    return parsed / 100 if parsed > 1 else parsed


def normalize_optional_mm(value):
    if value in ("", None):
        return None
    try:
        parsed = int(round(float(value)))
    except (TypeError, ValueError):
        return None
    if parsed <= 0:
        return None
    return parsed


def mat_color_warm_white():
    return public_palette_color(DEFAULT_MAT_COLOR)


def mat_color_for_variant(decor_style, image_analysis):
    return standard_mat_color(image_analysis)


def standard_mat_color(image_analysis):
    if image_analysis.get("monochrome") == "монохромное":
        return public_palette_color(MAT_COLOR_OPTIONS["museum_white"])

    temperature = image_analysis.get("temperature")
    lightness = image_analysis.get("lightness")
    if temperature == "теплый" and lightness == "светлый":
        return public_palette_color(MAT_COLOR_OPTIONS["warm_white"])
    if temperature == "теплый":
        return public_palette_color(MAT_COLOR_OPTIONS["warm_white"])
    return public_palette_color(MAT_COLOR_OPTIONS["museum_white"])


def signature_inner_mat_color(image_analysis):
    strategy = signature_inner_color_strategy(image_analysis)
    target_lab = strategy.get("target_lab")
    if target_lab is None:
        return mat_color_warm_white()

    return public_palette_color(
        nearest_palette_color(
            target_lab,
            excluded_families=strategy.get("excluded_families"),
            allowed_families=strategy.get("allowed_families"),
            allowed_roles=strategy.get("allowed_roles"),
        )
    )


def signature_inner_target_lab(image_analysis):
    return signature_inner_color_strategy(image_analysis).get("target_lab")


def signature_inner_color_strategy(image_analysis):
    palette = image_analysis.get("palette", {})
    accent = palette.get("accent", {}) if isinstance(palette, dict) else {}
    selected = accent.get("selected") if isinstance(accent, dict) else None
    excluded_families = signature_anchor_families(palette)
    grey_allowed = signature_grey_allowed(image_analysis, palette)
    if not selected:
        return {
            "mode": "fallback",
            "base_color": None,
            "target_lab": None,
            "similarity": {},
            "excluded_families": excluded_families,
            "allowed_families": None,
            "allowed_roles": None,
            "adjustments": [],
            "reason": "Signature: акцентный цвет не найден, используется резервный Warm White.",
        }

    if is_black_like_color(selected):
        target_lab, adjustments = graphite_inner_mat_lab(image_analysis)
        return {
            "mode": "graphite_for_black_accent",
            "base_color": selected,
            "target_lab": target_lab,
            "similarity": accent_similarity(selected, palette),
            "excluded_families": set(),
            "allowed_families": {"grey"},
            "allowed_roles": {"deep_neutral"},
            "adjustments": adjustments,
            "grey_allowed": True,
            "reason": (
                "Signature: акцентный цвет черный или почти черный; черный запрещен для нижнего паспарту, "
                "поэтому используется графит из палитры placed."
            ),
        }

    if is_neutral_color(selected):
        neutral_choice = signature_neutral_base_color(accent, palette, grey_allowed)
        base_color = neutral_choice.get("color") or selected
        target_lab, adjustments = adjusted_signature_lab(base_color, image_analysis)
        return {
            "mode": "image_candidate_for_neutral",
            "base_color": base_color,
            "base_source": neutral_choice.get("source"),
            "target_lab": target_lab,
            "similarity": accent_similarity(selected, palette),
            "excluded_families": grey_sensitive_excluded_families(excluded_families, grey_allowed, base_color),
            "allowed_families": None,
            "allowed_roles": None,
            "adjustments": adjustments,
            "grey_allowed": grey_allowed,
            "reason": (
                "Signature: выбранный акцент нейтральный, поэтому новый нейтральный цвет не добавляется автоматически; "
                "для нижнего паспарту используется подходящий цвет-кандидат из изображения."
            ),
        }

    similarity = accent_similarity(selected, palette)
    if similarity.get("similar", False):
        fallback = farthest_accent_candidate(accent, palette, similarity)
        base_color = fallback.get("color") or selected
        target_lab, adjustments = adjusted_signature_lab(base_color, image_analysis)
        return {
            "mode": "distant_accent_candidate",
            "base_color": base_color,
            "base_source": fallback.get("source"),
            "target_lab": target_lab,
            "similarity": similarity,
            "excluded_families": grey_sensitive_excluded_families(excluded_families, grey_allowed, base_color),
            "allowed_families": None,
            "allowed_roles": None,
            "candidate_distances": fallback.get("distances", {}),
            "adjustments": adjustments,
            "grey_allowed": grey_allowed,
            "reason": (
                "Signature: выбранный акцент находится в одной цветовой группе с основным или вторичным; "
                "выбран самый дальний подходящий кандидат акцента."
            ),
        }

    target_lab, adjustments = adjusted_signature_lab(selected, image_analysis)
    return {
        "mode": "accent",
        "base_color": selected,
        "base_source": accent.get("source"),
        "target_lab": target_lab,
        "similarity": similarity,
        "excluded_families": grey_sensitive_excluded_families(excluded_families, grey_allowed, selected),
        "allowed_families": None,
        "allowed_roles": None,
        "candidate_distances": {},
        "adjustments": adjustments,
        "grey_allowed": grey_allowed,
        "reason": "Signature: акцент достаточно самостоятельный, поэтому нижнее паспарту использует приглушенный акцентный цвет.",
    }


def adjusted_signature_lab(color, image_analysis):
    lab = color_lab(color)
    if lab is None:
        return None, []

    l_value, a_value, b_value = lab
    adjustments = []
    original_l = l_value

    if l_value < INNER_MAT_MIN_L:
        l_value = 38
        a_value *= 0.82
        b_value *= 0.82
        adjustments.append("Акцент темнее L=25: Hue сохранен, цвет осветлен до спокойного диапазона L=30-45, насыщенность снижена.")
    elif l_value < 40:
        l_value = min(55, l_value + 20)
        a_value *= 0.85
        b_value *= 0.85
        adjustments.append("Акцент в диапазоне L=25-40: цвет осветлен и немного приглушен.")
    else:
        a_value *= 0.84
        b_value *= 0.84
        adjustments.append("Акцент светлее L=40: Hue сохранен, насыщенность снижена.")

    image_l = image_lightness_value(image_analysis)
    l_value, lightness_adjustments = enforce_inner_mat_lightness(l_value, image_l)
    adjustments.extend(lightness_adjustments)

    l_value, a_value, b_value, contrast_adjustments = reduce_inner_mat_visual_weight(
        l_value,
        a_value,
        b_value,
        image_analysis,
        original_l,
    )
    adjustments.extend(contrast_adjustments)

    return (clamp_float(l_value, 0, 100), a_value, b_value), adjustments


def enforce_inner_mat_lightness(l_value, image_l):
    adjustments = []
    minimum_l = INNER_MAT_MIN_L
    if image_l is not None:
        minimum_l = max(minimum_l, image_l - INNER_MAT_MAX_DARKER_THAN_IMAGE)

    while l_value < minimum_l:
        l_value += 5
        adjustments.append(f"Светлота нижнего паспарту поднята на 5 пунктов до L={round(l_value, 1)}.")

    return clamp_float(l_value, minimum_l, 100), adjustments


def reduce_inner_mat_visual_weight(l_value, a_value, b_value, image_analysis, original_l):
    image_l = image_lightness_value(image_analysis)
    image_contrast_value = image_contrast_metric(image_analysis)
    if image_l is None:
        return l_value, a_value, b_value, []

    max_gap = max(18, image_contrast_value * 0.75)
    gap = abs(l_value - image_l)
    if gap <= max_gap:
        return l_value, a_value, b_value, []

    direction = 1 if l_value > image_l else -1
    l_value = image_l + direction * max_gap
    if l_value < image_l - INNER_MAT_MAX_DARKER_THAN_IMAGE:
        l_value = image_l - INNER_MAT_MAX_DARKER_THAN_IMAGE
    a_value *= 0.82
    b_value *= 0.82
    return (
        clamp_float(l_value, INNER_MAT_MIN_L, 100),
        a_value,
        b_value,
        [
            (
                "Контраст нижнего паспарту с изображением был сильнее внутренних отношений изображения; "
                f"L скорректирован от исходного акцента L={round(original_l, 1)}, насыщенность снижена."
            )
        ],
    )


def graphite_inner_mat_lab(image_analysis):
    image_l = image_lightness_value(image_analysis)
    target_l = INNER_MAT_GRAPHITE_TARGET_L
    if normalize_visual_level(image_analysis.get("lightness")) == "light" and normalize_level(image_analysis.get("contrast")) == "low":
        target_l = 38
    if image_l is not None:
        target_l = max(target_l, min(40, image_l - INNER_MAT_MAX_DARKER_THAN_IMAGE))
    target_l = clamp_float(target_l, 25, 40)
    return (target_l, 0, 0), [f"Черный акцент заменен на графитовый диапазон палитры placed: целевая светлота L={round(target_l, 1)}."]


def is_black_like_color(color):
    lab = color_lab(color)
    if lab is None:
        return False
    l_value, a_value, b_value = lab
    chroma = color.get("chroma")
    if chroma is None:
        chroma = sqrt(a_value * a_value + b_value * b_value)
    return l_value < INNER_MAT_MIN_L and float(chroma) < 12


def image_lightness_value(image_analysis):
    metrics = image_analysis.get("metrics", {}) if isinstance(image_analysis, dict) else {}
    value = metrics.get("lightness") if isinstance(metrics, dict) else None
    try:
        return float(value)
    except (TypeError, ValueError):
        level = normalize_visual_level(image_analysis.get("lightness") if isinstance(image_analysis, dict) else None)
        return {"light": 72.0, "medium": 52.0, "dark": 32.0}.get(level, 52.0)


def image_contrast_metric(image_analysis):
    metrics = image_analysis.get("metrics", {}) if isinstance(image_analysis, dict) else {}
    value = metrics.get("contrast") if isinstance(metrics, dict) else None
    try:
        return float(value)
    except (TypeError, ValueError):
        return {"low": 22.0, "medium": 36.0, "high": 52.0}.get(normalize_level(image_analysis.get("contrast")), 36.0)


def signature_grey_allowed(image_analysis, palette):
    if is_monochrome_image(image_analysis):
        return True
    if image_analysis.get("temperature") == "нейтральный":
        return True
    grey_present = image_palette_has_grey(palette)
    if image_analysis.get("temperature") == "теплый":
        return False
    if image_analysis.get("temperature") == "холодный":
        return grey_present
    return grey_present


def image_palette_has_grey(palette):
    if not isinstance(palette, dict):
        return False
    for role in ("primary", "secondary"):
        color = palette.get(role)
        if isinstance(color, dict) and color.get("family") == "grey":
            return True
    accent = palette.get("accent", {})
    if isinstance(accent, dict):
        selected = accent.get("selected")
        if isinstance(selected, dict) and selected.get("family") == "grey":
            return True
        candidates = accent.get("candidates", {})
        if isinstance(candidates, dict):
            for color in candidates.values():
                if isinstance(color, dict) and color.get("family") == "grey":
                    return True
    return False


def grey_sensitive_excluded_families(base_excluded_families, grey_allowed, base_color):
    families = set(base_excluded_families or [])
    if not grey_allowed:
        families.add("grey")
    return families


def signature_neutral_base_color(accent, palette, grey_allowed):
    candidates = accent.get("candidates", {}) if isinstance(accent, dict) else {}
    selected = accent.get("selected") if isinstance(accent, dict) else None

    ordered = []
    if isinstance(candidates, dict):
        for source in ("area", "pop", "temperature", "light"):
            ordered.append((source, candidates.get(source)))
    ordered.append(("selected", selected))

    if grey_allowed:
        for source, candidate in ordered:
            if candidate:
                return {"source": source, "color": candidate}

    for source, candidate in ordered:
        if candidate and candidate.get("family") != "grey":
            return {"source": source, "color": candidate}

    if isinstance(palette, dict):
        for source in ("secondary", "primary"):
            candidate = palette.get(source)
            if isinstance(candidate, dict) and candidate.get("family") != "grey":
                return {"source": source, "color": candidate}

    return {"source": "selected", "color": selected}


def signature_anchor_families(palette):
    families = set()
    if not isinstance(palette, dict):
        return families
    for role in ("primary", "secondary"):
        color = palette.get(role)
        family = color.get("family") if isinstance(color, dict) else None
        if family and family not in NEUTRAL_COLOR_FAMILIES:
            families.add(family)
    return families


def farthest_accent_candidate(accent, palette, similarity):
    candidates = accent.get("candidates", {}) if isinstance(accent, dict) else {}
    anchor_roles = similarity.get("similar_roles") or [similarity.get("closest_role")]
    anchor_roles = [role for role in anchor_roles if role in {"primary", "secondary"}]
    if not anchor_roles:
        anchor_roles = ["primary", "secondary"]

    anchors = [
        palette.get(role)
        for role in anchor_roles
        if isinstance(palette, dict) and palette.get(role)
    ]
    anchor_labs = [color_lab(anchor) for anchor in anchors]
    anchor_labs = [lab for lab in anchor_labs if lab is not None]
    if not anchor_labs:
        return {"color": accent.get("selected"), "source": accent.get("source"), "distances": {}}

    selected_hex = (accent.get("selected") or {}).get("hex")
    scored = []
    seen = set()
    for source, candidate in candidates.items():
        if not candidate:
            continue
        candidate_hex = candidate.get("hex")
        if not candidate_hex or candidate_hex in seen:
            continue
        seen.add(candidate_hex)
        candidate_lab = color_lab(candidate)
        if candidate_lab is None:
            continue
        distances = [delta_e(candidate_lab, anchor_lab) for anchor_lab in anchor_labs]
        distance_score = min(distances)
        source_penalty = 0.01 if candidate_hex == selected_hex else 0
        scored.append((distance_score - source_penalty, source, candidate, distances))

    if not scored:
        return {"color": accent.get("selected"), "source": accent.get("source"), "distances": {}}

    scored.sort(key=lambda item: item[0], reverse=True)
    _score, source, candidate, distances = scored[0]
    distance_map = {
        role: round(distance, 2)
        for role, distance in zip(anchor_roles, distances)
    }
    return {"color": candidate, "source": source, "distances": distance_map}


def accent_similarity(accent_color, palette):
    accent_lab = color_lab(accent_color)
    if accent_lab is None:
        return {"similar": False, "primary_delta_e": None, "secondary_delta_e": None, "closest_role": None, "similar_roles": []}

    closest_role = None
    closest_delta = None
    distances = {}
    similar = False
    similar_roles = []
    for role in ("primary", "secondary"):
        anchor = palette.get(role) if isinstance(palette, dict) else None
        anchor_lab = color_lab(anchor) if anchor else None
        if anchor_lab is None:
            distances[f"{role}_delta_e"] = None
            continue

        distance = delta_e(accent_lab, anchor_lab)
        same_family = accent_color.get("family") and accent_color.get("family") == anchor.get("family")
        role_similar = distance <= ACCENT_SIMILAR_DELTA_E or (
            same_family and distance <= ACCENT_SAME_FAMILY_DELTA_E
        )
        distances[f"{role}_delta_e"] = round(distance, 2)
        if closest_delta is None or distance < closest_delta:
            closest_delta = distance
            closest_role = role
        similar = similar or role_similar
        if role_similar:
            similar_roles.append(role)

    return {
        "similar": similar,
        "primary_delta_e": distances.get("primary_delta_e"),
        "secondary_delta_e": distances.get("secondary_delta_e"),
        "closest_role": closest_role,
        "similar_roles": similar_roles,
    }


def is_neutral_color(color):
    family = color.get("family")
    if family in NEUTRAL_COLOR_FAMILIES:
        return True

    lab = color_lab(color)
    if lab is None:
        return False
    _l_value, a_value, b_value = lab
    chroma = color.get("chroma")
    if chroma is None:
        chroma = sqrt(a_value * a_value + b_value * b_value)
    return float(chroma) < 10


def normalize_visual_level(value):
    normalized = str(value or "").strip().lower()
    if normalized in {"light", "high", "светлый", "светлая", "высокий", "высокая", "svetlyy"}:
        return "light"
    if normalized in {"dark", "low", "темный", "тёмный", "темная", "тёмная", "низкий", "низкая", "temnyy"}:
        return "dark"
    return "medium"


def nearest_palette_color(target_lab, excluded_families=None, allowed_families=None, allowed_roles=None):
    excluded_families = set(excluded_families or [])
    allowed_families = set(allowed_families or [])
    allowed_roles = set(allowed_roles or [])
    candidates = [
        color
        for color in PLACED_PALETTE.values()
        if color.get("family") not in excluded_families
        and (not allowed_families or color.get("family") in allowed_families)
        and (not allowed_roles or color.get("role") in allowed_roles)
    ]
    if not candidates:
        candidates = list(PLACED_PALETTE.values())
    candidates.sort(key=lambda color: (delta_e(target_lab, palette_lab(color)), palette_chroma(color)))
    return candidates[0]


def color_lab(color):
    lab = color.get("lab")
    if isinstance(lab, (list, tuple)) and len(lab) == 3:
        return tuple(float(value) for value in lab)

    rgb = color.get("rgb")
    if isinstance(rgb, (list, tuple)) and len(rgb) == 3:
        return rgb_to_lab(tuple(int(value) for value in rgb))

    hex_value = color.get("hex")
    if hex_value:
        return rgb_to_lab(hex_to_rgb(hex_value))

    return None


def palette_lab(color):
    return rgb_to_lab(hex_to_rgb(color["hex"]))


def palette_chroma(color):
    _l, a_value, b_value = palette_lab(color)
    return sqrt(a_value * a_value + b_value * b_value)


def delta_e(first_lab, second_lab):
    return sqrt(sum((first_lab[index] - second_lab[index]) ** 2 for index in range(3)))


def rgb_to_lab(rgb):
    r_value, g_value, b_value = [srgb_channel_to_linear(channel / 255) for channel in rgb]
    x_value = (r_value * 0.4124 + g_value * 0.3576 + b_value * 0.1805) / 0.95047
    y_value = (r_value * 0.2126 + g_value * 0.7152 + b_value * 0.0722) / 1.0
    z_value = (r_value * 0.0193 + g_value * 0.1192 + b_value * 0.9505) / 1.08883

    fx = lab_pivot(x_value)
    fy = lab_pivot(y_value)
    fz = lab_pivot(z_value)
    return (116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz))


def srgb_channel_to_linear(value):
    if value <= 0.04045:
        return value / 12.92
    return ((value + 0.055) / 1.055) ** 2.4


def lab_pivot(value):
    if value > 0.008856:
        return value ** (1 / 3)
    return (7.787 * value) + (16 / 116)


def clamp_float(value, low, high):
    return max(low, min(high, float(value)))


def format_optional_metric(value):
    if value is None:
        return "n/a"
    return f"{float(value):.2f}"


def public_palette_color(color):
    return {"id": color["id"], "name": color["name"], "hex": color["hex"]}


def mat_color_reason(mat, decor_style, image_analysis):
    if not mat.enabled:
        return "Цвет паспарту не рассчитывается."
    if decor_style == DecorStyle.standard.value:
        return f"Standard: выбран {mat.outer_color['name']} ({mat.outer_color['hex']}) по таблице цвета паспарту."
    return (
        f"Signature: верхнее паспарту выбрано как Standard - {mat.outer_color['name']} ({mat.outer_color['hex']}); "
        f"нижнее паспарту выбрано от смягченного акцентного цвета после проверки светлоты и серого правила - "
        f"{mat.inner_color['name']} ({mat.inner_color['hex']})."
    )


def color_facts(mat, decor_style, image_analysis):
    facts = ["Цвет рамы зафиксирован как #000000."]
    if not mat.enabled:
        facts.append("Паспарту не используется, цвет не выбирается.")
        return facts

    facts.extend(
        [
            f"Вариант оформления: {decor_style}.",
            f"Монохромность: {image_analysis.get('monochrome')}.",
            f"Температура изображения: {image_analysis.get('temperature')}.",
            f"Светлота изображения: {image_analysis.get('lightness')}.",
            f"Цвет верхнего паспарту: {mat.outer_color['name']} ({mat.outer_color['hex']}).",
        ]
    )
    if decor_style == DecorStyle.standard.value:
        facts.append("Для Standard применена таблица из `Цвет паспарту.md`; монохромное изображение имеет приоритет над температурой и светлотой.")
    else:
        strategy = signature_inner_color_strategy(image_analysis)
        similarity = strategy.get("similarity", {})
        accent = image_analysis.get("palette", {}).get("accent", {})
        selected = accent.get("selected") if isinstance(accent, dict) else None
        facts.append(
            "Стратегия нижнего паспарту Signature: "
            f"{strategy.get('mode')}; {strategy.get('reason')}"
        )
        facts.append(
            "Схожесть акцента: "
            f"основной Delta E {format_optional_metric(similarity.get('primary_delta_e'))}, "
            f"вторичный Delta E {format_optional_metric(similarity.get('secondary_delta_e'))}; "
            f"схожий={similarity.get('similar', False)}, "
            f"роли={', '.join(similarity.get('similar_roles') or []) or 'нет'}."
        )
        base_color = strategy.get("base_color")
        if base_color:
            source = strategy.get("base_source") or "selected"
            facts.append(f"Базовый цвет нижнего паспарту: {color_fact(base_color)}, источник {source}.")
        candidate_distances = strategy.get("candidate_distances") or {}
        if candidate_distances:
            facts.append(
                "Дистанции выбранного кандидата до конфликтующих цветов: "
                + ", ".join(f"{role} Delta E {format_optional_metric(distance)}" for role, distance in candidate_distances.items())
                + "."
            )
        excluded_families = ", ".join(sorted(strategy.get("excluded_families") or [])) or "нет"
        facts.append(f"Исключенные семьи для нижнего паспарту: {excluded_families}.")
        allowed_families = ", ".join(sorted(strategy.get("allowed_families") or [])) or "все допустимые"
        allowed_roles = ", ".join(sorted(strategy.get("allowed_roles") or [])) or "все допустимые"
        facts.append(f"Разрешенные семьи/роли палитры: семьи - {allowed_families}; роли - {allowed_roles}.")
        facts.append(f"Серый допустим для нижнего паспарту: {'да' if strategy.get('grey_allowed') else 'нет'}.")
        facts.append(f"Акцентный цвет: {color_fact(selected) if selected else 'не найден'}.")
        target_lab = strategy.get("target_lab")
        if target_lab:
            facts.append(f"Расчетный LAB нижнего паспарту после коррекций: L={round(target_lab[0], 1)}, a={round(target_lab[1], 1)}, b={round(target_lab[2], 1)}.")
        for adjustment in strategy.get("adjustments") or []:
            facts.append(adjustment)
        facts.append(f"Цвет нижнего паспарту: {mat.inner_color['name']} ({mat.inner_color['hex']}).")
    return facts


def mat_reason(mat, decor_style, size_profile, mat_size_config=None):
    if not mat.enabled:
        return "Паспарту не используется."
    mat_size_config = normalize_mat_size_config(mat_size_config)
    size_style = mat_size_style_for_geometry(decor_style)
    percentage = int(round(mat_size_config["percentages"][size_profile][size_style] * 100))
    max_size = mat_size_config["max_mm"][size_profile][size_style]
    limit_note = f", ограничение {max_size} мм" if max_size is not None else ""
    base_reason = (
        f"Размер паспарту: окно меньше изображения на {mat.overlap_mm} мм с каждой стороны; "
        f"верх и боковые края {mat.left_mm} мм "
        f"({percentage}% от меньшей стороны работы{limit_note}), нижний край {mat.bottom_mm} мм."
    )
    if decor_style != DecorStyle.signature.value:
        return base_reason
    return (
        f"{base_reason} Для Signature общий размер поля совпадает со Standard; нижнее паспарту занимает внутренние 20% поля: "
        f"{mat.inner_reveal_left_mm}/{mat.inner_reveal_top_mm}/{mat.inner_reveal_right_mm}/{mat.inner_reveal_bottom_mm} мм."
    )


def mat_facts(mat, decor_style, size_profile, width, height, mat_size_config=None):
    if not mat.enabled:
        return ["Паспарту отключено, размер не рассчитывается."]
    mat_size_config = normalize_mat_size_config(mat_size_config)
    size_style = mat_size_style_for_geometry(decor_style)
    percentage = int(round(mat_size_config["percentages"][size_profile][size_style] * 100))
    raw_size = int(round(min(width, height) * mat_size_config["percentages"][size_profile][size_style]))
    max_size = mat_size_config["max_mm"][size_profile][size_style]
    window_width = width - 2 * mat.overlap_mm
    window_height = height - 2 * mat.overlap_mm
    facts = [
        f"Меньшая сторона работы: {min(width, height)} мм.",
        f"Размерный профиль: {SIZE_PROFILE_LABELS[size_profile]}.",
        f"Вариант оформления: {decor_style}.",
        f"Окно паспарту: {window_width} x {window_height} мм.",
        f"Нахлест паспарту на изображение: {mat.overlap_mm} мм с каждой стороны.",
        f"Процент по таблице: {percentage}%.",
        f"Размер по проценту до ограничения: {raw_size} мм.",
        f"Левый/правый/верхний край: {mat.left_mm} мм.",
        f"Нижний край: {mat.bottom_mm} мм.",
        f"Цвет верхнего паспарту: {mat.outer_color['name']} ({mat.outer_color['hex']}).",
    ]
    if max_size is not None:
        facts.insert(5, f"Максимум по таблице: {max_size} мм.")
    if decor_style == DecorStyle.signature.value:
        facts.extend(
            [
                "Signature: окно нижнего паспарту совпадает с окном Standard.",
                "Signature: общий размер поля совпадает со Standard; верхнее паспарту сокращено до внешних 80%, нижнее раскрытие занимает внутренние 20%.",
                (
                    "Видимая внутренняя полоса нижнего паспарту: "
                    f"{mat.inner_reveal_left_mm}/{mat.inner_reveal_top_mm}/"
                    f"{mat.inner_reveal_right_mm}/{mat.inner_reveal_bottom_mm} мм."
                ),
                f"Цвет нижнего паспарту: {mat.inner_color['name']} ({mat.inner_color['hex']}).",
            ]
        )
    return facts


def build_geometry(width, height, frame_width, mat, size_profile):
    if mat.enabled:
        window_width = width - 2 * mat.overlap_mm
        window_height = height - 2 * mat.overlap_mm
        mat_outer_width = window_width + mat.left_mm + mat.right_mm
        mat_outer_height = window_height + mat.top_mm + mat.bottom_mm
    else:
        window_width = width
        window_height = height
        mat_outer_width = width
        mat_outer_height = height

    return GeometrySpec(
        size_profile=size_profile,
        aspect=classify_aspect(width, height),
        window_width_mm=window_width,
        window_height_mm=window_height,
        mat_outer_width_mm=mat_outer_width,
        mat_outer_height_mm=mat_outer_height,
        outer_width_mm=mat_outer_width + 2 * frame_width,
        outer_height_mm=mat_outer_height + 2 * frame_width,
    )


def renderer_geometry(spec):
    frame = spec["frame"]
    mat = spec["mat"]
    geometry = {
        "frame": frame["width_mm"],
        "passepartout": mat["left_mm"] if mat and mat["enabled"] else 0,
        "mat_left": mat["left_mm"] if mat and mat["enabled"] else 0,
        "mat_right": mat["right_mm"] if mat and mat["enabled"] else 0,
        "mat_top": mat["top_mm"] if mat and mat["enabled"] else 0,
        "mat_bottom": mat["bottom_mm"] if mat and mat["enabled"] else 0,
        "overlap": mat["overlap_mm"] if mat and mat["enabled"] else 0,
        "inner_reveal": mat["inner_reveal_mm"] if mat and mat["enabled"] else 0,
        "inner_reveal_left": mat["inner_reveal_left_mm"] if mat and mat["enabled"] else 0,
        "inner_reveal_right": mat["inner_reveal_right_mm"] if mat and mat["enabled"] else 0,
        "inner_reveal_top": mat["inner_reveal_top_mm"] if mat and mat["enabled"] else 0,
        "inner_reveal_bottom": mat["inner_reveal_bottom_mm"] if mat and mat["enabled"] else 0,
        "frame_color": hex_to_rgb(frame.get("hex", "#2B2925")),
        "frame_id": frame.get("id"),
        "frame_material": frame.get("material", "wood"),
        "frame_profile": frame.get("profile", "natural_wood"),
        "glass": spec.get("glass", {}).get("type", "none"),
    }

    if mat and mat["enabled"] and mat["outer_color"]:
        geometry["mat_color"] = hex_to_rgb(mat["outer_color"]["hex"])
    if mat and mat["enabled"] and mat["inner_color"]:
        geometry["inner_mat_color"] = hex_to_rgb(mat["inner_color"]["hex"])

    return geometry


def analysis_facts(image_analysis):
    palette = image_analysis["palette"]
    metrics = image_analysis.get("metrics", {})
    facts = [
        f"Основной цвет: {color_fact(palette.get('primary'))}.",
        f"Вторичный цвет: {color_fact(palette.get('secondary'))}.",
        f"Акцентный цвет: {accent_fact(palette.get('accent'))}.",
        f"Цветовая температура: {image_analysis['temperature']}.",
        f"Светлота: {image_analysis['lightness']}.",
        f"Насыщенность: {image_analysis['chroma_level']}.",
        f"Монохромность: {image_analysis['monochrome']}.",
        f"Заполненность кадра: {image_analysis['frame_occupancy']}.",
        f"Контраст: {image_analysis['contrast']}.",
    ]
    if metrics:
        facts.append(
            "Метрики: "
            f"L={metrics.get('lightness')}, "
            f"C={metrics.get('chroma')}, "
            f"monochrome={metrics.get('monochrome_score')}, "
            f"contrast={metrics.get('contrast')}, "
            f"occupancy={metrics.get('frame_occupancy')}, "
            f"temperature={metrics.get('temperature_score')}."
        )
    return facts


def color_fact(color):
    if not color:
        return "не найден"
    return f"{color['hex']} ({color['family']}, доля {round(color['share'] * 100, 1)}%)"


def accent_fact(accent):
    if not accent or not accent.get("selected"):
        return "не найден"
    selected = accent["selected"]
    source = accent.get("source") or "unknown"
    confidence = accent.get("confidence") or "unknown"
    return f"{color_fact(selected)}, источник {source}, уверенность {confidence}"


def placeholder_title(decor_style):
    return {
        "standard": "Standard: технический рендер",
        "signature": "Signature: технический рендер",
    }[decor_style]


def normalize_artwork_type(value):
    normalized = str(value or "poster").strip().lower()
    aliases = {
        "постер": "poster",
        "poster": "poster",
        "фото": "photo",
        "photo": "photo",
        "акварель": "watercolor",
        "watercolor": "watercolor",
        "гравюра": "engraving",
        "engraving": "engraving",
        "ботаническая иллюстрация": "botanical",
        "ботаника": "botanical",
        "botanical": "botanical",
        "холст": "canvas",
        "canvas": "canvas",
        "объемная": "volumetric",
        "объёмная": "volumetric",
        "volumetric": "volumetric",
    }
    return aliases.get(normalized, "poster")


def classify_size_profile(width, height):
    short_side = min(width, height)
    if short_side >= 600:
        return "extra_large"
    if short_side >= 401:
        return "large"
    if short_side >= 300:
        return "medium"
    return "small"


def normalize_level(value):
    normalized = str(value or "").strip().lower()
    if normalized in ("low", "низкая", "низкий"):
        return "low"
    if normalized in ("medium", "средняя", "средний", "нейтральный"):
        return "medium"
    if normalized in ("high", "высокая", "высокий"):
        return "high"
    return "medium"


def glass_type_label(value):
    return {
        "museum": "музейное",
        "regular": "обычное",
        "none": "нет",
    }.get(value, value)


def classify_aspect(width, height):
    ratio = width / height
    if 0.92 <= ratio <= 1.08:
        return "square"
    if ratio > 1.8 or ratio < 0.55:
        return "panoramic"
    if ratio < 0.92:
        return "portrait"
    return "landscape"


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


def hex_to_rgb(value):
    value = value.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


def clamp_int(value, low, high):
    return max(low, min(high, int(round(float(value)))))
