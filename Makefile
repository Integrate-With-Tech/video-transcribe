# Makefile for Video Transcription Tool

.PHONY: help install install-dev test lint format clean build publish setup-dev

# Default target
help:
	@echo "Video Transcription Tool - Development Commands"
	@echo "=============================================="
	@echo ""
	@echo "Setup:"
	@echo "  make setup-dev    Set up development environment"
	@echo "  make install      Install the package"
	@echo "  make install-dev  Install with development dependencies"
	@echo ""
	@echo "Development:"
	@echo "  make test         Run tests with coverage"
	@echo "  make lint         Run linting checks"
	@echo "  make format       Format code with black"
	@echo "  make type-check   Run type checking with mypy"
	@echo ""
	@echo "Build & Publish:"
	@echo "  make build        Build distribution packages"
	@echo "  make clean        Clean build artifacts"
	@echo "  make publish      Publish to PyPI (requires credentials)"
	@echo ""
	@echo "Utilities:"
	@echo "  make security     Run security checks"
	@echo "  make requirements Update requirements files"

# Setup development environment
setup-dev:
	@echo "🛠️  Setting up development environment..."
	python -m venv venv
	@echo "📦 Created virtual environment. Activate with:"
	@echo "   source venv/bin/activate  # Linux/macOS"
	@echo "   venv\\Scripts\\activate     # Windows"
	@echo ""
	@echo "Then run: make install-dev"

# Install the package
install:
	pip install -e .

# Install with development dependencies
install-dev:
	pip install --upgrade pip
	pip install -r requirements-dev.txt
	pip install -e .

# Run tests
test:
	@echo "🧪 Running tests..."
	pytest tests/ -v --cov=transcribe_batch --cov-report=term-missing --cov-report=html

# Run quick tests (without coverage)
test-quick:
	@echo "⚡ Running quick tests..."
	pytest tests/ -v

# Linting
lint:
	@echo "🔍 Running linting checks..."
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

# Code formatting
format:
	@echo "✨ Formatting code..."
	black .
	@echo "Code formatted with black"

# Format check (CI mode)
format-check:
	@echo "🔍 Checking code formatting..."
	black --check --diff .

# Type checking
type-check:
	@echo "🔍 Running type checks..."
	mypy transcribe_batch.py --ignore-missing-imports

# Security checks
security:
	@echo "🛡️  Running security checks..."
	safety check --file requirements.txt
	pip-audit --requirement requirements.txt

# All quality checks
quality: lint format-check type-check security
	@echo "✅ All quality checks completed"

# Clean build artifacts
clean:
	@echo "🧹 Cleaning build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf __pycache__/
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete

# Build distribution packages
build: clean
	@echo "📦 Building distribution packages..."
	python -m build

# Publish to PyPI (requires authentication)
publish: build
	@echo "🚀 Publishing to PyPI..."
	@echo "⚠️  This will publish to PyPI. Make sure you're ready!"
	@read -p "Continue? (y/N): " confirm && [ "$$confirm" = "y" ]
	twine upload dist/*

# Publish to Test PyPI
publish-test: build
	@echo "🧪 Publishing to Test PyPI..."
	twine upload --repository testpypi dist/*

# Update requirements files
requirements:
	@echo "📝 Updating requirements files..."
	pip-compile requirements.in --output-file=requirements.txt
	pip-compile requirements-dev.in --output-file=requirements-dev.txt

# Run the transcription tool with example settings
demo:
	@echo "🎬 Running demo transcription..."
	@echo "Make sure you have MP4 files in input_mp4/ directory"
	python transcribe_batch.py run \
		--input input_mp4 \
		--output outputs \
		--model small \
		--language auto \
		--compute-type int8 \
		--beam 1 \
		--summarizer bart \
		--timeout 600

# Show project status
status:
	@echo "📊 Project Status"
	@echo "================"
	@echo "Python version: $(shell python --version)"
	@echo "Pip version: $(shell pip --version)"
	@echo "Virtual environment: $(VIRTUAL_ENV)"
	@echo ""
	@echo "📁 Project structure:"
	@find . -maxdepth 2 -type f -name "*.py" -o -name "*.md" -o -name "*.toml" | head -10
	@echo ""
	@echo "🧪 Test files:"
	@find tests/ -name "*.py" | wc -l | xargs echo "  Test files:"
	@echo ""
	@echo "📦 Dependencies:"
	@pip list --format=freeze | wc -l | xargs echo "  Installed packages:"

# Check if all tools are installed
check-tools:
	@echo "🔧 Checking required tools..."
	@command -v python >/dev/null 2>&1 || { echo "❌ Python not found"; exit 1; }
	@command -v pip >/dev/null 2>&1 || { echo "❌ Pip not found"; exit 1; }
	@command -v ffmpeg >/dev/null 2>&1 || { echo "❌ FFmpeg not found"; exit 1; }
	@echo "✅ All required tools are available"