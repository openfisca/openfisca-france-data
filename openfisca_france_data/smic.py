"Calcule divers Smic"

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
for year in range(2002, 2021):
    try:

        smic_horaire_brut[year] = openfisca_france_tax_benefit_system.parameters(year).marche_travail.salaire_minimum.smic_h_b
    except:
        continue

# Sources BDM
# Pour les années avant 2010: BDM donne un indice en base 2000. On multiplie à
#partir du chiffre de 2010. Les résultats pour les années après 2010 sont les
#mêmes à un euro près. 1996-1999 ont la meeeeeême valeur que 2000.
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
    2009: 12 * 1044.91,
    2008: 12 * 1026.01,
    2007: 12 * 995.76,
    2006: 12 * 970.81,
    2005: 12 * 933.01,
    2004: 12 * 885.37,
    2003: 12 * 838.50,
    2002: 12 * 810.52,
    2001: 12 * 784.82,
    2000: 12 * 756.08,
    1999: 12 * 756.08,
    1998: 12 * 756.08,
    1997: 12 * 756.08,
    1996: 12 * 756.08,
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
    2009: .03,
    2008: .03,
    2007: .03,
    2006: .03,
    2005: .03,
    2004: .03,
    2003: .03,
    2002: .03,
    2001: .03,
    2000: .03,
    1999: .03,
    1998: .03,
    1997: .03,
    1996: .03,
    }

def smic_annuel_imposable_from_net(year):
    smic_net = smic_annuel_net_by_year[year]
    smic_brut = smic_horaire_brut[year] * 35 * 52
    smic_imposable = (
        smic_net
        + (.024 + 0.005) * (1 - abattement_by_year[year]) * smic_brut
        )
    return smic_imposable


smic_annuel_imposable_by_year = dict([
    (year, smic_annuel_imposable_from_net(year))
    for year in range(2002, 2021)
    ])


smic_horaire_brut_by_year = dict([
    (
        year,
        openfisca_france_tax_benefit_system.parameters(year).marche_travail.salaire_minimum.smic_h_b
        )
    for year in range(2002, 2021)
    ])

smic_annuel_brut_by_year = dict([
    (year, value * 35 * 52)
    for year, value in smic_horaire_brut_by_year.items()
    ])