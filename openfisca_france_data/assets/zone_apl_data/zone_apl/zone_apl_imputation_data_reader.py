from pandas import read_csv
import numpy as np


if __name__ == '__main__':

    with open('zone_apl_2006.csv') as zone_csv:
        Z = read_csv(zone_csv, delimiter = ";")

    #% PSDC99          population sans double compte 99
    #% Pop_mun_2006    population municipale 2006

    #% M.POL99 de 1 à  4
    #% REG de    11 à 94
    #% TAU99      0 à 10
    #% TU99       0 à  8
    #% zone
    #
    grouped_5 =  Z.groupby(['TU99','TAU99','REG','POL99','Zone'], as_index=False)
    pop   = grouped_5['Pop_mun_2006'].aggregate(np.sum)

    # prepare result matrix by building empty result matrix
    res = pop.copy()
    res.pop('Zone')
    res.pop('Pop_mun_2006')

    res['zone1'] = 0
    res['zone2'] = 0
    res['zone3'] = 0
    print(res)
    print(pop.Pop_mun_2006[pop['Zone'] == 1])

    res['zone1'] = res['zone1'] + pop.Pop_mun_2006[pop['Zone']==1]
    res['zone2'] = res['zone2'] + pop.Pop_mun_2006[pop['Zone']==2]
    res['zone3'] = res['zone3'] + pop.Pop_mun_2006[pop['Zone']==3]

    print(res.to_string())

    for col in ('zone1', 'zone2', 'zone3'):
        res[col][np.isnan(res[col])] = 0

    print(res.to_string())
    res2 = res.groupby(['TU99', 'TAU99', 'REG', 'POL99'])

    final = res2.agg({
        'zone1': np.sum,
        'zone2': np.sum,
        'zone3': np.sum
        })
    final['total'] = final['zone1'] + final['zone2'] + final['zone3']
    final['proba_zone1'] = final['zone1']/final['total']
    final['proba_zone2'] = final['zone2']/final['total']
    final['proba_zone3'] = final['zone3']/final['total']

    final.pop('zone1')
    final.pop('zone2')
    final.pop('zone3')
    final.pop('total')

    final = final.reset_index()

    print(final)

    # Sanity check
    # s = final['p1'] + final['p2'] + final['p3']

    final.to_csv('./zone_apl_imputation_data.csv')
