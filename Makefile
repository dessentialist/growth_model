# Simple packaging makefile for local dev and UX Phases 12–13

.PHONY: venv install run_ui run_baseline test lint clean

PY := python3
VENV := venv
PIP := $(VENV)/bin/pip
PYTHON := $(VENV)/bin/python
PYTEST := $(VENV)/bin/pytest
STREAMLIT := $(VENV)/bin/streamlit

venv:
	$(PY) -m venv $(VENV)
	$(PIP) install --upgrade pip

install: venv
	$(PIP) install -r requirements.txt

run_ui: install
	$(STREAMLIT) run ui/app.py

run_baseline: install
	$(PYTHON) simulate_fff_growth.py --preset baseline

test: install
	$(PYTEST) -q

lint:
	$(PYTHON) make_lint.py

clean:
	rm -rf $(VENV)
	find . -name "__pycache__" -type d -prune -exec rm -rf {} +
	find . -name ".pytest_cache" -type d -prune -exec rm -rf {} +


