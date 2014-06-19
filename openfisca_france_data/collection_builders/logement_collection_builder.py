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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import logging
import os


from openfisca_france_data.surveys import Survey, SurveyCollection
log = logging.getLogger(__name__)


def build_empty_logement_survey_collection(years= None):

    if years is None:
        log.error("A list of years to process is needed")

    logement_survey_collection = SurveyCollection(name = "logement")
    logement_survey_collection.set_config_files_directory()
    input_data_directory = logement_survey_collection.config.get('data', 'input_directory')
    output_data_directory = logement_survey_collection.config.get('data', 'output_directory')

    for year in years:
        surveys = logement_survey_collection.surveys

        survey_name = 'logement_{}'.format(year)
        hdf5_file_path = os.path.join(
            os.path.dirname(output_data_directory),
            "{}{}".format(survey_name, ".h5")
            )
        survey = Survey(
            name = survey_name,
            hdf5_file_path = hdf5_file_path
            )
        surveys[survey_name] = survey

        yr = str(year)[2:]
        yr1 = str(year+1)[2:]

        if yr == "03":
            lgt_men = "menage"
            lgt_logt = None
            renameidlgt = dict(ident='ident')

        elif yr in ["06" ,"07", "08", "09"]: # TODO: clean this
            lgt_men = "menage1"
            lgt_lgt = "logement"
            renameidlgt = dict(idlog='ident')

        logement_tables = {
            "adresse" : "adresse",
            "lgt_menage" : lgt_men,
            "lgt_logt" : lgt_lgt,
            }

        RData_directory = os.path.join(os.path.dirname(input_data_directory),'R','logement', str(year))
        SasData_directory = os.path.join(os.path.dirname(input_data_directory),'enqlog2006/enq_06')


        for name, Rdata_table in logement_tables.iteritems():
          Rdata_file = os.path.join(RData_directory, "{}.Rdata".format(Rdata_table))
          sas_file = os.path.join(SasData_directory, "{}.sas7bdat".format(Rdata_table))
          survey.insert_table(name = name,
                              year = year,
                              Rdata_file = Rdata_file,
                              Rdata_table = Rdata_table,
                              sas_file = sas_file
                              )

    return logement_survey_collection


if __name__ == '__main__':

    logement_survey_collection = build_empty_logement_survey_collection(years = [2006])
#    logement_survey_collection.fill_hdf_from_Rdata()
    logement_survey_collection.fill_hdf_from_sas(["logement_2006"]) #TODO give the corect data directory (in os.path.join(os.etc...))
    logement_survey_collection.dump(collection = "logement")
