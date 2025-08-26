# Cross-Platform Makefile for Growth System v2
# Automatically detects OS and provides appropriate commands

.PHONY: venv install run_ui run_baseline test lint clean help detect_os

# Detect operating system - default to Unix/Linux/macOS
# Windows users will be redirected to Python script
PY := python3
VENV := venv
PIP := $(VENV)/bin/pip
PYTHON := $(VENV)/bin/python
PYTEST := $(VENV)/bin/pytest
STREAMLIT := $(VENV)/bin/streamlit
IS_WINDOWS := 0

# Help target
help:
	@echo "🚀 Growth System v2 - Makefile (Unix/Linux/macOS)"
	@echo "================================================="
	@echo ""
	@echo "Available commands:"
	@echo "  make install      - Install dependencies and setup environment"
	@echo "  make run_ui       - Launch the Streamlit UI"
	@echo "  make run_baseline - Run baseline simulation"
	@echo "  make test         - Run test suite"
	@echo "  make lint         - Run code linting"
	@echo "  make clean        - Clean up generated files"
	@echo "  make help         - Show this help message"
	@echo ""
	@echo "💡 For Windows users: Use 'python setup_cross_platform.py' instead"
	@echo "Python: $(PY)"
	@echo "Virtual Environment: $(VENV)"
	@echo ""

# Detect OS and show appropriate message
detect_os:
	@echo "🔍 Operating System Detection:"
	@echo "  Detected OS: Unix/Linux/macOS"
	@echo "  Python Command: $(PY)"
	@echo "  Virtual Environment: $(VENV)"
	@echo ""

# Virtual environment setup
venv:
	@echo "📦 Creating virtual environment..."
	$(PY) -m venv $(VENV)
	$(PIP) install --upgrade pip

# Install dependencies
install: detect_os venv
	@echo "📚 Installing dependencies..."
	$(PIP) install -r requirements.txt

# Run UI
run_ui: install
	@echo "🌐 Launching Streamlit UI..."
	$(STREAMLIT) run ui/app.py

# Run baseline simulation
run_baseline: install
	@echo "🎯 Running baseline simulation..."
	$(PYTHON) simulate_growth.py --preset baseline

# Run tests
test: install
	@echo "🧪 Running test suite..."
	$(PYTEST) -q

# Run linting
lint:
	@echo "🔍 Running code linting..."
	$(PYTHON) make_lint.py

# Clean up generated files
clean:
	@echo "🧹 Cleaning up generated files..."
	rm -rf $(VENV)
	find . -name "__pycache__" -type d -prune -exec rm -rf {} + 2>/dev/null || true
	find . -name ".pytest_cache" -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Cleanup complete!"

# Default target
.DEFAULT_GOAL := help


