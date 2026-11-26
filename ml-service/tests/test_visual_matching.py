from io import BytesIO

import numpy as np
from PIL import Image

from app.visual_matching import VisualMatcher


def image_bytes(color):
    output = BytesIO()
    Image.new("RGB", (4, 4), color).save(output, format="PNG")
    return output.getvalue()


class FakeReferenceClient:
    def __init__(self, references):
        self.references = references
        self.images = {}
        self.reads = []

    def list_references(self):
        return list(self.references)

    def read_image(self, reference_id):
        self.reads.append(reference_id)
        return self.images[reference_id]


class FakeEncoder:
    def __init__(self):
        self.calls = 0

    def image_embedding(self, image):
        self.calls += 1
        colors = {
            (255, 0, 0): np.array([1.0, 0.0], dtype=np.float32),
            (0, 255, 0): np.array([0.8, 0.6], dtype=np.float32),
            (0, 0, 255): np.array([0.0, 1.0], dtype=np.float32),
        }
        return colors[image.convert("RGB").getpixel((0, 0))]


def reference(reference_id, product_id, color, modified=1):
    return {
        "referenceImageId": reference_id,
        "productId": product_id,
        "contentType": "image/png",
        "fileSize": 80,
        "lastModifiedNanos": modified,
        "available": True,
        "color": color,
        "brand": "Acme",
        "productName": "Widget",
        "expectedText": "Acme Widget",
        "barcode": None,
        "imageType": "FRONT",
    }


def setup_matcher(references):
    client = FakeReferenceClient(references)
    for item in references:
        client.images[item["referenceImageId"]] = image_bytes(item["color"])
    encoder = FakeEncoder()
    return VisualMatcher(encoder, client), client, encoder


def test_cosine_similarity_ranks_reference_matches():
    refs = [
        reference(1, 10, (0, 255, 0)),
        reference(2, 20, (0, 0, 255)),
        reference(3, 30, (255, 0, 0)),
    ]
    matcher, client, _ = setup_matcher(refs)

    matches, errors = matcher.match(Image.new("RGB", (4, 4), (255, 0, 0)))

    assert errors == []
    assert [item["referenceImageId"] for item in matches] == [3, 1, 2]
    assert np.isclose(matches[0]["similarityScore"], 1.0)
    assert np.isclose(matches[1]["similarityScore"], 0.8)
    assert client.reads == [1, 2, 3]


def test_empty_reference_database_returns_no_matches():
    matcher, _, encoder = setup_matcher([])

    matches, errors = matcher.match(Image.new("RGB", (2, 2), "red"))

    assert matches == []
    assert errors == []
    assert encoder.calls == 0


def test_missing_reference_file_is_reported_and_skipped():
    item = reference(1, 10, (255, 0, 0))
    item["available"] = False
    matcher, _, encoder = setup_matcher([item])

    matches, errors = matcher.match(Image.new("RGB", (2, 2), "red"))

    assert matches == []
    assert errors == ["Reference image 1 is missing from storage."]
    assert encoder.calls == 0


def test_cache_refreshes_changed_images_and_removes_deleted_images():
    refs = [reference(1, 10, (255, 0, 0))]
    matcher, client, encoder = setup_matcher(refs)
    matcher.refresh()
    assert encoder.calls == 1

    refs[0] = reference(1, 10, (0, 255, 0), modified=2)
    client.images[1] = image_bytes((0, 255, 0))
    matcher.refresh()
    assert encoder.calls == 2

    client.references = []
    result = matcher.refresh()
    assert result["embeddedCount"] == 0


def test_forced_refresh_rebuilds_existing_embeddings():
    refs = [reference(1, 10, (255, 0, 0))]
    matcher, _, encoder = setup_matcher(refs)
    matcher.refresh()

    matcher.refresh(force=True)

    assert encoder.calls == 2


def test_metadata_refresh_updates_cached_reference_without_reembedding():
    refs = [reference(1, 10, (255, 0, 0))]
    matcher, _, encoder = setup_matcher(refs)
    matcher.refresh()

    refs[0]["expectedText"] = "Updated reference text"
    matcher.refresh()

    cached = matcher.cached_references()[0][1]
    assert encoder.calls == 1
    assert cached.expected_text == "Updated reference text"
