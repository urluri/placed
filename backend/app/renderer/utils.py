import numpy as np

PREVIEW_DPI = 72


def mm_to_px(mm):
    return int(mm * PREVIEW_DPI / 25.4)


def clamp(value, low=0, high=255):
    return max(low, min(high, value))


def adjust_color(color, factor):
    return tuple(clamp(int(channel * factor)) for channel in color)


def add_noise_to_color(base, noise):
    arr = np.zeros((noise.shape[0], noise.shape[1], 3), dtype=np.float32)
    arr[:] = base
    arr += noise[:, :, None]
    return np.clip(arr, 0, 255).astype(np.uint8)


def rect_size(rect):
    left, top, right, bottom = rect
    return right - left, bottom - top
