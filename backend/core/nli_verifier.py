from sentence_transformers import CrossEncoder

# Conservative char limit: ~512 tokens at ~1.7 chars/token.
# Prevents silent truncation inside the model which would skew entailment scores.
_MAX_CHARS = 900


class NLIVerifier:
    def __init__(self):
        self.model = None

    def load(self):
        self.model = CrossEncoder("cross-encoder/nli-deberta-v3-small")

    def verify(self, premise: str, hypothesis: str) -> dict:
        """
        Returns softmax scores for the NLI labels.
        cross-encoder/nli-deberta-v3-small id2label: 0=contradiction, 1=entailment, 2=neutral.
        """
        if self.model is None:
            raise RuntimeError("NLIVerifier not loaded")
        scores = self.model.predict(
            [(premise[:_MAX_CHARS], hypothesis[:_MAX_CHARS])],
            apply_softmax=True,
        )[0]
        return {
            "contradiction": float(scores[0]),
            "entailment": float(scores[1]),
            "neutral": float(scores[2]),
        }


nli_verifier = NLIVerifier()
