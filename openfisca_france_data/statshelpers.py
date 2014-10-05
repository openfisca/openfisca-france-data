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


from __future__ import division

from numpy import cumsum, ones
from pandas import DataFrame


def gini(values, weights = None, bin_size = None):
    '''
    Gini coefficient (normalized to 1)
    Using fastgini formula :


                      i=N      j=i
                      SUM W_i*(SUM W_j*X_j - W_i*X_i/2)
                      i=1      j=1
          G = 1 - 2* ----------------------------------
                           i=N             i=N
                           SUM W_i*X_i  *  SUM W_i
                           i=1             i=1


        where observations are sorted in ascending order of X.

    From http://fmwww.bc.edu/RePec/bocode/f/fastgini.html
    '''
    if weights is None:
        weights = ones(len(values))

    df = DataFrame({'x': values, 'w':weights})
    df = df.sort_index(by='x')
    x = df['x']
    w = df['w']
    wx = w*x

    cdf = cumsum(wx)-0.5*wx
    numerator = (w*cdf).sum()
    denominator = ((wx).sum())*(w.sum())
    gini = 1 - 2*(numerator/denominator)

    return gini


def kakwani(values, ineq_axis, weights = None):
    '''
    Computes the Kakwani index
    '''
    from scipy.integrate import simps

    if weights is None:
        weights = ones(len(values))

#    sign = -1
#    if tax == True:
#        sign = -1
#    else:
#        sign = 1

    PLCx, PLCy = pseudo_lorenz(values, ineq_axis, weights)
    LCx, LCy = lorenz(ineq_axis, weights)

    del PLCx

    return simps((LCy - PLCy), LCx)


def lorenz(values, weights = None):
    '''
    Computes Lorenz Curve coordinates
    '''
    if weights is None:
        weights = ones(len(values))

    df = DataFrame({'v': values, 'w':weights})
    df = df.sort_index(by = 'v')
    x = cumsum(df['w'])
    x = x/float(x[-1:])
    y = cumsum(df['v']*df['w'])
    y = y/float(y[-1:])

    return x, y


def pseudo_lorenz(values, ineq_axis, weights = None):
    '''
    Computes The pseudo Lorenz Curve coordinates
    '''
    if weights is None:
        weights = ones(len(values))
    df = DataFrame({'v': values, 'a': ineq_axis, 'w':weights})
    df = df.sort_index(by = 'a')
    x = cumsum(df['w'])
    x = x/float(x[-1:])
    y = cumsum(df['v']*df['w'])
    y = y/float(y[-1:])

    return x, y
