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
        Returns {layer1_flagged, flagged_tokens}.
        Runs token classification on the raw tool_text string and collects
        any tokens labelled UNAUTHORIZED (BIO prefix stripped).
        """
        if self.pipe is None:
            raise RuntimeError("ToolCallVerifier not loaded")
        results = self.pipe(tool_text)
        flagged = []
        for r in results:
            label = str(r.get("entity_group", r.get("entity", ""))).upper()
            for prefix in ("B-", "I-"):
                if label.startswith(prefix):
                    label = label[len(prefix):]
                    break
            if label == "UNAUTHORIZED":
                flagged.append(r.get("word", "").strip())
        return {
            "layer1_flagged": bool(flagged),
            "flagged_tokens": flagged,
        }


toolcall_verifier = ToolCallVerifier()
