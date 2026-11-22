"""Small OpenCV preprocessing pipeline for later product-image analysis.

Images stay as uint8 BGR arrays for OCR and YOLO. The pipeline decodes image
bytes, resizes large images to a manageable size, trims plain uniform borders,
and reduces noise while preserving edges. Border trimming only removes plain
borders; it does not locate the product (YOLO will do that on Day 9). A separate
helper can create normalized float arrays for later models when they need them.
"""

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass(frozen=True)
class PreprocessResult:
    """Processed image plus the sizes and steps needed to describe the work."""

    image: np.ndarray
    original_size: tuple[int, int]
    processed_size: tuple[int, int]
    steps: list[str]


def decode_image(data: bytes) -> np.ndarray:
    """Decode encoded image bytes as a three-channel BGR uint8 array."""
    if not data:
        raise ValueError("Could not decode image.")

    encoded = np.frombuffer(data, np.uint8)
    image = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Could not decode image.")
    return image


def resize_to_max_side(image: np.ndarray, max_side: int = 1024) -> np.ndarray:
    """Shrink large images to max_side while keeping their aspect ratio."""
    if max_side < 1:
        raise ValueError("max_side must be at least 1.")

    height, width = image.shape[:2]
    longest_side = max(height, width)
    if longest_side <= max_side:
        return image

    scale = max_side / longest_side
    new_width = max(1, int(round(width * scale)))
    new_height = max(1, int(round(height * scale)))
    return cv2.resize(
        image,
        (new_width, new_height),
        interpolation=cv2.INTER_AREA,
    )


def trim_uniform_borders(
    image: np.ndarray,
    tolerance: int = 12,
    margin: int = 10,
) -> np.ndarray:
    """Crop plain uniform borders while keeping a safety margin around content.

    This only trims plain borders; it does not locate the product. YOLO will
    locate products on Day 9.
    """
    height, width = image.shape[:2]

    # Use only the outer one-pixel frame to estimate the plain background color.
    if height == 1:
        outer_frame = image[0, :, :]
    elif width == 1:
        outer_frame = image[:, 0, :]
    else:
        outer_frame = np.concatenate(
            (
                image[0, :, :],
                image[-1, :, :],
                image[1:-1, 0, :],
                image[1:-1, -1, :],
            ),
            axis=0,
        )
    background = np.median(outer_frame, axis=0)

    # Mark pixels whose largest channel difference exceeds the tolerance.
    differences = np.abs(image.astype(np.int16) - background)
    foreground_mask = np.max(differences, axis=2) > tolerance
    foreground_y, foreground_x = np.where(foreground_mask)
    if foreground_x.size == 0:
        return image

    # Expand the foreground bounds by the requested margin and clamp to edges.
    left = max(0, int(foreground_x.min()) - margin)
    right = min(width, int(foreground_x.max()) + 1 + margin)
    top = max(0, int(foreground_y.min()) - margin)
    bottom = min(height, int(foreground_y.max()) + 1 + margin)
    cropped = image[top:bottom, left:right]

    # Keep the original whenever a small crop could discard too much context.
    if cropped.shape[0] * cropped.shape[1] < 0.25 * height * width:
        return image
    return cropped


def reduce_noise(image: np.ndarray) -> np.ndarray:
    """Smooth noise without changing the image's shape or data type."""
    # Bilateral filtering smooths noise while keeping edges sharp, which matters
    # for text and logo outlines.
    return cv2.bilateralFilter(image, d=5, sigmaColor=50, sigmaSpace=50)


def to_normalized_float(image: np.ndarray) -> np.ndarray:
    """Scale an image to float32 values from 0.0 to 1.0 for later models."""
    return image.astype(np.float32) / 255.0


def preprocess_image(data: bytes, max_side: int = 1024) -> PreprocessResult:
    """Decode, resize, trim plain borders, and reduce noise in that order."""
    decoded = decode_image(data)
    original_height, original_width = decoded.shape[:2]

    resized = resize_to_max_side(decoded, max_side=max_side)
    trimmed = trim_uniform_borders(resized)
    trim_step = (
        "trim_uniform_borders:cropped"
        if trimmed.shape[:2] != resized.shape[:2]
        else "trim_uniform_borders:skipped"
    )
    processed = reduce_noise(trimmed)
    processed_height, processed_width = processed.shape[:2]

    return PreprocessResult(
        image=processed,
        original_size=(original_width, original_height),
        processed_size=(processed_width, processed_height),
        steps=[
            "decode_image",
            "resize_to_max_side",
            trim_step,
            "reduce_noise",
        ],
    )
