import torch
from transformers import pipeline


class ToolCallVerifier:
    def __init__(self):
        self.pipe = None

    def load(self):
        device = 0 if torch.cuda.is_available() else -1
        self.pipe = pipeline(
            "token-classification",
            model="llm-semantic-router/toolcall-verifier",
            device=device,
            aggregation_strategy="simple",
        )

    def verify(self, tool_text: str) -> dict:
        """
        Returns {layer1_flagged, flagged_tokens, token_scores}.
        Runs token classification on the raw tool_text string and collects
        any tokens labelled UNAUTHORIZED (BIO prefix stripped).
        token_scores is a list of (token, score) tuples.
        """
        if self.pipe is None:
            raise RuntimeError("ToolCallVerifier not loaded")
        results = self.pipe(tool_text)
        flagged = []
        token_scores = []
        for r in results:
            label = str(r.get("entity_group", r.get("entity", ""))).upper()
            for prefix in ("B-", "I-"):
                if label.startswith(prefix):
                    label = label[len(prefix):]
                    break
            if label == "UNAUTHORIZED":
                token = r.get("word", "").strip()
                score = float(r.get("score", 0.0))
                flagged.append(token)
                token_scores.append((token, score))
        return {
            "layer1_flagged": bool(flagged),
            "flagged_tokens": flagged,
            "token_scores": token_scores,
        }


toolcall_verifier = ToolCallVerifier()
