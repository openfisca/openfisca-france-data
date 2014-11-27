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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import gc
import logging

from openfisca_survey_manager.surveys import SurveyCollection
# from openfisca_france_data.build_openfisca_survey_data import save_temp
# from openfisca_france_data.build_openfisca_survey_data.utils import assert_dtype

log = logging.getLogger(__name__)

from openfisca_france_data.temporary import TemporaryStore

temporary_store = TemporaryStore.create(file_name = "indirect_taxation_tmp")

def test(year = None):
    """
    Demo
    """
    matrice_passage_data_frame, selected_parametres_fiscalite_data_frame = \
        get_transfert_data_frames(year)


    assert year is not None
    # load data
    bdf_survey_collection = SurveyCollection.load(collection = 'budget_des_familles')
    survey = bdf_survey_collection.surveys['budget_des_familles_{}'.format(year)]

    c05d = survey.get_values(table = "c05d")
    print c05d.columns
    print c05d.info()
    df = matrice_passage_data_frame[['poste{}'.format(year), 'posteCOICOP']]
    print df.info()
    print df.head()
    grouped = df.groupby('posteCOICOP')
    print grouped.first()
    print grouped.groups
    print len(grouped.groups)
    print grouped.min()
    print grouped.groups
    for name, group in grouped:
        print name
        print group

 #   c05d['COICOP'] = c05d.rename()

#    print c05d.describe()
#    gc.collect()
#    c05d = survey.get_values(table = "c05d")
#    individu = survey.get_values(table = "individu")
#    print individu.columns
#    print individu.info()
#    print individu.describe()
#    temporary_store["test"] = c05d
#    temporary_store.close()


def get_transfert_data_frames(year = 2005):
    from pandas import read_excel
    import os
    directory_path = os.path.normpath("/home/benjello/IPP/openfisca_france_indirect_taxation")
    matrice_passage_file_path = os.path.join(directory_path, "Matrice passage {}-COICOP.xls".format(year))
    parametres_fiscalite_file_path = os.path.join(directory_path, "Parametres fiscalite indirecte.xls")
    matrice_passage_data_frame = read_excel(matrice_passage_file_path)
    print matrice_passage_data_frame
    print matrice_passage_data_frame["label{}".format(year)][0]
    parametres_fiscalite_data_frame = read_excel(parametres_fiscalite_file_path, sheetname = "categoriefiscale")
    selected_parametres_fiscalite_data_frame = \
        parametres_fiscalite_data_frame[parametres_fiscalite_data_frame.annee == year]
    print selected_parametres_fiscalite_data_frame
    return matrice_passage_data_frame, selected_parametres_fiscalite_data_frame



if __name__ == '__main__':
    log.info('Entering 01_pre_proc')
    import sys
    import time
    logging.basicConfig(level = logging.INFO, stream = sys.stdout)
    deb = time.clock()
    year = 2005
    test(year = year)

    log.info("step 01 demo duration is {}".format(time.clock() - deb))
