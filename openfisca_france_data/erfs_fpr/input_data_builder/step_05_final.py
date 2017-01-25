# -*- coding: utf-8 -*-


import gc
import logging
import pandas as pd


from openfisca_france_data.utils import (
    id_formatter, print_id, normalizes_roles_in_entity,
    )
from openfisca_survey_manager.temporary import temporary_store_decorator

log = logging.getLogger(__name__)


@temporary_store_decorator(file_name = 'erfs_fpr')
def create_input_data_frame(temporary_store = None, year = None):
    assert temporary_store is not None
    assert year is not None

    log.info('step_05_create_input_data_frame: Etape finale ')
    individus = temporary_store['individus_{}'.format(year)]
    menages = temporary_store['menages_{}'.format(year)]
    variables = [
        'activite',
        'age_en_mois',
        'age',
        'categorie_salarie',
        'chomage_brut',
        'chomage_imposable',
        'contrat_de_travail',
        'effectif_entreprise',
        'heures_remunerees_volume',
        'idfam',
        'idfoy',
        'idmen',
        'noindiv',
        'pensions_alimentaires_percues',
        'quifam',
        'quifoy',
        'quimen',
        'rag',
        'retraite_brute',
        'retraite_imposable',
        'ric',
        'rnc',
        'statut_marital',
        'salaire_imposable',
        'taux_csg_remplacement',
        ]

    individus = create_ids_and_roles(individus)[variables].copy()
    gc.collect()
    #
    menages = extract_menages_variables(menages)
    individus = create_collectives_foyer_variables(individus, menages)
    #
    data_frame = individus.merge(
        menages[
            ['idmen', 'loyer', 'statut_occupation_logement', 'taxe_habitation', 'wprm', 'zone_apl']
            ],
        on = 'idmen'
        )
    del individus, menages
    #
    data_frame = format_ids_and_roles(data_frame)
    assert 'f4ba' in data_frame.columns
    temporary_store['input_{}'.format(year)] = data_frame
    return data_frame


def create_collectives_foyer_variables(individus, menages):
    menages_revenus_fonciers = menages[['idmen', 'rev_fonciers_bruts']].copy()
    idmens = menages_revenus_fonciers.query('(rev_fonciers_bruts > 0)')['idmen'].tolist()
    menages_multi_foyers = (individus
        .query('idmen in @idmens')[['idmen', 'idfoy', 'age']]  # On ne garde que les ménages avec des revenus fonciers
        .groupby('idmen')
        .filter(lambda x: x.idfoy.nunique() > 1)  # On ne garde que les ménages avec plus d'un foyer fiscal
        .sort_values(['idmen', 'age'], ascending = False)  # On garde les ages élevés en premier
        # .drop_duplicates(['idmen', 'idfoy'])  # On garde les individus les plus agés d'un même foyer fiscal: inutile
        .drop_duplicates(['idmen'])  # On garde le foyer fiscal du plus agés du ménage
        .drop('age', axis = 1)
        .reset_index(drop = True)
        )
    menages_simple_foyer = (individus
        .query('idmen in @idmens')[['idmen', 'idfoy']]  # On ne garde que les ménages avec des revenus fonciers
        .groupby('idmen')
        .filter(lambda x: x.idfoy.nunique() == 1)  # On ne garde que les ménages avec plus d'un foyer fiscal
        .drop_duplicates(['idmen', 'idfoy'])
        .reset_index(drop = True)
        )
    assert set(menages_multi_foyers.idmen.tolist() + menages_simple_foyer.idmen.tolist()) == set(idmens)
    menages_foyers_correspondance = pd.concat([menages_multi_foyers, menages_simple_foyer], ignore_index = True)
    del menages_multi_foyers, menages_simple_foyer
    foyers_revenus_fonciers = menages_foyers_correspondance.merge(
        menages_revenus_fonciers,
        how = 'inner',
        on = 'idmen'
        )
    assert len(foyers_revenus_fonciers) == len(idmens)
    del menages_foyers_correspondance, menages_revenus_fonciers
    foyers_revenus_fonciers['quifoy'] = 0
    foyers_revenus_fonciers.drop('idmen', axis = 1, inplace = True)
    assert set(foyers_revenus_fonciers.columns) == set(['idfoy', 'rev_fonciers_bruts', 'quifoy'])
    individus = individus.merge(foyers_revenus_fonciers, how = 'outer', on = ['idfoy', 'quifoy'])
    assert set(idmens) == set(individus .query('(rev_fonciers_bruts > 0)')['idmen'].tolist())
    individus.rename(columns = {'rev_fonciers_bruts': 'f4ba'}, inplace = True)
    return individus


def create_ids_and_roles(individus):
    old_by_new_variables = {
        'ident': 'idmen',
        }
    individus.rename(
        columns = old_by_new_variables,
        inplace = True,
        )
    individus['quimen'] = 9
    individus.loc[individus.lpr == 1, 'quimen'] = 0
    individus.loc[individus.lpr == 2, 'quimen'] = 1
    individus['idfoy'] = individus['idfam'].copy()
    individus['quifoy'] = individus['quifam'].copy()
    return individus


def format_ids_and_roles(data_frame):
    for entity_id in ['idmen', 'idfoy', 'idfam']:
        log.info('Reformat ids: {}'.format(entity_id))
        data_frame = id_formatter(data_frame, entity_id)
    data_frame.reset_index(drop = True, inplace = True)
    data_frame = normalizes_roles_in_entity(data_frame, 'foy')
    data_frame = normalizes_roles_in_entity(data_frame, 'men')
    print_id(data_frame)
    return data_frame


@temporary_store_decorator(file_name = 'erfs_fpr')
def extract_menages_variables_from_store(temporary_store = None, year = None):
    assert temporary_store is not None
    assert year is not None
    menages = temporary_store['menages_{}'.format(year)]
    return extract_menages_variables(menages)


def extract_menages_variables(menages):
    variables = ['ident', 'wprm', 'taxe_habitation', 'rev_fonciers_bruts']
    external_variables = ['loyer', 'zone_apl', 'statut_occupation_logement']
    for external_variable in external_variables:
        if external_variable in menages.columns:
            log.info("Found {} in menages table: we keep it".format(external_variable))
            variables.append(external_variable)
    menages = menages[variables].copy()
    menages.taxe_habitation = - menages.taxe_habitation  # taxes should be negative
    menages.rename(columns = dict(ident = 'idmen'), inplace = True)
    return menages


if __name__ == '__main__':
    import sys
    logging.basicConfig(level = logging.INFO, stream = sys.stdout)
    year = 2012
    data_frame = create_input_data_frame(year = year)

# TODO
# Variables revenus collectifs
#   rev_etranger  -> etr
#   rev_financier_prelev_lib_imputes revenus financiers(prélévement libératoire) et imputés
#   rev_fonciers_bruts Revenus fonciers avant déduction de la CSG -> f4ba  DONE (sur plus agé déclarant du ménage)
#   rev_valeurs_mobilieres_bruts
# Mais aussi:
#   pens_alim_versee
#   Pensions alimentaires versées à des enfants majeurs:
#     décision de justice définitive avant 2006 6GI 6GJ (1er et 2e enfant)
#   Autres pensions alimentaires versées à des enfants majeurs:
#     6EL 6EM
#   Autres pensions alimentaires versées (enfants mineurs, ascendants,…):
#     décision de justice définitive avant 2006  6GP
#   Autres pensions alimentaires versées (enfants mineurs, ascendants,…):
#     6GU
#  th -> taxe_habitation DONE
