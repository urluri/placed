from dataclasses import asdict, dataclass
from enum import Enum

from .image_analysis import analyze_image


class DecorStyle(str, Enum):
    standard = "standard"
    modern = "modern"
    signature = "signature"


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


def build_decoration_set(image_path, artwork_width_mm, artwork_height_mm, artwork_type, interior_style):
    width = clamp_int(artwork_width_mm, 50, 3000)
    height = clamp_int(artwork_height_mm, 50, 3000)
    image_analysis = analyze_image(image_path)

    variants = [
        build_placeholder_variant(DecorStyle.standard.value, width, height, artwork_type, interior_style, image_analysis),
        build_placeholder_variant(DecorStyle.modern.value, width, height, artwork_type, interior_style, image_analysis),
        build_placeholder_variant(DecorStyle.signature.value, width, height, artwork_type, interior_style, image_analysis),
    ]

    return {
        "image_analysis": image_analysis,
        "variants": [serialize_dataclass(variant) for variant in variants],
    }


def build_placeholder_variant(decor_style, width, height, artwork_type, interior_style, image_analysis):
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
    mat = MatSpec(
        enabled=False,
        outer_color=None,
        inner_color=None,
        left_mm=0,
        right_mm=0,
        top_mm=0,
        bottom_mm=0,
        overlap_mm=0,
        inner_reveal_mm=0,
    )
    glass = GlassSpec(type="none", required=False)
    geometry = build_geometry(width, height, frame.width_mm, mat)

    return DecorationSpec(
        decor_style=decor_style,
        title=placeholder_title(decor_style),
        artwork_type=str(artwork_type or "unknown"),
        frame=frame,
        mat=mat,
        glass=glass,
        shadow_box=False,
        geometry=geometry,
        reasons=[
            "Расчеты изображения выполнены, но алгоритм подбора оформления пока отключен.",
            "Показан только технический рендер: черная рама без паспарту и стекла.",
        ],
        warnings=["Это не рекомендация по оформлению."],
        decision_tree=[
            {
                "title": "Входные данные",
                "result": "Пользовательские параметры сохранены для будущего этапа принятия решений.",
                "facts": [
                    f"Тип работы: {artwork_type}.",
                    f"Физический размер: {width} x {height} мм.",
                    f"Стиль интерьера: {interior_style}.",
                    f"Вариант оформления: {decor_style}.",
                ],
            },
            {
                "title": "Расчеты изображения",
                "result": "Вычислены наблюдаемые характеристики изображения. Они пока не влияют на оформление.",
                "facts": analysis_facts(image_analysis),
            },
            {
                "title": "Алгоритм отключен",
                "result": "Старая логика удалена. Новые правила еще не определены.",
                "facts": [
                    "Renderer получает только техническую спецификацию.",
                    "Паспарту отключено.",
                    "Стекло отключено.",
                    "Цвет рамы зафиксирован как #000000.",
                ],
            }
        ],
    )


def build_geometry(width, height, frame_width, mat):
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
        size_profile="manual",
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
        f"Акцентный цвет: {color_fact(palette.get('accent'))}.",
        f"Цветовая температура: {image_analysis['temperature']}.",
        f"Светлота: {image_analysis['lightness']}.",
        f"Насыщенность: {image_analysis['chroma_level']}.",
        f"Заполненность кадра: {image_analysis['frame_occupancy']}.",
        f"Контраст: {image_analysis['contrast']}.",
    ]
    if metrics:
        facts.append(
            "Метрики: "
            f"L={metrics.get('lightness')}, "
            f"C={metrics.get('chroma')}, "
            f"contrast={metrics.get('contrast')}, "
            f"occupancy={metrics.get('frame_occupancy')}, "
            f"temperature={metrics.get('temperature_score')}."
        )
    return facts


def color_fact(color):
    if not color:
        return "не найден"
    return f"{color['hex']} ({color['family']}, доля {round(color['share'] * 100, 1)}%)"


def placeholder_title(decor_style):
    return {
        "standard": "Standard: технический рендер",
        "modern": "Modern: технический рендер",
        "signature": "Signature: технический рендер",
    }[decor_style]


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
