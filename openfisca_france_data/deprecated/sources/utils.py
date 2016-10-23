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


from pandas import  HDFStore, read_csv

def csv2hdf5(csv_name, h5_name, dfname, option='frame'):
    """
    Convert a csv file to a dataframe in a hdf5

    Parameters:

    csv_name: string
              csv file name
    h5_name : string
              hdf5 file name
    dfname  : string
              dataframe name
    option  : string, 'frame' or 'table', default to 'frame'
              stoing type in the pytable
    """

    table = read_csv(csv_name)
    store = HDFStore(h5_name)

    if option == 'frame':
        store.put(dfname, table)

    elif option == 'table': # for frame_table à la pytables
        object_cols =  table.dtypes[ table.dtypes == 'object']
        print object_cols.index
        try:
            store.append(dfname,table)
        except:
            print table.get_dtype_counts()
            object_cols =  table.dtypes[ table.dtypes == 'object']

            for col in object_cols.index:
                print 'removing object column :', col
                del table[col]

            store.append(dfname,table)

    print store
    store.close()

def test_hdf5(h5_name):
    store = HDFStore(h5_name)
    for key in store.keys():
        print key

    store.close()


if __name__ == '__main__':
    pass
