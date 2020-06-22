from baserow.core.utils import (
    extract_allowed, set_allowed_attrs, to_pascal_case, to_snake_case,
    remove_special_characters, dict_to_object
)


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


def test_to_pascal_case():
    assert to_pascal_case('This is a TEST') == 'ThisIsATest'


def test_to_snake_case():
    assert to_snake_case('This is a TEST') == 'this_is_a_test'
    assert to_snake_case('This  is a test') == 'this_is_a_test'


def test_remove_special_characters():
    assert remove_special_characters('Test @#$% .. ;;') == 'Test'
    assert remove_special_characters('Test @#$% ..', remove_spaces=False) == 'Test  '


def test_dict_to_object():
    d1 = {'a': 'b', 'c': 'd'}
    o1 = dict_to_object(d1)

    assert o1.a == 'b'
    assert o1.c == 'd'
    assert not hasattr(o1, 'b')
    assert not hasattr(o1, 'd')
    assert not hasattr(o1, 'e')
