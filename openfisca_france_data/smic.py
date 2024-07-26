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

        smic_horaire_brut[year] = openfisca_france_tax_benefit_system.parameters(year).marche_travail.salaire_minimum.smic.smic_b_horaire
    except:
        continue

# Sources BDM
# Pour les années avant 2010: BDM donne un indice en base 2000. On multiplie à
# partir du chiffre de 2010. Les résultats pour les années après 2010 sont les
# mêmes à un euro près. 1996-1999 ont la meeeeeême valeur que 2000.
smic_annuel_net_by_year = {
    2022: 4 * 1269.02 + 8 * 1302.64, # latest value as of May, assuming no change over the year to come
    2021: 9 * 1230.6 + 3 * 1258.22,

    2020: 12 * 1218.6,
    2019: 12 * 1204.19,
    2018: 9 * 1173.60 + 3 * 1187.83,  # Baisse de la cotisation chômage en cours d'annnée
    2017: 12 * 1151.50,
    2016: 12 * 1141.61,
    2015: 12 * 1135.99,
    2014: 12 * 1128.70,
    2013: 12 * 1120.43,
    2012: 2 * 1116.87 + 4 * 1118.29 + 6 * 1096.88,
    2011: 11 * 1072.07 + 1094.71,

    2010: 12 * 1056.24,
    2009: 6 * 1050.63 + 6 * 1037.53,
    2008: 6 * 1037.53 + 2 * 1028 + 4 * 1005.36,
    2007: 6 * 1005.36 + 6 * 985.11,
    2006: 6 * 984.61 + 6 * 956.04,
    2005: 12 * 933,
    2004: 12 * 880,
    2003: 12 * 838,
    2002: 12 * 810,
    2001: 12 * 785,
    2000: 12 * 756, # 2000 onwards: based on 151.67 working hours

    1999: 12 * 823,
    1998: 12 * 813,
    1997: 12 * 784,
    1996: 12 * 759,
    1995: 12 * 739,
    1994: 12 * 718,
    1993: 12 * 709,
    1992: 12 * 700,
    1991: 12 * 679,
    1990: 12 * 651,

    1989: 12 * 624,
    1988: 12 * 606,
    1987: 12 * 594,
    1986: 12 * 575,
    1985: 12 * 556,
    1984: 12 * 516,
    1983: 12 * 478,
    1982: 12 * 429, # 1982 onwards: based on 169 working hours
    1981: 12 * 378,
    1980: 12 * 317,

    1979: 12 * 277,
    1978: 12 * 252,
    1977: 12 * 223,
    1976: 12 * 199,
    1975: 12 * 175,
    1974: 12 * 147,
    1973: 12 * 119,
    1972: 12 * 102,
    1971: 12 * 91,
    1970: 12 * 83,

    1969: 12 * 76,
    1968: 12 * 65,
    1967: 12 * 51,
    1966: 12 * 50,
    1965: 12 * 48,
    1964: 12 * 46,
    1963: 12 * 46,
    1962: 12 * 42,
    1961: 12 * 40,
    1960: 12 * 40,

    1959: 12 * 39,
    1958: 12 * 36,
    1957: 12 * 33,
    1956: 12 * 31,
    1955: 12 * 31,
    1954: 12 * 29,
    1953: 12 * 24,
    1952: 12 * 24,
    1951: 12 * 23,
    1950: 12 * 20, # 1950 onwards: based on 173.3 working hours
    }

# get availability of parameters
# p = openfisca_france_tax_benefit_system.parameters

# t = p.prelevements_sociaux.contributions_sociales.csg.activite.imposable.abattement[1]

# t = openfisca_france_tax_benefit_system.parameters.prelevements_sociaux.contributions_sociales.csg.abattement.sous_4pss
# t3 = t.values_list
# sd = t3[t3.__len__() - 1]
# sd.instant_str

# check coverage
start_year = min(smic_annuel_net_by_year.keys())
end_year = max(smic_annuel_net_by_year.keys())

smic_horaire_brut = dict()
for year in range(start_year, end_year+1):
    try:
        # this collects the data from openfisca-france/openfisca_france/parameters/marche_travail/salaire_minimum/smic/smic_b_horaire.yaml ?
        # if year < 1970: log.warning('SMIC before 1970 (SMIG) depends on zone. Which one to use is unclear. TBD.')
        # else : openfisca_france\parameters\marche_travail\salaire_minimum\smic\smic_b_horaire.yaml
        smic_horaire_brut[year] = openfisca_france_tax_benefit_system.get_parameters_at_instant(instant = periods.period(year).start).marche_travail.salaire_minimum.smic.smic_b_horaire
    except:
        continue

# recheck coverage for gross hourly SMIC availability
start_year = min(smic_horaire_brut.keys())
end_year = max(smic_horaire_brut.keys())

def smic_annuel_imposable_from_net(year, smic_hor_brut):
    try:
        # TODO: the formula is not 100 % flexible, I have hard-coded the 4 PSS cut-off; this could be improved in the future
        # then again, it seems not to be used at all for OFF-ERFS, just the smic_horaire_brut
        params = openfisca_france_tax_benefit_system.get_parameters_at_instant(instant = periods.period(year).start)
        smic_net = smic_annuel_net_by_year[year]
        working_hours = params.marche_travail.salaire_minimum.smic.nb_heures_travail_mensuel
        smic_brut = smic_hor_brut * working_hours * 12
        taux_csg = params.prelevements_sociaux.contributions_sociales.csg.activite.imposable.taux
        taux_crds = params.prelevements_sociaux.contributions_sociales.crds.taux
        pss = params.prelevements_sociaux.pss.plafond_securite_sociale_annuel
        abatt_sous_4pss = params.prelevements_sociaux.contributions_sociales.csg.activite.abattement.rates[0]
        use_plafond = params.prelevements_sociaux.contributions_sociales.csg.activite.abattement.rates.__len__() == 2
        if use_plafond:
            abatt_dessus_4pss = params.prelevements_sociaux.contributions_sociales.csg.activite.abattement.rates[1]

        # precise formula is kinda unnecessary, since SMIC won't ever be beyond 4 PSS. but still, for the heck of it.
        if use_plafond:
            base_csg_crds = (1 - abatt_sous_4pss) * min(smic_brut, 4 * pss) + (smic_brut > 4 * pss) * (1 - abatt_dessus_4pss) * (smic_brut - 4 * pss)
        else:
            base_csg_crds = (1 - abatt_sous_4pss) * smic_brut

        # final result, add CSG and CRDS to SMIC net
        smic_imposable = (smic_net + (taux_csg + taux_crds) * base_csg_crds)
    except:
        # not all parameters available, return NA
        smic_imposable = None

    return smic_imposable


smic_annuel_imposable_by_year = dict([
    (year, smic_annuel_imposable_from_net(year, smic_horaire_brut[year]))
    for year in range(start_year, end_year)
    ])


smic_horaire_brut_by_year = dict([
    (year, openfisca_france_tax_benefit_system.get_parameters_at_instant(instant = periods.period(year).start).marche_travail.salaire_minimum.smic.smic_b_horaire)
    for year in range(start_year, end_year)
    ])


smic_annuel_brut_by_year = dict([
    (year,
    smic_horaire_brut_by_year[year] * openfisca_france_tax_benefit_system.get_parameters_at_instant(instant = periods.period(year).start).marche_travail.salaire_minimum.smic.nb_heures_travail_mensuel * 12)
    for year in range(start_year, end_year)
    ])
