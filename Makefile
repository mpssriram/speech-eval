UV ?= $(HOME)/.local/bin/uv
export PYTEST_DISABLE_PLUGIN_AUTOLOAD := 1
export TMPDIR := $(CURDIR)/.pytest_work/tmp

.PHONY: test
test:
	mkdir -p "$(TMPDIR)"
	env -u PYTHONPATH $(UV) run pytest --basetemp=.pytest_work/runs
