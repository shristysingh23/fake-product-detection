import numpy as np
import pytest
import torch
from PIL import Image

from app.clip_service import ClipImageEncoder, ClipModelLoadError, MODEL_ID


class FakeModel:
    def to(self, device):
        return self

    def eval(self):
        return self

    def get_image_features(self, **inputs):
        return torch.tensor([[3.0, 4.0]])


class FakeProcessor:
    def __call__(self, *, images, return_tensors):
        assert images.mode == "RGB"
        assert return_tensors == "pt"
        return {}


def test_model_loads_once_and_image_embedding_is_normalized():
    calls = []

    def loader(model_id):
        calls.append(model_id)
        return FakeModel(), FakeProcessor()

    encoder = ClipImageEncoder(loader=loader)
    encoder.load_model()
    encoder.load_model()
    embedding = encoder.image_embedding(Image.new("RGB", (10, 10), "red"))

    assert calls == [MODEL_ID]
    assert np.allclose(embedding, [0.6, 0.8])
    assert np.isclose(np.linalg.norm(embedding), 1.0)


def test_model_loading_failure_is_reported():
    encoder = ClipImageEncoder(loader=lambda _: (_ for _ in ()).throw(OSError("offline")))
    with pytest.raises(ClipModelLoadError, match="Could not load"):
        encoder.load_model()


def test_invalid_image_input_is_rejected():
    encoder = ClipImageEncoder(loader=lambda _: (FakeModel(), FakeProcessor()))
    encoder.load_model()
    with pytest.raises(ValueError, match="empty image"):
        encoder.image_embedding(b"not an image")
