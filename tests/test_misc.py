from openfisca_france_data.utils import build_cerfa_fields_by_column_name  # type: ignore


def test_build_cerfa_fields_by_column_name():
    cerfa_fields_by_column_name_2006 = build_cerfa_fields_by_column_name(2006, [6, 7, 8])
    cerfa_fields_by_column_name_2009 = build_cerfa_fields_by_column_name(2006, [6, 7, 8])
    cerfa_fields_by_column_name_2012 = build_cerfa_fields_by_column_name(2012, [6, 7, 8])

    assert cerfa_fields_by_column_name_2006['f6ss'] == ['f6ss', 'f6st', 'f6su']
    assert cerfa_fields_by_column_name_2009['f6ss'] == ['f6ss', 'f6st', 'f6su']
    assert cerfa_fields_by_column_name_2012['f6ss'] == ['f6ss', 'f6st', 'f6su']

    # TODO check this
    # assert cerfa_fields_by_column_name_2009.get('f7vw') is None, "2009 f7vw = {} is not None".format(
    #     cerfa_fields_by_column_name_2009.get('f7vw'))
    assert cerfa_fields_by_column_name_2012.get('f7vw') == ['f7vw']
