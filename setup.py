#! /usr/bin/env python
# -*- coding: utf-8 -*-


"""OpenFisca -- a versatile microsimulation free software

OpenFisca includes a framework to simulate any tax and social system.
"""


from setuptools import setup, find_packages


classifiers = """\
Development Status :: 2 - Pre-Alpha
License :: OSI Approved :: GNU Affero General Public License v3
Operating System :: POSIX
Programming Language :: Python
Programming Language :: Python :: 3.7
Topic :: Scientific/Engineering :: Information Analysis
"""

doc_lines = __doc__.split('\n')


setup(
    name = 'OpenFisca-France-Data',
    version = '0.7.4',
    author = 'OpenFisca Team',
    author_email = 'contact@openfisca.fr',
    classifiers = [classifier for classifier in classifiers.split('\n') if classifier],
    description = doc_lines[0],
    keywords = 'benefit microsimulation social tax',
    license = 'http://www.fsf.org/licensing/licenses/agpl-3.0.html',
    long_description = '\n'.join(doc_lines[2:]),
    url = 'https://github.com/openfisca/openfisca-france-data',
    data_files = [
        # ('share/locale/fr/LC_MESSAGES', ['openfisca_france_data/i18n/fr/LC_MESSAGES/openfisca-france-data.mo']),
        ],
    include_package_data = True,
    extras_require = {
        'test': [
            'autopep8 >= 1.4.0, < 1.5.0',
            'coverage >= 4.5.0, < 4.6.0',
            'coveralls >= 1.5.0, < 1.6.0',
            'flake8 >= 3.7.0, < 3.8.0',
            'nose-exclude',
            ],
        },
    install_requires = [
        'OpenFisca-France >= 24.0.0, < 25.0',
        'OpenFisca-Survey-Manager[calmar] >= 0.11',
        'pandas >= 0.20.3',
        'tables',  # Needed by pandas.HDFStore
        'wquantiles >= 0.3'  # To compute weighted quantiles
        ],
    message_extractors = {
        'openfisca_france_data': [
            ('**.py', 'python', None),
            ],
        },
    packages = find_packages(),
    zip_safe = False,
    )
