from openfisca_france_data.erfs_fpr.get_survey_scenario import get_survey_scenario
from openfisca_france_data.reforms.inversion_directe_salaires import inversion_directe_salaires

survey_scenario = get_survey_scenario(year = 2014, reform = inversion_directe_salaires)


def test_inversion():
    survey_scenario.summarize_variable('salaire_de_base', force_compute = True)

    survey_scenario.summarize_variable('salaire_imposable', force_compute = True)
    survey_scenario.summarize_variable('salaire_de_base', force_compute = True)

    survey_scenario.summarize_variable('csg_imposable_salaire')
    data_frame_by_entity = survey_scenario.create_data_frame_by_entity(
        variables = [
            'salaire_de_base',
            'salaire_imposable',
            # 'csg_imposable_salaire',
            'categorie_salarie',
            'salaire_imposable_pour_inversion',
            # 'weight_individus',
            # 'wprm',
            ],
        )

    #famille = data_frame_by_entity['famille']
    individu = data_frame_by_entity['individu']
    menage = data_frame_by_entity['menage']

    individu.categorie_salarie.value_counts()
    prive = individu.query('categorie_salarie in [0, 1]')
    (prive.salaire_imposable - prive.salaire_imposable_pour_inversion).abs().max()
    survey_scenario.summarize_variable('salaire_imposable_pour_inversion')
    survey_scenario.summarize_variable('csg_deductible_salaire')
    survey_scenario.summarize_variable('chomage_brut')


if __name__ == '__main__':
    test_inversion()
