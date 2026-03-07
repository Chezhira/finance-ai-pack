# Finance AI Pack — Odoo 18 Month-End Automation

Month-end close on a multi-entity Odoo 18 instance means chasing the same three questions every period: *are all bank lines matched, does our VAT position agree with TRA, and can we proceed to reporting?* This repo automates those checks into a single CLI with deterministic, auditable outputs — no auto-posting, no secrets committed, fixture-first by default.

---

## What it does

| Command | What runs |
|---|---|
| `run bank_recon --period YYYY-MM` | Discovers bank journals → fetches statement lines → reconciles → aging buckets → tie-out vs ledger → artifacts |
| `run vat_pack --period_from YYYY-MM` | Loads Odoo VAT tax lines + TRA CSV/XLSX → monthly difference → exception register by category → HTML narrative |
| `run month_end --period YYYY-MM` | Runs both above → evaluates GREEN / AMBER / RED gating → checks for CFO override → final proceed decision |

**Outputs per command:** JSON · CSV · XLSX · HTML — written to `outputs/`, gitignored.

---

## Architecture

```
finance-ai-pack/
├── src/finance_ai_pack/
│   ├── cli.py                    # argparse entrypoint → run bank_recon / vat_pack / month_end
│   ├── config.py                 # Settings dataclass, FIXTURE_MODE env switch
│   ├── connectors/odoo/
│   │   ├── client.py             # XML-RPC client with typed error mapping
│   │   ├── fixtures_adapter.py   # Offline adapter — reads from fixtures/
│   │   └── live_adapter.py       # Live adapter — queries Odoo 18 via XML-RPC
│   ├── recon/
│   │   ├── bank/service.py       # Bank reconciliation engine
│   │   ├── vat/service.py        # VAT reconciliation + TRA import (CSV & XLSX)
│   │   ├── ledger/service.py     # Scaffold
│   │   └── petty_cash/service.py # Scaffold
│   ├── rules/
│   │   ├── month_end_gating.py   # GREEN / AMBER / RED threshold evaluator
│   │   ├── gating_rules.yml      # Configurable thresholds
│   │   └── bank_registry.yml     # Journal name → display name / currency mapping
│   └── outputs/writers.py        # JSON / CSV / XLSX / HTML writers (zero extra deps)
├── fixtures/
│   ├── odoo_statement_lines/     # banks.json + per-bank per-period line fixtures
│   ├── vat/                      # TRA templates + Odoo VAT line fixtures
│   └── overrides/                # Month-end RED override approvals
└── tests/                        # 20 unit tests, 1 live integration (opt-in)
```

---

## Quickstart (fixture mode — no Odoo required)

```bash
git clone https://github.com/Chezhira/finance-ai-pack.git
cd finance-ai-pack
pip install -e .

# Bank reconciliation
run bank_recon --period 2025-01

# VAT pack — single month
run vat_pack --period_from 2025-01

# VAT pack — date range with custom TRA file
run vat_pack --period_from 2025-01 --period_to 2025-03 \
  --tra_file fixtures/vat/tra_vat_2025-01.csv

# Full month-end gating check
run month_end --period 2025-01
```

Or via Docker:

```bash
cp .env.example .env
make up
make run-bank PERIOD=2025-01
make run-vat PERIOD=2025-01 TRA_FILE=fixtures/vat/tra_vat_2025-01.csv
make run-month-end PERIOD=2025-01
make down
```

---

## Live Odoo mode (AWS-hosted Odoo 18)

Fixture mode is the default. To connect to a live instance:

```bash
cp .env.example .env
# Edit .env:
# FIXTURE_MODE=false
# ODOO_URL=https://your-odoo.example.com
# ODOO_DB=your_db
# ODOO_USERNAME=admin
# ODOO_PASSWORD=your_password

make run-bank PERIOD=2025-01
```

Live mode notes:
- Authentication is XML-RPC username/password only.
- VAT extraction reads posted `account.move.line` records filtered by `tax_line_id.type_tax_use`.
- VAT control tie-out is best-effort when no dedicated control account mapping is available.
- No auto-posting in this release.
- No PDF parsing in this release.

---

## Month-end gating

The `month_end` command evaluates three signals against configurable thresholds in `rules/gating_rules.yml`:

| Signal | GREEN | AMBER | RED |
|---|---|---|---|
| Unmatched bank lines | 0 | ≤ 5 | > 5 |
| Unexplained amount | 0 | ≤ 1,000 | > 1,000 |
| Max VAT monthly difference | 0 | ≤ 250 | > 250 |

A **RED** status blocks proceed unless a manual override exists in `fixtures/overrides/month_end_overrides.json` with an approver name.

---

## VAT pack outputs

Running `run vat_pack` generates:

- `outputs/vat_monthly_summary.{json,csv,xlsx}` — per-period Odoo vs TRA with input/output differences
- `outputs/vat_exception_register.{json,csv,xlsx}` — categorised exceptions: timing/posting period · missing documents · wrong tax tags · credit notes/reversals · FX rounding
- `outputs/vat_pack_report.html` — narrative + summary tables

### TRA file format

```csv
period,input_vat,output_vat
2025-01,1600.00,1450.00
2025-02,1700.00,1680.00
```

Both `.csv` and `.xlsx` are accepted. Column names must be exactly `period`, `input_vat`, `output_vat`.

---

## Running tests

```bash
pip install pytest openpyxl
pytest -v
```

The live integration test (`test_live_odoo_integration.py`) is skipped unless both `LIVE_ODOO=1` and `FIXTURE_MODE=false` are set.

---

## Principles

- **Fixture-first** — all commands run offline by default; no Odoo credentials required.
- **Proposal outputs only** — generates exception registers and tie-out reports; never posts to Odoo.
- **No secrets committed** — all live credentials via environment variables; `.env` is gitignored.
- **Deterministic** — same fixtures always produce the same outputs; safe to run in CI.

---

## Author

**Zahidah Murira** · Finance Lead · CMA · CGBA · CFA Level I
[github.com/Chezhira](https://github.com/Chezhira)
