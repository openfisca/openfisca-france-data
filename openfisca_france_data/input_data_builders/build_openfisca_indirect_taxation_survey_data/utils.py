#! /usr/bin/env python
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
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


from __future__ import division


def collapsesum(data_frame, by = None, var = None):
    '''
    Pour une variable, fonction qui calcule la moyenne pondérée au sein de chaque groupe.
    '''
    assert by is not None
    assert var is not None
    grouped = data_frame.groupby([by])
    return grouped.apply(lambda x: weighted_sum(groupe = x, var =var))


def find_nearest_inferior(years, year):
    # years = year_data_list
    anterior_years = [
        available_year for available_year in years if available_year <= year
        ]
    return max(anterior_years)


# ident_men_dtype = numpy.dtype('O')
ident_men_dtype = 'str'


def weighted_sum(groupe, var):
    '''
    Fonction qui calcule la moyenne pondérée par groupe d'une variable
    '''
    data = groupe[var]
    weights = groupe['pondmen']
    return (data * weights).sum()
