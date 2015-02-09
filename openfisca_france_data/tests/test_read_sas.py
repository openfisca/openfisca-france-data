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


import os
import gc

from sas7bdat import SAS7BDAT


#current_dir = os.path.dirname(os.path.realpath(__file__))


def test(table):
    data_directory = "/home/benjello/data/INSEE/"
    sas_file_path = os.path.join(
        data_directory,
        'budget_des_familles',
        '2011',
        'sas',
        table + '.sas7bdat',
        )
    return SAS7BDAT(sas_file_path).to_data_frame()


if __name__ == '__main__':

    tables = [
#        "a04",
#        "abocom",
#        "assu",
#        "autvehic",
#        "automobile",
#        "bienscult",
#        "biensdur",
#        "c05",
#        "carnets",
#        "compl_sante",
        "depindiv",  # test
#        "depmen",    # test
##        "enfanthorsdom",
##        "garage",
##        "individu",
#        "menage",   # test
#        "revind_dom",  # test
#        "revmen_dom",  # test
        ]
    for table in tables:
        print table
        df = test(table)
        gc.collect()