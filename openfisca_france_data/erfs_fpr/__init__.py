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


def get_of2erf(year=None):
    of2erf = dict()
    of2erf["csg"] = "csgim"  # imposable, et "csgdm", déductible
#of2erf["csgd"] = "csgdm"
    of2erf["crds"] = "crdsm"
    of2erf["irpp"] = "zimpom"
    of2erf["ppe"] = "m_ppem"
    of2erf["af"] =  "m_afm"
#af_base
#af_majo
#af_forf
    of2erf["cf"] = "m_cfm"
    of2erf["paje_base"] = "m_pajem"
    of2erf["paje_nais"] = "m_naism"
    of2erf["paje_clca"] = ""
    of2erf["paje_clmg"] = ""
    of2erf["ars"] = "m_arsm"
    of2erf["aeeh"] = "m_aesm" # allocation d'éducation spéciale
    of2erf["asf"] = "m_asfm"
    of2erf["aspa"] = "m_minvm"
    of2erf["aah"] = "m_aahm"
    of2erf["caah"] = "m_caahm"
#of2erf["rmi"] = "m_rmim"
    of2erf["rsa"] = "m_rsam"
    of2erf["rsa_act"] = ""
    of2erf["aefa"] = "m_crmim"
    of2erf["api"] = "m_apim"
    of2erf["logt"] = "logtm"
    of2erf["alf"] = "m_alfm"
    of2erf["als"] = "m_alsm"
    of2erf["apl"] = "m_aplm"
    return of2erf


def get_erf2of():
    of2erf = get_of2erf()
    erf2of = dict((v,k) for k, v in of2erf.iteritems())
    return erf2of
