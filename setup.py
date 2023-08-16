from setuptools import setup, find_namespace_packages


with open('README.md') as file:
    long_description = file.read()

setup(
    name = "OpenFisca-France-Data",
    version = "2.0.2",
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
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Information Analysis",
        ],
    package_data = {
        'openfisca_france_data': ['assets/aggregats/taxipp/agregats_tests_taxipp_2_0.xlsx',
                                  'assets/aggregats/ines/ines_2019.json'],
        },
    entry_points = {
        'console_scripts': [
            'build-erfs-fpr=openfisca_france_data.erfs_fpr.input_data_builder:main',
            'compare-erfs-fpr-input=openfisca_france_data.erfs_fpr.comparison:compare',
            'create-test-erfs-fpr=openfisca_france_data.erfs_fpr.test_case_creation:create_test',
            ],
        },
    python_requires = ">= 3.9",
    install_requires = [
        "click >= 8.0.0, < 9.0.0",
        "matplotlib >= 3.1.1, < 4.0.0",
        "multipledispatch >= 0.6.0, < 1.0.0",
        "openFisca-france >= 150.0.0, < 151.0.0",
        "openFisca-survey-manager >= 1, < 2.0.0",
        "wquantiles >= 0.3.0, < 1.0.0",  # To compute weighted quantiles
        ],
    extras_require = {
        "test": [
            "autopep8 >= 2.0.2, < 3",
            "bumpver >= 2022.1120",
            "dtale",
            "flake8 >= 6.0.0, < 7.0.0",
            "ipdb >=0.13, <1.0",
            "ipython >= 7.5.0, < 8.0.0",
            "mypy >= 0.670, < 1.0.0",
            "pypandoc",
            'pytest >= 7.2.2, < 8.0',
            "scipy >= 1.2.1, < 2.0.0",
            "toolz >= 0.9.0, < 1.0.0",
            ],
        },
    packages = find_namespace_packages(exclude = ("docs", "tests")),
    )
