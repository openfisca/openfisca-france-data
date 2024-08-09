from openfisca_france.model.base import (
    FoyerFiscal,
    Individu,
    YEAR,
    Variable,
    Reform
)

from numpy import maximum as max_

class AnnualisationVariablesIR(Reform):
    name = "Annualisation des variables dans le calcul de l'impôt sur le revenu"
    tax_benefit_system_name = "openfisca_france"

    def apply(self):

        class salaire_imposable(Variable):
            value_type = float
            unit = 'currency'
            cerfa_field = {  # (f1aj, f1bj, f1cj, f1dj, f1ej)
                0: '1AJ',
                1: '1BJ',
                2: '1CJ',
                3: '1DJ',
                4: '1EJ',
                }
            entity = Individu
            label = 'Salaires imposables'
            reference = 'https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000042683657'
            definition_period = YEAR

        class retraite_imposable(Variable):
            unit = 'currency'
            value_type = float
            cerfa_field = {
                0: '1AS',
                1: '1BS',
                2: '1CS',
                3: '1DS',
                4: '1ES',
                }
            entity = Individu
            label = 'Retraites au sens strict imposables (rentes à titre onéreux exclues)'
            reference = 'http://vosdroits.service-public.fr/particuliers/F415.xhtml'
            definition_period = YEAR

        class chomage_imposable(Variable):
            value_type = float
            unit = 'currency'
            cerfa_field = {
                0: '1AP',
                1: '1BP',
                2: '1CP',
                3: '1DP',
                4: '1EP',
                }
            entity = Individu
            label = 'Allocations chômage imposables'
            reference = 'http://www.insee.fr/fr/methodes/default.asp?page=definitions/chomage.htm'
            definition_period = YEAR


        baseline_revenus_capitaux_pfu = self.baseline.get_variable(
            "revenus_capitaux_prelevement_forfaitaire_unique_ir"
        )
        formula_revenus_capitaux_pfu = (
            baseline_revenus_capitaux_pfu.get_formula("2021-01-01")
        )

        class revenus_capitaux_prelevement_forfaitaire_unique_ir(Variable):
            value_type = float
            entity = FoyerFiscal
            label = 'Revenus des valeurs et capitaux mobiliers soumis au prélèvement forfaitaire unique (partie impôt sur le revenu)'
            definition_period = YEAR

            def formula_2021_01_01(foyer_fiscal, period, parameters):
                return formula_revenus_capitaux_pfu(foyer_fiscal, period.first_month, parameters) * 12


        baseline_revenus_capitaux_prelevement_bareme = self.baseline.get_variable(
            "revenus_capitaux_prelevement_bareme"
        )
        formula_revenus_capitaux_prelevement_bareme = (
            baseline_revenus_capitaux_prelevement_bareme.get_formula("2021-01-01")
        )

        class revenus_capitaux_prelevement_bareme(Variable):
            value_type = float
            entity = FoyerFiscal
            label = 'Revenus du capital imposés au barème (montants bruts)'
            reference = 'http://bofip.impots.gouv.fr/bofip/3775-PGP'
            definition_period = YEAR

            def formula_2021_01_01(foyer_fiscal, period, parameters):
                formula_revenus_capitaux_prelevement_bareme(foyer_fiscal, period.first_month, parameters) * 12

        baseline_revenus_capitaux_prelevement_liberatoire = self.baseline.get_variable(
            "revenus_capitaux_prelevement_liberatoire"
        )
        formula_revenus_capitaux_prelevement_liberatoire = (
            baseline_revenus_capitaux_prelevement_liberatoire.get_formula("2021-01-01")
        )

        class revenus_capitaux_prelevement_liberatoire(Variable):
            value_type = float
            entity = FoyerFiscal
            label = 'Revenu du capital imposé au prélèvement libératoire (montants bruts)'
            reference = 'http://bofip.impots.gouv.fr/bofip/3817-PGP'
            definition_period = YEAR

            def formula_2021_01_01(foyer_fiscal, period, parameters):
                return formula_revenus_capitaux_prelevement_liberatoire(foyer_fiscal, period, parameters) * 12

        class revenus_individuels(Variable):
            value_type = float
            entity = FoyerFiscal
            label = "Somme des revenus_individuels utilisés pour l'imputation des revenus du capital"
            definition_period = YEAR

            def formula(foyer_fiscal, period):
                revenu_assimile_salaire_i = foyer_fiscal.members("revenu_assimile_salaire", period)
                revenu_assimile_salaire = foyer_fiscal.sum(revenu_assimile_salaire_i)
                revenu_assimile_pension_i = foyer_fiscal.members("revenu_assimile_pension", period)
                revenu_assimile_pension = foyer_fiscal.sum(revenu_assimile_pension_i)
                rpns_imposables_i = foyer_fiscal.members("rpns_imposables", period)
                rpns_imposables = foyer_fiscal.sum(rpns_imposables_i)

                return max_(revenu_assimile_salaire + revenu_assimile_pension + rpns_imposables, 0)

        baseline_rfr = self.baseline.get_variable(
            "rfr"
        )
        formula_rfr = (
            baseline_rfr.get_formula()
        )

        class rfr(Variable):
            value_type = float
            entity = FoyerFiscal
            label = "Revenu fiscal de référence"
            definition_period = YEAR

            def formula(foyer_fiscal, period, parameters):
                rfr = formula_rfr(foyer_fiscal, period, parameters)
                return max_(rfr, 0)

        class salaire_imposable_large(Variable):
            value_type = float
            entity = Individu
            label = "Salaires imposables au sens large, mais sans le chomage imposable"
            definition_period = YEAR

            def formula(individu, period):
                revenu_assimile_salaire = individu("revenu_assimile_salaire", period)
                chomage_imposable = individu("chomage_imposable", period)

                return revenu_assimile_salaire - chomage_imposable

        class rfr_par_part(Variable):
            value_type = float
            entity = FoyerFiscal
            label = "Revenu fiscal de référence par part"
            definition_period = YEAR

            def formula(foyer_fiscal,period):
                rfr = foyer_fiscal("rfr", period)
                nbptr = foyer_fiscal("nbptr", period)

                return rfr / nbptr


        variables_annualisees = [
            salaire_imposable,
            retraite_imposable,
            chomage_imposable,
            revenus_capitaux_prelevement_forfaitaire_unique_ir,
            revenus_capitaux_prelevement_bareme,
            revenus_capitaux_prelevement_liberatoire,
            rfr
        ]

        variables_ajout = [
            revenus_individuels,
            salaire_imposable_large,
            rfr_par_part
            ]

        for variable in variables_annualisees:
            self.update_variable(variable)

        for variable in variables_ajout:
            self.add_variable(variable)
