# TubeBendCalculator Development Tasks
# Usage: make <target>

.PHONY: check lint typecheck test validate

# Check Python syntax
check:
	@echo "Checking syntax..."
	@python3 -m py_compile $$(find . -name "*.py" -not -path "./typings/*")
	@echo "Syntax OK"

# Run linter
lint:
	@ruff check . --ignore E402,E501,E712,E722,F403,I001,UP037,W291,W292,W293 --exclude typings

# Run type checker
typecheck:
	@pyright --project pyrightconfig.json

# Run unit tests with pytest
test:
	@pytest tests/ -v --tb=short

# Run all validation (use before committing)
validate: check lint test
	@echo ""
	@echo "All validation passed!"
