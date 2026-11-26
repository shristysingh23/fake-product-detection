import threading

import numpy as np
import torch
import torch.nn.functional as functional
from PIL import Image


MODEL_ID = "openai/clip-vit-base-patch32"


class ClipModelLoadError(RuntimeError):
    pass


class ClipImageEncoder:
    def __init__(self, loader=None):
        self._loader = loader
        self._model = None
        self._processor = None
        self._device = "cpu"
        self._lock = threading.Lock()

    @property
    def loaded(self) -> bool:
        return self._model is not None and self._processor is not None

    def load_model(self) -> None:
        if self.loaded:
            return
        with self._lock:
            if self.loaded:
                return
            try:
                if self._loader is None:
                    from transformers import CLIPModel, CLIPProcessor
                    model = CLIPModel.from_pretrained(MODEL_ID)
                    processor = CLIPProcessor.from_pretrained(MODEL_ID)
                else:
                    model, processor = self._loader(MODEL_ID)

                self._device = "cuda" if torch.cuda.is_available() else "cpu"
                self._model = model.to(self._device)
                self._model.eval()
                self._processor = processor
            except Exception as exc:
                self._model = None
                self._processor = None
                raise ClipModelLoadError(
                    f"Could not load pretrained CLIP model {MODEL_ID}."
                ) from exc

    def image_embedding(self, image: Image.Image) -> np.ndarray:
        if not self.loaded:
            raise ClipModelLoadError(f"CLIP model {MODEL_ID} is not loaded.")
        if not isinstance(image, Image.Image) or image.width == 0 or image.height == 0:
            raise ValueError("Cannot create a CLIP embedding from an empty image.")

        try:
            inputs = self._processor(images=image.convert("RGB"), return_tensors="pt")
            model_inputs = {
                key: value.to(self._device) if hasattr(value, "to") else value
                for key, value in inputs.items()
            }
            with torch.inference_mode():
                features = self._model.get_image_features(**model_inputs)
                if hasattr(features, "pooler_output"):
                    features = features.pooler_output
                embedding = functional.normalize(features, p=2, dim=-1)[0]
            return embedding.detach().cpu().numpy().astype(np.float32, copy=False)
        except Exception as exc:
            raise RuntimeError("CLIP image feature extraction failed.") from exc
