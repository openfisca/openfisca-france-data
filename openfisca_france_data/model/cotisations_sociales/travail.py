# -*- coding: utf-8 -*-


# OpenFisca -- A versatile microsimulation software
# By: OpenFisca Team <contact@openfisca.fr>
#
# Copyright (C) 2011, 2012, 2013, 2014 OpenFisca Team
# https://github.com/openfisca
#
# This file is part of OpenFisca.
#
# OpenFisca is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# OpenFisca is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


from __future__ import division

import logging

from openfisca_core.enumerations import Enum


CAT = Enum(['prive_non_cadre',
            'prive_cadre',
            'public_titulaire_etat',
            'public_titulaire_militaire',
            'public_titulaire_territoriale',
            'public_titulaire_hospitaliere',
            'public_non_titulaire'])


log = logging.getLogger(__name__)

############################################################################
# # Salaires
############################################################################


def _taille_entreprise(nbsala):
    '''
    0 : "Non pertinent"
    1 : "Moins de 10 salariés"
    2 : "De 10 à 19 salariés"
    3 : "De 20 à 199 salariés"
    4 : "Plus de 200 salariés"
    '''
    return (0 + 1 * (nbsala >= 1) + 1 * (nbsala >= 4) + 1 * (nbsala >= 5)
              + 1 * (nbsala >= 7))


def _type_sal(titc, statut, chpub, cadre):
    '''
    Catégorie de salarié
    '''
    cadre = (statut == 8) * (chpub > 3) * cadre
    # noncadre = (statut ==8)*(chpub>3)*not_(cadre)

    # etat_stag = (chpub==1)*(titc == 1)
    etat_tit = (chpub == 1) * (titc == 2)
    etat_cont = (chpub == 1) * (titc == 3)

    militaire = 0  # TODO:

    # colloc_stag = (chpub==2)*(titc == 1)
    colloc_tit = (chpub == 2) * (titc == 2)
    colloc_cont = (chpub == 2) * (titc == 3)

    # hosp_stag = (chpub==2)*(titc == 1)
    hosp_tit = (chpub == 2) * (titc == 2)
    hosp_cont = (chpub == 2) * (titc == 3)

    contract = (colloc_cont + hosp_cont + etat_cont) > 1

    return (0 + 1 * cadre + 2 * etat_tit + 3 * militaire
            + 4 * colloc_tit + 5 * hosp_tit + 6 * contract)
