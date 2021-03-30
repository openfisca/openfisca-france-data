from openfisca_core import periods

from openfisca_france_data import openfisca_france_tax_benefit_system


# smic_horaire_brut = {  # smic horaire brut moyen sur l'année
#     2017: 9.76,
#     2016: 9.67,
#     2015: 9.61,
#     2014: 9.53,
#     2013: 9.43,
#     2012: 9.4 * 6 / 12 + 9.22 * 6 / 12,
#     2011: 9.19 * 1 / 12 + 9.0 * 11 / 12 ,
#     2010: 8.86,
#     }

smic_horaire_brut = dict()
for year in range(2010, 2021):
    try:
        smic_horaire_brut[year] = openfisca_france_tax_benefit_system.get_parameters_at_instant(instant = periods.period(year).start).cotsoc.gen.smic_h_b
    except:
        continue

# Sources BDM
smic_annuel_net_by_year = {
    2020: 12 * 1200.0,
    2019: 12 * 1200.0,
    2018: 9 * 1173.60 + 3 * 1187.83,  # Baisse de la cotisaation chômage en cours d'annnée
    2017: 12 * 1151.50,
    2016: 12 * 1141.61,
    2015: 12 * 1135.99,
    2014: 12 * 1128.70,
    2013: 12 * 1120.43,
    2012: 2 * 1116.87 + 4 * 1118.29 + 6 * 1096.88,
    2011: 11 * 1072.07 + 1094.71,
    2010: 12 * 1056.24,
    }

abattement_by_year = {
    2020: .0175,
    2019: .0175,
    2018: .0175,
    2017: .0175,
    2016: .0175,
    2015: .0175,
    2014: .0175,
    2013: .0175,
    2012: .0175,
    2011: .03,
    2010: .03,
    }


def smic_annuel_imposbale_from_net(year):
    smic_net = smic_annuel_net_by_year[year]
    smic_brut = smic_horaire_brut[year] * 35 * 52
    smic_imposable = (
        smic_net
        + (.024 + 0.005) * (1 - abattement_by_year[year]) * smic_brut
        )
    return smic_imposable


smic_annuel_imposbale_by_year = dict([
    (year, smic_annuel_imposbale_from_net(year))
    for year in range(2010, 2021)
    ])


smic_horaire_brut_by_year = dict([
    (year, openfisca_france_tax_benefit_system.get_parameters_at_instant(instant = periods.period(year).start).cotsoc.gen.smic_h_b)
    for year in range(2005, 2021)
    ])

smic_annuel_brut_by_year = dict([
    (year, value * 35 * 52)
    for year, value in smic_horaire_brut_by_year.items()
    ])