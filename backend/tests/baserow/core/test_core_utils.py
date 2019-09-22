from baserow.core.utils import extract_allowed, set_allowed_attrs


def test_extract_allowed():
    assert extract_allowed({
        'test_1': 'test_1',
        'test_2': 'test_2'
    }, ['test_1']) == {
        'test_1': 'test_1'
    }

    assert extract_allowed({}, ['test_1']) == {}
    assert extract_allowed({'test_1': 'test'}, ['test_2']) == {}
    assert extract_allowed({'test_1': 'test'}, []) == {}


def test_set_allowed_attrs():
    class Tmp(object):
        test_1 = None
        test_2 = None

    tmp1 = Tmp()
    tmp1 = set_allowed_attrs(
        {'test_1': 'test', 'test_2': 'test'},
        ['test_1'],
        tmp1
    )

    assert tmp1.test_1 == 'test'
    assert tmp1.test_2 is None
