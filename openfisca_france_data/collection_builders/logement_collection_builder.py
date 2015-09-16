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
# import getpass
import logging
import os
import pkg_resources

from openfisca_survey_manager.scripts.surv import add_survey_to_collection, create_data_file_by_format
from openfisca_survey_manager.survey_collections import SurveyCollection
openfisca_france_data_location = pkg_resources.get_distribution('openfisca-france-data').location
config_files_directory = os.path.join(openfisca_france_data_location)


log = logging.getLogger(__name__)


def build_survey_collection(name = None, erase_collection_json = False, overwrite_surveys = False,
        data_directory_path_by_year = None, source_format = 'sas'):

    assert name is not None
    assert data_directory_path_by_year is not None
    years = data_directory_path_by_year.keys()
    if years is None:
        log.error("A list of years to process is needed")

    if erase_collection_json:
        survey_collection = SurveyCollection(
            name = name, config_files_directory = config_files_directory)
    else:
        try:
            survey_collection = SurveyCollection.load(
                collection = name, config_files_directory = config_files_directory)
        except ConfigParser.NoOptionError:
            survey_collection = SurveyCollection(
                name = name, config_files_directory = config_files_directory)

    for year, data_directory_path in data_directory_path_by_year.iteritems():
        if not os.path.isdir(data_directory_path):
            input_data_directory = survey_collection.config.get('data', 'input_directory')
            assert os.path.isdir(input_data_directory)
            data_directory_path = os.path.join(input_data_directory, data_directory_path)
            assert os.path.isdir(input_data_directory)

        data_file_by_format = create_data_file_by_format(data_directory_path)
        print data_file_by_format
        survey_name = '{}_{}'.format(name, year)
        add_survey_to_collection(
            survey_name = survey_name,
            survey_collection = survey_collection,
            sas_files = data_file_by_format[source_format],
            )
        collections_directory = survey_collection.config.get('collections', 'collections_directory')
        collection_json_path = os.path.join(collections_directory, "{}.json".format(name))
        survey_collection.dump(json_file_path = collection_json_path)
        surveys = [survey for survey in survey_collection.surveys if survey.name.endswith(str(year))]
        survey_collection.fill_hdf(source_format = source_format, surveys = surveys, overwrite = overwrite_surveys)
    return survey_collection


if __name__ == '__main__':
    import logging
    import sys
    import datetime
    start_time = datetime.datetime.now()
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)

#    years = [2006, 2007, 2008, 2009]
#    erfs_survey_collection = build_survey_collection(name = 'erfs', years = years, erase_collection_json = True,
#        overwrite_surveys = False)

    logement_survey_collection = build_survey_collection(
        name = 'logement',
        data_directory_path_by_year = {
            2006: 'INSEE/logement/2006'
            },
        erase_collection_json = True,
        overwrite_surveys = True,
        )

    log.info("The program have been executed in {}".format(datetime.datetime.now() - start_time))



#        if yr == "03":
#            lgt_men = "menage"
#            lgt_logt = None
#            renameidlgt = dict(ident='ident')
#
#        elif yr in ["06" ,"07", "08", "09"]: # TODO: clean this
#            lgt_men = "menage1"
#            lgt_lgt = "logement"
#            renameidlgt = dict(idlog='ident')
#
#        logement_tables = {
#            "adresse" : "adresse",
#            "lgt_menage" : lgt_men,
#            "lgt_logt" : lgt_lgt,
#            }
#
#        RData_directory = os.path.join(os.path.dirname(input_data_directory),'R','logement', str(year))
#        SasData_directory = os.path.join(os.path.dirname(input_data_directory),'enqlog2006/enq_06')
#
#
#        for name, Rdata_table in logement_tables.iteritems():
#          Rdata_file = os.path.join(RData_directory, "{}.Rdata".format(Rdata_table))
#          sas_file = os.path.join(SasData_directory, "{}.sas7bdat".format(Rdata_table))
#          survey.insert_table(name = name,
#                              year = year,
#                              Rdata_file = Rdata_file,
#                              Rdata_table = Rdata_table,
#                              sas_file = sas_file
#                              )
#
#    return logement_survey_collection
#
#
