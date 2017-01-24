# -*- coding: utf-8 -*-

from __future__ import division


import logging
import numpy as np


from openfisca_france_data.tests import base as base_survey
from openfisca_france_data.erfs_fpr.scenario import ErfsFprSurveyScenario
from openfisca_france_data.aggregates import Aggregates


log = logging.getLogger(__name__)


def test_erfs_fpr_survey_simulation_aggregates(year = 2012):
    np.seterr(all='raise')
    tax_benefit_system = base_survey.get_cached_reform(
        reform_key = 'inversion_directe_salaires',
        tax_benefit_system = base_survey.france_data_tax_benefit_system,
        )
    survey_scenario = ErfsFprSurveyScenario.create(
        tax_benefit_system = tax_benefit_system,
        reference_tax_benefit_system = tax_benefit_system,
        year = year,
        )
    return survey_scenario


def test_erfs_fpr_aggregates_reform():
    '''
    test aggregates value with data
    :param year: year of data and simulation to test agregates
    :param reform: optional argument, put an openfisca_france.refoms object, default None
    '''
    survey_scenario = ErfsFprSurveyScenario.create(data_year = 2012, year = 2015, reform_key = 'plf2015')
    aggregates = Aggregates(survey_scenario = survey_scenario)
    base_data_frame = aggregates.compute_aggregates()

    return aggregates, base_data_frame


if __name__ == '__main__':
    import logging
    log = logging.getLogger(__name__)
    import sys
    logging.basicConfig(level = logging.INFO, stream = sys.stdout)
    # aggregates_data_frame, difference_data_frame,
    survey_scenario = test_erfs_fpr_survey_simulation_aggregates()

    aggregates = Aggregates(survey_scenario = survey_scenario)
    df = aggregates.compute_aggregates()
    difference_data_frame = aggregates.compute_difference()
    # return aggregates.base_data_frame, difference_data_frame, survey_scenario

    # df = test_erfs_aggregates_reform()


# survey_scenario.summarize_variable('salaire_imposable')
# salaire_imposable: 52 periods * 127126 cells * item size 4 (float32, default = 0) = 25.2M

# 2010-04: mean = 8446.36035156, min = 2.76261019707, max = 2167496.5, mass = 1.07e+09, default = 0.0%, median = 2.83261013031
# 2010-05: mean = 8446.359375, min = 2.76261019707, max = 2167496.5, mass = 1.07e+09, default = 0.0%, median = 2.83261013031
# 2010-06: mean = 8446.36425781, min = 2.76261019707, max = 2167496.5, mass = 1.07e+09, default = 0.0%, median = 2.83261013031
# 2010-07: mean = 8446.36914062, min = 2.76261019707, max = 2167496.5, mass = 1.07e+09, default = 0.0%, median = 2.83261013031
# 2010-08: mean = 8446.37207031, min = 2.76261019707, max = 2167496.5, mass = 1.07e+09, default = 0.0%, median = 2.83261013031
# 2010-09: mean = 8446.375, min = 2.76261019707, max = 2167496.5, mass = 1.07e+09, default = 0.0%, median = 2.83261013031
# 2010-10: mean = 8446.37597656, min = 2.76261019707, max = 2167496.5, mass = 1.07e+09, default = 0.0%, median = 2.83261013031
# 2010-11: mean = 8446.37988281, min = 2.76261019707, max = 2167496.5, mass = 1.07e+09, default = 0.0%, median = 2.83261013031
# 2010-12: mean = 7283.9609375, min = 2.54261016846, max = 2135010.25, mass = 9.26e+08, default = 0.0%, median = 2.83261013031
# 2011-01: mean = 8438.84472656, min = 2.77209997177, max = 2167607.0, mass = 1.07e+09, default = 0.0%, median = 2.84209990501
# 2011-02: mean = 8438.84472656, min = 2.77209997177, max = 2167607.0, mass = 1.07e+09, default = 0.0%, median = 2.84209990501
# 2011-03: mean = 8438.84472656, min = 2.77209997177, max = 2167607.0, mass = 1.07e+09, default = 0.0%, median = 2.84209990501
# 2011-04: mean = 8438.84472656, min = 2.77209997177, max = 2167607.0, mass = 1.07e+09, default = 0.0%, median = 2.84209990501
# 2011-05: mean = 8438.84472656, min = 2.77209997177, max = 2167607.0, mass = 1.07e+09, default = 0.0%, median = 2.84209990501
# 2011-06: mean = 8438.84472656, min = 2.77209997177, max = 2167607.0, mass = 1.07e+09, default = 0.0%, median = 2.84209990501
# 2011-07: mean = 8439.91503906, min = 2.77209997177, max = 2167607.0, mass = 1.07e+09, default = 0.0%, median = 2.84209990501
# 2011-08: mean = 8439.91699219, min = 2.77209997177, max = 2167607.0, mass = 1.07e+09, default = 0.0%, median = 2.84209990501
# 2011-09: mean = 8439.92089844, min = 2.77209997177, max = 2167607.0, mass = 1.07e+09, default = 0.0%, median = 2.84209990501
# 2011-10: mean = 8439.92578125, min = 2.77209997177, max = 2167607.0, mass = 1.07e+09, default = 0.0%, median = 2.84209990501
# 2011-11: mean = 8439.92480469, min = 2.77209997177, max = 2167607.0, mass = 1.07e+09, default = 0.0%, median = 2.84209990501
# 2011-12: mean = 7275.52832031, min = 2.55209994316, max = 2134811.5, mass = 9.25e+08, default = 0.0%, median = 2.84209990501
# 2012-01: mean = 8446.91113281, min = 2.83648991585, max = 2168076.75, mass = 1.07e+09, default = 0.0%, median = 2.90648984909
# 2012-02: mean = 8446.91210938, min = 2.83648991585, max = 2168076.75, mass = 1.07e+09, default = 0.0%, median = 2.90648984909
# 2012-03: mean = 8446.9140625, min = 2.83648991585, max = 2168076.75, mass = 1.07e+09, default = 0.0%, median = 2.90648984909
# 2012-04: mean = 8446.91796875, min = 2.83648991585, max = 2168076.75, mass = 1.07e+09, default = 0.0%, median = 2.90648984909
# 2012-05: mean = 8446.91699219, min = 2.83648991585, max = 2168076.75, mass = 1.07e+09, default = 0.0%, median = 2.90648984909
# 2012-06: mean = 8446.91796875, min = 2.83648991585, max = 2168076.75, mass = 1.07e+09, default = 0.0%, median = 2.90648984909
# 2012-07: mean = 8446.91992188, min = 2.83648991585, max = 2168076.75, mass = 1.07e+09, default = 0.0%, median = 2.90648984909
# 2012-08: mean = 8446.95898438, min = 2.89342999458, max = 2168076.75, mass = 1.07e+09, default = 0.0%, median = 2.96342992783
# 2012-09: mean = 8446.95898438, min = 2.89342999458, max = 2168076.75, mass = 1.07e+09, default = 0.0%, median = 2.96342992783
# 2012-10: mean = 8446.95800781, min = 2.89342999458, max = 2168076.75, mass = 1.07e+09, default = 0.0%, median = 2.96342992783
# 2012-11: mean = 8455.38867188, min = 2.89342999458, max = 2168113.5, mass = 1.07e+09, default = 0.0%, median = 2.96342992783
# 2012-12: mean = 7287.64013672, min = 2.67342996597, max = 2134927.75, mass = 9.26e+08, default = 0.0%, median = 2.96342992783
# 2008: mean = 0.0, min = 0.0, max = 0.0, mass = 0.00e+00, default = 100.0%, median = 0.0
# 2009: mean = 0.0, min = 0.0, max = 0.0, mass = 0.00e+00, default = 100.0%, median = 0.0
# 2010: mean = 7295.37744141, min = 2.54261016846, max = 2135010.25, mass = 9.27e+08, default = 0.0%, median = 2.83261013031
# year:2010-10: mean = 100129.523438, min = 33.0167350769, max = 25978468.0, mass = 1.27e+10, default = 0.0%, median = 34.0767288208
# year:2010-11: mean = 100123.070312, min = 33.026222229, max = 25978580.0, mass = 1.27e+10, default = 0.0%, median = 34.0862197876
# year:2010-12: mean = 100116.625, min = 33.0357131958, max = 25978692.0, mass = 1.27e+10, default = 0.0%, median = 34.0957107544
# 2011: mean = 7289.37304688, min = 2.55209994316, max = 2135010.0, mass = 9.27e+08, default = 0.0%, median = 2.84209990501
# year:2011-02: mean = 100116.257812, min = 33.1095924377, max = 25978960.0, mass = 1.27e+10, default = 0.0%, median = 34.1695899963
# year:2011-03: mean = 100124.328125, min = 33.1739807129, max = 25979428.0, mass = 1.27e+10, default = 0.0%, median = 34.2339782715
# year:2011-04: mean = 100132.40625, min = 33.2383728027, max = 25979896.0, mass = 1.27e+10, default = 0.0%, median = 34.2983703613
# year:2011-05: mean = 100140.476562, min = 33.3027610779, max = 25980364.0, mass = 1.27e+10, default = 0.0%, median = 34.3627586365
# year:2011-06: mean = 100148.53125, min = 33.3671531677, max = 25980834.0, mass = 1.27e+10, default = 0.0%, median = 34.4271507263
# year:2011-07: mean = 100156.617188, min = 33.4315414429, max = 25981304.0, mass = 1.27e+10, default = 0.0%, median = 34.4915390015
# year:2011-08: mean = 100163.625, min = 33.4959335327, max = 25981774.0, mass = 1.27e+10, default = 0.0%, median = 34.5559310913
# year:2011-09: mean = 100170.671875, min = 33.6172637939, max = 25982244.0, mass = 1.27e+10, default = 0.0%, median = 34.6772613525
# year:2011-10: mean = 100177.703125, min = 33.7385940552, max = 25982714.0, mass = 1.27e+10, default = 0.0%, median = 34.7985916138
# year:2011-11: mean = 100184.734375, min = 33.8599205017, max = 25983184.0, mass = 1.27e+10, default = 0.0%, median = 34.919921875
# year:2011-12: mean = 100200.195312, min = 33.9812507629, max = 25983692.0, mass = 1.27e+10, default = 0.0%, median = 35.0412483215
# 2012: mean = 100212.320312, min = 34.1025848389, max = 25983808.0, mass = 1.27e+10, default = 0.0%, median = 35.1625785828