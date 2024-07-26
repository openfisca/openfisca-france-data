import numpy as np
import logging

from openfisca_core import periods
from openfisca_core.periods.date_unit import DateUnit
from openfisca_core.taxscales import MarginalRateTaxScale, combine_tax_scales
from openfisca_core.formula_helpers import switch
from openfisca_france.model.base import TypesCategorieSalarie, TAUX_DE_PRIME
from openfisca_france.model.prelevements_obligatoires.prelevements_sociaux.cotisations_sociales.base import (
    cotisations_salarie_by_categorie_salarie,
    )
from openfisca_france_data.smic import smic_horaire_brut
from openfisca_france_data import openfisca_france_tax_benefit_system


log = logging.getLogger(__name__)


def get_baremes_salarie(parameters, categorie_salarie, period, exclude_alsace_moselle = True):
    assert categorie_salarie in [
        "prive_cadre",
        "prive_non_cadre",
        "public_non_titulaire",
        "public_titulaire_etat",
        "public_titulaire_hospitaliere",
        "public_titulaire_territoriale",
        ]

    cotisations_salaries = cotisations_salarie_by_categorie_salarie[categorie_salarie]
    cotisations_salarie_retenues = list()

    for cotisation_salarie in cotisations_salaries:
        bareme = parameters.cotsoc.cotisations_salarie.children[categorie_salarie].children[cotisation_salarie]
        if exclude_alsace_moselle and "alsace_moselle" in cotisation_salarie:
            continue

        if bareme(period).thresholds and bareme(period).rates:
            cotisations_salarie_retenues.append(cotisation_salarie)

    return set(cotisations_salarie_retenues)



def create_salaire_de_base(individus, period = None, revenu_type = 'imposable', tax_benefit_system = None):
    """
    Calcule la variable salaire_de_base à partir du salaire imposable par inversion du barème
    de cotisations sociales correspondant à la catégorie à laquelle appartient le salarié.
    """
    assert period is not None
    assert revenu_type in ['net', 'imposable']
    for variable in ['categorie_salarie', 'contrat_de_travail', 'heures_remunerees_volume']:
        assert variable in individus.columns, "{} is missing".format(variable)
    assert tax_benefit_system is not None

    parameters = tax_benefit_system.parameters(period.start)
    salarie = parameters.cotsoc.cotisations_salarie
    plafond_securite_sociale_mensuel = parameters.prelevements_sociaux.pss.plafond_securite_sociale_mensuel
    parameters_csg_deductible = parameters.prelevements_sociaux.contributions_sociales.csg.activite.deductible
    taux_csg = parameters_csg_deductible.taux
    taux_abattement = parameters.prelevements_sociaux.contributions_sociales.csg.activite.abattement.rates[0]
    try:
        seuil_abattement = parameters.prelevements_sociaux.contributions_sociales.csg.activite.abattement.thresholds[1]
    except IndexError:  # Pour gérer le fait que l'abattement n'a pas toujours été limité à 4 PSS
        seuil_abattement = None
    csg_deductible = MarginalRateTaxScale(name = 'csg_deductible')
    csg_deductible.add_bracket(0, taux_csg * (1 - taux_abattement))
    if seuil_abattement is not None:
        csg_deductible.add_bracket(seuil_abattement, taux_csg)

    if revenu_type == 'net':  # On ajoute CSG imposable et crds

        parameters_csg_imposable = parameters.prelevements_sociaux.contributions_sociales.csg.activite.imposable
        taux_csg = parameters_csg_imposable.taux
        taux_abattement = parameters.prelevements_sociaux.contributions_sociales.csg.activite.abattement.rates[0]
        try:
            seuil_abattement = parameters.prelevements_sociaux.contributions_sociales.csg.activite.abattement.thresholds[1]
        except IndexError:  # Pour gérer le fait que l'abattement n'a pas toujours été limité à 4 PSS
            seuil_abattement = None
        csg_imposable = MarginalRateTaxScale(name = 'csg_imposable')
        csg_imposable.add_bracket(0, taux_csg * (1 - taux_abattement))
        if seuil_abattement is not None:
            csg_imposable.add_bracket(seuil_abattement, taux_csg)

        parameters_crds = parameters.prelevements_sociaux.contributions_sociales.crds.activite
        taux_csg = parameters_crds.taux
        taux_abattement = parameters.prelevements_sociaux.contributions_sociales.csg.activite.abattement.rates[0]
        try:
            seuil_abattement = parameters.prelevements_sociaux.contributions_sociales.csg.activite.abattement.thresholds[1]
        except IndexError:  # Pour gérer le fait que l'abattement n'a pas toujours été limité à 4 PSS
            seuil_abattement = None
        crds = MarginalRateTaxScale(name = 'crds')
        crds.add_bracket(0, taux_csg * (1 - taux_abattement))
        if seuil_abattement is not None:
            crds.add_bracket(seuil_abattement, taux_csg)

    # Check baremes
    target_by_categorie_salarie = dict(
        (categorie_salarie, get_baremes_salarie(tax_benefit_system.parameters, categorie_salarie, period))
        for categorie_salarie in ['prive_cadre', 'prive_non_cadre', 'public_non_titulaire']
        )

    for categorie_salarie, target in target_by_categorie_salarie.items():
        baremes_collection = salarie[categorie_salarie]
        baremes_to_remove = list()
        for name, bareme in baremes_collection._children.items():
            if name not in target:
                baremes_to_remove.append(name)

        # We split since we cannot remove from dict while iterating
        for name in baremes_to_remove:
            del baremes_collection._children[name]

    for categorie_salarie, target in target_by_categorie_salarie.items():
        test = set(
            name for name, bareme in salarie[categorie_salarie]._children.items()
            # if isinstance(bareme, MarginalRateTaxScale)
            )
        # assert target[categorie] == test, 'target: {} \n test {}'.format(target[categorie], test)
    del bareme

    # On ajoute la CSG deductible et on proratise par le plafond de la sécurité sociale
    # Pour éviter les divisions 0 /0 dans le switch qui sert à calculer le salaire_pour_inversion_proratise
    whours = parameters.marche_travail.salaire_minimum.smic.nb_heures_travail_mensuel

    if period.unit == 'year':
        nb_mois = 12
    elif period.unit == 'month':
        nb_mois = period.size
    else:
        raise
    plafond_securite_sociale = plafond_securite_sociale_mensuel * nb_mois
    heures_temps_plein = whours * nb_mois

    if revenu_type == 'imposable':
        salaire_pour_inversion = individus.salaire_imposable
    else:
        salaire_pour_inversion = individus.salaire_net

    categorie_salarie = individus.categorie_salarie
    contrat_de_travail = individus.contrat_de_travail
    heures_remunerees_volume = individus.heures_remunerees_volume

    heures_remunerees_volume_avoid_warning = heures_remunerees_volume + (heures_remunerees_volume == 0) * 1e9
    salaire_pour_inversion_proratise = switch(
        contrat_de_travail,
        {
            # temps plein
            0: salaire_pour_inversion / plafond_securite_sociale,
            # temps partiel
            1: salaire_pour_inversion / (
                (heures_remunerees_volume_avoid_warning / heures_temps_plein) * plafond_securite_sociale
                ),
            }
        )

    def add_agirc_gmp_to_agirc(agirc, parameters, period):
        if period.unit == 'year':
            nb_mois = 12
        elif period.unit == 'month':
            nb_mois = period.size
        else:
            raise
        plafond_securite_sociale = plafond_securite_sociale_mensuel * nb_mois
        salaire_charniere = parameters.prelevements_sociaux.regimes_complementaires_retraite_secteur_prive.gmp.salaire_charniere_annuel * (nb_mois / 12) / plafond_securite_sociale
        cotisation = parameters.prelevements_sociaux.regimes_complementaires_retraite_secteur_prive.gmp.cotisation_forfaitaire_mensuelle.part_salariale * nb_mois
        n = (cotisation + 1) * 12 # pour permettre la mensualisation en cas d'inversion, en évitant un taux 12 fois plus élevé sur une tranche 12 fois plus étroite
        agirc.add_bracket(n / plafond_securite_sociale, 0)
        agirc.rates[0] = cotisation / n
        agirc.thresholds[2] = salaire_charniere

    salaire_de_base = 0.0
    for categorie in ['prive_non_cadre', 'prive_cadre', 'public_non_titulaire']:
        if categorie == 'prive_cadre' and "agirc" in salarie[categorie]._children:
            print("adding GMP")
            add_agirc_gmp_to_agirc(salarie[categorie].agirc, parameters, period)

        bareme = combine_tax_scales(salarie[categorie])
        bareme.add_tax_scale(csg_deductible)
        if revenu_type == 'net':
            bareme.add_tax_scale(csg_imposable)
            bareme.add_tax_scale(crds)

        assert bareme.inverse().thresholds[0] == 0, "Invalid inverse bareme for {}:\n {}".format(
            categorie, bareme.inverse())
        for rate in bareme.inverse().rates:  # Vérification que l'on peut inverser correctement
            assert rate > 0

        brut_proratise = bareme.inverse().calc(salaire_pour_inversion_proratise)
        assert np.isfinite(brut_proratise).all()
        brut = plafond_securite_sociale * switch(
            contrat_de_travail,
            {
                # temps plein
                0: brut_proratise,
                # temps partiel
                1: brut_proratise * (heures_remunerees_volume / (heures_temps_plein)),
                }
            )
        salaire_de_base += (
            (categorie_salarie == TypesCategorieSalarie[categorie].index) * brut
            )

    individus['salaire_de_base'] = salaire_de_base

    if period.unit == 'year':
        year = period.start.year
        individus.loc[
            (individus.contrat_de_travail == 0) & (individus.salaire_de_base > 0),
            'salaire_de_base'
            ] = np.maximum(salaire_de_base, smic_horaire_brut[year] * 35 * 52 / 12)
        individus.loc[
            (individus.contrat_de_travail == 1) & (individus.salaire_de_base > 0),
            'salaire_de_base'
            ] = np.maximum(salaire_de_base, smic_horaire_brut[year] * heures_remunerees_volume)


def create_traitement_indiciaire_brut(individus, period = None, revenu_type = 'imposable',
            tax_benefit_system = None):
    """
    Calcule le traitement indiciaire brut à partir du salaire imposable ou du salaire net.
    Note : le supplément familial de traitement est imposable. Pas géré
    """
    assert period is not None
    assert revenu_type in ['net', 'imposable']
    assert tax_benefit_system is not None

    for variable in ['categorie_salarie', 'contrat_de_travail', 'heures_remunerees_volume']:
        assert variable in individus.columns

    if revenu_type == 'imposable':
        assert 'salaire_imposable' in individus.columns
        salaire_pour_inversion = individus.salaire_imposable
    else:
        assert 'salaire_net' in individus.columns
        salaire_pour_inversion = individus.salaire_net

    categorie_salarie = individus.categorie_salarie
    contrat_de_travail = individus.contrat_de_travail
    heures_remunerees_volume = individus.heures_remunerees_volume

    parameters = tax_benefit_system.parameters(period.start)

    salarie = parameters.cotsoc.cotisations_salarie
    plafond_securite_sociale_mensuel = parameters.prelevements_sociaux.pss.plafond_securite_sociale_mensuel
    parameters_csg_deductible = parameters.prelevements_sociaux.contributions_sociales.csg.activite.deductible
    taux_csg = parameters_csg_deductible.taux
    taux_abattement = parameters.prelevements_sociaux.contributions_sociales.csg.activite.abattement.rates[0]
    try:
        seuil_abattement = parameters.prelevements_sociaux.contributions_sociales.csg.activite.abattement.thresholds[1]
    except IndexError:  # Pour gérer le fait que l'abattement n'a pas toujours été limité à 4 PSS
        seuil_abattement = None
    csg_deductible = MarginalRateTaxScale(name = 'csg_deductible')
    csg_deductible.add_bracket(0, taux_csg * (1 - taux_abattement))
    if seuil_abattement is not None:
        csg_deductible.add_bracket(seuil_abattement, taux_csg)

    if revenu_type == 'net':
        # Cas des revenus nets:
        # comme les salariés du privé, on ajoute CSG imposable et crds qui s'appliquent à tous les revenus
        # 1. csg imposable
        parameters_csg_imposable = parameters.prelevements_sociaux.contributions_sociales.csg.activite.imposable
        taux_csg = parameters_csg_imposable.taux
        taux_abattement = parameters.prelevements_sociaux.contributions_sociales.csg.activite.abattement.rates[0]
        try:
            seuil_abattement = parameters.prelevements_sociaux.contributions_sociales.csg.activite.abattement.thresholds[1]
        except IndexError:  # Pour gérer le fait que l'abattement n'a pas toujours été limité à 4 PSS
            seuil_abattement = None
        csg_imposable = MarginalRateTaxScale(name = 'csg_imposable')
        csg_imposable.add_bracket(0, taux_csg * (1 - taux_abattement))
        if seuil_abattement is not None:
            csg_imposable.add_bracket(seuil_abattement, taux_csg)
        # 2. crds
        parameters_crds = parameters.prelevements_sociaux.contributions_sociales.crds.activite
        taux_csg = parameters_crds.taux
        taux_abattement = parameters.prelevements_sociaux.contributions_sociales.csg.activite.abattement.rates[0]
        try:
            seuil_abattement = parameters.prelevements_sociaux.contributions_sociales.csg.activite.abattement.thresholds[1]
        except IndexError:  # Pour gérer le fait que l'abattement n'a pas toujours été limité à 4 PSS
            seuil_abattement = None
        crds = MarginalRateTaxScale(name = 'crds')
        crds.add_bracket(0, taux_csg * (1 - taux_abattement))
        if seuil_abattement is not None:
            crds.add_bracket(seuil_abattement, taux_csg)

    # Check baremes
    target = dict()
    target['public_titulaire_etat'] = set(['excep_solidarite', 'pension', 'rafp'])
    target['public_titulaire_hospitaliere'] = set(['excep_solidarite', 'cnracl_s_ti', 'rafp'])
    target['public_titulaire_territoriale'] = set(['excep_solidarite', 'cnracl_s_ti', 'rafp'])

    categories_salarie_du_public = [
        'public_titulaire_etat',
        'public_titulaire_hospitaliere',
        'public_titulaire_territoriale',
        ]

    for categorie in categories_salarie_du_public:
        baremes_collection = salarie[categorie]
        test = set(
            name for name, bareme in salarie[categorie]._children.items()
            if isinstance(bareme, MarginalRateTaxScale) and name != 'cnracl_s_nbi'
            )
        # assert target[categorie] == test, 'target for {}: \n  target = {} \n  test = {}'.format(categorie, target[categorie], test)

    # Barèmes à éliminer :
        # cnracl_s_ti = taux hors NBI -> OK
        # cnracl_s_nbi = taux NBI -> On ne le prend pas en compte pour l'instant
    for categorie in [
        'public_titulaire_hospitaliere',
        'public_titulaire_territoriale',
        ]:
        baremes_collection = salarie[categorie]
        baremes_to_remove = list()
        baremes_to_remove.append('cnracl_s_nbi')
        for name in baremes_to_remove:
            if 'cnracl_s_nbi' in baremes_collection:
                del baremes_collection._children[name]

    salarie = salarie._children.copy()
    # RAFP des agents titulaires
    for categorie in categories_salarie_du_public:
        baremes_collection = salarie[categorie]
        baremes_collection['rafp'].multiply_rates(TAUX_DE_PRIME, inplace = True)

    # On ajoute la CSG déductible et on proratise par le plafond de la sécurité sociale
    whours = parameters.marche_travail.salaire_minimum.smic.nb_heures_travail_mensuel

    if period.unit == 'year':
        plafond_securite_sociale = plafond_securite_sociale_mensuel * 12
        heures_temps_plein = whours * 12
    elif period.unit == 'month':
        plafond_securite_sociale = plafond_securite_sociale_mensuel * period.size
        heures_temps_plein = whours * period.size
    else:
        raise

    # Pour a fonction publique la csg est calculée sur l'ensemble salbrut(=TIB) + primes
    # Imposable = (1 + taux_prime) * TIB - csg[(1 + taux_prime) * TIB] - pension[TIB]
    for categorie in categories_salarie_du_public:
        bareme_csg_deduc_public = csg_deductible.multiply_rates(
            1 + TAUX_DE_PRIME, inplace = False, new_name = "csg deduc public")
        if revenu_type == 'net':
            bareme_csg_imp_public = csg_imposable.multiply_rates(
                1 + TAUX_DE_PRIME, inplace = False, new_name = "csg imposable public")
            bareme_crds_public = crds.multiply_rates(
                1 + TAUX_DE_PRIME, inplace = False, new_name = "crds public")

    for categorie in categories_salarie_du_public:
        bareme_prime = MarginalRateTaxScale(name = "taux de prime")
        bareme_prime.add_bracket(0, -TAUX_DE_PRIME)  # barème équivalent à taux_prime*TIB

    heures_remunerees_volume_avoid_warning = heures_remunerees_volume + (heures_remunerees_volume == 0) * 1e9
    salaire_pour_inversion_proratise = switch(
        contrat_de_travail,
        {
            # temps plein
            0: salaire_pour_inversion / plafond_securite_sociale,
            # temps partiel
            1: salaire_pour_inversion / (
                (heures_remunerees_volume_avoid_warning / heures_temps_plein) * plafond_securite_sociale
                ),
            }
        )

    traitement_indiciaire_brut = 0.0

    for categorie in categories_salarie_du_public:
        for key, value in salarie[categorie]._children.items():
            log.debug(key, value)
        bareme = combine_tax_scales(salarie[categorie])
        log.debug('bareme cotsoc : {}'.format(bareme))
        bareme.add_tax_scale(bareme_csg_deduc_public)
        log.debug('bareme cotsoc + csg_deduc: {}'.format(bareme))
        if revenu_type == 'net':
            bareme.add_tax_scale(bareme_csg_imp_public)
            log.debug('bareme cotsoc + csg_deduc + csg_imp: {}'.format(bareme))
            bareme.add_tax_scale(bareme_crds_public)
            log.debug('bareme cotsoc + csg_deduc + csg_imp + crds: {}'.format(bareme))

        bareme.add_tax_scale(bareme_prime)
        log.debug('bareme cotsoc + csg_deduc + csg_imp + crds + prime: {}'.format(bareme))

        brut_proratise = bareme.inverse().calc(salaire_pour_inversion_proratise)

        assert np.isfinite(brut_proratise).all()
        brut = plafond_securite_sociale * switch(
            contrat_de_travail,
            {
                # temps plein
                0: brut_proratise,
                # temps partiel
                1: brut_proratise * (heures_remunerees_volume / (heures_temps_plein)),
                }
            )

        if period.start.year>2017:traitement_indiciaire_brut += (
                (categorie_salarie == TypesCategorieSalarie[categorie].index) * brut / (1 + 0.0076)
                ) # Prise en compte de l'indemnité compensatrice de csg, qui sera recalculée. Non prise en compte des exonérations de cotisation sur cette indemnité
        else:
            traitement_indiciaire_brut += (
                (categorie_salarie == TypesCategorieSalarie[categorie].index) * brut
                )
        if (categorie_salarie == TypesCategorieSalarie[categorie].index).any():
            log.debug("Pour {} : brut = {}".format(TypesCategorieSalarie[categorie].index, brut))
            log.debug('bareme direct: {}'.format(bareme))

    individus['traitement_indiciaire_brut'] = traitement_indiciaire_brut
    individus['primes_fonction_publique'] = TAUX_DE_PRIME * traitement_indiciaire_brut


def create_revenus_remplacement_bruts(individus, period, tax_benefit_system, revenu_type = 'net'):
    assert 'taux_csg_remplacement' in individus

    individus.chomage_imposable.fillna(0, inplace = True)
    individus.retraite_imposable.fillna(0, inplace = True)
    if revenu_type == 'imposable':
        assert 'salaire_imposable' in individus.columns
        salaire_pour_inversion = individus.salaire_imposable
    elif revenu_type == 'net':
        assert 'salaire_net' in individus.columns
        salaire_pour_inversion = individus.salaire_net
    else :
        raise Exception("revenu_type not implemented")
    salaire_pour_inversion.fillna(0, inplace = True)

    parameters = tax_benefit_system.get_parameters_at_instant(period.start)
    csg = parameters.prelevements_sociaux.contributions_sociales.csg
    csg_deductible_chomage = csg.remplacement.allocations_chomage.deductible
    pss = parameters.prelevements_sociaux.pss.plafond_securite_sociale_annuel
    taux_abattement_csg_chomage = parameters.prelevements_sociaux.contributions_sociales.csg.activite.abattement.rates[0]
    seuil_abattement_csg_chomage = parameters.prelevements_sociaux.contributions_sociales.csg.activite.abattement.thresholds[1]
    taux_plein = csg_deductible_chomage.taux_plein
    taux_reduit = csg_deductible_chomage.taux_reduit
    liste_smic_mensuel = []
    for month in period.get_subperiods(DateUnit.MONTH):
        smic_horaire_mois = openfisca_france_tax_benefit_system.parameters.marche_travail.salaire_minimum.smic.smic_b_horaire(month)
        nb_heures_mois = openfisca_france_tax_benefit_system.parameters.marche_travail.salaire_minimum.smic.nb_heures_travail_mensuel(month)
        smic_mensuel = smic_horaire_mois * nb_heures_mois
        liste_smic_mensuel.append(smic_mensuel)

    seuil_chomage_net_exoneration = (
        sum(liste_smic_mensuel)
        * (
            (individus.taux_csg_remplacement == 2) / (1 - taux_reduit)
            + (individus.taux_csg_remplacement >= 3) / (1 - taux_plein)
            )
        ) - salaire_pour_inversion # théoriquement, il s'agit du net pour salaire et rpns, mais il n'est pas toujours disponible en pratique
    exonere_csg_chomage = (
        (individus.taux_csg_remplacement < 2)
        | (individus.chomage_imposable <= seuil_chomage_net_exoneration)
        )
    taux_csg_chomage = np.where(
        individus.taux_csg_remplacement < 2,
        0,
        (individus.taux_csg_remplacement == 2) * taux_reduit
        + (individus.taux_csg_remplacement >= 3) * taux_plein
        )
    threshold = seuil_abattement_csg_chomage * pss * (1 - (taux_csg_chomage * (1 - taux_abattement_csg_chomage)))
    base_csg_chomage = np.where(
        individus.chomage_imposable <= threshold,
        individus.chomage_imposable * (1 - taux_abattement_csg_chomage) / (1 - (taux_csg_chomage * (1 - taux_abattement_csg_chomage))),
        (individus.chomage_imposable - seuil_abattement_csg_chomage * taux_abattement_csg_chomage * pss) / (1 - taux_csg_chomage)
        )
    individus['chomage_brut'] = np.where(
        exonere_csg_chomage,
        individus.chomage_imposable,
        individus.chomage_imposable + (base_csg_chomage * taux_csg_chomage)
    )
    assert individus['chomage_brut'].notnull().all()

    csg_deductible_retraite = parameters.prelevements_sociaux.contributions_sociales.csg.remplacement.pensions_retraite_invalidite.deductible
    taux_plein = csg_deductible_retraite.taux_plein
    taux_reduit = csg_deductible_retraite.taux_reduit
    if period.start.year >= 2019:
        taux_median = csg_deductible_retraite.taux_median
        individus['retraite_brute'] = (
        (individus.taux_csg_remplacement < 2) * individus.retraite_imposable
        + (individus.taux_csg_remplacement == 2) * individus.retraite_imposable / (1 - taux_reduit)
        + (individus.taux_csg_remplacement == 3) * individus.retraite_imposable / (1 - taux_median)
        + (individus.taux_csg_remplacement == 4) * individus.retraite_imposable / (1 - taux_plein)
        )
    else:
        individus['retraite_brute'] = (
            (individus.taux_csg_remplacement < 2) * individus.retraite_imposable
            + (individus.taux_csg_remplacement == 2) * individus.retraite_imposable / (1 - taux_reduit)
            + (individus.taux_csg_remplacement >= 3) * individus.retraite_imposable / (1 - taux_plein)
            )
    assert individus['retraite_brute'].notnull().all()
