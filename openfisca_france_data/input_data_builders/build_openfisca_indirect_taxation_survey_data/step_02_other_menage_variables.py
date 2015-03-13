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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import logging


from openfisca_survey_manager.survey_collections import SurveyCollection

log = logging.getLogger(__name__)

from openfisca_france_data.temporary import TemporaryStore

temporary_store = TemporaryStore.create(file_name = "indirect_taxation_tmp")


def build_other_menage_variables(year = None):
    """Build menage consumption by categorie fiscale dataframe """

    assert year is not None
    # Load data
    bdf_survey_collection = SurveyCollection.load(collection = 'budget_des_familles')
    survey = bdf_survey_collection.get_survey('budget_des_familles_{}'.format(year))

    c05d = survey.get_values(table = "c05d")
    kept_variables = [u'ident_men', u'pondmen']
    c05d = c05d[kept_variables]

    menage = survey.get_values(table = "menage")
    kept_variables = [u'ident_men', u'pondmen', u'revtot', u'revtotuc', u'decuc']
    menage = menage[kept_variables]
    data_frame = menage.merge(c05d, copy = True)
    return data_frame


if __name__ == '__main__':
    import sys
    import time
    logging.basicConfig(level = logging.INFO, stream = sys.stdout)
    deb = time.clock()
    year = 2005
    build_other_menage_variables(year = year)

    log.info("step 01 demo duration is {}".format(time.clock() - deb))
