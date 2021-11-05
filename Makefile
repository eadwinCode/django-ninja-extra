.PHONY: help docs
.DEFAULT_GOAL := help

help:
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

clean: ## Removing cached python compiled files
	find . -name \*pyc  | xargs  rm -fv
	find . -name \*pyo | xargs  rm -fv
	find . -name \*~  | xargs  rm -fv
	find . -name __pycache__  | xargs  rm -rfv

install: ## Install dependencies
	flit install --deps develop --symlink

lint: ## Run code linters
	black --check ninja_extra tests
	isort --check ninja_extra tests
	flake8 ninja_extra tests
	mypy ninja_extra

fmt format: ## Run code formatters
	black ninja_extra tests
	isort ninja_extra tests

test: ## Run tests
	pytest .

test-cov: ## Run tests with coverage
	pytest --cov=ninja_extra --cov-report term-missing tests

doc-deploy: ## Run Deploy Documentation
	make clean
	mkdocs gh-deploy --force