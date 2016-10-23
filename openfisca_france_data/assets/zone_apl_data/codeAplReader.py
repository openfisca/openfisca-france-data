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


import csv, pickle

if __name__ == '__main__':

    codeDict = {}
    fileName = 'zone_apl.csv'

    code = csv.reader(open(fileName), delimiter = ";")

    for row in code:
        codeDict.update({row[2]:(row[1],row[4])})

    #print codeDict['75017']

    outputFile = open("code_apl", 'wb')
    pickle.dump(codeDict, outputFile)
    outputFile.close()
