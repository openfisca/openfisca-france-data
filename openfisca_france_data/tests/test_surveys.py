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


# TODO: modify and move to openfisca_survey_manager

import os


from openfisca_france_data.collection_builders.erfs_collection_builder import build_empty_erfs_survey_collection
from openfisca_survey_manager.surveys import Survey, SurveyCollection


current_dir = os.path.dirname(os.path.realpath(__file__))


def test_survey_dump_load():
    erfs_survey_collection = build_empty_erfs_survey_collection()
    erfs_survey = erfs_survey_collection.surveys['erfs_2006']
    saved_fake_survey_file_path = os.path.join(current_dir, 'saved_fake_survey')
    erfs_survey.dump(saved_fake_survey_file_path)
    erfs_survey_bis = Survey.load(saved_fake_survey_file_path)
    assert erfs_survey.to_json() == erfs_survey_bis.to_json()


def test_survey_collection_dump_load():
    erfs_survey_collection = build_empty_erfs_survey_collection()
    saved_fake_survey_collection_file_path = os.path.join(current_dir, 'saved_fake_survey_collection')
    erfs_survey_collection.dump(saved_fake_survey_collection_file_path)
    erfs_survey_collection_bis = SurveyCollection.load(saved_fake_survey_collection_file_path)
    assert erfs_survey_collection.to_json().keys() == erfs_survey_collection_bis.to_json().keys()
    assert erfs_survey_collection.to_json().get('name') == erfs_survey_collection_bis.to_json().get('name')
    assert erfs_survey_collection.to_json() == erfs_survey_collection_bis.to_json()


def test_find_tables():
    erfs_survey_collection = SurveyCollection.load(collection = "erfs")
    erfs_survey = erfs_survey_collection.surveys['erfs_2006']
    tables = erfs_survey.find_tables(variable = "ident")
    print tables


if __name__ == '__main__':
    import logging
    log = logging.getLogger(__name__)
    import sys
    logging.basicConfig(level = logging.INFO, stream = sys.stdout)
#    test_survey_dump_load()
#    test_survey_collection_dump_load()
    test_find_tables()
