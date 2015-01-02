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


from pandas import  HDFStore, ExcelFile, concat, DataFrame
import os
from openfisca_core.simulations import SurveySimulation
from src.plugins.survey.aggregates import Aggregates



def build_totals():
    h5_name = "../amounts.h5"
    store = HDFStore(h5_name)

    files = ['logement_tous_regime', 'pfam_tous_regimes',
             'minima_sociaux_tous_regimes', 'IRPP_PPE', 'cotisations_TousRegimes' ]

    first = True
    for xlsfile in files:
        xls = ExcelFile(xlsfile + '.xlsx')
        print xls.path_or_buf
        df_a = xls.parse('amounts', na_values=['NA'])
        try:
            df_b   = xls.parse('benef', na_values=['NA'])
        except:
            df_b = DataFrame()

        if first:
            amounts_df = df_a
            benef_df =  df_b
            first = False
        else:
            amounts_df = concat([amounts_df, df_a])
            benef_df =  concat([benef_df, df_b])

    amounts_df, benef_df = amounts_df.set_index("var"), benef_df.set_index("var")
    print amounts_df.to_string()
    print benef_df.to_string()
    store['amounts'] = amounts_df
    store['benef']   = benef_df
    store.close




def test():
    country = "france"
    for year in range(2006,2010):

        yr = str(year)
        simu = SurveySimulation()
        simu.set_config(year = yr, country = country)
        simu.set_param()

        agg = Aggregates()
        agg.set_simulation(simu)

        for col in agg.varlist:
            print col

if __name__ == '__main__':
    #test()
    build_totals()
