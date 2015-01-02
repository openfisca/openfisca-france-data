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


# TODO: THIS NEEDS CLEANING

# this directory contains:
#   - zone_apl_2006.csv : PSDC99, Pop_mun_2006, Zone, REG, POL99, TU99, TAU99
#   - zone_apl.csv : example of row : PARIS    Paris    75012    75056    1
#   - zone_apl_imputation_data : ,TU99,TAU99,REG,POL99,proba_zone1,proba_zone2,proba_zone3


# zone_apl_imputation_data_reader.py uses zone_apl_2006 to build zone_apl_imputation_data

# code_apl in france.data is used by a widget codeAplReader was used to produce it.
# Should be stored here
