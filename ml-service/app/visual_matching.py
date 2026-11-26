from dataclasses import dataclass, replace
from io import BytesIO
import logging
import os
import threading

import httpx
import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError

from app.clip_service import ClipImageEncoder


logger = logging.getLogger(__name__)


class ReferenceServiceError(RuntimeError):
    pass


@dataclass(frozen=True)
class CachedReference:
    product_id: int
    fingerprint: tuple[int, int, str]
    embedding: np.ndarray
    image: Image.Image
    brand: str | None
    product_name: str | None
    expected_text: str | None
    barcode: str | None
    image_type: str


class BackendReferenceClient:
    def __init__(self, base_url: str | None = None, timeout: float = 10.0):
        self._client = httpx.Client(
            base_url=(base_url or os.getenv(
                "REFERENCE_BACKEND_URL", "http://127.0.0.1:8080"
            )).rstrip("/"),
            timeout=timeout,
        )

    def list_references(self) -> list[dict]:
        response = self._client.get("/api/ml/reference-images")
        response.raise_for_status()
        return response.json()

    def read_image(self, reference_image_id: int) -> bytes:
        response = self._client.get(
            f"/api/ml/reference-images/{reference_image_id}/content"
        )
        response.raise_for_status()
        return response.content


class VisualMatcher:
    def __init__(self, encoder: ClipImageEncoder, reference_client):
        self._encoder = encoder
        self._reference_client = reference_client
        self._cache: dict[int, CachedReference] = {}
        self._lock = threading.RLock()

    def refresh(self, force: bool = False) -> dict:
        try:
            references = self._reference_client.list_references()
        except (httpx.HTTPError, OSError) as exc:
            raise ReferenceServiceError(
                "The Spring reference-image service is unavailable."
            ) from exc

        active_ids = {
            int(item["referenceImageId"])
            for item in references
            if item.get("available", True)
        }
        errors: list[str] = []
        with self._lock:
            for reference_id in list(self._cache):
                if force or reference_id not in active_ids:
                    del self._cache[reference_id]

            for item in references:
                reference_id = int(item["referenceImageId"])
                if not item.get("available", True):
                    errors.append(
                        f"Reference image {reference_id} is missing from storage."
                    )
                    self._cache.pop(reference_id, None)
                    continue

                fingerprint = (
                    int(item.get("fileSize", 0)),
                    int(item.get("lastModifiedNanos", 0)),
                    str(item.get("contentType", "")),
                )
                product_id = int(item["productId"])
                brand = item.get("brand")
                product_name = item.get("productName")
                expected_text = item.get("expectedText")
                barcode = item.get("barcode")
                image_type = str(item.get("imageType", "UNKNOWN")).upper()
                cached = self._cache.get(reference_id)
                if not force and cached is not None and cached.fingerprint == fingerprint:
                    if (
                        cached.product_id,
                        cached.brand,
                        cached.product_name,
                        cached.expected_text,
                        cached.barcode,
                        cached.image_type,
                    ) != (
                        product_id,
                        brand,
                        product_name,
                        expected_text,
                        barcode,
                        image_type,
                    ):
                        self._cache[reference_id] = replace(
                            cached,
                            product_id=product_id,
                            brand=brand,
                            product_name=product_name,
                            expected_text=expected_text,
                            barcode=barcode,
                            image_type=image_type,
                        )
                    continue

                self._cache.pop(reference_id, None)
                try:
                    image_bytes = self._reference_client.read_image(reference_id)
                    with Image.open(BytesIO(image_bytes)) as source:
                        reference_image = ImageOps.exif_transpose(source).convert("RGB")
                        reference_image.load()
                    embedding = self._encoder.image_embedding(reference_image)
                    self._cache[reference_id] = CachedReference(
                        product_id,
                        fingerprint,
                        embedding,
                        reference_image.copy(),
                        brand,
                        product_name,
                        expected_text,
                        barcode,
                        image_type,
                    )
                except (
                    httpx.HTTPError,
                    OSError,
                    UnidentifiedImageError,
                    ValueError,
                    RuntimeError,
                ) as exc:
                    logger.warning(
                        "Could not cache visual reference image %s: %s",
                        reference_id,
                        exc,
                    )
                    errors.append(
                        f"Reference image {reference_id} could not be embedded."
                    )

            return {
                "referenceCount": len(references),
                "embeddedCount": len(self._cache),
                "errors": errors,
            }

    def cached_references(self) -> list[tuple[int, CachedReference]]:
        with self._lock:
            return list(self._cache.items())

    def match(self, uploaded_image: Image.Image) -> tuple[list[dict], list[str]]:
        try:
            refresh_result = self.refresh()
        except ReferenceServiceError as exc:
            return [], [str(exc)]

        with self._lock:
            references = list(self._cache.items())
        if not references:
            return [], refresh_result["errors"]

        try:
            upload_embedding = self._encoder.image_embedding(uploaded_image)
        except (RuntimeError, ValueError) as exc:
            return [], refresh_result["errors"] + [f"CLIP visual matching failed: {exc}"]

        matches = []
        for reference_image_id, reference in references:
            similarity = float(np.dot(upload_embedding, reference.embedding))
            matches.append({
                "productId": reference.product_id,
                "referenceImageId": reference_image_id,
                "similarityScore": float(np.clip(similarity, -1.0, 1.0)),
            })
        matches.sort(key=lambda result: result["similarityScore"], reverse=True)
        return matches, refresh_result["errors"]
