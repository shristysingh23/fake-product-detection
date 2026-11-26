from io import BytesIO

import cv2
import pytest
from PIL import Image

from app.preprocessing import preprocess_image


def make_image(image_format="JPEG", size=(40, 30)):
    stream = BytesIO()
    Image.new("RGB", size, color=(30, 30, 30)).save(stream, format=image_format)
    return stream.getvalue()


@pytest.mark.parametrize("image_format", ["JPEG", "PNG", "WEBP"])
def test_supported_formats_preprocess(image_format):
    image, metadata = preprocess_image(make_image(image_format))
    assert image.shape[0] > 0
    assert metadata["preprocessed"] is True
    assert metadata["format"] == image_format


def test_invalid_image_is_rejected():
    with pytest.raises(ValueError, match="readable"):
        preprocess_image(b"not an image")


def test_dark_image_is_enhanced():
    image, metadata = preprocess_image(make_image("PNG"))
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    assert gray.mean() > 20
    assert isinstance(metadata["blurScore"], float)
