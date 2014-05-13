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


import os

from openfisca_france_data.read_dbf import read_dbf
current_dir = os.path.dirname(os.path.realpath(__file__))


def test():
    dbf_file_path = os.path.join("/home/benjello/data/INSEE/Enquetes_emploi/emploi06/donnees/INDIV061.dbf")
    data_frame = read_dbf(dbf_file_path)
    print data_frame.info()

if __name__ == '__main__':
    import time
    deb = time.clock()
    test()
    print time.clock() - deb
