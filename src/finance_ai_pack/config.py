from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    fixture_mode: bool = True
    odoo_url: str = ""
    odoo_db: str = ""
    odoo_user: str = ""
    odoo_password: str = ""


    @staticmethod
    def from_env() -> "Settings":
        fixture_mode = os.getenv("FIXTURE_MODE", "true").lower() in {"1", "true", "yes"}
        return Settings(
            fixture_mode=fixture_mode,
            odoo_url=os.getenv("ODOO_URL", ""),
            odoo_db=os.getenv("ODOO_DB", ""),
            odoo_user=os.getenv("ODOO_USER", ""),
            odoo_password=os.getenv("ODOO_PASSWORD", ""),
        )
