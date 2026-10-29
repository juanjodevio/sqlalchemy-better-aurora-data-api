SHELL=/bin/bash

lint:
	uv run ruff check .

test: lint
	uv run python ./test/test.py -v

init_docs:
	uv run --group docs sphinx-quickstart docs

docs:
	uv run --group docs sphinx-build docs docs/html

install:
	-rm -rf dist
	uv build
	uv pip install --system --upgrade dist/*.whl

.PHONY: test release docs

include common.mk
