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
    aegis_trajectory_weight: float
    aegis_flag_threshold: float


def load_settings() -> Settings:
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
        aegis_trajectory_weight=float(os.getenv("AEGIS_TRAJECTORY_WEIGHT", "0.3")),
        aegis_flag_threshold=float(os.getenv("AEGIS_FLAG_THRESHOLD", "0.3")),
    )


settings = load_settings()
