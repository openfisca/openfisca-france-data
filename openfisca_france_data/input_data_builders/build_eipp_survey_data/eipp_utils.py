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

import os

from numpy import array
from pandas import ExcelFile


current_dir = os.path.dirname(os.path.realpath(__file__))
variables_corresp = os.path.join(current_dir, 'correspondances_eipp_OF.xlsx')
print variables_corresp


def build_ipp2of_variables():
    '''
    Création du dictionnaire dont les clefs sont les noms des variables IPP
    et les arguments ceux des variables OF
    '''
    def _dic_corresp(onglet):
        names = ExcelFile(variables_corresp).parse(onglet)
        return dict(array(names.loc[names['equivalence'].isin([1, 5, 8]), ['Var_TAXIPP', 'Var_OF']]))

    ipp2of_input_variables = _dic_corresp('input')
    ipp2of_output_variables = _dic_corresp('output')
    return ipp2of_input_variables, ipp2of_output_variables


def build_input_OF(data, ipp2of_input_variables, tax_benefit_system):
    print 'On commence buid_input'

    def _qui(data, entity):
        qui = "qui" + entity
        print 'qui', qui
        #idi = "id" + entity
        data[qui] = 2   # TODO incrémenter les pac du foyer/enfats des familles/autres personnes des ménages
        data.loc[data['decl'] == 1, qui] = 0
        data.loc[data['conj'] == 1, qui] = 1
        if entity == "men":
            data.loc[data['concu'] == 1, qui] = 1
        #j = 2
#        while any(data.duplicated([qui, idi])):
#            data.loc[data.duplicated([qui, idi]), qui] = j + 1
#            j += 1
        return data[qui]

    def _so(data):  # TODO: mettre directement la variable de EE au lieu de passer par TAXIPP
        data["so"] = 0
        data.loc[data['proprio_empr'] == 1, 'so'] = 1
        data.loc[data['proprio'] == 1, 'so'] = 2
        data.loc[data['locat'] == 1, 'so'] = 4
        data.loc[data['loge'] == 1, 'so'] = 6
        return data['so']

    def _compl(var):
        var = 1 - var
        var = var.astype(int)
        return var

# TODO: refaire cette fonction avec la nouvelle propagation des variables entre les membres d'une entité
# (cf. work at Etalab)

#    def _count_by_entity(data, var, entity, bornes):
#        ''' Compte le nombre de 'var compris entre les 'bornes' au sein de l''entity' '''
#        id = 'id' + entity
#        qui = 'qui' + entity
#        data.index = data[id]
#        cond = (bornes[0] <= data[var])*(data[var] <= bornes[1])*(data[qui] > 1)
#        print cond
#        col = DataFrame(data.loc[cond, :].groupby(id).size(), index = data.index).fillna(0)
#        col.reset_index()
#        return col
#
#    def _count_enf(data):
#        data["f7ea"] = _count_by_entity(data, 'age', 'foy', [11, 14])  # nb enfants ff au collège (11-14)
#        data["f7ec"] = _count_by_entity(data, 'age', 'foy', [15, 17])  # #nb enfants ff au lycée  15-17
#        data["f7ef"] = _count_by_entity(data, 'age', 'foy', [18, 99])  # nb enfants ff enseignement sup > 17
#        data = data.drop(["nenf1113", "nenf1415", "nenf1617", "nenfmaj1819", "nenfmaj20", "nenfmaj21plus", "nenfnaiss",
#                          "nenf02", "nenf35", "nenf610"], axis = 1)
#        data.index = range(len(data))
#        return data

    def _workstate(data):
        # TODO: titc should be filled in to deal with civil servant
        data['chpub'] = 0
        data.loc[data['public'] == 1, 'chpub'] = 1
        data.loc[data['public'] == 0, 'chpub'] = 6
        # Activité : [0'Actif occupé',  1'Chômeur', 2'Étudiant, élève', 3'Retraité', 4'Autre inactif']), default = 4)
        # act5 : [0"Salarié",1"Indépendant",2"Chômeur",3"Retraité",4"Inactif"] => pas utilisé ?

        data.loc[data['fi'] == 1, 'activite'] = 0
        data.loc[data['fi'] == 2, 'activite'] = 1
        data.loc[data['fi'] == 3, 'activite'] = 2
        data.loc[data['fi'] == 4, 'activite'] = 0  # TODO: Les militaires
        data.loc[data['fi'] == 5, 'activite'] = 3  # TODO: cf. gestion de l'homogénéisation EE de IPP (les retraités semblent être inclus dans la catégorie inactif)
        data.loc[data['fi'] == 6, 'activite'] = 4

        data['statut'] = 8
        data.loc[data['public'] == 1, 'statut'] = 11
        # [0"Non renseigné/non pertinent",1"Exonéré",2"Taux réduit",3"Taux plein"]
        data['taux_csg_remplacement'] = 3
        data.loc[data['csg_exo'] == 1, 'taux_csg_remplacement'] = 1
        data.loc[data['csg_part'] == 1, 'taux_csg_remplacement'] = 2
        data = data.drop(['csg_tout', 'csg_exo', 'csg_part'], axis = 1)
        # data['ebic_impv'] = 20000
        data['exposition_accident'] = 0
        return data

    data['nbj'] = 0  # TODO: rajouter Nombre d'enfants majeurs célibataires sans enfant
    data['nbh'] = 4  # TODO: rajouter Nombre d'enfants à charge en résidence alternée, non mariés de moins de 18 ans au 1er janvier de l'année n-1, ou nés en n-1 ou handicapés quel que soit l'âge
    data['stat_prof'] = 0  # TODO: rajouter le statut professionnel dans eipp

    def _var_to_ppe(data):
        data['ppe_du_sa'] = 0
        data.loc[data['stat_prof'] == 0, 'ppe_du_sa'] = data.loc[data['stat_prof'] == 0, 'nbh']
        data['ppe_du_ns'] = 0
        data.loc[data['stat_prof'] == 1, 'ppe_du_ns'] = data.loc[data['stat_prof'] == 1, 'nbj']

        data['ppe_tp_sa'] = 0
        data.loc[(data['stat_prof'] == 0) & (data['nbh'] >= 151.67 * 12), 'ppe_tp_sa'] = 1
        data['ppe_tp_ns'] = 0
        data.loc[(data['stat_prof'] == 1) & (data['nbj'] >= 360), 'ppe_tp_ns'] = 1
        return data

    data['inactif'] = 0 #TODO:

    def _var_to_pfam(data):
        data.loc[(data['activite'].isin([3, 4, 5, 6])), 'inactif'] = 1
        data.loc[(data['activite'] == 1) & (data['chom_irpp'] == 0), 'inactif'] = 1
        data.loc[(data['activite'] == 0) & (data['sal_irpp'] == 0), 'inactif'] = 1
        data['partiel1'] = 0
        data.loc[(data['nbh'] / 12 <= 77) & (data['nbh'] / 12 > 0), 'partiel1'] = 1
        data['partiel2'] = 0
        data.loc[(data['nbh'] / 12 <= 151) & (data['nbh'] / 12 > 77), 'partiel2'] = 1
        return data

    print 'avant', list(data.columns.values)
    data.rename(columns = ipp2of_input_variables, inplace = True)
    print 'après', list(data.columns.values)

    print 'On a fait rename'

    data['quifoy'] = _qui(data, 'foy')
    print 'test'
    min_idfoy = data["idfoy"].min()
    if min_idfoy > 0:
        data["idfoy"] -= min_idfoy
    data['quimen'] = _qui(data, 'men')
    min_idmen = data["idmen"].min()
    if min_idmen > 0:
        data["idmen"] -= min_idmen
    min_idfam = data["idfam"].min()
    if min_idfam > 0:
        data["idfam"] -= min_idfam

    data["idfam"] = data["idmen"]  # TODO: rajouter les familles dans TAXIPP
    data["quifam"] = data['quimen']

    # print data[['idfoy','idmen', 'quimen','quifoy', 'decl', 'conj', 'con2']].to_string()
    data['so'] = _so(data)
#    data = _count_enf(data)
    data = _workstate(data)
    #data["caseN"] = _compl(data["caseN"]) #TODO: faire une fonction pour gérer l'imputation de cette case
    data = _var_to_ppe(data)
    data = _var_to_pfam(data)
    data['invalide'] = 0

    print 'On va dropper'

    variables_to_drop = [
        variable
        for variable in data.columns
        if variable not in tax_benefit_system.column_by_name
        ]
    print 'data.columns', data.columns
    print 'tax_benefit_system.column_by_name', tax_benefit_system.column_by_name
    print 'variables_to_drop', variables_to_drop
    #print data.iloc[44:]
  #  data.drop(variables_to_drop, axis = 1, inplace = True)
    print 'youpi on a droppé'

#    data.rename(columns = {"id_conj" : "conj"}, inplace = True)
    data['age_en_mois'] = data['age'] * 12
    return data
