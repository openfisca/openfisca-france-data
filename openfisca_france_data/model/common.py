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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.


from __future__ import division

from numpy import arange, argsort, asarray, cumsum, linspace, logical_and as and_, repeat

from openfisca_france.model.base import QUIFAM, QUIFOY


CHEF = QUIFAM['chef']
ENFS = [QUIFAM['enf{}'.format(i)] for i in range(1, 10)]
PART = QUIFAM['part']
VOUS = QUIFOY['vous']


def mark_weighted_percentiles(a, labels, weights, method, return_quantiles=False):
# from http://pastebin.com/KTLip9ee
    # a is an input array of values.
    # weights is an input array of weights, so weights[i] goes with a[i]
    # labels are the names you want to give to the xtiles
    # method refers to which weighted algorithm.
    #      1 for wikipedia, 2 for the stackexchange post.

    # The code outputs an array the same shape as 'a', but with
    # labels[i] inserted into spot j if a[j] falls in x-tile i.
    # The number of xtiles requested is inferred from the length of 'labels'.

    # First method, "vanilla" weights from Wikipedia article.
    if method == 1:

        # Sort the values and apply the same sort to the weights.
        N = len(a)
        sort_indx = argsort(a)
        tmp_a = a[sort_indx].copy()
        tmp_weights = weights[sort_indx].copy()

        # 'labels' stores the name of the x-tiles the user wants,
        # and it is assumed to be linearly spaced between 0 and 1
        # so 5 labels implies quintiles, for example.
        num_categories = len(labels)
        breaks = linspace(0, 1, num_categories + 1)

        # Compute the percentile values at each explicit data point in a.
        cu_weights = cumsum(tmp_weights)
        p_vals = (1.0 / cu_weights[-1]) * (cu_weights - 0.5 * tmp_weights)

        # Set up the output array.
        ret = repeat(0, len(a))
        if(len(a) < num_categories):
            return ret

        # Set up the array for the values at the breakpoints.
        quantiles = []

        # Find the two indices that bracket the breakpoint percentiles.
        # then do interpolation on the two a_vals for those indices, using
        # interp-weights that involve the cumulative sum of weights.
        for brk in breaks:
            if brk <= p_vals[0]:
                i_low = 0
                i_high = 0
            elif brk >= p_vals[-1]:
                i_low = N - 1
                i_high = N - 1
            else:
                for ii in range(N - 1):
                    if (p_vals[ii] <= brk) and (brk < p_vals[ii + 1]):
                        i_low = ii
                        i_high = ii + 1

            if i_low == i_high:
                v = tmp_a[i_low]
            else:
                # If there are two brackets, then apply the formula as per Wikipedia.
                v = (tmp_a[i_low] +
                    ((brk - p_vals[i_low]) / (p_vals[i_high] - p_vals[i_low])) * (tmp_a[i_high] - tmp_a[i_low]))

            # Append the result.
            quantiles.append(v)

        # Now that the weighted breakpoints are set, just categorize
        # the elements of a with logical indexing.
        for i in range(0, len(quantiles) - 1):
            lower = quantiles[i]
            upper = quantiles[i + 1]
            ret[and_(a >= lower, a < upper)] = labels[i]

        #make sure upper and lower indices are marked
        ret[a <= quantiles[0]] = labels[0]
        ret[a >= quantiles[-1]] = labels[-1]

        return ret

    # The stats.stackexchange suggestion.
    elif method == 2:

        N = len(a)
        sort_indx = argsort(a)
        tmp_a = a[sort_indx].copy()
        tmp_weights = weights[sort_indx].copy()

        num_categories = len(labels)
        breaks = linspace(0, 1, num_categories + 1)

        cu_weights = cumsum(tmp_weights)

        # Formula from stats.stackexchange.com post.
        s_vals = [0.0]
        for ii in range(1, N):
            s_vals.append(ii * tmp_weights[ii] + (N - 1) * cu_weights[ii - 1])
        s_vals = asarray(s_vals)

        # Normalized s_vals for comapring with the breakpoint.
        norm_s_vals = (1.0 / s_vals[-1]) * s_vals

        # Set up the output variable.
        ret = repeat(0, N)
        if(N < num_categories):
            return ret

        # Set up space for the values at the breakpoints.
        quantiles = []

        # Find the two indices that bracket the breakpoint percentiles.
        # then do interpolation on the two a_vals for those indices, using
        # interp-weights that involve the cumulative sum of weights.
        for brk in breaks:
            if brk <= norm_s_vals[0]:
                i_low = 0
                i_high = 0
            elif brk >= norm_s_vals[-1]:
                i_low = N - 1
                i_high = N - 1
            else:
                for ii in range(N - 1):
                    if (norm_s_vals[ii] <= brk) and (brk < norm_s_vals[ii + 1]):
                        i_low = ii
                        i_high = ii + 1

            if i_low == i_high:
                v = tmp_a[i_low]
            else:
                # Interpolate as in the method 1 method, but using the s_vals instead.
                v = (tmp_a[i_low] +
                    (((brk * s_vals[-1]) - s_vals[i_low]) /
                        (s_vals[i_high] - s_vals[i_low])) * (tmp_a[i_high] - tmp_a[i_low]))
            quantiles.append(v)

        # Now that the weighted breakpoints are set, just categorize
        # the elements of a as usual.
        for i in range(0, len(quantiles) - 1):
            lower = quantiles[i]
            upper = quantiles[i + 1]
            ret[and_(a >= lower, a < upper)] = labels[i]

        #make sure upper and lower indices are marked
        ret[a <= quantiles[0]] = labels[0]
        ret[a >= quantiles[-1]] = labels[-1]

        if return_quantiles:
            return ret, quantiles
        else:
            return ret


def _champm_ind(self, champm_holder):
    return self.cast_from_entity_to_roles(champm_holder)


def _champm_fam(self, champm_ind_holder):
    return self.filter_role(champm_ind_holder, role = CHEF)


def _champm_foy(self, champm_ind_holder):
    return self.filter_role(champm_ind_holder, role = VOUS)


def _decile(nivvie, champm, wprm):
    '''
    Décile de niveau de vie disponible
    'men'
    '''
    labels = arange(1, 11)
    method = 2
    decile, values = mark_weighted_percentiles(nivvie, labels, wprm * champm, method, return_quantiles = True)
#    print values
#    print len(values)
#    print (nivvie*champm).min()
#    print (nivvie*champm).max()
#    print decile.min()
#    print decile.max()
#    print (nivvie*(decile==1)*champm*wprm).sum()/( ((decile==1)*champm*wprm).sum() )
    del values
    return decile * champm


def _decile_net(nivvie_net, champm, wprm):
    '''
    Décile de niveau de vie net
    'men'
    '''
    labels = arange(1, 11)
    method = 2
    decile, values = mark_weighted_percentiles(nivvie_net, labels, wprm * champm, method, return_quantiles = True)
    return decile * champm


def _pauvre40(nivvie, champm, wprm):
    '''
    Indicatrice de pauvreté à 50% du niveau de vie median
    'men'
    '''
    labels = arange(1, 3)
    method = 2
    percentile, values = mark_weighted_percentiles(nivvie, labels, wprm * champm, method, return_quantiles = True)
    threshold = .4 * values[1]
    return (nivvie <= threshold) * champm


def _pauvre50(nivvie, champm, wprm):
    '''
    Indicatrice de pauvreté à 50% du niveau de vie median
    'men'
    '''
    labels = arange(1, 3)
    method = 2
    percentile, values = mark_weighted_percentiles(nivvie, labels, wprm * champm, method, return_quantiles = True)
    threshold = .5 * values[1]
    return (nivvie <= threshold) * champm


def _pauvre60(nivvie, champm, wprm):
    '''
    Indicatrice de pauvreté à 60% du niveau de vie median
    'men'
    '''
    labels = arange(1, 3)
    method = 2
    percentile, values = mark_weighted_percentiles(nivvie, labels, wprm * champm, method, return_quantiles = True)
    threshold = .6 * values[1]
    return (nivvie <= threshold) * champm


def _weight_ind(self, wprm_holder):
    return self.cast_from_entity_to_roles(wprm_holder)


def _weight_fam(self, weight_ind_holder):
    return self.filter_role(weight_ind_holder, role = CHEF)


def _weight_foy(self, weight_ind_holder):
    return self.filter_role(weight_ind_holder, role = VOUS)
