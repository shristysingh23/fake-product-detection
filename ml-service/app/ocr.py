from dataclasses import dataclass
import threading

import cv2


@dataclass
class TextRegion:
    text: str
    confidence: float


_ocr_lock = threading.Lock()
_easy_reader = None
_paddle_reader = None


def _get_easy_reader():
    global _easy_reader
    if _easy_reader is None:
        try:
            import easyocr
            _easy_reader = easyocr.Reader(["en"], gpu=False)
        except Exception:
            _easy_reader = False
    return _easy_reader


def _get_paddle_reader():
    global _paddle_reader
    if _paddle_reader is None:
        try:
            from paddleocr import PaddleOCR
            _paddle_reader = PaddleOCR(use_angle_cls=True, lang="en", show_log=False)
        except Exception:
            _paddle_reader = False
    return _paddle_reader


def extract_text(image) -> tuple[list[dict], str | None]:
    regions: list[dict] = []

    with _ocr_lock:
        paddle = _get_paddle_reader()
        if paddle:
            try:
                result = paddle.ocr(image, cls=True)
                for line in result or []:
                    for region in line or []:
                        text = str(region[1][0]).strip()
                        confidence = float(region[1][1])
                        if text:
                            regions.append({"text": text, "confidence": confidence})
                return regions, None
            except Exception as exc:
                pass

        easy_reader = _get_easy_reader()
        if easy_reader:
            try:
                result = easy_reader.readtext(image, detail=1)
                for region in result:
                    text = str(region[1]).strip()
                    confidence = float(region[2])
                    if text:
                        regions.append({"text": text, "confidence": confidence})
                return regions, None
            except Exception:
                pass

    # Fallback does not invent OCR text and keeps the service usable if no OCR
    # engine is installed.
    return regions, "OCR engine unavailable. No text regions could be extracted."
