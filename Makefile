UV ?= $(HOME)/.local/bin/uv
export PYTEST_DISABLE_PLUGIN_AUTOLOAD := 1
TMPDIR := $(CURDIR)/.pytest_work/tmp

.PHONY: up down test test-host reproduce-quick reproduce
up:
	docker compose up --build

down:
	docker compose down

test:
	mkdir -p reports/reproduced
	docker compose run --rm --build --no-deps tools python -m pytest

test-host: export TMPDIR := $(CURDIR)/.pytest_work/tmp
test-host:
	mkdir -p "$(TMPDIR)"
	env -u PYTHONPATH $(UV) run pytest --basetemp=.pytest_work/runs

reproduce-quick:
	mkdir -p reports/reproduced
	docker compose run --rm --build --no-deps tools python -m speecheval.reproduce --quick

reproduce:
	mkdir -p reports/reproduced
	docker compose run --rm --build --no-deps tools python -m speecheval.reproduce
