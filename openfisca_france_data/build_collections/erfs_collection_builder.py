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

import os
import logging

from openfisca_france_data.surveys import Survey, SurveyCollection

log = logging.getLogger(__name__)

def build_empty_erfs_survey_collection(years= None):
    if years is None:
        log.error("A list of years to process is needed")

    erfs_survey_collection = SurveyCollection(name = "erfs")
    erfs_survey_collection.set_config_files_directory()
    input_data_directory = erfs_survey_collection.config.get('data', 'input_directory')
    output_data_directory = erfs_survey_collection.config.get('data', 'output_directory')

    for year in years:
        yr = str(year)[2:]
        yr1 = str(year+1)[2:]

        eec_variables = [
            'acteu',
            'agepr',
            'chpub',
            'cohab',
            'contra',
            'ddipl',
            'dip11',
            'encadr',
            'forter',
            'ident',
            'lien',
            'lpr',
            'mrec',
            'naia',
            'naim',
            'nbsala',
            'noi',
            'noicon',
            'noimer',
            'noindiv',
            'noiper',
            'prosa',
            'retrai',
            'rga',
            'rstg',
            'sexe',
            'statut',
            'stc',
            'titc',
            'txtppb',
            ]
        eec_rsa_variables = ["sp0" + str(i) for i in range(0,10)] + ["sp10", "sp11"] + [
                'adeben',
                'adfdap',
                'amois',
                'ancchom',
                'ancentr',
                'ancinatm',
                'datant',
                'dimtyp',
                'rabsp',
                'raistp',
                'raistp',
                'rdem',
                'sitant',
                ]
        eec_aah_variables = [ "maahe", "rc1rev"]
        eec_variables += eec_rsa_variables + eec_aah_variables

        erf_tables = {
            "erf_menage": {  # Enquête revenu fiscaux, table ménage
                "Rdata_table" : "menage" + yr,
                "sas_file" : u"Ménages/menage" + yr,
                "year" : year,
                "variables" : None,
                },
            "eec_menage": {  # Enquête emploi en continu, table ménage
                "Rdata_table" : "mrf" + yr + "e" + yr + "t4",
                "sas_file" : u"Ménages/mrf" + yr + "e" + yr + "t4",
                "year" : year,
                "variables" : None,
                },
            "foyer": {      # Enquête revenu fiscaux, table foyer
                "Rdata_table" : "foyer" + yr,
                "sas_file" : "Foyers/foyer" + yr,
                "year": year,
                "variables" : None,
                },
            "erf_indivi": {  # Enquête revenu fiscaux, table individu
                "Rdata_table" : "indivi" + yr,
                "sas_file" :"Individus/indivi{}".format(year, yr),
                "year": year,
                "variables" : ['noi','noindiv','ident','declar1','quelfic','persfip','declar2','persfipd','wprm',
                     "zsali","zchoi","ztsai","zreti","zperi","zrsti","zalri","zrtoi","zragi","zrici","zrnci",
                     "zsalo","zchoo","ztsao","zreto","zpero","zrsto","zalro","zrtoo","zrago","zrico","zrnco",
                     ],
                },
            "eec_indivi": {  # Enquête emploi en continue, table individu
                "Rdata_table" : "irf" + yr + "e" + yr + "t4",
                "sas_file" : "Individus/irf" + yr + "e" + yr + "t4",
                "year" : year,
                "variables" : eec_variables,
                },
            "eec_cmp_1": {  # Enquête emploi en continue, table complémentaire 1
                "Rdata_table" : "icomprf" + yr + "e" + yr1 + "t1",
                "sas_file" : "Tables complémentaires/icomprf" + yr + "e" + yr1 + "t1",
                "year" : year,
                "variables" : eec_variables,
                },
            "eec_cmp_2": {
                "Rdata_table" : "icomprf" + yr + "e" + yr1 + "t2",
                "sas_file" : "Tables complémentaires/icomprf" + yr + "e" + yr1 + "t2",
                "year" : year,
                "variables" : eec_variables,
                },
            "eec_cmp_3": {
                "Rdata_table" : "icomprf" + yr + "e" + yr1 + "t3",
                "sas_file" : "Tables complémentaires/icomprf" + yr + "e" + yr1 + "t3",
                "year" : year,
                "variables" : eec_variables,
                },
        }

        # Build absolute path for Rdata_file
        for table in erf_tables.values():
            table["Rdata_file"] = os.path.join(
                os.path.dirname(input_data_directory),
                'R',
                'erf',
                str(year),
                table["Rdata_table"] + str(".Rdata"),
                )
            table["sas_file"] = os.path.join(
                os.path.dirname(input_data_directory),
                'ERFS_20{}'.format(yr),
                table["sas_file"] + str(".sas7bdat"),
                )
        survey_name = 'erfs_{}'.format(year)
        hdf5_file_path = os.path.join(
            os.path.dirname(output_data_directory),
            "{}{}".format(survey_name, ".h5")
            )
        survey = Survey(
            name = survey_name,
            hdf5_file_path = hdf5_file_path
            )

        for table, table_kwargs in erf_tables.iteritems():
            survey.insert_table(name = table, **table_kwargs)
            print table_kwargs.keys()
        surveys = erfs_survey_collection.surveys
        print surveys
        surveys[survey_name] = survey
    return erfs_survey_collection


if __name__ == '__main__':
    import logging
    import sys
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    erfs_survey_collection = build_empty_erfs_survey_collection(
        years = [2006, 2007, 2008, 2009],
        )
    erfs_survey_collection.fill_hdf_from_sas(surveys_name = ["erfs_2006"])
    erfs_survey_collection.dump(collection = "erfs")
