from __future__ import annotations

from finance_ai_pack.config import Settings


class OdooClient:
    """Placeholder client. v1 defaults to fixture mode and avoids external calls."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def is_live_enabled(self) -> bool:
        return not self.settings.fixture_mode and bool(self.settings.odoo_url)
