# -*- coding: utf-8 -*-


from .base import * # noqa  analysis:ignore


class idmen_original(Variable):
    column = IntCol
    entity = Menage
    label = u"Identifiant ménage, lien avec l'identifiant dérivé de l'ERF"


class idfoy_original(Variable):
    column = IntCol
    entity = FoyerFiscal
    label = u"Identifiant foyer, lien avec l'identifiant dérivé de l'ERF"


class idfam_original(Variable):
    column = IntCol
    entity = Famille
    label = u"Identifiant famille, lien avec l'identifiant dérivé de l'ERF"


# class txtppb(Variable):
#     column = EnumCol(
#         enum = Enum(
#             [
#                 u"Sans objet",
#                 u"Moins d'un mi-temps (50%)",
#                 u"Mi-temps (50%)",
#                 u"Entre 50 et 80%",
#                 u"80%",
#                 u"Plus de 80%",
#                 ],
#             ),
#         )
#     entity = Individu
#     label = u"Taux du temps partiel"

# #   zones apl and calibration


# class tu99(Variable):
#     column = EnumCol(
#         enum = Enum(
#             [
#                 u'Communes rurales',
#                 u'moins de 5 000 habitants',
#                 u'5 000 à 9 999 habitants',
#                 u'10 000 à 19 999 habitants',
#                 u'20 000 à 49 999 habitants',
#                 u'50 000 à 99 999 habitants',
#                 u'100 000 à 199 999 habitants',
#                 u'200 000 habitants ou plus (sauf agglomération parisienne)',
#                 u'agglomération parisienne'
#                 ],
#             ),
#         )
#     entity = Menage
#     label = u"Tranche d'unité urbaine"


# class tau99(Variable):
#     column = EnumCol(
#         enum = Enum(
#             [
#                 u'Communes hors aire urbaine',
#                 u'Aire urbaine de moins de 15 000 habitants',
#                 u'Aire urbaine de 15 000 à 19 999 habitants',
#                 u'Aire urbaine de 20 000 à 24 999 habitants',
#                 u'Aire urbaine de 25 000 à 34 999 habitants',
#                 u'Aire urbaine de 35 000 à 49 999 habitants',
#                 u'Aire urbaine de 50 000 à 99 999 habitants',
#                 u'Aire urbaine de 100 000 à 199 999 habitants',
#                 u'Aire urbaine de 200 000 à 499 999 habitants',
#                 u'Aire urbaine de 500 000 à 9 999 999 habitants',
#                 u'Aire urbaine de Paris'
#                 ]
#             ),
#         )
#     label = u"tranche d'aire urbaine"
#     entity = Menage


# class reg(Variable):
#     column = EnumCol(
#         enum = Enum(
#             [
#                 u'Ile-de-France',
#                 u'Champagne-Ardenne',
#                 u'Picardie',
#                 u'Haute-Normandie',
#                 u'Centre',
#                 u'Basse-Normandie',
#                 u'Bourgogne',
#                 u'Nord-Pas de Calais',
#                 u'Lorraine',
#                 u'Alsace',
#                 u'Franche-Comté',
#                 u'Pays de la Loire',
#                 u'Bretagne',
#                 u'Poitou-Charentes',
#                 u'Aquitaine',
#                 u'Midi-Pyrénées',
#                 u'Limousin',
#                 u'Rhône-Alpes',
#                 u'Auvergne',
#                 u'Languedoc-Roussillon',
#                 u"Provence-Alpes-Côte-d'Azur",
#                 u'Corse'
#                 ],
#             ),
#         )
#     label = u"Région"
#     entity = Menage


# class pol99(Variable):
#     column = EnumCol(
#         enum = Enum(
#             [
#                 u"Commune appartenant à un pôle urbain",
#                 u"Commune monopolarisée (appartenant à une couronne périurbaine)",
#                 u"Commune monopolarisée",
#                 u"Espace à dominante rurale"
#                 ]
#             ),
#         )
#     label = u"Catégorie de la commune au sein du découpage en aires et espaces urbains"
#     entity = Menage


# class cstotpragr(Variable):
#     column = EnumCol(
#         enum = Enum(
#             [
#                 u"Non renseignée",
#                 u"Agriculteurs exploitants",
#                 u"Artisans, commerçants, chefs d'entreprise",
#                 u"Cadres supérieurs",
#                 u"Professions intermédiaires",
#                 u"Employés",
#                 u"Ouvriers",
#                 u"Retraités",
#                 u"Autres inactifs"
#                 ],
#             ),
#         )
#     label = u"catégorie socio_professionelle agrégée de la personne de référence"
#     entity = Menage


# class naf16pr(Variable):
#     column = EnumCol(
#         enum = Enum(
#             [
#                 u"Sans objet",
#                 u"Non renseignée",
#                 u"Agriculture, sylviculture et pêche",
#                 u"Industries agricoles",
#                 u"Industries des biens de consommation",
#                 u"Industrie automobile",
#                 u"Industries des biens d'équipement",
#                 u"Industries des biens intermédiaires",
#                 u"Energie",
#                 u"Construction",
#                 u"Commerce et réparations",
#                 u"Transports",
#                 u"Activités financières",
#                 u"Activités immobilières",
#                 u"Services aux entreprises",
#                 u"Services aux particuliers",
#                 u"Education, santé, action sociale",
#                 u"Administrations"
#                 ],
#             start = -1,  # 17 postes + 1 (-1: sans objet, 0: nonrenseigné)
#             ),
#         )
#     entity = Menage
#     label = u"activité économique de l'établissement de l'emploi principal actuel de la personne de référence"


# class nafg17npr(Variable):
#     column = EnumCol(
#         enum = Enum(
#             [
#                 u"Sans objet",
#                 u"Non renseignée",
#                 u"Agriculture, sylviculture et pêche",
#                 u"Industries extractives, énergie, eau, gestion des déchets et dépollution",
#                 u"Fabrication de denrées alimentaires, de boissons et de produits à base de tabac",
#                 u"Cokéfaction et raffinage",
#                 u"Fabrication d'équipements électriques, électroniques, informatiques ; fabrication de machines",
#                 u"Fabrication de matériels de transport",
#                 u"Fabrication d'autres produits industriels",
#                 u"Construction",
#                 u"Commerce ; réparation d'automobiles et de motocycles",
#                 u"Transports et entreposage",
#                 u"Hébergement et restauration",
#                 u"Information et communication",
#                 u"Activités financières et d'assurance",
#                 u"Activités immobilières",
#                 u"Activités scientifiques et techniques ; services administratifs et de soutien",
#                 u"Administration publique, enseignement, santé humaine et action sociale",
#                 u"Autres activités de services",
#                 ],
#             start = -1,
#             ),  # 17 postes + 1 (-1: sans objet, 0: nonrenseigné)
#         )
#     label = u"activité économique de l'établissement de l'emploi principal actuel de la personne de référence"
#     entity = Menage


# class ddipl(Variable):
#     column = EnumCol(
#         enum = Enum(
#             [
#                 u"Non renseigné"
#                 u"Diplôme supérieur",
#                 u"Baccalauréat + 2 ans",
#                 u"Baccalauréat ou brevet professionnel ou autre diplôme de ce niveau",
#                 u"CAP, BEP ou autre diplôme de ce niveau",
#                 u"Brevet des collèges",
#                 u"Aucun diplôme ou CEP"
#                 ],
#             start = 1,
#             ),
#         )
#     entity = Individu


class champm(Variable):
    column = BoolCol(default = True)
    entity = Menage


class wprm(Variable):
    column = FloatCol(default = 1)
    entity = Menage
    label = u"Effectifs"


class wprm_init(Variable):
    column = FloatCol
    entity = Menage
    label = u"Effectifs"
