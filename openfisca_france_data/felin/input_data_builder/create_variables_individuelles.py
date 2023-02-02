import logging
import numpy as np

from openfisca_core import periods


log = logging.getLogger(__name__)


def create_taux_csg_remplacement(individus, period, tax_benefit_system, sigma = (28.1) ** 2):
    """
    """
    assert 'revkire' in individus
    assert 'nbp' in individus
    assert period.start.year >= 2015

    rfr = individus.revkire
    nbptr = individus.nbp / 100

    def compute_taux_csg_remplacement(rfr, nbptr):
        parameters = tax_benefit_system.get_parameters_at_instant(period.start)
        seuils = parameters.prelevements_sociaux.contributions_sociales.csg.remplacement.pensions_de_retraite_et_d_invalidite
        seuil_exoneration = seuils.seuil_de_rfr_1 + (nbptr - 1) * seuils.demi_part_suppl
        seuil_reduction = seuils.seuil_de_rfr_2 + (nbptr - 1) * seuils.demi_part_suppl
        taux_csg_remplacement = 0.0 * rfr
        if period.start.year >= 2019:
            seuil_taux_intermediaire = seuils.seuil_rfr3 + (nbptr - 1) * seuils.demi_part_suppl_rfr3
            taux_csg_remplacement = np.where(
                rfr <= seuil_exoneration,
                1,
                np.where(
                    rfr <= seuil_reduction,
                    2,
                    np.where(
                        rfr <= seuil_taux_intermediaire,
                        3,
                        4,
                        )
                    )
                )
        else:
            taux_csg_remplacement = np.where(
                rfr <= seuil_exoneration,
                1,
                np.where(
                    rfr <= seuil_reduction,
                    2,
                    3,
                    )
                )

        return taux_csg_remplacement

    individus['taux_csg_remplacement'] = compute_taux_csg_remplacement(rfr, nbptr)

    assert individus['taux_csg_remplacement'].isin(range(5)).all()
