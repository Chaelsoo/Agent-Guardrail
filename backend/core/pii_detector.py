from __future__ import annotations

BLOCK_ENTITIES = {"PASSWORD", "CREDITCARDNUMBER", "SOCIALNUMBER"}
REDACT_ENTITIES = {
    "EMAIL", "EMAILADDRESS",
    "PHONE", "PHONENUMBER",
    "CREDITCARD", "CREDITCARDNUMBER",
    "SSN", "SOCIALNUMBER", "SOCIALSECURITYNUMBER",
    "PASSPORT", "PASSPORTNUMBER",
    "DRIVERSLICENSE",
    "BANKACCOUNT",
    "PASSWORD",
    "IPADDRESS",
    "IBAN",
    "BITCOINADDRESS",
    "USERNAME",
}


class PIIDetector:
    pipe = None

    def load(self) -> None:
        from transformers import pipeline
        self.pipe = pipeline(
            "token-classification",
            model="iiiorg/piiranha-v1-detect-personal-information",
            aggregation_strategy="simple",
        )

    def scan(self, text: str) -> dict:
        if not self.pipe or not text.strip():
            return {
                "should_block": False,
                "block_reason": None,
                "redacted_text": text,
                "entities": [],
            }

        results = self.pipe(text)
        entities = [
            {
                "type": r["entity_group"],
                "word": r["word"],
                "score": float(r["score"]),
                "start": r["start"],
                "end": r["end"],
            }
            for r in results
        ]

        # Redact ALL detected PII - no blocking, just redaction
        redacted = text
        for e in sorted(entities, key=lambda x: x["start"], reverse=True):
            redacted = redacted[: e["start"]] + "[REDACTED]" + redacted[e["end"] :]

        return {
            "should_block": False,  # Never block, always redact
            "block_reason": None,
            "redacted_text": redacted,
            "entities": entities,
        }


pii_detector = PIIDetector()
