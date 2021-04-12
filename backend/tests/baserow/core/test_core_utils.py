from io import BytesIO
import pytest

from baserow.core.utils import (
    extract_allowed,
    set_allowed_attrs,
    to_pascal_case,
    to_snake_case,
    remove_special_characters,
    dict_to_object,
    random_string,
    sha256_hash,
    stream_size,
    truncate_middle,
)


def test_extract_allowed():
    assert extract_allowed({"test_1": "test_1", "test_2": "test_2"}, ["test_1"]) == {
        "test_1": "test_1"
    }

    assert extract_allowed({}, ["test_1"]) == {}
    assert extract_allowed({"test_1": "test"}, ["test_2"]) == {}
    assert extract_allowed({"test_1": "test"}, []) == {}


def test_set_allowed_attrs():
    class Tmp(object):
        test_1 = None
        test_2 = None

    tmp1 = Tmp()
    tmp1 = set_allowed_attrs({"test_1": "test", "test_2": "test"}, ["test_1"], tmp1)

    assert tmp1.test_1 == "test"
    assert tmp1.test_2 is None


def test_to_pascal_case():
    assert to_pascal_case("This is a TEST") == "ThisIsATest"


def test_to_snake_case():
    assert to_snake_case("This is a TEST") == "this_is_a_test"
    assert to_snake_case("This  is a test") == "this_is_a_test"


def test_remove_special_characters():
    assert remove_special_characters("Test @#$% .. ;;") == "Test"
    assert remove_special_characters("Test @#$% ..", remove_spaces=False) == "Test  "


def test_dict_to_object():
    d1 = {"a": "b", "c": "d"}
    o1 = dict_to_object(d1)

    assert o1.a == "b"
    assert o1.c == "d"
    assert not hasattr(o1, "b")
    assert not hasattr(o1, "d")
    assert not hasattr(o1, "e")


def test_random_string():
    assert len(random_string(32)) == 32
    assert random_string(32) != random_string(32)


def test_sha256_hash():
    assert sha256_hash(BytesIO(b"test")) == (
        "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08"
    )
    assert sha256_hash(BytesIO(b"Hello World")) == (
        "a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e"
    )


def test_stream_size():
    assert stream_size(BytesIO(b"test")) == 4


def test_truncate_middle():
    assert truncate_middle("testtesttest", 13) == "testtesttest"
    assert truncate_middle("testtesttest", 12) == "testtesttest"
    assert truncate_middle("testabcdecho", 11) == "test...echo"
    assert truncate_middle("testabcdecho", 10) == "test...cho"
    assert truncate_middle("testabcdecho", 9) == "tes...cho"
    assert truncate_middle("testabcdecho", 8) == "tes...ho"
    assert truncate_middle("testabcdecho", 7) == "te...ho"
    assert truncate_middle("testabcdecho", 6) == "te...o"
    assert truncate_middle("testabcdecho", 5) == "t...o"
    assert truncate_middle("testabcdecho", 4) == "t..."

    with pytest.raises(ValueError):
        truncate_middle("testtesttest", 3) == "..."
