# Architecture (PR #1 Scaffold)

- `src/finance_ai_pack/connectors/odoo`: Odoo access abstractions (fixture-first default).
- `src/finance_ai_pack/recon/*`: bank, ledger, and petty-cash reconciliation modules.
- `src/finance_ai_pack/rules`: bank registry and month-end gating rules.
- `src/finance_ai_pack/outputs`: writers for proposed journal and exception artifacts.
- `fixtures/`: sample data enabling no-credentials local CLI runs.
