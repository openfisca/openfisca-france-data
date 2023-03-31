import logging
import pandas as pd


from openfisca_survey_manager.temporary import temporary_store_decorator  # type: ignore


log = logging.getLogger(__name__)


@temporary_store_decorator(file_name = 'erfs_fpr')
def build_variables_foyers_fiscal(temporary_store = None, year = None):

    assert temporary_store is not None
    assert year is not None

    individus = temporary_store['individus_{}'.format(year)]
    menages = temporary_store['menages_{}'.format(year)]

    individus['idfoy'] = individus['idfam'].copy()
    individus['quifoy'] = individus['quifam'].copy()

    foyers_fiscaux = individus[['idfoy','ident',]].drop_duplicates()
    foyers_fiscaux = pd.merge(
        menages[[
            'ident',
            'rev_financier_prelev_lib_imputes',
            'rev_fonciers_bruts',
            'rev_valeurs_mobilieres_bruts',
            'wprm',
            ]],
        foyers_fiscaux,
        how = 'inner',
        on = 'ident'
        )
    # première version pour splitter les revenus du capital du ménage dans les foyers fiscaux
    # on attribue l'ensemble des revenus du capital du ménage au foyer avec la personne ayant les plus hauts revenus
    # procédure à améliorer
    idfoy = (individus
        .sort_values(
            [
                'ident',
                'salaire_de_base',
                'traitement_indiciaire_brut',
                'retraite_brute'
                ],
            ascending = False
            )
        .groupby('ident')
        .first()
        .idfoy
        )
    foyers_fiscaux['revenu_categoriel_foncier'] = foyers_fiscaux['rev_fonciers_bruts'] * foyers_fiscaux.idfoy.isin(idfoy)
    foyers_fiscaux['revenus_capitaux_prelevement_forfaitaire_unique_ir'] = foyers_fiscaux['rev_valeurs_mobilieres_bruts'] * foyers_fiscaux.idfoy.isin(idfoy)
    foyers_fiscaux['rev_financier_prelev_lib_imputes'] = foyers_fiscaux['rev_financier_prelev_lib_imputes'] * foyers_fiscaux.idfoy.isin(idfoy)

    temporary_store[f"foyers_fiscaux_{year}"] = foyers_fiscaux
