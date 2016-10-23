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


from openfisca_france.data.sources.config import DATA_DIR
from openfisca_france.data.sources.utils import csv2hdf5
import os


def get_csv_file_name(year):

    os.path.dirname(DATA_DIR)
    R_DIR = os.path.join(os.path.dirname(DATA_DIR),'R','openfisca', str(year))
    yr = str(year)[2:]
    fname = os.path.join(R_DIR,"final"+ yr + ".csv")
    return fname

def build_survey_psl():
    year = 2006
    h5_name = '../survey_psl.h5'
    dfname = 'survey_' + str(year)
    os.path.dirname(DATA_DIR)
    PSL_DIR = os.path.join(os.path.dirname(DATA_DIR),'PSL')
    csv_name = os.path.join(PSL_DIR,"psl_"+ str(year) + ".csv")
    print("Using " + csv_name + " to build " + h5_name)
    csv2hdf5(csv_name, h5_name, dfname)


def build_survey(year, option='frame'):
    h5_name = '../survey.h5'
    dfname = 'survey_' + str(year)
    csv_name = get_csv_file_name(year)
    print("Using " + csv_name + " to build " + h5_name)
    csv2hdf5(csv_name, h5_name, dfname, option=option)

def build_all_surveys( option = 'frame'):
    h5_name = '../survey.h5'
    try:
        os.remove(h5_name)
    except:
        pass
    for year in range(2006,2010):
        build_survey(year, option=option)




if __name__ == '__main__':

    build_all_surveys()
