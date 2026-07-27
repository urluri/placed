import numpy as np
from PIL import Image, ImageEnhance


def add_vignette(img, strength=0.11):
    arr = np.asarray(img).astype(np.float32)
    height, width = arr.shape[:2]
    y, x = np.ogrid[:height, :width]
    cx = width / 2
    cy = height / 2
    dx = (x - cx) / max(1, cx)
    dy = (y - cy) / max(1, cy)
    radius = np.sqrt(dx * dx + dy * dy)
    mask = 1 - np.clip((radius - 0.18) / 0.88, 0, 1) * strength
    arr *= mask[:, :, None]
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def add_film_grain(img, sigma=1.8):
    arr = np.asarray(img).astype(np.float32)
    grain = np.random.normal(0, sigma, arr.shape)
    arr += grain
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def add_chromatic_aberration(img, offset=1):
    if offset <= 0:
        return img

    arr = np.asarray(img)
    shifted = arr.copy()
    shifted[:, offset:, 0] = arr[:, :-offset, 0]
    shifted[:, :-offset, 2] = arr[:, offset:, 2]
    return Image.fromarray(shifted)


def color_grade(img):
    img = ImageEnhance.Contrast(img).enhance(1.05)
    img = ImageEnhance.Color(img).enhance(1.03)
    img = ImageEnhance.Sharpness(img).enhance(1.05)
    return img
