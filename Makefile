all: check-style test

uninstall:
	pip freeze | grep -v "^-e" | xargs pip uninstall -y

install:
	pip install --upgrade pip
	pip install --editable .[test] --upgrade

clean:
	rm -rf build dist
	find . -name '*.mo' -exec rm \{\} \;
	find . -name '*.pyc' -exec rm \{\} \;

check-syntax-errors:
	python -m compileall -q .

check-style:
	@# Do not analyse .gitignored files.
	@# `make` needs `$$` to output `$`. Ref: http://stackoverflow.com/questions/2382764.
	flake8 `git ls-files | grep "\.py$$"`

format-style:
	@# Do not analyse .gitignored files.
	@# `make` needs `$$` to output `$`. Ref: http://stackoverflow.com/questions/2382764.
	autopep8 `git ls-files | grep "\.py$$"`

test: clean check-syntax-errors
	nosetests openfisca_france_data/tests --ignore-files='(test_inflation.py|test_surveys.py|test_simulation.py|test_pivot_table.py|test_af.py|test_al.py|test_impot_revenu.py)' --exclude-dir=openfisca_france_data/tests/erfs_fpr --exe --with-doctest

test-local: clean check-syntax-errors
	nosetests openfisca_france_data/tests --ignore-files='(test_inflation.py|test_surveys.py|test_simulation.py|test_pivot_table.py|test_af.py|test_al.py|test_impot_revenu.py)' --exe --with-doctest

archive: clean
	git archive HEAD --format=zip > archive.zip

ctags:
	ctags --recurse=yes .
