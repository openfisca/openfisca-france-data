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


def build_empty_ipp_survey_collection(years= None):

    if years is None:
        log.error("A list of years to process is needed")

    base_ipp_survey_collection = SurveyCollection(name = "ipp")
    base_ipp_survey_collection.set_config_files_directory(config_files_directory)
    input_data_directory = base_ipp_survey_collection.config.get('data', 'input_directory')
    output_data_directory = base_ipp_survey_collection.config.get('data', 'output_directory')

    tables = ["base"]
    ipp_tables = dict()
    for year in [2013]:
        for table in tables:
            ipp_tables[table] = {
                "stata_file": os.path.join(
                    os.path.dirname(input_data_directory),
                    "fichiers_ipp",
                    "{}_{}.dta".format(table, year),
                    ),
                "year": year,
                }

        survey_name = u"ipp_{}".format(year)
        hdf5_file_path = os.path.join(
            os.path.dirname(output_data_directory),
            u"{}{}".format(survey_name, u".h5")
            )
        survey = Survey(
            name = survey_name,
            hdf5_file_path = hdf5_file_path
            )
        for table, table_kwargs in ipp_tables.iteritems():
            survey.insert_table(name = table, **table_kwargs)
        surveys = base_ipp_survey_collection.surveys
        surveys[survey_name] = survey
    return base_ipp_survey_collection


if __name__ == '__main__':
    import logging
    import sys
    import datetime
    start_time = datetime.datetime.now()
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    ipp_survey_collection = build_empty_ipp_survey_collection(
        years = [2013],
        )
    ipp_survey_collection.fill_hdf_from_stata(surveys_name = ["ipp_2013"])
    ipp_survey_collection.dump(collection = u"ipp")
    log.info("The program have been executed in {}".format( datetime.datetime.now()-start_time))

