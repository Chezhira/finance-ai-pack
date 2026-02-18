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

## Config
- Bank registry: `src/finance_ai_pack/rules/bank_registry.yml`
- Gating rules: `src/finance_ai_pack/rules/gating_rules.yml`

## Outputs
`outputs/` is intentionally gitignored for generated artifacts; `.gitkeep` ensures the folder exists.
