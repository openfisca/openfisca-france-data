from openfisca_france_data.erfs_fpr.get_survey_scenario import get_survey_scenario
from openfisca_france_data.reforms.inversion_directe_salaires import inversion_directe_salaires

survey_scenario = get_survey_scenario(year = 2014, reform = inversion_directe_salaires)

data_frame_by_entity = survey_scenario.create_data_frame_by_entity(
    variables = [
        'impot_revenu_restant_a_payer',
        'maries_ou_pacses',
        'nbptr',
        'rfr',
        'revenu_assimile_salaire',
        'statut_marital',
        'weight_foyers',
        'weight_individus',
        ],
    )

famille = data_frame_by_entity['famille']
foyer_fiscal = data_frame_by_entity['foyer_fiscal']
individu = data_frame_by_entity['individu']
menage = data_frame_by_entity['menage']

# statut_occupation
statut_marital = individu.groupby('statut_marital')['weight_individus'].sum()
assert 22e6 < statut_marital[1] < 25e6
assert 30e6 < statut_marital[2] < 32e6

foyer_fiscal.groupby('maries_ou_pacses')['weight_foyers'].sum() / 1e6
foyer_fiscal.groupby('nbptr')['weight_foyers'].sum() / 1e6

assert 25e6 < (foyer_fiscal.weight_foyers).sum()

print(foyer_fiscal.groupby('nbptr').apply(lambda x: (x.impot_revenu_restant_a_payer.astype('float') * x.weight_foyers.astype('float')).sum()))
print((foyer_fiscal.impot_revenu_restant_a_payer.astype('float') * foyer_fiscal.weight_foyers.astype('float')).sum() / 1e9)

# survey_scenario.summarize_variable('salaire_imposable')
# salaire_imposable: 1 periods * 127126 cells * item size 4 (float32, default = 0) = 496.6K

# 2012: mean = 7295.99511719, min = 2.61648988724, max = 2135010.0, mass = 9.28e+08, default = 0.0%, median = 2.90648984909

# survey_scenario.summarize_variable('revenu_assimile_salaire')
# revenu_assimile_salaire: 1 periods * 127126 cells * item size 4 (float32, default = 0) = 496.6K

# 2012: mean = 7751.25683594, min = 2.61648988724, max = 2135010.0, mass = 9.85e+08, default = 0.0%, median = 2.90648984909
