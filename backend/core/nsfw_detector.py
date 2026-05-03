from __future__ import annotations

import io


class NSFWDetector:
    pipe = None
    NSFW_THRESHOLD = 0.8

    def load(self) -> None:
        from transformers import pipeline
        self.pipe = pipeline(
            "image-classification",
            model="Falconsai/nsfw_image_detection",
        )

    def _open_image(self, image_data: bytes):
        from PIL import Image
        return Image.open(io.BytesIO(image_data)).convert("RGB")

    def is_nsfw(self, image_data: bytes) -> dict:
        if not self.pipe:
            return {"nsfw": False, "score": 0.0}
        try:
            img = self._open_image(image_data)
            results = self.pipe(img)
            score = next(
                (r["score"] for r in results if r["label"].lower() == "nsfw"),
                0.0,
            )
            return {"nsfw": float(score) > self.NSFW_THRESHOLD, "score": float(score)}
        except Exception:
            return {"nsfw": False, "score": 0.0}

    def extract_text(self, image_data: bytes) -> str:
        try:
            import pytesseract
            img = self._open_image(image_data)
            return pytesseract.image_to_string(img)
        except Exception:
            return ""


nsfw_detector = NSFWDetector()
