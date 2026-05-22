PYTHON = python3

UV = uv

FILE = file.txt

FLAKE = flake8 *.py

MYPY = mypy *.py --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

install:
	@$(UV) sync

run:
	@$(UV) run $(PYTHON) main.py
debug:
	@$(UV) run $(PYTHON) -m pdb main.py

clean:
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type d -name ".mypy_cache" -exec rm -rf {} +

lint:
	@$(UV) run $(FLAKE)
	@$(UV) run $(MYPY)