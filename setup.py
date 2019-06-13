# -*- coding: utf-8 -*-


from setuptools import setup, find_packages

with open('README.md') as file:
    long_description = file.read()

with open('LICENSE') as file:
    license = file.read()

setup(
    name = "OpenFisca-France-Data",
    version = "0.13.1",
    description = "OpenFisca-France-Data module to work with French survey data",
    long_description = long_description,
    author = "OpenFisca Team",
    author_email = "contact@openfisca.fr",
    url = "https://github.com/openfisca/openfisca-france-data",
    license = license,
    keywords = "tax benefit social survey data microsimulation",
    classifiers = [
        "Development Status :: 2 - Pre-Alpha",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Operating System :: POSIX",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.7",
        "Topic :: Scientific/Engineering :: Information Analysis",
        ],
    python_requires = ">= 3.7",
    install_requires = [
        "multipledispatch >= 0.6.0, < 1.0.0",
        "openfisca-core >= 34.2.2, < 35.0.0",
        "openFisca-france >= 42.1.0, < 43.0.0",
        "openFisca-survey-manager >= 0.28, < 1.0.0",
        "numpy >= 1.11,<1.16",  # openfisca-survey-manager deps and https://github.com/openfisca/openfisca-survey-manager/pull/79
        "numexpr == 2.6.8",
        "pandas >= 0.20.3, < 1.0.0",
        "tables >= 3.0.0, < 4.0.0",  # Needed by pandas.HDFStore
        "wquantiles >= 0.3.0, < 1.0.0",  # To compute weighted quantiles
        "matplotlib >= 3.1.1, < 4.0.0"
        ],
    extras_require = {
        "test": [
            "autopep8 >= 1.4.0, < 1.5.0",
            "flake8 >= 3.7.0, < 3.8.0",
            "ipython >= 7.5.0, < 8.0.0",
            "mypy >= 0.670, < 1.0.0",
            "pytest >= 4.3.0, < 5.0.0",
            "pytest-cov >= 2.6.0, < 3.0.0",
            "toolz >= 0.9.0, < 1.0.0",
            ],
        },
    packages = find_packages(exclude = ("docs", "tests")),
    )
