import numpy as np

from PIL import Image
from PIL import ImageFilter
from PIL import ImageEnhance


# ==========================================================
# Цветовые палитры
# ==========================================================

WALL_STYLES = {

    "paint": {
        "base": (236, 234, 230),
        "noise": 4,
        "blur": 0.7
    },

    "gallery": {
        "base": (242, 241, 238),
        "noise": 2,
        "blur": 0.5
    },

    "plaster": {
        "base": (239, 236, 228),
        "noise": 6,
        "blur": 0.8
    },

    "concrete": {
        "base": (220, 221, 222),
        "noise": 8,
        "blur": 1.2
    }

}


# ==========================================================
# Простая фрактальная текстура
# ==========================================================

def fractal_noise(width, height, octaves=5):

    result = np.zeros((height, width))

    amplitude = 1.0

    total = 0

    for i in range(octaves):

        scale = 2 ** i

        small = np.random.rand(
            max(2, height // scale),
            max(2, width // scale)
        )

        img = Image.fromarray(
            (small * 255).astype(np.uint8)
        )

        img = img.resize(
            (width, height),
            Image.Resampling.BICUBIC
        )

        arr = np.asarray(img) / 255.0

        result += arr * amplitude

        total += amplitude

        amplitude *= 0.5

    result /= total

    return result


# ==========================================================
# Виньетка
# ==========================================================

def vignette(width, height):

    y, x = np.ogrid[:height, :width]

    cx = width / 2
    cy = height / 2

    dx = (x - cx) / cx
    dy = (y - cy) / cy

    r = np.sqrt(dx * dx + dy * dy)

    mask = 1 - np.clip((r - 0.2) / 0.8, 0, 1)

    mask = 0.90 + mask * 0.10

    return mask


# ==========================================================
# Основная функция
# ==========================================================

def create_wall(width,
                height,
                style="paint"):

    cfg = WALL_STYLES[style]

    base = np.zeros(
        (height, width, 3),
        dtype=np.float32
    )

    base[:] = cfg["base"]

    # --------------------------------------------------
    # Крупная текстура
    # --------------------------------------------------

    large = fractal_noise(width, height, 4)

    # --------------------------------------------------
    # Мелкая текстура
    # --------------------------------------------------

    fine = np.random.normal(
        0,
        1,
        (height, width)
    )

    # --------------------------------------------------
    # Объединяем
    # --------------------------------------------------

    noise = (
        large * cfg["noise"]
        +
        fine * 0.8
    )

    for c in range(3):
        base[:, :, c] += noise

    # --------------------------------------------------
    # Глобальное освещение
    # --------------------------------------------------

    y, x = np.mgrid[0:height, 0:width]

    light = (
        1.03
        -
        0.05 * (x / width)
        -
        0.05 * (y / height)
    )

    for c in range(3):
        base[:, :, c] *= light

    # --------------------------------------------------
    # Виньетка
    # --------------------------------------------------

    vig = vignette(width, height)

    for c in range(3):
        base[:, :, c] *= vig

    # --------------------------------------------------
    # Ограничение
    # --------------------------------------------------

    base = np.clip(base, 0, 255)

    img = Image.fromarray(
        base.astype(np.uint8)
    )

    # --------------------------------------------------
    # Легкое размытие
    # --------------------------------------------------

    img = img.filter(
        ImageFilter.GaussianBlur(cfg["blur"])
    )

    # --------------------------------------------------
    # Небольшой контраст
    # --------------------------------------------------

    img = ImageEnhance.Contrast(img).enhance(1.03)

    # --------------------------------------------------
    # Небольшая насыщенность
    # --------------------------------------------------

    img = ImageEnhance.Color(img).enhance(0.98)

    return img
