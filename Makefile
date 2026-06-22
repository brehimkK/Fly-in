PYTHON = python3
MAIN = simulator.py
MAP ?= maps/medium/02_circular_loop.txt

.PHONY: install run debug clean lint lint-strict

install:
	@echo "Installing dependencies..."
	python3 -m venv v
	v/bin/python -m pip install --upgrade pip
	. v/bin/activate && pip install pygame webcolors flake8 mypy
run:
	@echo "Running the simulation engine..."
	@$(PYTHON) $(MAIN) $(MAP)

debug:
	@echo "Running in debug mode using pdb..."
	$(PYTHON) -m pdb $(MAIN) $(MAP)

clean:
	@echo "Cleaning up caches and temporary files..."
	rm -rf __pycache__ .mypy_cache
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type d -name ".mypy_cache" -exec rm -r {} +

lint:
	@echo "Running standard linter checks..."
	flake8 . --exclude v
	mypy . --exclude v --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs
