# Default tests run with make test and make quick-tests
NOSE_TESTS=tests planemo
# Default environment for make tox
ENV?=py27
# Extra arguments supplied to tox command
ARGS?=
# Location of virtualenv used for development.
VENV=.venv
# Source virtualenv to execute command (flake8, sphinx, twine, etc...)
IN_VENV=if [ -f $(VENV)/bin/activate ]; then . $(VENV)/bin/activate; fi;
# TODO: add this upstream as a remote if it doesn't already exist.
UPSTREAM=galaxyproject

.PHONY: clean-pyc clean-build docs clean

help:
	@echo "clean - remove all build, test, coverage and Python artifacts"
	@echo "clean-build - remove build artifacts"
	@echo "clean-pyc - remove Python file artifacts"
	@echo "clean-test - remove test and coverage artifacts"
	@echo "setup-venv - setup a development virutalenv in current directory."
	@echo "lint - check style using tox and flake8 for Python 2 and Python 3"
	@echo "lint-readme - check README formatting for PyPI"
	@echo "flake8 - check style using flake8 for current Python (faster than lint)"
	@echo "test - run tests with the default Python (faster than tox)"
	@echo "quick-test - run quickest tests with the default Python"
	@echo "coverage - check code coverage quickly with the default Python"
	@echo "docs - generate Sphinx HTML documentation, including API docs"
	@echo "open-docs - generate Sphinx HTML documentation and open in browser"
	@echo "open-rtd - open docs on readthedocs.org"
	@echo "open-project - open project on github"
	@echo "release - package, review, and upload a release"
	@echo "dist - package"
	@echo "update-extern - update external artifacts copied locally"

clean: clean-build clean-pyc clean-test

clean-build:
	rm -fr build/
	rm -fr dist/
	rm -fr *.egg-info

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test:
	rm -fr .tox/
	rm -f .coverage
	rm -fr htmlcov/

setup-venv:
	if [ ! -d $(VENV) ]; then virtualenv $(VENV); exit; fi;
	$(IN_VENV) pip install -r requirements.txt && pip install -r dev-requirements.txt

setup-git-hook-lint:
	cp scripts/pre-commit-lint .git/hooks/pre-commit

setup-git-hook-lint-and-test:
	cp scripts/pre-commit-lint-and-test .git/hooks/pre-commit

flake8:
	$(IN_VENV) flake8 --max-complexity 11 planemo tests

lint:
	$(IN_VENV) tox -e py27-lint && tox -e py34-lint

lint-readme:
	$(IN_VENV) python setup.py check -r -s

test:
	$(IN_VENV) nosetests $(NOSE_TESTS)

quick-test:
	$(IN_VENV) PLANEMO_SKIP_GALAXY_TESTS=1 nosetests $(NOSE_TESTS)

tox:
	$(IN_VENV) tox -e $(ENV) -- $(ARGS)

coverage:
	coverage run --source planemo setup.py test
	coverage report -m
	coverage html
	open htmlcov/index.html || xdg-open htmlcov/index.html

docs:
	rm -f docs/planemo.rst
	rm -f docs/planemo_ext.rst
	rm -f docs/modules.rst
	$(IN_VENV) sphinx-apidoc -f -o docs/ planemo_ext planemo_ext/galaxy/eggs
	$(IN_VENV) sphinx-apidoc -f -o docs/ planemo
	$(IN_VENV) python scripts/commands_to_rst.py
	$(IN_VENV) $(MAKE) -C docs clean
	$(IN_VENV) $(MAKE) -C docs html

_open-docs:
	open docs/_build/html/index.html || xdg-open docs/_build/html/index.html

open-docs: docs _open-docs

open-rtd: docs
	open https://planemo.readthedocs.org || xdg-open https://planemo.readthedocs.org

open-project:
	open https://github.com/galaxyproject/planemo || xdg-open https://github.com/galaxyproject/planemo

dist: clean
	$(IN_VENV) python setup.py sdist bdist_egg bdist_wheel
	ls -l dist

release-test-artifacts: dist
	$(IN_VENV) twine upload -r test dist/*
	open https://testpypi.python.org/pypi/planemo || xdg-open https://testpypi.python.org/pypi/planemo

release-aritfacts: release-test-artifacts
	@while [ -z "$$CONTINUE" ]; do \
		read -r -p "Have you executed release-test and reviewed results? [y/N]: " CONTINUE; \
	done ; \
	[ $$CONTINUE = "y" ] || [ $$CONTINUE = "Y" ] || (echo "Exiting."; exit 1;)
	@echo "Releasing"
	$(IN_VENV) twine upload dist/*

commit-version:
	$(IN_VENV) python scripts/commit_version.py $(VERSION)

new-version:
	$(IN_VENV) python scripts/new_version.py $(NEW_VERSION)

release: commit-version release-aritfacts new-version

push-release:
	git push $(UPSTREAM) master
	git push --tags $(UPSTREAM)

add-history:
	$(IN_VENV) python scripts/bootstrap_history.py $(ITEM)

update-extern:
	sh scripts/update_extern.sh
