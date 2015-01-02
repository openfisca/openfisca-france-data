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


import logging


from openfisca_survey_manager.surveys import SurveyCollection
from openfisca_france_data.erf import get_of2erf, get_erf2of
import numpy as np


log = logging.getLogger(__name__)


def build_erf_aggregates(variables = None, year = 2006, unit = 1e6):
    """
    Fetch the relevant aggregates from erf data
    """
    erfs_survey_collection = SurveyCollection.load(collection = "erfs")
    erfs_survey = erfs_survey_collection.surveys["erfs_{}".format(year)]


    of2erf = get_of2erf()
    erf2of = get_erf2of()

    if set(variables) <= set(of2erf.keys()):
        variables = [ of2erf[variable] for variable in variables]

    if variables is not None and "wprm" not in variables:
        variables.append("wprm")
    log.info("Fetching aggregates from erfs {} data".format(year))


    df = erfs_survey.get_values(variables = variables, table = "erf_menage")


    df.rename(columns = erf2of, inplace = True)
    wprm = df["wprm"]
    for col in df.columns:
        try:
            df[col] = df[col].astype(np.float64)
        except:
            pass
    df = df.mul(wprm, axis = 0)
    for col in list(set(df.columns) - set(['ident', 'wprm'])):
        try:
            df[col] = df[col].sum()/1e6
        except:
            pass

    return df.ix[0:1] # Aggregate so we only need 1 row


if __name__ == '__main__':
    df = build_erf_aggregates(variables = ["af"])
    print df.to_string()
