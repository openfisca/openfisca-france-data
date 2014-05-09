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


import logging
import sys
logging.basicConfig(level = logging.INFO, stream = sys.stdout)

from openfisca_france_data.build_openfisca_survey_data import (
    step_01_pre_processing as pre_processing,
    step_02_imputation_loyer as imputation_loyer,
    step_03_fip as fip,
    step_04_famille as famille,
    step_05_foyer as foyer,
    step_06_rebuild as rebuild,
#    step_07_invalides as invalides,
    step_08_final as final,
    )

def run_all(year = 2006, filename = "test", check = False):

    pre_processing.create_indivim(year = year)
    pre_processing.create_enfants_a_naitre(year = year)
    # imputation_loyer.create_imput_loyer(year = year)
    # fip.create_fip(year = year)
    famille.famille(year = year)
    foyer.sif(year = year)
    foyer.foyer_all(year = year)
    rebuild.create_totals(year = year)
    rebuild.create_final(year = year)
#    invalides.invalide(year = year)
    final.final(year = year, check = check)

if __name__ == '__main__':
    run_all(year = 2006, check = False)
    # import pdb
    # pdb.set_trace()
