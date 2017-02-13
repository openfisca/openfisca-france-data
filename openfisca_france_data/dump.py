#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import pandas as pd
from itertools import cycle

for entity in survey_scenario.tax_benefit_system.entities:
    print entity.key
    entity_data_frame = None
    for variable, holder in simulation.holder_by_name.iteritems():
        data_frame_by_variable = dict()
        if holder.entity.key != entity.key:
            continue

        print variable
        if holder._array is not None:
            array = holder._array
            print str(array)
            if array == ():
                continue

        elif holder._array_by_period is not None:
            if holder._array_by_period.values()[0].shape == ():  # constant value
                continue

            data_frame = pd.DataFrame(dict(
                (str(period), array) for period, array in holder._array_by_period.iteritems()
                ))
            if entity_data_frame is None:
                entity_data_frame = data_frame
            else:
                entity_data_frame = pd.concat(
                    [entity_data_frame, data_frame],
                    axis = 1,
                    )

        print '======'
    bim
    # entity_data_frame.to_stata('{}.dta'.format(entity.key))
