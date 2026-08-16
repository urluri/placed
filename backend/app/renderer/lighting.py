import numpy as np
from PIL import Image


def add_global_lighting(img, strength=0.08):
    arr = np.asarray(img).astype(np.float32)
    height, width = arr.shape[:2]
    y, x = np.mgrid[0:height, 0:width]

    falloff = (x / max(1, width)) * 0.62 + (y / max(1, height)) * 0.38
    light = 1.0 - strength * falloff

    arr *= light[:, :, None]
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
