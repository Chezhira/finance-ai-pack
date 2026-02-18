# PR #1 Scaffold Plan — Finance AI Pack v1 (Odoo 18-first)

## Objective
Deliver the initial repository scaffold for Finance AI Pack v1 with an Odoo 18-first architecture, runnable locally via Docker Compose, and testable without real Odoo credentials.

## Scope Anchors
- Docker Compose with **Postgres** + **Python app** service.
- First-pass repository structure for connectors, reconciliation modules, rules, outputs, CLI, tests, and docs.
- Multi-bank enabled by default, with pilot-bank fixtures for **NMB (TZS)** and **NBC (USD)**.
- Month-end gating model: **Green / Amber / Red**, with blocking on Red unless a recorded override exists.
- v1 explicitly avoids PDF parsing; uses Odoo statement lines (CSV/PDF ingestion as future optional add-on).
- No auto-posting to Odoo; output is proposed journals and exception artifacts only.
- Seed fixtures for local CLI runs with no live Odoo credentials.
- CLI commands:
  - `run bank_recon --period YYYY-MM`
  - `run vat_pack --period YYYY-MM`
  - `run month_end --period YYYY-MM`
- Include `.env.example`, `.gitignore`, and README run instructions.

## Delivery Plan

### 1) Repo + Runtime Scaffold
1. Add top-level package layout and module placeholders for connectors, recon engines, rules, outputs, CLI entrypoint, tests, and docs.
2. Add Python dependency and tooling baseline (`pyproject.toml`, package init files).
3. Add Docker setup:
   - `docker-compose.yml` with `db` (Postgres) and `app` (Python).
   - App container mounts source and reads `.env` variables.
   - DB initialized with default non-prod credentials for local development.

### 2) Config + Environment
1. Add `.env.example` with:
   - Odoo host/db/user/password placeholders.
   - Reconciliation defaults.
   - Month-end override and output-path settings.
2. Add `.gitignore` for Python caches, virtualenvs, test artifacts, build outputs, and local env files.

### 3) Domain Skeletons (No Heavy Logic Yet)
1. `connectors/odoo`: client abstraction and mock/fake adapter route.
2. `recon/bank`: bank reconciliation orchestrator with multi-bank discovery contract (fixture-driven for v1 scaffold).
3. `recon/ledger`: ledger-side comparison and mismatch data model placeholders.
4. `recon/petty_cash`: placeholder module integrated into month-end pipeline contract.
5. `rules`: gating evaluator for Green/Amber/Red and Red override recording schema.
6. `outputs`: renderers for proposed journals/exceptions (JSON/CSV artifact stubs).

### 4) CLI and Command Contracts
1. Add CLI entrypoint (`run`) that supports:
   - `bank_recon --period YYYY-MM`
   - `vat_pack --period YYYY-MM`
   - `month_end --period YYYY-MM`
2. Add period parsing/validation and deterministic fixture-backed execution.
3. Ensure command output explicitly states **“no auto-posting performed”**.

### 5) Fixture-First Execution
1. Add fixture files for:
   - Odoo statement lines for NMB TZS and NBC USD.
   - Ledger snapshots / VAT sample totals.
   - Expected status outcomes and exception examples.
2. Ensure all commands run offline against fixtures by default.

### 6) Tests + Documentation
1. Add baseline tests for command invocation, period parsing, gating behavior, and Red override requirement.
2. Update README with:
   - setup steps,
   - Docker run instructions,
   - local CLI examples,
   - fixture-only mode explanation,
   - non-goals (no PDF parsing, no auto-posting).

## Proposed Acceptance Criteria
- `docker compose up` starts `db` and `app` without manual patching.
- CLI commands execute for a sample period without real Odoo credentials.
- Bank recon includes both pilot banks from fixtures and is architected for later auto-discovery.
- `month_end` returns Green/Amber/Red and blocks Red without recorded override.
- Outputs are proposal artifacts only (journals/exceptions), with no posting side effects.
- README + `.env.example` + `.gitignore` fully present and coherent.

## File Checklist for PR #1

### Root
- [ ] `docker-compose.yml`
- [ ] `Dockerfile`
- [ ] `pyproject.toml`
- [ ] `.env.example`
- [ ] `.gitignore`
- [ ] `README.md` (expanded run instructions)

### Source Package
- [ ] `src/finance_ai_pack/__init__.py`
- [ ] `src/finance_ai_pack/cli.py`
- [ ] `src/finance_ai_pack/config.py`

### Connectors
- [ ] `src/finance_ai_pack/connectors/odoo/__init__.py`
- [ ] `src/finance_ai_pack/connectors/odoo/client.py`
- [ ] `src/finance_ai_pack/connectors/odoo/fixtures_adapter.py`

### Reconciliation Modules
- [ ] `src/finance_ai_pack/recon/bank/__init__.py`
- [ ] `src/finance_ai_pack/recon/bank/service.py`
- [ ] `src/finance_ai_pack/recon/ledger/__init__.py`
- [ ] `src/finance_ai_pack/recon/ledger/service.py`
- [ ] `src/finance_ai_pack/recon/petty_cash/__init__.py`
- [ ] `src/finance_ai_pack/recon/petty_cash/service.py`

### Rules + Outputs
- [ ] `src/finance_ai_pack/rules/__init__.py`
- [ ] `src/finance_ai_pack/rules/month_end_gating.py`
- [ ] `src/finance_ai_pack/outputs/__init__.py`
- [ ] `src/finance_ai_pack/outputs/writers.py`

### Fixtures
- [ ] `fixtures/odoo_statement_lines/nmb_tzs_2025-01.json`
- [ ] `fixtures/odoo_statement_lines/nbc_usd_2025-01.json`
- [ ] `fixtures/ledger/ledger_snapshot_2025-01.json`
- [ ] `fixtures/vat/vat_inputs_2025-01.json`
- [ ] `fixtures/overrides/month_end_overrides.json`

### Tests
- [ ] `tests/test_cli_commands.py`
- [ ] `tests/test_period_validation.py`
- [ ] `tests/test_month_end_gating.py`
- [ ] `tests/test_fixture_mode.py`

### Docs
- [ ] `docs/architecture.md`
- [ ] `docs/operating_model.md`
- [x] `docs/PR1_SCaffold_Plan.md`
