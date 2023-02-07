from setuptools import setup, find_packages


with open('README.md') as file:
    long_description = file.read()

setup(
    name = "OpenFisca-France-Data",
    version = "0.22.1",
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
    entry_points = {
        'console_scripts': ['build-erfs-fpr=openfisca_france_data.erfs_fpr.input_data_builder:main'],
        },
    python_requires = ">= 3.7",
    install_requires = [
        "click >= 8.0.0, < 9.0.0",
        "matplotlib >= 3.1.1, < 4.0.0",
        "multipledispatch >= 0.6.0, < 1.0.0",
        "openFisca-france >= 113.0.0, < 120.0.0",  # Max 120 because of a bug in OF : https://github.com/openfisca/openfisca-france/issues/1996
        "openFisca-survey-manager >= 0.44.2, < 1.0.0",
        "wquantiles >= 0.3.0, < 1.0.0",  # To compute weighted quantiles
        ],
    extras_require = {
        "test": [
            "autopep8 >= 1.4.0, < 1.5.0",
            "flake8 >= 3.7.0, < 3.8.0",
            "ipython >= 7.5.0, < 8.0.0",
            "mypy >= 0.670, < 1.0.0",
            "pytest >= 4.3.0, < 5.0.0",
            "pytest-cov >= 2.6.0, < 3.0.0",
            "scipy >= 1.2.1, < 2.0.0",
            "toolz >= 0.9.0, < 1.0.0",
            "bumpver >= 2022.1120",
            ],
        },
    packages = find_packages(exclude = ("docs", "tests")),
    )
