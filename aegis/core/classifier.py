from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
import torch


class SentinelClassifier:
    def __init__(self):
        self.pipe = None

    def load(self):
        tokenizer = AutoTokenizer.from_pretrained("qualifire/prompt-injection-sentinel")
        model = AutoModelForSequenceClassification.from_pretrained("qualifire/prompt-injection-sentinel")
        device = 0 if torch.cuda.is_available() else -1
        self.pipe = pipeline("text-classification", model=model,
                             tokenizer=tokenizer, device=device)

    def classify(self, text: str) -> dict:
        """Returns {score, label} where score is injection probability 0-1."""
        if self.pipe is None:
            raise RuntimeError("Classifier not loaded")
        result = self.pipe(text, truncation=True, max_length=512)[0]
        label = result["label"]   # "jailbreak" or "benign"
        score = result["score"] if label == "jailbreak" else 1.0 - result["score"]
        return {"score": score, "label": label, "confidence": result["score"]}

    def score(self, text: str) -> float:
        """Returns injection probability 0-1. Higher = more likely injection."""
        return self.classify(text)["score"]


classifier = SentinelClassifier()
