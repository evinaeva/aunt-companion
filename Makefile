PYTHON ?= python3
VENV ?= .venv

install:
	$(PYTHON) -m venv $(VENV)
	. $(VENV)/bin/activate && pip install -U pip

fmt:
	@echo "Formatting will be added by implementation."

test:
	@echo "Tests will be added by implementation."
