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
import pkg_resources

from openfisca_survey_manager.scripts.surv import add_survey_to_collection, create_data_file_by_format
from openfisca_survey_manager.survey_collections import SurveyCollection
openfisca_france_data_location = pkg_resources.get_distribution('openfisca-france-data').location
config_files_directory = os.path.join(openfisca_france_data_location)


log = logging.getLogger(__name__)


def build_erfs_survey_collection(years = None, erase = False, overwrite = False):

    if years is None:
        log.error("A list of years to process is needed")

    if erase:
        erfs_survey_collection = SurveyCollection(
            name = "erfs", config_files_directory = config_files_directory)
    else:
        try:
            erfs_survey_collection = SurveyCollection.load(
                collection = 'erfs', config_files_directory = config_files_directory)
        except ConfigParser.NoOptionError:
            erfs_survey_collection = SurveyCollection(
                name = "erfs", config_files_directory = config_files_directory)

    input_data_directory = erfs_survey_collection.config.get('data', 'input_directory')
    if getpass.getuser() == 'benjello':
        input_data_directory = os.path.join(os.path.dirname(input_data_directory), 'INSEE')
    else:
        input_data_directory = os.path.dirname(input_data_directory)

    for year in years:
        data_directory_path = os.path.join(
            input_data_directory,
            'ERF/ERFS_{}'.format(year)
            )
        data_file_by_format = create_data_file_by_format(data_directory_path)
        survey_name = 'erfs_{}'.format(year)

        add_survey_to_collection(
            survey_name = survey_name,
            survey_collection = erfs_survey_collection,
            sas_files = data_file_by_format['sas'],
            )

        collections_directory = erfs_survey_collection.config.get('collections', 'collections_directory')
        collection_json_path = os.path.join(collections_directory, "erfs" + ".json")
        erfs_survey_collection.dump(json_file_path = collection_json_path)
        surveys = [survey for survey in erfs_survey_collection.surveys if survey.name.endswith(str(year))]

        erfs_survey_collection.fill_hdf(source_format = 'sas', surveys = surveys, overwrite = overwrite)
    return erfs_survey_collection


if __name__ == '__main__':
    import logging
    import sys
    import datetime
    start_time = datetime.datetime.now()
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    years = [2006, 2007, 2008, 2009]
    erfs_survey_collection = build_erfs_survey_collection(years = years, erase = True,
        overwrite = False)
    log.info("The program have been executed in {}".format(datetime.datetime.now() - start_time))
