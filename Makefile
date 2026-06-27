PYTHON = python3
MAIN = simulator.py
MAP ?= maps/challenger/01_the_impossible_dream.txt

.PHONY: install run debug clean lint lint-strict

install:
	@echo "Installing dependencies..."
	python3 -m venv v
	v/bin/python -m pip install --upgrade pip
	. v/bin/activate && pip install pygame webcolors flake8 mypy
run:
	@echo "Running the simulation engine...\n"
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
	flake8 map_parser.py models.py pathfinder.py simulator.py visualizer.py
	mypy map_parser.py models.py pathfinder.py simulator.py visualizer.py --exclude v --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs