#! /usr/bin/env python
# -*- coding: utf-8 -*-


# OpenFisca -- A versatile microsimulation software
# By: OpenFisca Team <contact@openfisca.fr>
#
# Copyright (C) 2011, 2012, 2013, 2014 OpenFisca Team
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


import gc
import logging

from openfisca_survey_manager.surveys import SurveyCollection
# from openfisca_france_data.build_openfisca_survey_data import save_temp
# from openfisca_france_data.build_openfisca_survey_data.utils import assert_dtype

log = logging.getLogger(__name__)


def test(year = None):
    """
    Demo
    """
    assert year is not None
    # load data
    bdf_survey_collection = SurveyCollection.load(collection = 'budget_des_familles')
    survey = bdf_survey_collection.surveys['budget_des_familles_{}'.format(year)]
    c05d = survey.get_values(table = "c05d")
    print c05d.columns
    print c05d.info()
    print c05d.describe()
    gc.collect()
    c05d = survey.get_values(table = "c05d")
    individu = survey.get_values(table = "individu")
    print individu.columns
    print individu.info()
    print individu.describe()


if __name__ == '__main__':
    log.info('Entering 01_pre_proc')
    import sys
    import time
    logging.basicConfig(level = logging.INFO, stream = sys.stdout)
    deb = time.clock()
    year = 2005
    test(year = year)
    log.info("step 01 demo duration is {}".format(time.clock() - deb))
