# -*- coding: utf-8 -*-


# OpenFisca -- A versatile microsimulation software
# By: OpenFisca Team <contact@openfisca.fr>
#
# Copyright (C) 2011, 2012, 2013, 2014, 2015 OpenFisca Team
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


from .base import * # noqa  analysis:ignore


class idmen_original(Variable):
    column = IntCol
    entity_class = Menages
    label = u"Identifiant ménage, lien avec l'identifiant dérivé de l'ERF"


class idfoy_original(Variable):
    column = IntCol
    entity_class = FoyersFiscaux
    label = u"Identifiant foyer, lien avec l'identifiant dérivé de l'ERF"


class idfam_original(Variable):
    column = IntCol
    entity_class = Familles
    label = u"Identifiant famille, lien avec l'identifiant dérivé de l'ERF"


class titc(Variable):
    column = EnumCol(
        enum = Enum(
            [
                u"Sans objet ou non renseigné",
                u"Elève fonctionnaire ou stagiaire",
                u"Agent titulaire",
                u"Contractuel",
                ]
            ),
        )
    entity_class = Individus
    label = u"Statut, pour les agents de l'Etat des collectivités locales, ou des hôpitaux"
    # survey_only = True


class statut(Variable):
    column = EnumCol(
        enum = Enum(
            [
                u"Sans objet",
                u"Indépendants",
                u"Employeurs",
                u"Aides familiaux",
                u"Intérimaires",
                u"Apprentis",
                u"CDD (hors Etat, coll.loc.), hors contrats aidés",
                u"Stagiaires et contrats aides (hors Etat, coll.loc.)",
                u"Autres contrats (hors Etat, coll.loc.)",
                u"CDD (Etat, coll.loc.), hors contrats aidés",
                u"Stagiaires et contrats aidés (Etat, coll.loc.)",
                u"Autres contrats (Etat, coll.loc.)",
                ]
            ),
        )
    entity_class = Individus
    label = u"Statut détaillé mis en cohérence avec la profession"


class txtppb(Variable):
    column = EnumCol(
        enum = Enum(
            [
                u"Sans objet",
                u"Moins d'un mi-temps (50%)",
                u"Mi-temps (50%)",
                u"Entre 50 et 80%",
                u"80%",
                u"Plus de 80%",
                ],
            ),
        )
    entity_class = Individus
    label = u"Taux du temps partiel"


class chpub(Variable):
    column = EnumCol(
        enum = Enum(
            [
                u"Sans objet",
                u"Etat",
                u"Collectivités locales, HLM",
                u"Hôpitaux publics",
                u"Particulier",
                u"Entreprise publique (La Poste, EDF-GDF, etc.)",
                u"Entreprise privée, association",
                ],
            ),
        )
    entity_class = Individus
    label = u"Nature de l'employeur principal"


class cadre(Variable):
    column = BoolCol()
    entity_class = Individus
    label = u"Cadre salarié du privé"


#   zones apl and calibration


class tu99(Variable):
    column = EnumCol(
        enum = Enum(
            [
                u'Communes rurales',
                u'moins de 5 000 habitants',
                u'5 000 à 9 999 habitants',
                u'10 000 à 19 999 habitants',
                u'20 000 à 49 999 habitants',
                u'50 000 à 99 999 habitants',
                u'100 000 à 199 999 habitants',
                u'200 000 habitants ou plus (sauf agglomération parisienne)',
                u'agglomération parisienne'
                ],
            ),
        )
    entity_class = Menages
    label = u"Tranche d'unité urbaine"


class tau99(Variable):
    column = EnumCol(
        enum = Enum(
            [
                u'Communes hors aire urbaine',
                u'Aire urbaine de moins de 15 000 habitants',
                u'Aire urbaine de 15 000 à 19 999 habitants',
                u'Aire urbaine de 20 000 à 24 999 habitants',
                u'Aire urbaine de 25 000 à 34 999 habitants',
                u'Aire urbaine de 35 000 à 49 999 habitants',
                u'Aire urbaine de 50 000 à 99 999 habitants',
                u'Aire urbaine de 100 000 à 199 999 habitants',
                u'Aire urbaine de 200 000 à 499 999 habitants',
                u'Aire urbaine de 500 000 à 9 999 999 habitants',
                u'Aire urbaine de Paris'
                ]
            ),
        )
    label = u"tranche d'aire urbaine"
    entity_class = Menages


class reg(Variable):
    column = EnumCol(
        enum = Enum(
            [
                u'Ile-de-France',
                u'Champagne-Ardenne',
                u'Picardie',
                u'Haute-Normandie',
                u'Centre',
                u'Basse-Normandie',
                u'Bourgogne',
                u'Nord-Pas de Calais',
                u'Lorraine',
                u'Alsace',
                u'Franche-Comté',
                u'Pays de la Loire',
                u'Bretagne',
                u'Poitou-Charentes',
                u'Aquitaine',
                u'Midi-Pyrénées',
                u'Limousin',
                u'Rhône-Alpes',
                u'Auvergne',
                u'Languedoc-Roussillon',
                u"Provence-Alpes-Côte-d'Azur",
                u'Corse'
                ],
            ),
        )
    label = u"Région"
    entity_class = Menages


class pol99(Variable):
    column = EnumCol(
        enum = Enum(
            [
                u"Commune appartenant à un pôle urbain",
                u"Commune monopolarisée (appartenant à une couronne périurbaine)",
                u"Commune monopolarisée",
                u"Espace à dominante rurale"
                ]
            ),
        )
    label = u"Catégorie de la commune au sein du découpage en aires et espaces urbains"
    entity_class = Menages


class cstotpragr(Variable):
    column = EnumCol(
        enum = Enum(
            [
                u"Non renseignée",
                u"Agriculteurs exploitants",
                u"Artisans, commerçants, chefs d'entreprise",
                u"Cadres supérieurs",
                u"Professions intermédiaires",
                u"Employés",
                u"Ouvriers",
                u"Retraités",
                u"Autres inactifs"
                ],
            ),
        )
    label = u"catégorie socio_professionelle agrégée de la personne de référence"
    entity_class = Menages


class naf16pr(Variable):
    column = EnumCol(
        enum = Enum(
            [
                u"Sans objet",
                u"Non renseignée",
                u"Agriculture, sylviculture et pêche",
                u"Industries agricoles",
                u"Industries des biens de consommation",
                u"Industrie automobile",
                u"Industries des biens d'équipement",
                u"Industries des biens intermédiaires",
                u"Energie",
                u"Construction",
                u"Commerce et réparations",
                u"Transports",
                u"Activités financières",
                u"Activités immobilières",
                u"Services aux entreprises",
                u"Services aux particuliers",
                u"Education, santé, action sociale",
                u"Administrations"
                ],
            start = -1,  # 17 postes + 1 (-1: sans objet, 0: nonrenseigné)
            ),
        )
    entity_class = Menages
    label = u"activité économique de l'établissement de l'emploi principal actuel de la personne de référence"


class nafg17npr(Variable):
    column = EnumCol(
        enum = Enum(
            [
                u"Sans objet",
                u"Non renseignée",
                u"Agriculture, sylviculture et pêche",
                u"Industries extractives, énergie, eau, gestion des déchets et dépollution",
                u"Fabrication de denrées alimentaires, de boissons et de produits à base de tabac",
                u"Cokéfaction et raffinage",
                u"Fabrication d'équipements électriques, électroniques, informatiques ; fabrication de machines",
                u"Fabrication de matériels de transport",
                u"Fabrication d'autres produits industriels",
                u"Construction",
                u"Commerce ; réparation d'automobiles et de motocycles",
                u"Transports et entreposage",
                u"Hébergement et restauration",
                u"Information et communication",
                u"Activités financières et d'assurance",
                u"Activités immobilières",
                u"Activités scientifiques et techniques ; services administratifs et de soutien",
                u"Administration publique, enseignement, santé humaine et action sociale",
                u"Autres activités de services",
                ],
            start = -1,
            ),  # 17 postes + 1 (-1: sans objet, 0: nonrenseigné)
        )
    label = u"activité économique de l'établissement de l'emploi principal actuel de la personne de référence"
    entity_class = Menages


#    build_survey_column('typmen15', column = EnumCol(label = u"Type de ménage",
#                       entity_class = Menages,
#                       enum = Enum([u"Personne seule active",
#                                    u"Personne seule inactive",
#                                    u"Familles monoparentales, parent actif",
#                                    u"Familles monoparentales, parent inactif et au moins un enfant actif",
#                                    u"Familles monoparentales, tous inactifs",
#                                    u"Couples sans enfant, 1 actif",
#                                    u"Couples sans enfant, 2 actifs",
#                                    u"Couples sans enfant, tous inactifs",
#                                    u"Couples avec enfant, 1 membre du couple actif",
#                                    u"Couples avec enfant, 2 membres du couple actif",
#                                    u"Couples avec enfant, couple inactif et au moins un enfant actif",
#                                    u"Couples avec enfant, tous inactifs",
#                                    u"Autres ménages, 1 actif",
#                                    u"Autres ménages, 2 actifs ou plus",
#                                    u"Autres ménages, tous inactifs"],start = 1)))


class ageq(Variable):
    column = EnumCol(
        enum = Enum(
            [
                u"moins de 25 ans",
                u"25 à 29 ans",
                u"30 à 34 ans",
                u"35 à 39 ans",
                u"40 à 44 ans",
                u"45 à 49 ans",
                u"50 à 54 ans",
                u"55 à 59 ans",
                u"60 à 64 ans",
                u"65 à 69 ans",
                u"70 à 74 ans",
                u"75 à 79 ans",
                u"80 ans et plus",
                ],
            ),
        )
    label = u"âge quinquennal de la personne de référence"
    entity_class = Menages


#    build_survey_column_couple('nbinde, column = EnumCol(label = u"taille du ménage",
#                     entity_class = Menages,
#                     enum = Enum([u"Une personne",
#                                  u"Deux personnes",
#                                  u"Trois personnes",
#                                  u"Quatre personnes",
#                                  u"Cinq personnes",
#                                  u"Six personnes et plus"], start = 1))),


class ddipl(Variable):
    column = EnumCol(
        enum = Enum(
            [
                u"Non renseigné"
                u"Diplôme supérieur",
                u"Baccalauréat + 2 ans",
                u"Baccalauréat ou brevet professionnel ou autre diplôme de ce niveau",
                u"CAP, BEP ou autre diplôme de ce niveau",
                u"Brevet des collèges",
                u"Aucun diplôme ou CEP"
                ],
            start = 1,
            ),
        )
    entity_class = Individus


class act5(Variable):
    # 5 postes normalement TODO: check = 0
    column = EnumCol(
        enum = Enum([
            u"Salarié",
            u"Indépendant",
            u"Chômeur",
            u"Retraité",
            u"Inactif"],
            start = 1,
            ),
        )
    entity_class = Individus
    label = u"activité"
    # survey_only = True


# to remove

class champm(Variable):
    column = BoolCol(default = True)
    entity_class = Menages


class wprm(Variable):
    column = FloatCol(default = 1)
    entity_class = Menages
    label = u"Effectifs"


class wprm_init(Variable):
    column = FloatCol
    entity_class = Menages
    label = u"Effectifs"


class m_afeamam(Variable):
    column = IntCol
    entity_class = Menages


class m_agedm(Variable):
    column = IntCol
    entity_class = Menages


class m_clcam(Variable):
    column = IntCol
    entity_class = Menages


class m_colcam(Variable):
    column = IntCol
    entity_class = Menages


class m_mgamm(Variable):
    column = IntCol
    entity_class = Menages


class m_mgdomm(Variable):
    column = IntCol
    entity_class = Menages
