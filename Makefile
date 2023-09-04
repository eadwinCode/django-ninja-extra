.PHONY: help docs
.DEFAULT_GOAL := help

help:
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

clean: ## Removing cached python compiled files
	find . -name \*pyc  | xargs  rm -fv
	find . -name \*pyo | xargs  rm -fv
	find . -name \*~  | xargs  rm -fv
	find . -name __pycache__  | xargs  rm -rfv

install:clean ## Install dependencies
	flit install --deps develop --symlink
	pre-commit install -f

lint:fmt ## Run code linters
	make clean
	black --check ninja_extra tests
	ruff check ninja_extra tests
	mypy ninja_extra

fmt format:clean ## Run code formatters
	black ninja_extra tests
	ruff check --fix ninja_extra tests


test:clean ## Run tests
	pytest .

test-cov:clean ## Run tests with coverage
	make clean
	pytest --cov=ninja_extra --cov-report term-missing tests

doc-deploy:clean ## Run Deploy Documentation
	mkdocs gh-deploy --force
