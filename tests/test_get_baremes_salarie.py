import pytest


from openfisca_france import FranceTaxBenefitSystem
from openfisca_france_data.common import get_baremes_salarie


tax_benefit_system = FranceTaxBenefitSystem()
parameters = tax_benefit_system.parameters


target_by_period_by_categorie_salarie = {
    'prive_non_cadre': {
        2016: [
            'agff',
            'arrco',
            'asf',
            'chomage',
            'maladie',
            'vieillesse_deplafonnee',
            'vieillesse_plafonnee',
            ],
        2017: [
            'agff',
            'arrco',
            'asf',
            'chomage',
            'maladie',
            'vieillesse_deplafonnee',
            'vieillesse_plafonnee',
            ],
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
            'vieillesse_deplafonnee',
            'vieillesse_plafonnee',
            ],
        },
    'prive_cadre': {
        2016: [
            'agff',
            'agirc',
            'apec',
            'arrco',
            'asf',
            'cet',
            'chomage',
            'maladie',
            'vieillesse_deplafonnee',
            'vieillesse_plafonnee',
            ],
        2017: [
            'agff',
            'arrco',
            'agirc',
            'apec',
            'asf',
            'cet',
            'maladie',
            'chomage',
            'vieillesse_deplafonnee',
            'vieillesse_plafonnee',
            ],
        2018: [
            'agff',
            'arrco',
            'agirc',
            'apec',
            'asf',
            'cet',
            'chomage',
            'vieillesse_deplafonnee',
            'vieillesse_plafonnee',
            ],
        2019: [
            'agirc_arrco',
            'asf',
            'apec',
            'ceg',
            'cet2019',
            'vieillesse_deplafonnee',
            'vieillesse_plafonnee',
            ],
        },
    'public_non_titulaire': {
        2016: [
            'excep_solidarite',
            'ircantec',
            'maladie',
            'vieillesse_deplafonnee',
            'vieillesse_plafonnee',
            ],
        2017: [
            'excep_solidarite',
            'ircantec',
            'maladie',
            'vieillesse_deplafonnee',
            'vieillesse_plafonnee',
            ],
        2018: [
            'ircantec',
            'vieillesse_deplafonnee',
            'vieillesse_plafonnee',
            ],
        2019: [
            'ircantec',
            'vieillesse_deplafonnee',
            'vieillesse_plafonnee',
            ],
        },
    "public_titulaire_etat": {
        2016: [
            "excep_solidarite",
            "pension",
            "rafp",
            ],
        2017: [
            "excep_solidarite",
            "pension",
            "rafp",
            ],
        2018: [
            "pension",
            "rafp",
            ],
        2019: [
            "pension",
            "rafp",
            ],
        },
    "public_titulaire_hospitaliere": {
        2016: [
            "cnracl_s_ti",
            "cnracl_s_nbi",
            "excep_solidarite",
            "rafp",
            ],
        2017: [
            "cnracl_s_ti",
            "cnracl_s_nbi",
            "excep_solidarite",
            "rafp",
            ],
        2018: [
            "cnracl_s_ti",
            "cnracl_s_nbi",
            "rafp",
            ],
        2019: [
            "cnracl_s_ti",
            "cnracl_s_nbi",
            "rafp",
            ],
        },
    "public_titulaire_territoriale": {
        2016: [
            "cnracl_s_ti",
            "cnracl_s_nbi",
            "excep_solidarite",
            "rafp",
            ],
        2017: [
            "cnracl_s_ti",
            "cnracl_s_nbi",
            "excep_solidarite",
            "rafp",
            ],
        2018: [
            "cnracl_s_ti",
            "cnracl_s_nbi",
            "rafp",
            ],
        2019: [
            "cnracl_s_ti",
            "cnracl_s_nbi",
            "rafp",
            ],
        },
    }


def test_get_baremes_salarie():
    for categorie_salarie, target_by_period in target_by_period_by_categorie_salarie.items():
        for period, target in target_by_period.items():
            assert set(get_baremes_salarie(parameters, categorie_salarie, period, exclude_alsace_moselle = True)) == set(target), f"Error on {categorie_salarie} for {period}"
