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


import logging
import numpy
import pandas


from openfisca_france_data.temporary import temporary_store_decorator
from openfisca_survey_manager.survey_collections import SurveyCollection
from openfisca_france_data import default_config_files_directory as config_files_directory


log = logging.getLogger(__name__)


@temporary_store_decorator(config_files_directory = config_files_directory, file_name = 'indirect_taxation_tmp')
def build_homogeneisation_caracteristiques_sociales(temporary_store = None, year = None):
    """HOMOGENEISATION DES CARACTERISTIQUES SOCIALES DES MENAGES """

    assert temporary_store is not None
    assert year is not None
    # Load data
    bdf_survey_collection = SurveyCollection.load(
        collection = 'budget_des_familles', config_files_directory = config_files_directory)
    survey = bdf_survey_collection.get_survey('budget_des_familles_{}'.format(year))
    # ******************************************************************************************************************
    # * Etape n° 0-3 : HOMOGENEISATION DES CARACTERISTIQUES SOCIALES DES MENAGES
    # ******************************************************************************************************************
    # ******************************************************************************************************************

    if year == 1995:
        kept_variables = ['exdep', 'exrev', 'mena', 'v', 'ponderrd', 'nbpers', 'nbenf', 'typmen1', 'cohabpr', 'sexepr',
            'agepr', 'agecj', 'matripr', 'occuppr', 'occupcj', 'nbact', 'sitlog', 'stalog', 'mena', 'nm14a', 'typmen1']
        menage = survey.get_values(
            table = "socioscm",
            variables = kept_variables,
            )
        # cette étape de ne garder que les données dont on est sûr de la qualité et de la véracité
        # exdep = 1 si les données sont bien remplies pour les dépenses du ménage
        # exrev = 1 si les données sont bien remplies pour les revenus du ménage
        menage = menage[(menage.exdep == 1) & (menage.exrev == 1)]
        menage.rename(
            columns = {
                'v': 'vag',
                'mena': 'ident_men',
                'ponderrd': 'pondmen',
                'nbpers': 'npers',
                'nm14a': 'nenfants',
                'nbenf': 'nenfhors',
                'nbact': 'nactifs',
                'cohabpr': 'couplepr',
                'matripr': 'etamatri',
                'typmen1': 'typmen'
                },
            inplace = True,
            )
        # la variable vag est utilisée dans les modèles QAIDS et AIDS afin de faire variezr le temps et d'attibuer
        # le bon prix mensuel
        menage.agecj = menage.agecj.fillna(0)
        menage.nenfhors = menage.nenfhors.fillna(0)
        menage.vag = menage.vag.astype('int')

        menage['nadultes'] = menage['npers'] - menage['nenfants']
        menage['ocde10'] = 1 + 0.5 * numpy.maximum(0, menage['nadultes'] - 1) + 0.3 * menage['nenfants']

        # harmonisation des types de ménage sur la nomenclature 2010
        menage['typmen_'] = menage['typmen']
        menage.typmen[menage.typmen_ == 1] = 1
        menage.typmen[menage.typmen_ == 2] = 3
        menage.typmen[menage.typmen_ == 3] = 4
        menage.typmen[menage.typmen_ == 4] = 4
        menage.typmen[menage.typmen_ == 5] = 4
        menage.typmen[menage.typmen_ == 6] = 2
        menage.typmen[menage.typmen_ == 7] = 5
        del menage['typmen_']

        var_to_ints = ['couplepr', 'etamatri']
        for var_to_int in var_to_ints:
            menage[var_to_int] = menage[var_to_int].astype(int)

        #  Methode :
        #  1. on clean les variables (i.e. renames + changement de format (astype(int)))
        #  2. Reformatage des variables (réattribution des catégories pour quelles soient identiques
        #     pour les différentes années)

        menage["situacj"] = 0
        menage.situacj[menage.occupcj == 1] = 1
        menage.situacj[menage.occupcj == 3] = 3
        menage.situacj[menage.occupcj == 2] = 4
        menage.situacj[menage.occupcj == 5] = 5
        menage.situacj[menage.occupcj == 6] = 5
        menage.situacj[menage.occupcj == 7] = 6
        menage.situacj[menage.occupcj == 8] = 7
        menage.situacj[menage.occupcj == 4] = 8

        menage["situapr"] = 0
        menage.situapr[menage.occuppr == 1] = 1
        menage.situapr[menage.occuppr == 3] = 3
        menage.situapr[menage.occuppr == 2] = 4
        menage.situapr[menage.occuppr == 5] = 5
        menage.situapr[menage.occuppr == 6] = 5
        menage.situapr[menage.occuppr == 7] = 6
        menage.situapr[menage.occuppr == 8] = 7
        menage.situapr[menage.occuppr == 4] = 8

        menage["typlog"] = 0
        menage.typlog[menage.sitlog == 1] = 1
        menage.typlog[menage.sitlog != 1] = 2

        menage['stalog'] = menage['stalog'].astype(int)

        individus = survey.get_values(
            table = "individu",
            )
        variables = ['mena', 'v']
        individus.rename(
            columns = {'mena': 'identmen'},
            inplace = True,
            )
        menage.set_index('ident_men', inplace = True)

    if year == 2000:
        menage = survey.get_values(
            table = "menage",
            variables = [
                'ident', 'pondmen', 'nbact', 'nbenf1', 'nbpers', 'ocde10', 'sitlog', 'stalog', 'strate',
                'typmen1', 'zeat', 'stalog', 'vag', 'sexepr', 'sexecj', 'agecj', 'napr', 'nacj', 'cs2pr',
                'cs2cj', 'diegpr', 'dieppr', 'diespr', 'diegcj', 'diepcj', 'diescj', 'hod_nb', 'cohabpr',
                'occupapr', 'occupacj', 'occupbpr', 'occupbcj', 'occupcpr', 'occupccj', 'typmen1'
                ]
            )
        menage.rename(
            columns = {
                'ident': 'ident_men',
                'rev81': '0421',
                'ident': 'ident_men',
                'nbact': 'nactifs',
                'nbenf1': 'nenfants',
                'nbpers': 'npers',
                'hod_nb': 'nenfhors',
                'cohabpr': 'couplepr',
                'typmen1': 'typmen'
                },
            inplace = True,
            )
        menage.ocde10 = menage.ocde10 / 10
        # on met un numéro à chaque vague pour pouvoir faire un meilleur suivi des évolutions temporelles
        # pour le modèle de demande
        menage.agecj = menage.agecj.fillna(0)

        assert menage.notnull().all().all(), 'The following variables contains NaN values: {}'.format(
            list(menage.isnull().any()[menage.isnull().any()].index))

        menage['vag_'] = menage['vag']
        menage.vag.loc[menage.vag_ == 1] = 9
        menage.vag.loc[menage.vag_ == 2] = 10
        menage.vag.loc[menage.vag_ == 3] = 11
        menage.vag.loc[menage.vag_ == 4] = 12
        menage.vag.loc[menage.vag_ == 5] = 13
        menage.vag.loc[menage.vag_ == 6] = 14
        menage.vag.loc[menage.vag_ == 7] = 15
        menage.vag.loc[menage.vag_ == 8] = 16
        del menage['vag_']
        # harmonisation des types de ménage sur la nomenclature 2010
        menage['typmen_'] = menage['typmen']
        menage.typmen.loc[menage.typmen_ == 1] = 1
        menage.typmen.loc[menage.typmen_ == 2] = 3
        menage.typmen.loc[menage.typmen_ == 3] = 4
        menage.typmen.loc[menage.typmen_ == 4] = 4
        menage.typmen.loc[menage.typmen_ == 5] = 4
        menage.typmen.loc[menage.typmen_ == 6] = 2
        menage.typmen.loc[menage.typmen_ == 7] = 5
        del menage['typmen_']

        menage.couplepr = menage.couplepr.astype('int')
        menage["nadultes"] = menage['npers'] - menage['nenfants']

        menage.typmen = menage.typmen.astype('int')

        menage["situacj"] = 0
        menage.situacj.loc[menage.occupacj == 1] = 1
        menage.situacj.loc[menage.occupccj == 3] = 3
        menage.situacj.loc[menage.occupccj == 2] = 4
        menage.situacj.loc[menage.occupccj == 5] = 5
        menage.situacj.loc[menage.occupccj == 6] = 5
        menage.situacj.loc[menage.occupccj == 7] = 6
        menage.situacj.loc[menage.occupccj == 8] = 7
        menage.situacj.loc[menage.occupccj == 4] = 8

        menage["situapr"] = 0
        menage.situapr.loc[menage.occupapr == 1] = 1
        menage.situapr.loc[menage.occupapr == 3] = 3
        menage.situapr.loc[menage.occupapr == 2] = 4
        menage.situapr.loc[menage.occupapr == 5] = 5
        menage.situapr.loc[menage.occupapr == 6] = 5
        menage.situapr.loc[menage.occupapr == 7] = 6
        menage.situapr.loc[menage.occupapr == 8] = 7
        menage.situapr.loc[menage.occupapr == 4] = 8

        menage["natiocj"] = 0
        menage["natiopr"] = 0
        menage.natiocj.loc[menage.nacj == 1] = 1
        menage.natiocj.loc[menage.nacj == 2] = 1
        menage.natiocj.loc[menage.nacj == 3] = 2
        menage.natiopr.loc[menage.napr == 1] = 1
        menage.natiopr.loc[menage.napr == 2] = 1
        menage.natiopr.loc[menage.napr == 3] = 2

        menage["typlog"] = 0
        menage.typlog.loc[menage.sitlog == 1] = 1
        menage.typlog.loc[menage.sitlog != 1] = 2

        menage.set_index('ident_men', inplace = True)

        individus = survey.get_values(
            table = "individus",
            variables = ['ident', 'matri', 'lien', 'anais']
            )

        individus = individus.loc[individus.lien == 1].copy()
        individus.rename(
            columns = {'ident': 'ident_men', 'matri': 'etamatri'},
            inplace = True,
            )
        variables_to_destring = ['anais']
        for variable_to_destring in variables_to_destring:
            individus[variable_to_destring] = individus[variable_to_destring].astype('int').copy()
        individus['agepr'] = year - individus.anais
        individus.set_index('ident_men', inplace = True)

        assert menage.notnull().all().all(), 'The following variables contains NaN values: {}'.format(
            list(menage.isnull().any()[menage.isnull().any()].index))

        menage = menage.merge(individus, left_index = True, right_index = True)

    if year == 2005:
        menage = survey.get_values(table = "menage")
        # données socio-démographiques
        socio_demo_variables = ['agpr', 'agcj', 'couplepr', 'decuc', 'ident_men', 'nactifs', 'nenfants', 'nenfhors',
            'npers', 'ocde10', 'pondmen', 'sexecj', 'sexepr', 'typmen5', 'vag', 'zeat', 'cs24pr']
        socio_demo_variables += [column for column in menage.columns if column.startswith('dip14')]
        socio_demo_variables += [column for column in menage.columns if column.startswith('natio7')]
        # activité professionnelle
        activite_prof_variables = ['situacj', 'situapr']
        activite_prof_variables += [column for column in menage.columns if column.startswith('cs42')]
        # logement
        logement_variables = ['htl', 'strate']
        menage = menage[socio_demo_variables + activite_prof_variables + logement_variables]
        menage.rename(
            columns = {
                # "agpr": "agepr",
                "agcj": "agecj",
                "typmen5": "typmen",
                "cs24pr": "cs_pr"
                },
            inplace = True,
            )
        del menage['agpr']
        menage['nadultes'] = menage.npers - menage.nenfants
        for person in ['pr', 'cj']:
            menage['natio' + person] = (menage['natio7' + person] > 2)  # TODO: changer de convention ?
            del menage['natio7' + person]

        menage.agecj = menage.agecj.fillna(0)
        menage.nenfhors = menage.nenfhors.fillna(0)
        var_to_ints = ['ocde10', 'decuc', 'nactifs', 'nenfants', 'npers', 'pondmen', 'nadultes']
        assert menage.notnull().all().all(), 'The following variables contains NaN values: {}'.format(
            list(menage.isnull().any()[menage.isnull().any()].index))

        menage.couplepr = menage.couplepr > 2  # TODO: changer de convention ?
        menage.ocde10 = menage.ocde10 / 10
        menage.set_index('ident_men', inplace = True)
        # on met un numéro à chaque vague pour pouvoir faire un meilleur suivi des évolutions temporelles
        # pour le modèle de demande
        menage['vag_'] = menage['vag']
        menage.vag.loc[menage.vag_ == 1] = 17
        menage.vag.loc[menage.vag_ == 2] = 18
        menage.vag.loc[menage.vag_ == 3] = 19
        menage.vag.loc[menage.vag_ == 4] = 20
        menage.vag.loc[menage.vag_ == 5] = 21
        menage.vag.loc[menage.vag_ == 6] = 22
        del menage['vag_']

        stalog = survey.get_values(table = "depmen", variables = ['ident_men', 'stalog'])
        stalog['stalog'] = stalog.stalog.astype('int').copy()
        stalog['new_stalog'] = 0
        stalog.loc[stalog.stalog == 2, 'new_stalog'] = 1
        stalog.loc[stalog.stalog == 1, 'new_stalog'] = 2
        stalog.loc[stalog.stalog == 4, 'new_stalog'] = 3
        stalog.loc[stalog.stalog == 5, 'new_stalog'] = 4
        stalog.loc[stalog.stalog.isin([3, 6]), 'new_stalog'] = 5
        stalog.stalog = stalog.new_stalog.copy()
        del stalog['new_stalog']

        assert stalog.stalog.isin(range(1, 6)).all()
        stalog.set_index('ident_men', inplace = True)
        menage = menage.merge(stalog, left_index = True, right_index = True)
        menage['typlog'] = 2
        menage.loc[menage.htl.isin(['1', '5']), 'typlog'] = 1
        assert menage.typlog.isin([1, 2]).all()
        del menage['htl']

        individus = survey.get_values(table = 'individu')
        # Il y a un problème sur l'année de naissance,
        # donc on le recalcule avec l'année de naissance et la vague d'enquête
        individus['agepr'] = year - individus.anais
        individus.loc[individus.vag == 6, ['agepr']] = year + 1 - individus.anais
        individus = individus[individus.lienpref == 00].copy()
        kept_variables = ['ident_men', 'etamatri', 'agepr']
        individus = individus[kept_variables].copy()
        individus.etamatri.loc[individus.etamatri == 0] = 1
        individus['etamatri'] = individus['etamatri'].astype('int')  # MBJ TODO: define as a catagory ?
        individus.set_index('ident_men', inplace = True)
        menage = menage.merge(individus, left_index = True, right_index = True)

        individus = survey.get_values(
            table = 'individu',
            variables = ['ident_men', 'ident_ind', 'age', 'anais', 'vag', 'lienpref'],
            )
        # Il y a un problème sur l'année de naissance,
        # donc on le recalcule avec l'année de naissance et la vague d'enquête
        individus['age'] = year - individus.anais
        individus.loc[individus.vag == 6, ['age']] = year + 1 - individus.anais
        # Garder toutes les personnes du ménage qui ne sont pas la personne de référence et le conjoint
        individus = individus[(individus.lienpref != 00) & (individus.lienpref != 01)].copy()
        individus.sort(columns = ['ident_men', 'ident_ind'], inplace = True)

        # Inspired by http://stackoverflow.com/questions/17228215/enumerate-each-row-for-each-group-in-a-dataframe
        def add_col_numero(data_frame):
            data_frame['numero'] = numpy.arange(len(data_frame)) + 3
            return data_frame

        individus = individus.groupby(by = 'ident_men').apply(add_col_numero)
        pivoted = individus.pivot(index = 'ident_men', columns = "numero", values = 'age')
        pivoted.columns = ["age{}".format(column) for column in pivoted.columns]
        menage = menage.merge(pivoted, left_index = True, right_index = True, how = 'outer')

        individus = survey.get_values(
            table = 'individu',
            variables = ['ident_men', 'ident_ind', 'agfinetu', 'lienpref'],
            )
        individus.set_index('ident_men', inplace = True)
        pr = individus.loc[individus.lienpref == 00, 'agfinetu'].copy()
        conjoint = individus.loc[individus.lienpref == 01, 'agfinetu'].copy()
        conjoint.name = 'agfinetu_cj'
        agfinetu_merged = pandas.concat([pr, conjoint], axis = 1)
        menage = menage.merge(agfinetu_merged, left_index = True, right_index = True)
        temporary_store['donnes_socio_demog_{}'.format(year)] = menage

        # label var agepr "Age de la personne de référence au 31/12/${yearrawdata}"
        # label var agecj "Age du conjoint de la PR au 31/12/${yearrawdata}"
        # label var sexepr "Sexe de la personne de référence"
        # label var sexecj "Sexe du conjoint de la PR"
        # label var cs42pr "Catégorie socio-professionnelle de la PR"
        # label var cs42cj "Catégorie socio-professionnelle du conjoint de la PR"
        # label var ocde10 "Nombre d'unités de consommation (échelle OCDE)"
        # label var ident_men "Identifiant du ménage"
        # label var pondmen "Ponderation du ménage"
        # label var npers "Nombre total de personnes dans le ménage"
        # label var nadultes "Nombre d'adultes dans le ménage"
        # label var nenfants "Nombre d'enfants dans le ménage"
        # label var nenfhors "Nombre d'enfants vivant hors domicile"
        # label var nactifs  "Nombre d'actifs dans le ménage"
        # label var couplepr "Vie en couple de la personne de référence"
        # label define typmen5 1 "Personne seule" 2 "Famille monoparentale" 3 "Couple sans enfant" 4 "Couple avec enfants" 5 "Autre type de ménage (complexe)"
        # label values typmen5 typmen5
        # label var typmen5 "Type de ménage (5 modalités)"
        # label var etamatri "Situation matrimoniale de la personne de référence"
        # label define matripr 1 "Célibataire" 2 "Marié(e)" 3 "Veuf(ve)" 4 "Divorcé(e)"
        # label values etamatri matripr
        # label define occupation 1 "Occupe un emploi" ///
        # 2 "Apprenti" ///
        # 3 "Etudiant, élève, en formation"  ///
        # 4 "Chômeur (inscrit ou non à l'ANPE)" ///
        # 5 "Retraité, préretraité ou retiré des affaires" ///
        # 6 "Au foyer"  ///
        # 7 "Autre situation (handicapé)"  ///
        # 8 "Militaire du contingent"
        # label values situapr occupation
        # label values situacj occupation
        # label var situapr "Situation d'activité de la personne de référence"
        # label var situacj "Situation d'activité du conjoint de la PR"
        # label define diplome 10 "Diplôme de 3ème cycle universitaire, doctorat" ///
        # 12 "Diplôme d'ingénieur, grande école" ///
        # 20 "Diplôme de 2nd cycle universitaire" ///
        # 30 "Diplôme de 1er cycle universitaire" ///
        # 31 "BTS, DUT ou équivalent" ///
        # 33 "Diplôme des professions sociales et de la santé niveau Bac +2" ///
        # 41 "Baccalauréat général, brevet supérieur, capacité en droit" ///
        # 42 "Baccalauréat technologique" ///
        # 43 "Baccalauréat professionnel" ///
        # 44 "Brevet professionnel ou de technicien" ///
        # 50 "CAP, BEP ou diplôme de même niveau" ///
        # 60 "Brevet des collèges, BEPC" ///
        # 70 "Certificat d'études primaires" ///
        # 71 "Aucun diplôme"
        # label values dip14pr diplome
        # label values dip14cj diplome
        # label var dip14pr "Diplôme le plus élevé de la PR"
        # label var dip14cj "Diplôme le plus élevé du conjoint de la PR"
        # label define nationalite 1 "Français, par naissance ou naturalisation" 2 "Etranger"
        # label values natiopr nationalite
        # label values natiocj nationalite
        # label var natiopr "Nationalité de la personne de référence"
        # label var natiocj "Nationalité du conjoint de la PR"
        # label define logement 1 "Maison" 2 "Appartement"
        # label values typlog logement
        # label var typlog "Type de logement"
        # label define statutlogement 1 "Propriétaire ou copropriétaire" ///
        # 2 "Accédant à la propriété (rembourse un prêt)" ///
        # 3 "Locataire" ///
        # 4 "Sous-locataire" ///
        # 5 "Logé gratuitement"
        # label values stalog statutlogement
        # label var stalog "Statut d'occupation du logement"
        # label define viecouple 1 "Vit en couple" 2 "Ne vit pas en couple"
        # label values couplepr viecouple
        #
        # /* Recodage des CSP en 12 et 8 postes à partir de classification de l'INSEE (2003, PCS niveaux 1 et 2) */
        # gen cs24pr=00
        # replace cs24pr=10 if cs42pr=="11"
        # replace cs24pr=10 if cs42pr=="12"
        # replace cs24pr=10 if cs42pr=="13"
        # replace cs24pr=21 if cs42pr=="21"
        # replace cs24pr=22 if cs42pr=="22"
        # replace cs24pr=23 if cs42pr=="23"
        # replace cs24pr=31 if cs42pr=="31"
        # replace cs24pr=32 if cs42pr=="33"
        # replace cs24pr=32 if cs42pr=="34"
        # replace cs24pr=32 if cs42pr=="35"
        # replace cs24pr=36 if cs42pr=="37"
        # replace cs24pr=36 if cs42pr=="38"
        # replace cs24pr=41 if cs42pr=="42"
        # replace cs24pr=41 if cs42pr=="43"
        # replace cs24pr=41 if cs42pr=="44"
        # replace cs24pr=41 if cs42pr=="45"
        # replace cs24pr=46 if cs42pr=="46"
        # replace cs24pr=47 if cs42pr=="47"
        # replace cs24pr=48 if cs42pr=="48"
        # replace cs24pr=51 if cs42pr=="52"
        # replace cs24pr=51 if cs42pr=="53"
        # replace cs24pr=54 if cs42pr=="54"
        # replace cs24pr=55 if cs42pr=="55"
        # replace cs24pr=56 if cs42pr=="56"
        # replace cs24pr=61 if cs42pr=="62"
        # replace cs24pr=61 if cs42pr=="63"
        # replace cs24pr=61 if cs42pr=="64"
        # replace cs24pr=61 if cs42pr=="65"
        # replace cs24pr=66 if cs42pr=="67"
        # replace cs24pr=66 if cs42pr=="68"
        # replace cs24pr=69 if cs42pr=="69"
        # replace cs24pr=71 if cs42pr=="71"
        # replace cs24pr=72 if cs42pr=="72"
        # replace cs24pr=73 if cs42pr=="74"
        # replace cs24pr=73 if cs42pr=="75"
        # replace cs24pr=76 if cs42pr=="77"
        # replace cs24pr=76 if cs42pr=="78"
        # replace cs24pr=81 if cs42pr=="81"
        # replace cs24pr=82 if cs42pr=="83"
        # replace cs24pr=82 if cs42pr=="84"
        # replace cs24pr=82 if cs42pr=="85"
        # replace cs24pr=82 if cs42pr=="86"
        # replace cs24pr=82 if cs42pr=="**"
        # replace cs24pr=82 if cs42pr=="00"
        #

        menage['cs24pr'] = 0
        csp42s_by_csp24 = {
            10: ["11", "12", "13"],
            21: ["21"],
            22: ["22"],
            23: ["23"],
            31: ["31"],
            32: ["32", "33", "34", "35"],
            36: ["37", "38"],
            41: ["42", "43", "44", "45"],
            46: ["46"],
            47: ["47"],
            48: ["48"],
            51: ["52", "53"],
            54: ["54"],
            55: ["55"],
            56: ["56"],
            61: ["62", "63", "64", "65"],
            66: ["67", "68"],
            69: ["69"],
            71: ["71"],
            72: ["72"],
            73: ["74", "75"],
            76: ["77", "78"],
            81: ["81"],
            82: ["83", "84", "85", "86", "**", "00"],
            }
        for csp24, csp42s in csp42s_by_csp24.items():
            menage.loc[menage.cs42pr.isin(csp42s), 'cs24pr'] = csp24
        assert menage.cs24pr.isin(csp42s_by_csp24.keys()).all()

        menage['cs8pr'] = numpy.floor(menage.cs24pr / 10)
        assert menage.cs8pr.isin(range(1, 9)).all()

        variables = [
            'pondmen', 'npers', 'nenfants', 'nenfhors', 'nadultes', 'nactifs', 'ocde10', 'typmen',
            'sexepr', 'agepr', 'etamatri', 'couplepr', 'situapr', 'dip14pr', 'cs42pr', 'cs24pr', 'cs8pr', 'natiopr',
            'sexecj', 'agecj', 'situacj', 'dip14cj', 'cs42cj', 'natiocj', 'typlog', 'stalog'
            ] + ["age{}".format(age) for age in range(3, 14)]

        for variable in variables:
            assert variable in menage.columns, "{} is not a column of menage data frame".format(variable)

    if year == 2011:
        try:
            menage = survey.get_values(
                table = "MENAGE",
                variables = [
                    'ident_me', 'pondmen', 'npers', 'nenfants', 'nactifs', 'sexepr', 'sexecj', 'dip14cj', 'dip14pr',
                    'coeffuc', 'decuc1', 'typmen5'
                    ]
                ).sort(columns = ['ident_me'])
        except:
            menage = survey.get_values(
                table = "menage",
                variables = [
                    'ident_me', 'pondmen', 'npers', 'nenfants', 'nactifs', 'sexepr', 'sexecj', 'dip14cj', 'dip14pr',
                    'coeffuc', 'decuc1', 'typmen5'
                    ]
                ).sort(columns = ['ident_me'])
        menage.rename(
            columns = {
                'ident_me': 'ident_men',
                'coeffuc': 'ocde10',
                'typmen5': 'typmen',
                'decuc1': 'decuc'
                },
            inplace = True,
            )
        # ajout de la variable vag
        try:
            vague = survey.get_values(table = "DEPMEN")
        except:
            vague = survey.get_values(table = "depmen")
        kept_variables = ['vag']
        vague = vague[kept_variables]
        menage = menage.merge(vague, left_index = True, right_index = True)
        # on met un numéro à chaque vague pour pouvoir faire un meilleur suivi des évolutions temporelles
        # pour le modèle de demande
        menage['vag_'] = menage['vag']
        menage.vag.loc[menage.vag_ == 1] = 23
        menage.vag.loc[menage.vag_ == 2] = 24
        menage.vag.loc[menage.vag_ == 3] = 25
        menage.vag.loc[menage.vag_ == 4] = 26
        menage.vag.loc[menage.vag_ == 5] = 27
        menage.vag.loc[menage.vag_ == 6] = 28
        del menage['vag_']

    if year == 2011:
        menage.set_index('ident_men', inplace = True)
    temporary_store['donnes_socio_demog_{}'.format(year)] = menage


if __name__ == '__main__':
    import sys
    import time
    logging.basicConfig(level = logging.INFO, stream = sys.stdout)
    deb = time.clock()
    year = 2011
    build_homogeneisation_caracteristiques_sociales(year = year)

    log.info("step_0_3_homogeneisation_caracteristiques_sociales {}".format(time.clock() - deb))
