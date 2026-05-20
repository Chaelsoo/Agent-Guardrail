import os
from dataclasses import dataclass
from pathlib import Path
from typing import List

_HERE = Path(__file__).resolve().parent


@dataclass
class Settings:
    fail_closed: bool
    db_enabled: bool
    db_url: str
    agent_config_path: str
    cors_origins: List[str]
    # Detection
    aegis_threshold: float
    output_block_threshold: float
    output_flag_threshold: float
    # LLM Judge
    judge_enabled: bool
    judge_api_key: str
    judge_model: str
    judge_provider: str
    judge_audit_interval: int
    taint_resolution_threshold: int


def load_settings() -> Settings:
    judge_api_key = os.getenv("LLM_JUDGE_API_KEY", "").strip()
    return Settings(
        fail_closed=os.getenv("AEGIS_FAIL_CLOSED", "false").lower() in ("1", "true", "yes"),
        db_enabled=os.getenv("AEGIS_DB_ENABLED", "true").lower() in ("1", "true", "yes"),
        db_url=os.getenv("DATABASE_URL", "sqlite:///aegis.db"),
        agent_config_path=os.getenv(
            "AEGIS_AGENT_CONFIG_PATH",
            str(_HERE.parent / "agent_config.yaml"),
        ),
        cors_origins=os.getenv("AEGIS_CORS_ORIGINS", "*").split(","),
        aegis_threshold=float(os.getenv("AEGIS_THRESHOLD", "0.5")),
        output_block_threshold=float(os.getenv("OUTPUT_BLOCK_THRESHOLD", "0.75")),
        output_flag_threshold=float(os.getenv("OUTPUT_FLAG_THRESHOLD", "0.5")),
        judge_enabled=bool(judge_api_key),
        judge_api_key=judge_api_key,
        judge_model=os.getenv("LLM_JUDGE_MODEL", "openai/gpt-4o-mini"),
        judge_provider=os.getenv("LLM_JUDGE_PROVIDER", "auto"),
        judge_audit_interval=int(os.getenv("JUDGE_AUDIT_INTERVAL", "3")),
        taint_resolution_threshold=int(os.getenv("TAINT_RESOLUTION_THRESHOLD", "2")),
    )


settings = load_settings()
