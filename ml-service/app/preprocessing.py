from io import BytesIO

import cv2
import numpy as np
from PIL import Image, ImageOps


MAX_DIMENSION = 2400
MAX_FILE_SIZE = 10 * 1024 * 1024
SUPPORTED_FORMATS = {"JPEG", "PNG", "WEBP"}


def decode_upload(image_bytes: bytes) -> tuple[np.ndarray, str]:
    if len(image_bytes) > MAX_FILE_SIZE:
        raise ValueError("The uploaded image exceeds the 10 MB limit.")
    if not image_bytes:
        raise ValueError("The uploaded image is empty.")

    try:
        with Image.open(BytesIO(image_bytes)) as pil_image:
            pil_format = (pil_image.format or "").upper()
            if pil_format not in SUPPORTED_FORMATS:
                raise ValueError("Unsupported file format. Please upload JPEG, PNG or WebP.")
            pil_image = ImageOps.exif_transpose(pil_image)
            pil_image.load()
            pil_image = pil_image.convert("RGB")
            rgb = np.asarray(pil_image)
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError("The uploaded file is not a valid readable image.") from exc

    if rgb.size == 0:
        raise ValueError("The uploaded image is empty.")

    cv_image = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    return cv_image, pil_format


def preprocess_image(image_bytes: bytes) -> tuple[np.ndarray, dict]:
    image, image_format = decode_upload(image_bytes)
    height, width = image.shape[:2]
    original_dimensions = {"width": width, "height": height}

    scale = min(1.0, MAX_DIMENSION / max(width, height))
    if scale < 1.0:
        image = cv2.resize(
            image,
            (max(1, int(width * scale)), max(1, int(height * scale))),
            interpolation=cv2.INTER_AREA,
        )

    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    luminance, a_channel, b_channel = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced_luminance = clahe.apply(luminance)
    enhanced = cv2.cvtColor(
        cv2.merge((enhanced_luminance, a_channel, b_channel)),
        cv2.COLOR_LAB2BGR,
    )

    gray = cv2.cvtColor(enhanced, cv2.COLOR_BGR2GRAY)
    laplacian_variance = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    if laplacian_variance < 100:
        enhanced = cv2.GaussianBlur(enhanced, (3, 3), 0)

    return enhanced, {
        "originalDimensions": original_dimensions,
        "format": image_format,
        "orientationCorrected": True,
        "blurScore": round(laplacian_variance, 2),
        "preprocessed": True,
    }
