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


from pandas import  HDFStore, ExcelFile

def build_actualisation_group_vars_h5():
    h5_name = "../actualisation_groups.h5"
    store = HDFStore(h5_name)
    xls = ExcelFile('actualisation_groups.xls')
    df = xls.parse('data', na_values=['NA'])
    store['vars'] = df
    print df.to_string()
    print store
    from numpy import unique
    coeff_list = sorted(unique(df['coeff'].dropna()))
    print coeff_list
    groups = {}
    for coeff in coeff_list:
        groups[coeff] = list(df[ df['coeff']==coeff ]['var'])
    print groups
    store.close()

def build_actualisation_group_names_h5():
    h5_name = "../actualisation_groups.h5"
    store = HDFStore(h5_name)
    xls = ExcelFile('actualisation_groups.xls')
    df = xls.parse('defs', na_values=['NA'])
    store['names'] = df
    print df.to_string()
    store.close()

def build_actualisation_group_amounts_h5():
    h5_name = "../actualisation_groups.h5"
    store = HDFStore(h5_name)
    xls = ExcelFile('actualisation_groups.xls')
    df_a = xls.parse('amounts', na_values=['NA'])
    df_a = df_a.set_index(['case'], drop= True)
    df_b = xls.parse('benef', na_values=['NA'])
    df_c = xls.parse('corresp', na_values=['NA'])
    store['amounts'] = df_a
    store['benef']   = df_b
    store['corresp'] = df_c
    print df_a.to_string()
    print df_a.columns
    store.close()

def build_actualisation_groups():
    build_actualisation_group_vars_h5()
    build_actualisation_group_names_h5()

if __name__ == '__main__':
    pass
