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

import openfisca_france

from openfisca_survey_manager.surveys import Survey, SurveyCollection
from eipp_utils import build_input_OF, build_ipp2of_variables

log = logging.getLogger(__name__)


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
        ipp2of_input_variables, ipp2of_output_variables = build_ipp2of_variables()
#        print 'avant',list(base.columns.values)
#        base.rename(columns = ipp2of_input_variables, inplace = True)
#        print 'après',list(base.columns.values)

        TaxBenefitSystem = openfisca_france.init_country()
        tax_benefit_system = TaxBenefitSystem()

    data_frame = build_input_OF(base, ipp2of_input_variables, tax_benefit_system)
    return data_frame


def dump_data_frame(data_frame, year):

    from openfisca_france_data.build_openfisca_survey_data import utils

    utils.print_id(data_frame)
#    utils.control(data_frame, verbose = True)
    utils.check_structure(data_frame)

    survey_collection = SurveyCollection(name = "eipp")
    survey_collection.set_config_files_directory()
    output_data_directory = survey_collection.config.get('data', 'output_directory')
    survey_name = "eipp_data_{}".format(year)
    table = "input"
    hdf5_file_path = os.path.join(
        os.path.dirname(output_data_directory),
        "{}{}".format(survey_name, ".h5"),
        )

    survey = Survey(
        name = survey_name,
        hdf5_file_path = hdf5_file_path,
        )
    survey.insert_table(name = table)
    survey.fill_hdf(table, data_frame)
    survey_collection.surveys[survey_name] = survey
    survey_collection.dump(collection = "eipp")

if __name__ == '__main__':
    #import time
    #start = time.time()
    data_frame = adaptation_eipp_to_OF(years = [2011], check = False)
    dump_data_frame(data_frame, 2011)
    #log.info("{}".format( time.time() - start ))
    # import pdb
    # pdb.set_trace()
