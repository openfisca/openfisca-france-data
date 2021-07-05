from openfisca_france_data.erfs_fpr.get_survey_scenario import get_survey_scenario
from openfisca_france_data.reforms.inversion_directe_salaires import inversion_directe_salaires

survey_scenario = get_survey_scenario(year = 2014, reform = inversion_directe_salaires)

data_frame_by_entity = survey_scenario.create_data_frame_by_entity(
    variables = [
        'age',
        'aides_logement',
        'aide_logement_montant_brut',
        'apl',
        'alf',
        'als',
        'statut_occupation_logement',
        'weight_familles',
        'weight_individus',
        'wprm',
        ],
    )

famille = data_frame_by_entity['famille']
individu = data_frame_by_entity['individu']
menage = data_frame_by_entity['menage']

# statut_occupation
statut_occupation_logement_pct = menage.groupby('statut_occupation_logement')['wprm'].sum() / menage.wprm.sum()
print(statut_occupation_logement_pct)
# 2 proprietaire
assert .39 < statut_occupation_logement_pct[2] < .41
# accedant
assert .17 < statut_occupation_logement_pct[1] < .18
# locataire (indiferrencie)
assert .39 < statut_occupation_logement_pct[3:7].sum() < .43

11e10 < (famille.aide_logement_montant_brut * famille.weight_familles).sum()
11e10 < (
    (famille.apl * famille.weight_familles).sum()
    + (famille.als * famille.weight_familles).sum()
    + (famille.alf * famille.weight_familles).sum()
    )
