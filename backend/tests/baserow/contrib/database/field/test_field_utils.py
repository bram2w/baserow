from baserow.contrib.database.fields.utils import get_field_id_from_field_key


def test_get_field_id_from_field_key_strict():
    assert get_field_id_from_field_key("not") is None
    assert get_field_id_from_field_key("field_1") == 1
    assert get_field_id_from_field_key("field_22") == 22
    assert get_field_id_from_field_key("is") is None
    assert get_field_id_from_field_key("1") == 1
    assert get_field_id_from_field_key(1) == 1
    assert get_field_id_from_field_key("f1") is None

    assert get_field_id_from_field_key("f1", False) == 1
    assert get_field_id_from_field_key("1", False) == 1
    assert get_field_id_from_field_key(1, False) == 1
    assert get_field_id_from_field_key("field_1", False) == 1
    assert get_field_id_from_field_key("field1", False) == 1
