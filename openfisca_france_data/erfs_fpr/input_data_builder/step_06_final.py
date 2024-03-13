import gc
import logging
import pandas

from openfisca_france_data.utils import (id_formatter, print_id, normalizes_roles_in_entity)
from openfisca_survey_manager.temporary import temporary_store_decorator  # type: ignore
from openfisca_survey_manager.input_dataframe_generator import set_table_in_survey  # type: ignore

log = logging.getLogger(__name__)


@temporary_store_decorator(file_name = 'erfs_fpr')
def create_input_data_frame(temporary_store = None, year = None, export_flattened_df_filepath = None):
    assert temporary_store is not None
    assert year is not None

    individus = temporary_store['individus_{}'.format(year)]
    menages = temporary_store['menages_{}'.format(year)]

    # ici : variables à garder
    var_individus = [
        'activite',
        'age',
        'categorie_salarie',
        'categorie_non_salarie',
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
        'pensions_invalidite',
        'quifam',
        'quifoy',
        'quimen',
        'rag',
        'retraite_brute',
        'ric',
        'rnc',
        'rpns_imposables',
        'salaire_de_base',
        'statut_marital',
        "primes_fonction_publique",
        "traitement_indiciaire_brut",
        ]

    if year >= 2018:
        var_menages = [
            'idmen',
            'loyer',
            'statut_occupation_logement',
            'taxe_habitation',
            'wprm',
            'zone_apl',
            'logement_conventionne',
            'prest_precarite_hand' # on récupère la variable de montant de aah / caah pour pouvoir faire une imputation du handicap
        ]
    else:
        var_menages = [
            'idmen',
            'loyer',
            'taxe_habitation',
            'wprm',
            ]

    individus = create_ids_and_roles(individus)
    individus = individus[var_individus].copy()
    gc.collect()

    # This looks like it could have a sizeable impact
    missingvariablesmenages = ["taxe_habitation"]
    for k in missingvariablesmenages:
        menages[k] = 0


    menages = extract_menages_variables(menages)

    # individus = create_collectives_foyer_variables(individus, menages)

    idmens = individus.idmen.unique()
    menages = menages.loc[
        menages.idmen.isin(idmens),
        var_menages
        ].copy()
    survey_name = 'openfisca_erfs_fpr_' + str(year)

    # Formats ids
    individus = format_ids_and_roles(individus)
    menages = menages.rename(columns = {'idmen':'idmen_original'})
    unique_idmen = individus[['idmen','idmen_original']].drop_duplicates()
    assert len(unique_idmen) == len(menages), "Number of idmen should be the same individus and menages tables."

    menages = menages.merge(unique_idmen,
                            how = 'inner',
                            on = 'idmen_original')

    if export_flattened_df_filepath:
        supermerge = individus.merge(
            menages,
            right_index = True,
            left_on = "idmen",
            suffixes = ("", "_x"))
        log.debug(f"Saving to {export_flattened_df_filepath}")
        supermerge.to_hdf(export_flattened_df_filepath, key = "input")

    # Enters the individual table into the openfisca_erfs_fpr collection
    individus = individus.sort_values(by = ['idmen', 'idfoy', 'idfam'])
    log.debug(f"Saving entity 'individu' in collection 'openfisca_erfs_fpr' and survey name '{survey_name}' with set_table_in_survey")
    set_table_in_survey(
        individus,
        entity = "individu",
        period = year,
        collection = "openfisca_erfs_fpr",
        survey_name = survey_name,
        )

    menages = menages.sort_values(by = ['idmen'])
    log.debug(f"Saving entity 'menage' in collection 'openfisca_erfs_fpr' and survey name '{survey_name}' with set_table_in_survey")
    set_table_in_survey(
        menages,
        entity = "menage",
        period = year,
        collection = "openfisca_erfs_fpr",
        survey_name = survey_name,
        )
    log.debug("End of create_input_data_frame")


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

    # update idmens, as some households may have dropped out, causing errors
    # this is kind of a dirty fix, better solution would be to fix the dropping out itself
    # for instance: 2017, 17000919 drops out bc. no "chef de famille" which is weird, neet to investigate
    idmens_old = idmens.copy()
    idmens = set(menages_multi_foyers.idmen.to_list()).union(set(menages_simple_foyer.idmen.to_list()))

    dropouts = set(idmens).symmetric_difference(set(idmens_old))
    if len(dropouts) == 0:
        log.info('No households have been dropped. All clear.')
    else:
        log.warning('Some households [{}] have dropped out. You should investigate why this has happened. [{}]'.format(len(dropouts), ','.join(str(e) for e in dropouts)))

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
    individus.rename(columns = {'rev_fonciers_bruts': 'revenu_categoriel_foncier'}, inplace = True)
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
        data_frame = data_frame.sort_values(by = ['idmen', 'idfoy', 'idfam'])
        log.debug('Reformat ids: {}'.format(entity_id))
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
    variables = ['ident', 'wprm', 'taxe_habitation']
    external_variables = ['loyer', 'zone_apl', 'statut_occupation_logement','logement_conventionne', 'prest_precarite_hand']
    for external_variable in external_variables:
        if external_variable in menages.columns:
            log.debug("Found {} in menages table: we keep it".format(external_variable))
            variables.append(external_variable)
    menages = menages[variables].copy()
    menages.taxe_habitation = - menages.taxe_habitation  # taxes should be negative
    menages.rename(columns = dict(ident = 'idmen'), inplace = True)
    return menages


if __name__ == '__main__':
    import sys
    logging.basicConfig(level = logging.INFO, stream = sys.stdout)
    year = 2014
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
