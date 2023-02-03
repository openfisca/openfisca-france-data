all: check-style test

uninstall:
	pip freeze | grep -v "^-e" | xargs pip uninstall -y

install:
	pip install --upgrade pip setuptools twine wheel
	pip install --editable .[test] --upgrade

clean:
	rm -rf build dist
	find . -name '*.mo' | xargs rm -rf
	find . -name '*.pyc' | xargs rm -rf
	find . -name '__pycache__' | xargs rm -rf

check-syntax-errors:
	python -m compileall -q .

check-scripts:
	@# Do not analyse .gitignored files.
	@# `make` needs `$$` to output `$`. Ref: http://stackoverflow.com/questions/2382764.
	shellcheck `git ls-files | grep "\.sh$$"`

check-style:
	@# Do not analyse .gitignored files.
	@# `make` needs `$$` to output `$`. Ref: http://stackoverflow.com/questions/2382764.
	flake8 `git ls-files | grep "\.py$$"`

format-style:
	@# Do not analyse .gitignored files.
	@# `make` needs `$$` to output `$`. Ref: http://stackoverflow.com/questions/2382764.
	autopep8 `git ls-files | grep "\.py$$"`

test: clean check-syntax-errors
	pytest --ignore=tests/erfs_fpr/integration

test-local: clean check-syntax-errors
	pytest

archive: clean
	git archive HEAD --format=zip > archive.zip

ctags:
	ctags --recurse=yes .

bump:
	bumpver update --minor
