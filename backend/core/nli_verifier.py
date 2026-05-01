from sentence_transformers import CrossEncoder


class NLIVerifier:
    def __init__(self):
        self.model = None

    def load(self):
        self.model = CrossEncoder("cross-encoder/nli-deberta-v3-small")

    def verify(self, premise: str, hypothesis: str) -> dict:
        """
        Returns scores for [contradiction, neutral, entailment].
        The cross-encoder/nli-deberta-v3-small label order is:
        index 0 = contradiction, 1 = neutral, 2 = entailment.
        """
        if self.model is None:
            raise RuntimeError("NLIVerifier not loaded")
        scores = self.model.predict([(premise, hypothesis)], apply_softmax=True)[0]
        return {
            "contradiction": float(scores[0]),
            "neutral": float(scores[1]),
            "entailment": float(scores[2]),
        }


nli_verifier = NLIVerifier()
