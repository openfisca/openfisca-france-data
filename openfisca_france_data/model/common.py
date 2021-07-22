from numpy import arange


try:
    from openfisca_survey_manager.statshelpers import weighted_quantiles
except ImportError:
    weighted_quantiles = None

try:
    from openfisca_survey_manager.statshelpers import mark_weighted_percentiles
except ImportError:
    mark_weighted_percentiles = None

from openfisca_france_data.model.base import *  # noqa analysis:ignore


class assiette_csg_salaire(Variable):
    value_type = float
    entity = Individu
    label = "Assiette CSG salaires"
    definition_period = MONTH

    def formula(individu, period, parameters):
        assiette_csg_abattue = individu('assiette_csg_abattue', period)
        assiette_csg_non_abattue = individu('assiette_csg_non_abattue', period)
        plafond_securite_sociale = individu('plafond_securite_sociale', period)
        abattement = parameters(period.start).prelevements_sociaux.contributions_sociales.csg.activite.deductible.abattement
        assiette = assiette_csg_abattue - abattement.calc(
            assiette_csg_abattue,
            factor = plafond_securite_sociale,
            round_base_decimals = 2,
            ) + assiette_csg_non_abattue
        return assiette


class assiette_csg_retraite(Variable):
    value_type = float
    entity = Individu
    label = "Assiette CSG retraite"
    definition_period = MONTH

    def formula(individu, period, parameters):
        retraite_brute = individu('retraite_brute', period)
        taux_csg_remplacement = individu('taux_csg_remplacement', period)
        return retraite_brute * (taux_csg_remplacement >= 2)


class assiette_csg_chomage(Variable):
    value_type = float
    entity = Individu
    label = "Assiette CSG chomage"
    definition_period = MONTH

    def formula(individu, period, parameters):
        chomage_brut = individu('chomage_brut', period)
        taux_csg_remplacement = individu('taux_csg_remplacement', period)
        return chomage_brut * (taux_csg_remplacement >= 2)


class decile(Variable):
    value_type = Enum
    possible_values = Deciles
    default_value = Deciles.hors_champs
    entity = Menage
    label = "Décile de niveau de vie disponible"
    definition_period = YEAR

    def formula(menage, period):
        menage_ordinaire = menage('menage_ordinaire', period)
        niveau_de_vie = menage('niveau_de_vie', period)
        wprm = menage('wprm', period)
        labels = arange(1, 11)
        method = 2
        if len(wprm) == 1:
            return wprm * 0
        decile, values = mark_weighted_percentiles(
            niveau_de_vie, labels, wprm * menage_ordinaire, method, return_quantiles = True)
        del values
        return decile * menage_ordinaire


class centile(Variable):
    value_type = Enum
    possible_values = Deciles
    default_value = Deciles.hors_champs
    entity = Menage
    label = "Centile de niveau de vie disponible"
    definition_period = YEAR

    def formula(menage, period):
        menage_ordinaire = menage('menage_ordinaire', period)
        niveau_de_vie = menage('niveau_de_vie', period)
        wprm = menage('wprm', period)
        labels = arange(1, 101)
        method = 2
        if len(wprm) == 1:
            return wprm * 0
        centile, values = mark_weighted_percentiles(
            niveau_de_vie, labels, wprm * menage_ordinaire, method, return_quantiles = True)
        del values
        return centile * menage_ordinaire


class decile_rfr(Variable):
    value_type = Enum
    possible_values = Deciles
    default_value = Deciles.hors_champs
    entity = FoyerFiscal
    label = "Décile de revenu fiscal de référence"
    definition_period = YEAR

    def formula(foyer_fiscal, period):
        rfr = foyer_fiscal('rfr', period)
        weight_foyers = foyer_fiscal('weight_foyers', period)
        menage_ordinaire_foyers_fiscaux = foyer_fiscal('menage_ordinaire_foyers_fiscaux', period)
        labels = arange(1, 11)
        # Alternative method
        # method = 2
        # decile, values = mark_weighted_percentiles(niveau_de_vie, labels, pondmen, method, return_quantiles = True)
        decile, values = weighted_quantiles(rfr, labels, weight_foyers * menage_ordinaire_foyers_fiscaux, return_quantiles = True)
        return decile


class centile_rfr(Variable):
    value_type = Enum
    possible_values = Deciles
    default_value = Deciles.hors_champs
    entity = FoyerFiscal
    label = "Centile de revenu fiscal de référence"
    definition_period = YEAR

    def formula(foyer_fiscal, period):
        rfr = foyer_fiscal('rfr', period)
        weight_foyers = foyer_fiscal('weight_foyers', period)
        menage_ordinaire_foyers_fiscaux = foyer_fiscal('menage_ordinaire_foyers_fiscaux', period)
        labels = arange(1, 101)
        centile, values = weighted_quantiles(rfr, labels, weight_foyers * menage_ordinaire_foyers_fiscaux, return_quantiles = True)
        return centile


class decile_rfr_par_part(Variable):
    value_type = Enum
    possible_values = Deciles
    default_value = Deciles.hors_champs
    entity = FoyerFiscal
    label = "Décile de revenu fiscal de référence par part fiscale"
    definition_period = YEAR

    def formula(foyer_fiscal, period):
        rfr = foyer_fiscal('rfr', period)
        nbptr = foyer_fiscal('nbptr', period)
        weight_foyers = foyer_fiscal('weight_foyers', period)
        menage_ordinaire_foyers_fiscaux = foyer_fiscal('menage_ordinaire_foyers_fiscaux', period)
        labels = arange(1, 11)
        # Alternative method
        # method = 2
        # decile, values = mark_weighted_percentiles(niveau_de_vie, labels, pondmen, method, return_quantiles = True)
        decile, values = weighted_quantiles(
            rfr / nbptr, labels, weight_foyers * menage_ordinaire_foyers_fiscaux, return_quantiles = True)
        return decile


class centile_rfr_par_part(Variable):
    value_type = Enum
    possible_values = Deciles
    default_value = Deciles.hors_champs
    entity = FoyerFiscal
    label = "Centile de revenu fiscal de référence par part fiscale"
    definition_period = YEAR

    def formula(foyer_fiscal, period):
        rfr = foyer_fiscal('rfr', period)
        nbptr = foyer_fiscal('nbptr', period)
        weight_foyers = foyer_fiscal('weight_foyers', period)
        menage_ordinaire_foyers_fiscaux = foyer_fiscal('menage_ordinaire_foyers_fiscaux', period)
        labels = arange(1, 101)
        centile, values = weighted_quantiles(
            rfr / nbptr, labels, weight_foyers * menage_ordinaire_foyers_fiscaux, return_quantiles = True)
        return centile


class pauvre40(Variable):
    value_type = bool
    entity = Menage
    label = "Ménage en dessous du seuil de pauvreté à 40%"
    definition_period = YEAR

    def formula(menage, period):
        menage_ordinaire = menage('menage_ordinaire', period)
        nivvie = menage('nivvie', period)
        wprm = menage('wprm', period)
        labels = arange(1, 3)
        method = 2
        if len(wprm) == 1:
            return wprm * 0
        percentile, values = mark_weighted_percentiles(nivvie, labels, wprm * menage_ordinaire, method, return_quantiles = True)
        threshold = .4 * values[1]
        return (nivvie <= threshold) * menage_ordinaire


class pauvre50(Variable):
    value_type = bool
    entity = Menage
    label = "Ménage en dessous du seuil de pauvreté à 50%"
    definition_period = YEAR


    def formula(menage, period):
        menage_ordinaire = menage('menage_ordinaire', period)
        nivvie = menage('nivvie', period)
        wprm = menage('wprm', period)
        labels = arange(1, 3)
        method = 2
        if len(wprm) == 1:
            return wprm * 0

        percentile, values = mark_weighted_percentiles(nivvie, labels, wprm * menage_ordinaire, method, return_quantiles = True)
        threshold = .5 * values[1]
        return (nivvie <= threshold) * menage_ordinaire


class pauvre60(Variable):
    value_type = bool
    entity = Menage
    label = "Ménage en dessous du seuil de pauvreté à 60%"
    definition_period = YEAR

    def formula(menage, period):
        menage_ordinaire = menage('menage_ordinaire', period)
        nivvie = menage('nivvie', period)
        wprm = menage('wprm', period)
        labels = arange(1, 3)
        method = 2
        if len(wprm) == 1:
            return wprm * 0

        percentile, values = mark_weighted_percentiles(nivvie, labels, wprm * menage_ordinaire, method, return_quantiles = True)
        threshold = .6 * values[1]
        return (nivvie <= threshold) * menage_ordinaire
