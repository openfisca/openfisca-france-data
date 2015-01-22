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

import pkg_resources
import logging
import os

from openfisca_survey_manager.surveys import Survey, SurveyCollection

openfisca_france_data_location = pkg_resources.get_distribution('openfisca-france-data').location
config_files_directory = os.path.join(openfisca_france_data_location)

log = logging.getLogger(__name__)


def build_empty_bdf_survey_collection(years = None):

    if years is None:
        log.error("A list of years to process is needed")

    bdf_survey_collection = SurveyCollection(name = "bdf")
    bdf_survey_collection.set_config_files_directory(config_files_directory)
    input_data_directory = bdf_survey_collection.config.get('data', 'input_directory')
    output_data_directory = bdf_survey_collection.config.get('data', 'output_directory')

    tables_by_year = {
        2000: [
            "biensdur",
            "consomen",
            "depindiv",
            "depmen",
            "exautoc",
            "individus",
            "menage",
            "prautoc",
            "vetement",
            ],
        2005: [
            "a04d",
            "autlogements",
            "automobile",
            "biensdur",
            "c05d",
            "depindiv",
            "depmen",
            "individu",
            "menage",
            # Sociodem.sd2
            "vetements",
            ],
        }

    for year in years:
        surveys = bdf_survey_collection.surveys

        survey_name = 'budget_des_familles_{}'.format(year)
        hdf5_file_path = os.path.join(
            os.path.dirname(output_data_directory),
            "{}{}".format(survey_name, ".h5")
            )
        survey = Survey(
            name = survey_name,
            hdf5_file_path = hdf5_file_path
            )
        surveys[survey_name] = survey

#       TODO; deal with previous years
#        sas_data_directory = os.path.join(
#            os.path.dirname(input_data_directory),
#            'INSEE/budget_des_familles/{}/sas'.format(year)
#            )
        stata_data_directory = os.path.join(
            os.path.dirname(input_data_directory),
            'INSEE/budget_des_familles/{}/stata'.format(year)
            )

        for table_name in tables_by_year[year]:
            stata_file = os.path.join(stata_data_directory, "{}.dta".format(table_name))
            survey.insert_table(name = table_name,
                                year = year,
                                stata_file = stata_file,
                                )
    return bdf_survey_collection


if __name__ == '__main__':
    years = [2005]
    bdf_survey_collection = build_empty_bdf_survey_collection(years = years)
    for year in years:
        bdf_survey_collection.fill_hdf_from_stata(surveys_name = ["budget_des_familles_{}".format(year)])
    bdf_survey_collection.dump(collection = "budget_des_familles")
