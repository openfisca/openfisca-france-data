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
#

import ConfigParser
import getpass
import logging
import os


from openfisca_survey_manager.scripts.surv import add_survey_to_collection, create_data_file_by_format
from openfisca_survey_manager.survey_collections import SurveyCollection
from openfisca_france_data import default_config_files_directory as config_files_directory


log = logging.getLogger(__name__)


def build_bdf_survey_collection(years = None, erase = False, overwrite = False):

    if years is None:
        log.error("A list of years to process is needed")

    if erase:
        bdf_survey_collection = SurveyCollection(
            name = "budget_des_familles", config_files_directory = config_files_directory)
    else:
        try:
            bdf_survey_collection = SurveyCollection.load(
                collection = 'budget_des_familles', config_files_directory = config_files_directory)
        except ConfigParser.NoOptionError:
            bdf_survey_collection = SurveyCollection(
                name = "budget_des_familles", config_files_directory = config_files_directory)

    input_data_directory = bdf_survey_collection.config.get('data', 'input_directory')
    if getpass.getuser() == 'benjello':
        input_data_directory = os.path.join(os.path.dirname(input_data_directory), 'INSEE')
    else:
        input_data_directory = os.path.dirname(input_data_directory)

    for year in years:
        data_directory_path = os.path.join(
            input_data_directory,
            'budget_des_familles/{}'.format(year)
            )
        data_file_by_format = create_data_file_by_format(data_directory_path)
        survey_name = 'budget_des_familles_{}'.format(year)

        add_survey_to_collection(
            survey_name = survey_name,
            survey_collection = bdf_survey_collection,
            stata_files = data_file_by_format['stata'],
            )

        collections_directory = bdf_survey_collection.config.get('collections', 'collections_directory')
        collection_json_path = os.path.join(collections_directory, "budget_des_familles" + ".json")
        bdf_survey_collection.dump(json_file_path = collection_json_path)
        surveys = [survey for survey in bdf_survey_collection.surveys if survey.name.endswith(str(year))]
        bdf_survey_collection.fill_hdf(source_format = 'stata', surveys = surveys, overwrite = overwrite)
    return bdf_survey_collection


if __name__ == '__main__':
    years = [2005, 2011]
    bdf_survey_collection = build_bdf_survey_collection(years = years, erase = False, overwrite = False)
