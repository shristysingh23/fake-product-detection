from typing import Iterable

import cv2


def detect_barcodes(image) -> tuple[list[dict], list[dict], str | None]:
    barcodes: list[dict] = []
    qr_codes: list[dict] = []

    try:
        detector = cv2.QRCodeDetector()
        ok, decoded_info, points, _ = detector.detectAndDecodeMulti(image)
        if ok:
            for value in decoded_info:
                value = str(value).strip()
                if value:
                    qr_codes.append({"type": "QR_CODE", "value": value})
    except Exception:
        pass

    try:
        from pyzbar.pyzbar import decode
        from pyzbar.locations import bounding_rect
        from PIL import Image
        import numpy as np
        pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        for decoded in decode(pil_image):
            value = decoded.data.decode("utf-8", errors="replace").strip()
            if not value:
                continue
            type_name = str(decoded.type)
            if type_name.upper().startswith("QR"):
                qr_codes.append({"type": type_name, "value": value})
            else:
                barcodes.append({"type": type_name, "value": value})
    except Exception:
        pass

    if not barcodes and not qr_codes:
        return barcodes, qr_codes, None
    return barcodes, qr_codes, None
