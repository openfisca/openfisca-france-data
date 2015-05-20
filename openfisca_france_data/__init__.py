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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.


import os
import pkg_resources

from .model.base import TaxBenefitSystem
from .model import input_variables  # Load input variables into entities. # noqa analysis:ignore
from .model import model  # Load output variables into entities. # noqa analysis:ignore


def init_country():
    """Create a country-specific TaxBenefitSystem for use with data."""
    return TaxBenefitSystem


AGGREGATES_DEFAULT_VARS = [
    'cotsoc_noncontrib',
    'csg',
    'crds',
    'irpp',
    'ppe',
    'ppe_brute',
    'af',
    'af_base',
    'af_majo',
    'af_forf',
    'cf',
    'paje_base',
    'paje_nais',
    'paje_clca',
    'paje_clmg',
    'ars',
    'aeeh',
    'asf',
    'aspa',
    'aah',
    'caah',
    'rsa',
    'rsa_act',
    'aefa',
    'api',
#    'majo_rsa',
    'psa',
    'aides_logement',
    'alf',
    'als',
    'apl',
    ]
    # ajouter csgd pour le calcul des agrégats erfs
    # ajouter rmi pour le calcul des agrégats erfs

default_config_files_directory = os.path.join(
    pkg_resources.get_distribution('openfisca-survey-manager').location)

COUNTRY_DIR = os.path.dirname(os.path.abspath(__file__))
FILTERING_VARS = ["champm"]
PLUGINS_DIR = os.path.join(COUNTRY_DIR, 'plugins')
WEIGHT = "wprm"
WEIGHT_INI = "wprm_init"


def preproc_inputs(self, datatable):
    """Preprocess inputs table: country specific manipulations

    Parameters
    ----------
    datatable : a DataTable object
                the DataTable containing the input variables of the model

    """
    try:
        datatable.propagate_to_members(WEIGHT, 'ind')
    #    datatable.propagate_to_members('rfr_n_2', 'ind')
    #    datatable.propagate_to_members('nbptr_n_2', 'ind')
    except:
        pass
