.PHONY: install test cov preflight fixtures history zip docker-build docker-test clean

install:
	pip install -e .

test:
	pytest

cov:
	pytest --cov=finpy --cov-report=term-missing

preflight:
	python scripts/preflight.py

fixtures:
	python scripts/build_fixtures.py

history:
	python scripts/replay_history.py scripts/commit_plan.json

zip:
	python scripts/make_zip.py

docker-build:
	docker build -t finpy .

docker-test:
	docker run --rm finpy

clean:
	rm -rf build dist *.egg-info .pytest_cache .hypothesis htmlcov .coverage
