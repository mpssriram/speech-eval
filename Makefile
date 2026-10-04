UV ?= $(HOME)/.local/bin/uv
export PYTEST_DISABLE_PLUGIN_AUTOLOAD := 1

.PHONY: test
test:
	env -u PYTHONPATH $(UV) run pytest
