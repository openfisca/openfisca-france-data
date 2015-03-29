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


from pandas import HDFStore


from openfisca_france_data.input_data_builders import get_input_data_frame


current_dir = os.path.dirname(os.path.realpath(__file__))
hdf5_file_realpath = os.path.join(current_dir, 'data_files', 'fake_openfisca_input_data.h5')


def build_by_extraction(year = 2006):
    df = get_input_data_frame(year)
    output = df.ix[0:1]
    for symbol in ['fam', 'foy', 'men']:
        output['id{}_original'.format(symbol)] = output['id{}'.format(symbol)]
    output['sali'] = 20000
    output['wprm'] = 100
    store = HDFStore(hdf5_file_realpath)
    store.put(str(year), output)
    store.close()


def get_fake_input_data_frame(year = 2006):
    store = HDFStore(hdf5_file_realpath)
    input_data_frame = store.select(str(year))
    input_data_frame.rename(
        columns = dict(sali = 'sal', choi = 'cho', rsti = 'rst'),
        inplace = True,
        )
    input_data_frame.reset_index(inplace = True)
    return input_data_frame


if __name__ == '__main__':
    year = 2006
    # build_by_extraction(year = year)
    df = get_fake_input_data_frame(year = year)
