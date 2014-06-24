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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import logging
import os
import sys

import openfisca_france

from openfisca_france_data.surveys import Survey, SurveyCollection

from eipp_utils import build_input_OF, build_ipp2of_input

def adaptation_eipp_to_OF(years = None, filename = "test", check = False):
    """
    Adapation des bases ERFS FPR de l'IPP pour OF
    """
    if years is None:
        log.error("A list of years to process is needed")

    for year in years:
    # load data
        eipp_survey_collection = SurveyCollection.load(collection = 'eipp')
        survey = eipp_survey_collection.surveys['eipp_{}'.format(year)]
        base = survey.get_values(table = "base")
        ipp2of_input_variables = build_ipp2of_input()
#        print 'avant',list(base.columns.values)
#        base.rename(columns = ipp2of_input_variables, inplace = True)
#        print 'après',list(base.columns.values)

        TaxBenefitSystem = openfisca_france.init_country()
        tax_benefit_system = TaxBenefitSystem()

        build_input_OF(base, ipp2of_input_variables, tax_benefit_system)

if __name__ == '__main__':
    #import time
    #start = time.time()
    adaptation_eipp_to_OF(years = [2011], check = False)
    #log.info("{}".format( time.time() - start ))
    # import pdb
    # pdb.set_trace()