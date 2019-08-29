clean_venv:
	rm -rf .venv

.venv: clean_venv
	python -m venv --clear .venv
	. ./.venv/bin/activate && poetry install --develop=amino_census
