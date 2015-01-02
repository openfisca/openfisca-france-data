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


import logging
import os

from openfisca_survey_manager.surveys import Survey, SurveyCollection
from openfisca_france_data.input_data_builders.build_openfisca_indirect_taxation_survey_data.step_01_consumption_by_categorie_fiscale \
    import build_menage_consumption_by_categorie_fiscale

from openfisca_france_data.input_data_builders.build_openfisca_indirect_taxation_survey_data.step_02_other_menage_variables \
    import build_other_menage_variables

log = logging.getLogger(__name__)



def run_all(year = 2005, filename = "test_indirect_taxation"):

#    df = build_other_menage_variables(year = year)
    consumption = build_menage_consumption_by_categorie_fiscale(year = year)
    menage = build_other_menage_variables(year = year)
    data_frame = menage.merge(consumption, copy = True)

    # Saving the data_frame
    openfisca_survey_collection = SurveyCollection(name = "openfisca_indirect_taxation")
    openfisca_survey_collection.set_config_files_directory()
    output_data_directory = openfisca_survey_collection.config.get('data', 'output_directory')
    survey_name = "openfisca_indirect_taxation_data_{}".format(year)
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
    openfisca_survey_collection.surveys[survey_name] = survey
    openfisca_survey_collection.dump(collection = "openfisca_indirect_taxation")


if __name__ == '__main__':
    import time
    start = time.time()
    run_all(year = 2005)
    log.info("{}".format(time.time() - start))
