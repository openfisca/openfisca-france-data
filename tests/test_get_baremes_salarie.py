import pytest


from openfisca_france import FranceTaxBenefitSystem
from openfisca_france_data.common import get_baremes_salarie


tax_benefit_system = FranceTaxBenefitSystem()
parameters = tax_benefit_system.parameters


target_by_period_by_categorie_salarie = {
    'prive_non_cadre': {
        2018: [
            'agff',
            'arrco',
            'asf',
            'chomage',
            'vieillesse_deplafonnee',
            'vieillesse_plafonnee',
            ],
        2019: [
            'agirc_arrco',
            'asf',
            'ceg',
            'cet2019',
            'chomage',
            'vieillesse_deplafonnee',
            'vieillesse_plafonnee',
            ],
        },
    }


def test_get_baremes_salarie():
    for categorie_salarie, target_by_period in target_by_period_by_categorie_salarie.items():
        for period, target in target_by_period.items():
            assert set(get_baremes_salarie(parameters, categorie_salarie, period, exclude_alsace_moselle = True)) == set(target)
