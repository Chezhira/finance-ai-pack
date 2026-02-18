# Finance AI Pack (Odoo 18-first)

Scaffold for month-end automation, VAT pack support, and multi-bank reconciliation checks.

## Principles
- Fixture-only mode by default (no live Odoo creds required).
- No PDF parsing in v1 (use Odoo statement lines / fixtures).
- No auto-posting to Odoo (proposal outputs and exceptions only).

## Repo Structure
- `src/finance_ai_pack/connectors/odoo`
- `src/finance_ai_pack/recon/bank`
- `src/finance_ai_pack/recon/ledger`
- `src/finance_ai_pack/recon/petty_cash`
- `src/finance_ai_pack/rules`
- `src/finance_ai_pack/outputs`
- `src/finance_ai_pack/cli.py`
- `tests/`
- `docs/`

## Quickstart
1. Copy `.env.example` to `.env`.
2. Start services: `make up`
3. Run commands:
   - `make run-bank PERIOD=2025-01`
   - `make run-vat PERIOD=2025-01`
   - `make run-month-end PERIOD=2025-01`
4. Run tests: `make test`
5. Stop services: `make down`

## Live Odoo mode (AWS-hosted Odoo 18)
Fixture mode remains the default. To opt into live Odoo:

1. Copy `.env.example` to `.env`.
2. Set `FIXTURE_MODE=false`.
3. Populate:
   - `ODOO_URL`
   - `ODOO_DB`
   - `ODOO_USERNAME` (or `ODOO_USER` alias)
   - `ODOO_PASSWORD`
4. Run: `make run-bank PERIOD=YYYY-MM`

Notes:
- Live integration uses XML-RPC username/password auth only.
- Integration tests are opt-in and only run when both `LIVE_ODOO=1` and `FIXTURE_MODE=false`.
- CI should keep fixture defaults and never run live tests by default.
- No PDF parsing in this release.
- No auto-posting in this release.

## Config
- Bank registry: `src/finance_ai_pack/rules/bank_registry.yml`
- Gating rules: `src/finance_ai_pack/rules/gating_rules.yml`

## Outputs
`outputs/` is intentionally gitignored for generated artifacts; `.gitkeep` ensures the folder exists.
Bank reconciliation now writes JSON, CSV, XLSX, and HTML artifacts, plus `bank_controls_rollup` for month-end gating input.
