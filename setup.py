#! /usr/bin/env python
# -*- coding: utf-8 -*-


# OpenFisca -- A versatile microsimulation software
# By: OpenFisca Team <contact@openfisca.fr>
#
# Copyright (C) 2011, 2012, 2013, 2014, 2015 OpenFisca Team
# https://github.com/openfisca
#
# This file is part of OpenFisca.
#
# OpenFisca is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# OpenFisca is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


"""OpenFisca -- a versatile microsimulation free software

OpenFisca includes a framework to simulate any tax and social system.
"""


from setuptools import setup, find_packages


classifiers = """\
Development Status :: 2 - Pre-Alpha
License :: OSI Approved :: GNU Affero General Public License v3
Operating System :: POSIX
Programming Language :: Python
Topic :: Scientific/Engineering :: Information Analysis
"""

doc_lines = __doc__.split('\n')


setup(
    name = 'OpenFisca-France-Data',
    version = '0.5.8',
    author = 'OpenFisca Team',
    author_email = 'contact@openfisca.fr',
    classifiers = [classifier for classifier in classifiers.split('\n') if classifier],
    description = doc_lines[0],
    keywords = 'benefit microsimulation social tax',
    license = 'http://www.fsf.org/licensing/licenses/agpl-3.0.html',
    long_description = '\n'.join(doc_lines[2:]),
    url = 'https://github.com/openfisca/openfisca-france-data',
    data_files = [
        ('share/locale/fr/LC_MESSAGES', ['openfisca_france_data/i18n/fr/LC_MESSAGES/openfisca-france-data.mo']),
        ],
    install_requires = [
        'OpenFisca-France >= 15.0.0, < 16.0',
        'OpenFisca-Core >= 6.0, < 7.0',
        'OpenFisca-Survey-Manager[calmar] >= 0.7.0',
        'pandas == 0.20.3',
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
