# -*- coding: utf-8 -*-


from openfisca_france.model.base import *


class Deciles(Enum):
    __order__ = 'hors_champs decile_1 decile_2 decile_3 decile_4 decile_5 decile_6 decile_7 decile_8 decile_9 decile_10'  # Needed to keep the order in Python 2
    hors_champs = u"Hors champ"
    decile_1 = u"1er décile"
    decile_2 = u"2nd décile"
    decile_3 = u"3e décile"
    decile_4 = u"4e décile"
    decile_5 = u"5e décile"
    decile_6 = u"6e décile"
    decile_7 = u"7e décile"
    decile_8 = u"8e décile"
    decile_9 = u"9e décile"
    decile_10 = u"10e décile"
