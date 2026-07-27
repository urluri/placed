import numpy as np
from PIL import Image


def add_global_lighting(img, strength=0.08):
    arr = np.asarray(img).astype(np.float32)
    height, width = arr.shape[:2]
    y, x = np.mgrid[0:height, 0:width]

    light = (
        1.0
        + strength * (1 - x / max(1, width))
        + strength * (1 - y / max(1, height))
        - strength
    )

    arr *= light[:, :, None]
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
