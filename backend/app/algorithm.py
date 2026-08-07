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
    "small": {"standard": 0.35, "signature": 0.40},
    "medium": {"standard": 0.25, "signature": 0.30},
    "large": {"standard": 0.15, "signature": 0.20},
    "extra_large": {"standard": 0.10, "signature": 0.15},
}

MAT_SIZE_MAX_MM = {
    "small": {"standard": None, "signature": None},
    "medium": {"standard": None, "signature": None},
    "large": {"standard": None, "signature": None},
    "extra_large": {"standard": 70, "signature": 80},
}

SIGNATURE_INNER_MAT_RATIO = 0.8

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

DEFAULT_MAT_COLOR = PLACED_PALETTE["PW004"]

MAT_COLOR_OPTIONS = {
    "ivory": PLACED_PALETTE["PW004"],
    "warm_white": PLACED_PALETTE["PW003"],
    "museum_white": PLACED_PALETTE["PW001"],
}


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
    frame = FrameOption(
        id="renderer-placeholder-frame",
        name="Черная техническая рама",
        material="wood",
        color_family="neutral",
        width_mm=20,
        depth_mm=24,
        profile="flat",
        hex="#000000",
    )
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
            f"Багет пока технический: черная рама {frame.width_mm} мм.",
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
                "result": "Вычислены наблюдаемые характеристики изображения. Они пока не влияют на оформление.",
                "facts": analysis_facts(image_analysis),
            },
            {
                "title": "Цвета",
                "result": mat_color_reason(mat, decor_style, image_analysis) if mat.enabled else "Цвет паспарту не рассчитывается.",
                "facts": color_facts(mat, decor_style, image_analysis),
            }
        ],
    )


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
    base_size = mat_base_size(width, height, decor_style, size_profile, mat_size_config)
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
        overlap_mm=0,
        inner_reveal_mm=inner_reveal_top,
        inner_reveal_left_mm=inner_reveal_left,
        inner_reveal_right_mm=inner_reveal_right,
        inner_reveal_top_mm=inner_reveal_top,
        inner_reveal_bottom_mm=inner_reveal_bottom,
    )


def signature_inner_reveal(outer_field_mm):
    reveal = int(round(outer_field_mm * (1 - SIGNATURE_INNER_MAT_RATIO)))
    return max(1, reveal)


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


def mat_color_ivory():
    return public_palette_color(DEFAULT_MAT_COLOR)


def mat_color_for_variant(decor_style, image_analysis):
    return standard_mat_color(image_analysis)


def standard_mat_color(image_analysis):
    if image_analysis.get("monochrome") == "монохромное":
        return public_palette_color(MAT_COLOR_OPTIONS["museum_white"])

    temperature = image_analysis.get("temperature")
    lightness = image_analysis.get("lightness")
    if temperature == "теплый" and lightness == "светлый":
        return public_palette_color(MAT_COLOR_OPTIONS["ivory"])
    if temperature == "теплый":
        return public_palette_color(MAT_COLOR_OPTIONS["warm_white"])
    return public_palette_color(MAT_COLOR_OPTIONS["museum_white"])


def signature_inner_mat_color(image_analysis):
    target_lab = signature_inner_target_lab(image_analysis)
    if target_lab is None:
        return mat_color_ivory()

    return public_palette_color(nearest_palette_color(target_lab))


def signature_inner_target_lab(image_analysis):
    accent = image_analysis.get("palette", {}).get("accent", {})
    selected = accent.get("selected") if isinstance(accent, dict) else None
    if not selected:
        return None

    lab = color_lab(selected)
    if lab is None:
        return None

    lightness = image_analysis.get("lightness")
    l_value, a_value, b_value = lab
    if lightness == "светлый":
        l_value -= 15
    elif lightness == "темный":
        l_value += 15

    return (clamp_float(l_value, 0, 100), a_value * 0.5, b_value * 0.5)


def nearest_palette_color(target_lab):
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


def public_palette_color(color):
    return {"id": color["id"], "name": color["name"], "hex": color["hex"]}


def mat_color_reason(mat, decor_style, image_analysis):
    if not mat.enabled:
        return "Цвет паспарту не рассчитывается."
    if decor_style == DecorStyle.standard.value:
        return f"Standard: выбран {mat.outer_color['name']} ({mat.outer_color['hex']}) по таблице цвета паспарту."
    return (
        f"Signature: верхнее паспарту выбрано как Standard - {mat.outer_color['name']} ({mat.outer_color['hex']}); "
        f"нижнее паспарту выбрано от акцентного цвета через ближайший оттенок палитры placed - "
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
        accent = image_analysis.get("palette", {}).get("accent", {})
        selected = accent.get("selected") if isinstance(accent, dict) else None
        facts.append(f"Акцентный цвет: {color_fact(selected) if selected else 'не найден'}.")
        facts.append("Насыщенность расчетного цвета нижнего паспарту уменьшена на 50%.")
        if image_analysis.get("lightness") == "светлый":
            facts.append("Изображение светлое: светлота расчетного цвета нижнего паспарту уменьшена на 15.")
        elif image_analysis.get("lightness") == "темный":
            facts.append("Изображение темное: светлота расчетного цвета нижнего паспарту увеличена на 15.")
        else:
            facts.append("Изображение средней светлоты: светлота расчетного цвета нижнего паспарту не менялась.")
        facts.append(f"Цвет нижнего паспарту: {mat.inner_color['name']} ({mat.inner_color['hex']}).")
    return facts


def mat_reason(mat, decor_style, size_profile, mat_size_config=None):
    if not mat.enabled:
        return "Паспарту не используется."
    mat_size_config = normalize_mat_size_config(mat_size_config)
    percentage = int(round(mat_size_config["percentages"][size_profile][decor_style] * 100))
    max_size = mat_size_config["max_mm"][size_profile][decor_style]
    limit_note = f", ограничение {max_size} мм" if max_size is not None else ""
    base_reason = (
        f"Размер паспарту: верх и боковые края {mat.left_mm} мм "
        f"({percentage}% от меньшей стороны работы{limit_note}), нижний край {mat.bottom_mm} мм."
    )
    if decor_style != DecorStyle.signature.value:
        return base_reason
    return (
        f"{base_reason} Для Signature добавлено нижнее паспарту: видимая внутренняя полоса "
        f"{mat.inner_reveal_left_mm}/{mat.inner_reveal_top_mm}/{mat.inner_reveal_right_mm}/{mat.inner_reveal_bottom_mm} мм."
    )


def mat_facts(mat, decor_style, size_profile, width, height, mat_size_config=None):
    if not mat.enabled:
        return ["Паспарту отключено, размер не рассчитывается."]
    mat_size_config = normalize_mat_size_config(mat_size_config)
    percentage = int(round(mat_size_config["percentages"][size_profile][decor_style] * 100))
    raw_size = int(round(min(width, height) * mat_size_config["percentages"][size_profile][decor_style]))
    max_size = mat_size_config["max_mm"][size_profile][decor_style]
    facts = [
        f"Меньшая сторона работы: {min(width, height)} мм.",
        f"Размерный профиль: {SIZE_PROFILE_LABELS[size_profile]}.",
        f"Вариант оформления: {decor_style}.",
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
                "Signature: нижнее паспарту считается как 80% от соответствующих полей верхнего.",
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
        mat_outer_width = width + mat.left_mm + mat.right_mm
        mat_outer_height = height + mat.top_mm + mat.bottom_mm
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
        "inner_reveal": mat["inner_reveal_mm"] if mat and mat["enabled"] else 0,
        "inner_reveal_left": mat["inner_reveal_left_mm"] if mat and mat["enabled"] else 0,
        "inner_reveal_right": mat["inner_reveal_right_mm"] if mat and mat["enabled"] else 0,
        "inner_reveal_top": mat["inner_reveal_top_mm"] if mat and mat["enabled"] else 0,
        "inner_reveal_bottom": mat["inner_reveal_bottom_mm"] if mat and mat["enabled"] else 0,
        "frame_color": hex_to_rgb(frame.get("hex", "#2B2925")),
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
