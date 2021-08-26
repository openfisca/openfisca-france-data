import numpy as np
import logging

from openfisca_core import periods
from openfisca_core.taxscales import MarginalRateTaxScale, combine_tax_scales
from openfisca_core.formula_helpers import switch
from openfisca_france.model.base import TypesCategorieSalarie, TAUX_DE_PRIME
from openfisca_france.model.prelevements_obligatoires.prelevements_sociaux.cotisations_sociales.base import (
    cotisations_salarie_by_categorie_salarie,
    )
from openfisca_france_data.smic import smic_horaire_brut


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
    taux_abattement = parameters_csg_deductible.abattement.rates[0]
    try:
        seuil_abattement = parameters_csg_deductible.abattement.thresholds[1]
    except IndexError:  # Pour gérer le fait que l'abattement n'a pas toujours était limité à 4 PSS
        seuil_abattement = None
    csg_deductible = MarginalRateTaxScale(name = 'csg_deductible')
    csg_deductible.add_bracket(0, taux_csg * (1 - taux_abattement))
    if seuil_abattement is not None:
        csg_deductible.add_bracket(seuil_abattement, taux_csg)

    if revenu_type == 'net':  # On ajoute CSG imposable et crds

        parameters_csg_imposable = parameters.prelevements_sociaux.contributions_sociales.csg.activite.imposable
        taux_csg = parameters_csg_imposable.taux
        taux_abattement = parameters_csg_imposable.abattement.rates[0]
        try:
            seuil_abattement = parameters_csg_imposable.abattement.thresholds[1]
        except IndexError:  # Pour gérer le fait que l'abattement n'a pas toujours était limité à 4 PSS
            seuil_abattement = None
        csg_imposable = MarginalRateTaxScale(name = 'csg_imposable')
        csg_imposable.add_bracket(0, taux_csg * (1 - taux_abattement))
        if seuil_abattement is not None:
            csg_imposable.add_bracket(seuil_abattement, taux_csg)

        parameters_crds = parameters.prelevements_sociaux.contributions_sociales.crds.activite
        taux_csg = parameters_crds.taux
        taux_abattement = parameters_crds.abattement.rates[0]
        try:
            seuil_abattement = parameters_crds.abattement.thresholds[1]
        except IndexError:  # Pour gérer le fait que l'abattement n'a pas toujours était limité à 4 PSS
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

        # We split since we cannot remove from dict while iterating
        for name in baremes_to_remove:
            del baremes_collection._children[name]

    for categorie_salarie, target in target_by_categorie_salarie.items():
        test = set(
            name for name, bareme in salarie[categorie_salarie]._children.items()
            # if isinstance(bareme, MarginalRateTaxScale)
            )
        assert target == test, f"target: {sorted(target)} \n test {sorted(test)}"
    del bareme

    # On ajoute la CSG deductible et on proratise par le plafond de la sécurité sociale
    # Pour éviter les divisions 0 /0 dans le switch qui sert à calculer le salaire_pour_inversion_proratise
    if period.unit == 'year':
        plafond_securite_sociale = plafond_securite_sociale_mensuel * 12
        heures_temps_plein = 52 * 35
    elif period.unit == 'month':
        plafond_securite_sociale = plafond_securite_sociale_mensuel * period.size
        heures_temps_plein = (52 * 35 / 12) * period.size
    else:
        raise

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

    def add_agirc_gmp_to_agirc(agirc, parameters):
        plafond_securite_sociale_annuel = parameters.prelevements_sociaux.pss.plafond_securite_sociale_annuel
        salaire_charniere = parameters.prelevements_sociaux.regimes_complementaires_retraite_secteur_prive.gmp.salaire_charniere_annuel / plafond_securite_sociale_annuel
        cotisation = parameters.prelevements_sociaux.regimes_complementaires_retraite_secteur_prive.gmp.cotisation_forfaitaire_mensuelle_en_euros.part_salariale * 12
        n = (cotisation + 1) * 12
        agirc.add_bracket(n / plafond_securite_sociale_annuel, 0)
        agirc.rates[0] = cotisation / n
        agirc.thresholds[2] = salaire_charniere

    salaire_de_base = 0.0
    for categorie in ['prive_non_cadre', 'prive_cadre', 'public_non_titulaire']:
        if categorie == 'prive_cadre' and "agirc" in salarie[categorie]._children:
            print("adding GMP")
            add_agirc_gmp_to_agirc(salarie[categorie].agirc, parameters)

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
    Calcule le tratement indiciaire brut à partir du salaire imposable ou du salaire net.
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

    legislation = tax_benefit_system.parameters(period.start)

    salarie = legislation.cotsoc.cotisations_salarie
    plafond_securite_sociale_mensuel = legislation.prelevements_sociaux.pss.plafond_securite_sociale_mensuel
    legislation_csg_deductible = legislation.prelevements_sociaux.contributions_sociales.csg.activite.deductible
    taux_csg = legislation_csg_deductible.taux
    taux_abattement = legislation_csg_deductible.abattement.rates[0]
    try:
        seuil_abattement = legislation_csg_deductible.abattement.thresholds[1]
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
        legislation_csg_imposable = legislation.prelevements_sociaux.contributions_sociales.csg.activite.imposable
        taux_csg = legislation_csg_imposable.taux
        taux_abattement = legislation_csg_imposable.abattement.rates[0]
        try:
            seuil_abattement = legislation_csg_imposable.abattement.thresholds[1]
        except IndexError:  # Pour gérer le fait que l'abattement n'a pas toujours été limité à 4 PSS
            seuil_abattement = None
        csg_imposable = MarginalRateTaxScale(name = 'csg_imposable')
        csg_imposable.add_bracket(0, taux_csg * (1 - taux_abattement))
        if seuil_abattement is not None:
            csg_imposable.add_bracket(seuil_abattement, taux_csg)
        # 2. crds
        legislation_crds = legislation.prelevements_sociaux.contributions_sociales.crds.activite
        taux_csg = legislation_crds.taux
        taux_abattement = legislation_crds.abattement.rates[0]
        try:
            seuil_abattement = legislation_crds.abattement.thresholds[1]
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
        assert target[categorie] == test, 'target for {}: \n  target = {} \n  test = {}'.format(categorie, target[categorie], test)

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
    if period.unit == 'year':
        plafond_securite_sociale = plafond_securite_sociale_mensuel * 12
        heures_temps_plein = 52 * 35
    elif period.unit == 'month':
        plafond_securite_sociale = plafond_securite_sociale_mensuel * period.size
        heures_temps_plein = (52 * 35 / 12) * period.size
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
        traitement_indiciaire_brut += (
            (categorie_salarie == TypesCategorieSalarie[categorie].index) * brut
            )
        if (categorie_salarie == TypesCategorieSalarie[categorie].index).any():
            log.debug("Pour {} : brut = {}".format(TypesCategorieSalarie[categorie].index, brut))
            log.debug('bareme direct: {}'.format(bareme))

    individus['traitement_indiciaire_brut'] = traitement_indiciaire_brut
    individus['primes_fonction_publique'] = TAUX_DE_PRIME * traitement_indiciaire_brut


def create_revenus_remplacement_bruts(individus, period, tax_benefit_system):
    assert 'taux_csg_remplacement' in individus

    individus.chomage_imposable.fillna(0, inplace = True)
    individus.retraite_imposable.fillna(0, inplace = True)

    parameters = tax_benefit_system.parameters(period.start)
    csg = parameters.prelevements_sociaux.contributions_sociales.csg
    csg_deductible_chomage = csg.chomage.deductible
    taux_plein = csg_deductible_chomage.taux_plein
    taux_reduit = csg_deductible_chomage.taux_reduit
    seuil_chomage_net_exoneration = (
        (35 * 52) * smic_horaire_brut[period.start.year]
        * (
            (individus.taux_csg_remplacement == 2) / (1 - taux_reduit)
            + (individus.taux_csg_remplacement == 3) / (1 - taux_plein)
            )
        )
    exonere_csg_chomage = (
        (individus.taux_csg_remplacement < 2)
        | (individus.chomage_imposable <= seuil_chomage_net_exoneration)
        )
    individus['chomage_brut'] = np.where(
        exonere_csg_chomage,
        individus.chomage_imposable,
        (individus.taux_csg_remplacement == 2) * individus.chomage_imposable / (1 - taux_reduit)
        + (individus.taux_csg_remplacement == 3) * individus.chomage_imposable / (1 - taux_plein)
        )
    assert individus['chomage_brut'].notnull().all()

    csg_deductible_retraite = parameters.prelevements_sociaux.contributions_sociales.csg.retraite_invalidite.deductible
    taux_plein = csg_deductible_retraite.taux_plein
    taux_reduit = csg_deductible_retraite.taux_reduit
    individus['retraite_brute'] = (
        (individus.taux_csg_remplacement < 2) * individus.retraite_imposable
        + (individus.taux_csg_remplacement == 2) * individus.retraite_imposable / (1 - taux_reduit)
        + (individus.taux_csg_remplacement == 3) * individus.retraite_imposable / (1 - taux_plein)
        )
    assert individus['retraite_brute'].notnull().all()
