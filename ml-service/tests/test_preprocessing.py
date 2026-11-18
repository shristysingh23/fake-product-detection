"""Unit tests for OpenCV image decoding and preprocessing helpers."""

import cv2
import numpy as np
import pytest

from app.preprocessing import (
    PreprocessResult,
    decode_image,
    preprocess_image,
    reduce_noise,
    resize_to_max_side,
    to_normalized_float,
    trim_uniform_borders,
)


def encode_png(image):
    """Encode a synthetic BGR image to PNG bytes entirely in memory."""
    success, encoded = cv2.imencode(".png", image)
    assert success
    return encoded.tobytes()


# Check that valid PNG bytes decode to the original dimensions and BGR uint8 format.
def test_decode_image_valid_png_returns_bgr_uint8_with_correct_size():
    source = np.zeros((24, 36, 3), dtype=np.uint8)

    decoded = decode_image(encode_png(source))

    assert decoded.shape == (24, 36, 3)
    assert decoded.dtype == np.uint8
    assert (decoded.shape[1], decoded.shape[0]) == (36, 24)


# Check that arbitrary non-image bytes raise the specified decode error.
def test_decode_image_random_bytes_raises_value_error():
    with pytest.raises(ValueError, match="^Could not decode image\\.$"):
        decode_image(b"random bytes that are not an image")


# Check that empty bytes raise the specified decode error.
def test_decode_image_empty_bytes_raises_value_error():
    with pytest.raises(ValueError, match="^Could not decode image\\.$"):
        decode_image(b"")


# Check that a 2000 by 1000 image shrinks to 1024 by 512 without distortion.
def test_resize_to_max_side_shrinks_and_keeps_aspect_ratio():
    source = np.zeros((1000, 2000, 3), dtype=np.uint8)

    resized = resize_to_max_side(source, max_side=1024)

    assert (resized.shape[1], resized.shape[0]) == (1024, 512)
    assert resized.shape[1] / resized.shape[0] == source.shape[1] / source.shape[0]


# Check that an image already below the maximum is returned pixel-for-pixel unchanged.
def test_resize_to_max_side_leaves_small_image_unchanged():
    source = np.random.default_rng(0).integers(0, 256, (300, 400, 3), dtype=np.uint8)

    resized = resize_to_max_side(source)

    assert resized.shape == source.shape
    assert np.array_equal(resized, source)


# Check that max_side values below one are rejected.
def test_resize_to_max_side_rejects_zero_max_side():
    with pytest.raises(ValueError):
        resize_to_max_side(np.zeros((4, 4, 3), dtype=np.uint8), max_side=0)


# Check that plain white borders crop to the colored square plus the requested margins.
def test_trim_uniform_borders_crops_square_and_keeps_its_pixels():
    source = np.full((400, 400, 3), 255, dtype=np.uint8)
    source[100:300, 100:300] = [10, 20, 200]

    cropped = trim_uniform_borders(source)

    assert cropped.shape[:2] == (220, 220)
    assert np.count_nonzero(np.all(cropped == [10, 20, 200], axis=2)) == 200 * 200


# Check that an image with no foreground difference is returned unchanged.
def test_trim_uniform_borders_leaves_uniform_image_unchanged():
    source = np.full((40, 60, 3), 127, dtype=np.uint8)

    trimmed = trim_uniform_borders(source)

    assert trimmed is source
    assert np.array_equal(trimmed, source)


# Check that the safety rule rejects a crop under one quarter of the original area.
def test_trim_uniform_borders_keeps_image_when_crop_is_too_small():
    source = np.full((400, 400, 3), 255, dtype=np.uint8)
    source[200, 200] = [0, 0, 0]
    # A one-pixel speck expands to 21x21 with the 10-pixel margin (441 pixels),
    # which is less than 25% of the 160,000-pixel input, so safety must skip it.

    trimmed = trim_uniform_borders(source)

    assert trimmed is source


# Check that bilateral filtering lowers seeded noise while preserving shape and dtype.
def test_reduce_noise_lowers_pixel_standard_deviation():
    rng = np.random.default_rng(0)
    noise = rng.normal(0, 35, size=(128, 128, 3))
    source = np.clip(128 + noise, 0, 255).astype(np.uint8)

    filtered = reduce_noise(source)

    assert filtered.shape == source.shape
    assert filtered.dtype == source.dtype
    assert filtered.std() < source.std()


# Check that normalized output is float32 in range and maps 255 to 1.0.
def test_to_normalized_float_scales_uint8_to_zero_one():
    source = np.full((5, 7, 3), 255, dtype=np.uint8)

    normalized = to_normalized_float(source)

    assert normalized.dtype == np.float32
    assert normalized.min() >= 0.0
    assert normalized.max() <= 1.0
    assert np.all(normalized == 1.0)


# Check that the pipeline reports its input/output sizes and all four steps in order.
def test_preprocess_image_returns_sizes_and_ordered_steps():
    source = np.full((30, 40, 3), 127, dtype=np.uint8)

    result = preprocess_image(encode_png(source))

    assert isinstance(result, PreprocessResult)
    assert result.original_size == (40, 30)
    assert result.processed_size == (result.image.shape[1], result.image.shape[0])
    assert result.steps == [
        "decode_image",
        "resize_to_max_side",
        "trim_uniform_borders:skipped",
        "reduce_noise",
    ]


# Check that invalid encoded bytes fail at the decode step of the pipeline.
def test_preprocess_image_invalid_bytes_raises_value_error():
    with pytest.raises(ValueError, match="^Could not decode image\\.$"):
        preprocess_image(b"not a PNG")
