# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


with open('README.md') as file:
    long_description = file.read()

setup(
    name = "OpenFisca-France-Data",
    version = "0.14.1",
    description = "OpenFisca-France-Data module to work with French survey data",
    long_description = long_description,
    long_description_content_type="text/markdown",
    author = "OpenFisca Team",
    author_email = "contact@openfisca.fr",
    url = "https://github.com/openfisca/openfisca-france-data",
    license = "http://www.fsf.org/licensing/licenses/agpl-3.0.html",
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
        "openFisca-france >= 48.10.0, < 49.0.0",
        "openFisca-survey-manager >= 0.38.2, < 1.0.0",
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
