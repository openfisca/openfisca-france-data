## -*- coding: utf-8 -*-


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


from __future__ import division
from numpy import where, NaN, random
from openfisca_france.data.erf.build_survey import show_temp, load_temp, save_temp
from openfisca_france.data.erf.build_survey.utils import print_id, control, check_structure
from pandas import read_csv, HDFStore
from openfisca_france import DATA_SOURCES_DIR
import os


def final_check(year=2006):
    test_filename = os.path.join(DATA_SOURCES_DIR, "test.h5")
    survey_filename = os.path.join(DATA_SOURCES_DIR, "survey.h5")

    store = HDFStore(test_filename)
    survey = HDFStore(survey_filename)

    final2 = store.get('survey_2006')
    print survey
    finalT = survey.get('survey_2006')

    varlist = [
        'adeben',
        'adfdap',
        'amois',
        'ancchom',
        'ancentr',
        'anciatm',
        'ancrech',
        'anref',
        'contra',
        'datant',
        'dimtyp',
        'ident',
        'idfoy'
        'noi',
        'nondic',
        'rabs',
        'RABSP',
        'RAISTP',
        'raistp',
        'rdem',
        'retrai',
        'sitant',
        'sp10',
        'sp11',
        'stc',
        'TXTPPB',
        ]

    for i in range(0, 10):
        varname = 'sp0' + str(i)
        varlist.append(varname)

    varlist = set(varlist)
    columns = final2.columns
    columns = set(columns)

    print varlist.difference(columns)
    print final2.loc[
        final2.idfoy == 603018901,
        ['idfoy', 'quifoy', 'idfam', 'quifam', 'idmen', 'quimen', 'noi']
        ].to_string()

    return


if __name__ == '__main__':
    final_check()
