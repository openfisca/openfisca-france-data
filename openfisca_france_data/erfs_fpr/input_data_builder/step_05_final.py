import gc
import logging
import pandas

from openfisca_france_data.utils import (
    id_formatter, print_id, normalizes_roles_in_entity,
    )
from openfisca_survey_manager.temporary import temporary_store_decorator  # type: ignore
from openfisca_survey_manager.input_dataframe_generator import set_table_in_survey  # type: ignore

log = logging.getLogger(__name__)


@temporary_store_decorator(file_name = 'erfs_fpr')
def create_input_data_frame(temporary_store = None, year = None, export_flattened_df_filepath = None):
    assert temporary_store is not None
    assert year is not None

    log.info('step_05_create_input_data_frame: Etape finale ')
    individus = temporary_store['individus_{}'.format(year)]
    menages = temporary_store['menages_{}'.format(year)]

    variables = [
        'activite',
        'age',
        'categorie_salarie',
        'chomage_brut',
        'contrat_de_travail',
        'date_naissance',
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
        'ric',
        'rnc',
        'statut_marital',
        # 'salaire_imposable',
        'salaire_de_base',
        'taux_csg_remplacement',
        ]

    # TODO: fix this simplistic inference
    individus.rename(columns = {
        'ric_net': 'ric',
        'rag_net': 'rag',
        'rnc_net': 'rnc',
        },
        inplace = True
        )

    individus = create_ids_and_roles(individus)
    individus = individus[variables].copy()
    menages = menages.loc[(menages.ident).isin(set(individus.idmen))].copy()
    gc.collect()

    # This looks like it could have a sizeable impact
    missingvariablesmenages = ["taxe_habitation"]
    for k in missingvariablesmenages:
        menages[k] = 0

    # Again artificially putting missing variables in their default state
    menages["loyer"] = 0
    menages["zone_apl"] = 2
    menages["statut_occupation_logement"] = 0

    menages = extract_menages_variables(menages)
    individus = create_collectives_foyer_variables(individus, menages)
    idmens = individus.idmen.unique()
    menages = menages.loc[
        menages.idmen.isin(idmens),
        [
            'idmen',
            'loyer',
            'statut_occupation_logement',
            'taxe_habitation',
            'wprm',
            'zone_apl',
            ]
        ].copy()

    set_table_in_survey(
        menages,
        entity = "menage",
        period = year,
        collection = "openfisca_erfs_fpr",
        survey_name = 'input',
        )

    individus = format_ids_and_roles(individus)
    if export_flattened_df_filepath:
        supermerge = individus.merge(
            menages,
            right_index = True,
            left_on = "idmen",
            suffixes = ("", "_x"))
        supermerge.to_hdf(export_flattened_df_filepath, key = "input")
    # Enters the individual table into the openfisca_erfs_fpr collection
    set_table_in_survey(
        individus,
        entity = "individu",
        period = year,
        collection = "openfisca_erfs_fpr",
        survey_name = 'input',
        )


    # assert 'f4ba' in data_frame.columns


def create_collectives_foyer_variables(individus, menages):
    menages_revenus_fonciers = menages[['idmen', 'rev_fonciers_bruts']].copy()
    idmens = menages_revenus_fonciers.query('(rev_fonciers_bruts > 0)')['idmen'].tolist()
    # I'm not proud
    # TODO: WDF ?!
    idmens = [_ for _ in idmens if _ != 14024264]
    idmens = [_ for _ in idmens if _ != 15010850]
    idmens = [_ for _ in idmens if _ != 17000919]
    idmens = [_ for _ in idmens if _ != 18046072]
    idmens = [_ for _ in idmens if _ != 8019138]
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
    menages_foyers_correspondance = pandas.concat([menages_multi_foyers, menages_simple_foyer], ignore_index = True)
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
    individus.rename(
        columns = {'ident': 'idmen'},
        inplace = True,
        )
    individus['quimen'] = 2

    # checking that only one of "lpr" "lprm" exists, otherwise my
    # great hack wont work
    assert(("lpr" in individus.columns) or ("lprm" in individus.columns))

    lpr = "lpr" if "lpr" in individus.columns else "lprm"
    individus.loc[individus[lpr] == 1, 'quimen'] = 0
    individus.loc[individus[lpr] == 2, 'quimen'] = 1
    individus['idfoy'] = individus['idfam'].copy()
    individus['quifoy'] = individus['quifam'].copy()
    return individus


def format_ids_and_roles(data_frame):
    for entity_id in ['idmen', 'idfoy', 'idfam']:
        log.info('Reformat ids: {}'.format(entity_id))
        data_frame = id_formatter(data_frame, entity_id)
    data_frame.reset_index(drop = True, inplace = True)
    normalizes_roles_in_entity(data_frame, 'idfoy', 'quifoy')
    normalizes_roles_in_entity(data_frame, 'idmen', 'quimen')
    normalizes_roles_in_entity(data_frame, 'idfam', 'quifam')
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
    #TODO: 2007-2010 ont la variable rev_fonciers et non pas rev_fonciers_bruts. Est-ce la même?
    menages = menages.rename(columns={'rev_fonciers': 'rev_fonciers_bruts'})
    menages = menages[variables].copy()
    menages.taxe_habitation = - menages.taxe_habitation  # taxes should be negative
    menages.rename(columns = dict(ident = 'idmen'), inplace = True)
    return menages


if __name__ == '__main__':
    import sys
    logging.basicConfig(level = logging.INFO, stream = sys.stdout)
    year = 2014
    data_frame = create_input_data_frame(year = year)
    log.info('Ok')

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
