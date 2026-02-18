PERIOD ?= 2025-01

.PHONY: up down test lint run-bank run-vat run-month-end

up:
	docker compose up -d --build

down:
	docker compose down

test:
	PYTHONPATH=src python -m pytest -q

lint:
	@echo "lint target is optional; install ruff to enable"
	@if command -v ruff >/dev/null 2>&1; then ruff check src tests; else echo "ruff not installed, skipping"; fi

run-bank:
	PYTHONPATH=src python -m finance_ai_pack.cli bank_recon --period $(PERIOD)

run-vat:
	PYTHONPATH=src python -m finance_ai_pack.cli vat_pack --period $(PERIOD)

run-month-end:
	PYTHONPATH=src python -m finance_ai_pack.cli month_end --period $(PERIOD)
