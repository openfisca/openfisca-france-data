from openfisca_france_data.utils import build_cerfa_fields_by_variable
from openfisca_core.simulation_builder import SimulationBuilder
from openfisca_france_data.pote.annualisation_variables import AnnualisationVariablesIR
import openfisca_france



def liens_variables(year):
    '''
    Pour une année year de simulation de l'impôt sur le revenu renvoi :

    - les variables composées d'input variables qui ne sont utilisée que dans cette variables
    - la liste des input variables qui composent chaque variable du point précédent

    Ces listes vont être utilisées pour faire des pré calcul dans l'impôt sur le revenu afin de limiter le nombre de colonnes.

    '''

    var_foyer_fiscal = list()
    cerfa_var_dict = build_cerfa_fields_by_variable(year = year)

    for openfisca_var, cerfa in cerfa_var_dict.items():
        if len(cerfa) == 1:
            var_foyer_fiscal.append(openfisca_var)

    cas_type = {
        "individus": {
            "ind0": {
                "date_naissance": {'ETERNITY':'1970-01-01'},
                "salaire_imposable": {f"{year}":0},
                "retraite_imposable": {f"{year}":0},
                "chomage_imposable": {f"{year}":0}
            }
        }
    }
    tax_benefit_system = AnnualisationVariablesIR(openfisca_france.FranceTaxBenefitSystem())
    simulation = SimulationBuilder()
    simulation = simulation.build_from_entities(tax_benefit_system, cas_type)
    simulation.trace = True
    simulation.calculate('irpp_economique', year)
    lines = simulation.tracer.computation_log.lines()
    text = list()
    for line in lines:
        line = line.split(">>")
        if len(line)==2:
            text.append(line[0])

    indented_variables = list()
    for line in text:
        split_line = line.split("<")
        assert len(split_line) == 2
        assert split_line[1].startswith(str(year)), f"{split_line} doesn't start with {year}"
        indented_variables += [split_line[0]]

    indent_max = 0
    for line in indented_variables:
        level = (len(line) - len(line.lstrip()))/2
        if level > indent_max:
            indent_max = level

    tot = dict()
    for max in reversed(range(int(indent_max))):
        arborescence = dict()
        arborescence_i = dict()
        for line in indented_variables:
            indent = (len(line) - len(line.lstrip()))/2
            if indent < max:
                arborescence_i[indent] = line.lstrip()
            elif indent == max:
                arborescence[line.lstrip()] = arborescence_i
        tot[max] = arborescence

    i = 0
    dictionnaire_parent_enfants = dict()

    for max in reversed(range(2, int(indent_max + 1))):
        for line in indented_variables:
            level = (len(line) - len(line.lstrip()))/2
            if level == max - 1:
                variable = line.lstrip()
                rang_ident_1 = i
            if level == max:
                if i == rang_ident_1 + 1:
                    dictionnaire_parent_enfants[variable] = [line.lstrip()]
                else:
                    dictionnaire_parent_enfants[variable] += [line.lstrip()]
            i += 1
    variables = list(set([line.strip() for line in indented_variables]))

    dictionnaire_enfant_parents = dict()
    for variable in variables:
        dictionnaire_enfant_parents[variable] = []

    for parent, enfants in dictionnaire_parent_enfants.items():
        for enfant in enfants:
            dictionnaire_enfant_parents[enfant] += [parent]

    unique_appel = list()
    for enfant, parents in dictionnaire_enfant_parents.items():
        if len(parents) == 1:
            unique_appel += [enfant]
    assert len(unique_appel) == len(list(set(unique_appel))), "Il y a des doublons dans les appels uniques"

    variables_to_compute = list()
    for case_fiscal in var_foyer_fiscal:
        if case_fiscal in unique_appel:
            parent = dictionnaire_enfant_parents[case_fiscal]
            assert len(parent) == 1
            if parent[0] not in variables_to_compute: # si déjà dedans c'est qu'on a déjà checké que tous les enfants étaient bien appelés qu'une seule fois
                enfants_parent = dictionnaire_parent_enfants[parent[0]]
                unique_appel_enfants = [e for e in enfants_parent if e in unique_appel]
                only_case_fiscal = [c for c in enfants_parent if c in var_foyer_fiscal]
                if len(enfants_parent) == len(unique_appel_enfants):
                    if len(enfants_parent) == len(only_case_fiscal):
                        variables_to_compute += [parent[0]]

    variables_to_compute = [v for v in variables_to_compute if len(dictionnaire_parent_enfants[v])>1] # cela ne sert à rien de calculer si qu'une variable, aucun gain de colonnes
    enfants_tot = list()
    for var in variables_to_compute:
        enfants_tot += dictionnaire_parent_enfants[var]

    for enfant in dictionnaire_parent_enfants['duflot_pinel_denormandie_metropole'] + dictionnaire_parent_enfants['duflot_pinel_denormandie_om']:
        assert enfant.startswith("f7")
        ref = {'duflot_pinel_denormandie_metropole', 'duflot_pinel_denormandie_om'}
        assert set(dictionnaire_enfant_parents[enfant]).issubset(ref), f"{enfant}"
    enfants_tot = enfants_tot + dictionnaire_parent_enfants['duflot_pinel_denormandie_metropole']
    enfants_tot = enfants_tot + dictionnaire_parent_enfants['duflot_pinel_denormandie_om']
    variables_to_compute += ['duflot_pinel_denormandie_metropole', 'duflot_pinel_denormandie_om']

    return variables_to_compute, enfants_tot, dictionnaire_enfant_parents, dictionnaire_parent_enfants
