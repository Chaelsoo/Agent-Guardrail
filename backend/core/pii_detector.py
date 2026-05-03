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

        block_ents = [e for e in entities if e["type"].upper() in BLOCK_ENTITIES]
        should_block = bool(block_ents)
        block_reason = (
            f"Output contains critical PII: {', '.join(sorted({e['type'] for e in block_ents}))}"
            if should_block
            else None
        )

        # Redact all PII spans in reverse order to preserve character offsets
        redacted = text
        for e in sorted(entities, key=lambda x: x["start"], reverse=True):
            if e["type"].upper() in REDACT_ENTITIES:
                redacted = redacted[: e["start"]] + f"[{e['type']}]" + redacted[e["end"] :]

        return {
            "should_block": should_block,
            "block_reason": block_reason,
            "redacted_text": redacted,
            "entities": entities,
        }


pii_detector = PIIDetector()
