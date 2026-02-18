from __future__ import annotations

import json
from pathlib import Path


def load_statement_banks(fixtures_dir: Path) -> list[dict]:
    return json.loads((fixtures_dir / "odoo_statement_lines" / "banks.json").read_text())
