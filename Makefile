UV ?= $(HOME)/.local/bin/uv
export PYTEST_DISABLE_PLUGIN_AUTOLOAD := 1
TMPDIR := $(CURDIR)/.pytest_work/tmp

DATA_ARCHIVE ?=
FETCH_VOLUME = $(if $(DATA_ARCHIVE),--volume "$(abspath $(DATA_ARCHIVE)):/dataset-release.zip:ro",)
FETCH_ARGS = $(if $(DATA_ARCHIVE),--from-local /dataset-release.zip,)

.PHONY: up down test test-host fetch-data reproduce-quick reproduce reproduce-v2
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

fetch-data:
	mkdir -p reports/reproduced
	docker compose run --rm --build --no-deps $(FETCH_VOLUME) tools python scripts/fetch_data.py $(FETCH_ARGS)

reproduce-quick: fetch-data
	mkdir -p reports/reproduced
	docker compose run --rm --build --no-deps tools python -m speecheval.reproduce --quick

reproduce: fetch-data
	mkdir -p reports/reproduced
	docker compose run --rm --build --no-deps tools python -m speecheval.reproduce

reproduce-v2: fetch-data
	docker compose run --rm --build --no-deps tools python -m speecheval.evaluate_v2 --reproduce
