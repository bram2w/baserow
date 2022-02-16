import pytest

from io import BytesIO
from unittest.mock import MagicMock

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
    split_comma_separated_string,
    remove_invalid_surrogate_characters,
    grouper,
    Progress,
    ChildProgressBuilder,
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


def test_split_comma_separated_string():
    assert split_comma_separated_string('A,"B , C",D') == ["A", "B , C", "D"]
    assert split_comma_separated_string('A,\\"B,C') == ["A", '"B', "C"]
    assert split_comma_separated_string('A,\\"B,C\\,D') == ["A", '"B', "C,D"]


def test_remove_invalid_surrogate_characters():
    assert remove_invalid_surrogate_characters(b"test\uD83Dtest") == "testtest"


def test_grouper():
    assert list(grouper(2, [1, 2, 3, 4, 5])) == [(1, 2), (3, 4), (5,)]

    def g():
        for i in range(0, 10):
            yield i

    assert list(grouper(3, g())) == [(0, 1, 2), (3, 4, 5), (6, 7, 8), (9,)]


def test_progress():
    mock_event = MagicMock()

    progress = Progress(100)
    progress.register_updated_event(mock_event)
    progress.increment(state="State 1")

    assert mock_event.call_count == 1
    args = mock_event.call_args
    assert args[0][0] == 1
    assert args[0][1] == "State 1"

    progress.increment(
        by=10,
        state="State 2",
    )

    assert mock_event.call_count == 2
    args = mock_event.call_args
    assert args[0][0] == 11
    assert args[0][1] == "State 2"

    progress.increment(by=89, state="State 3")

    assert mock_event.call_count == 3
    args = mock_event.call_args
    assert args[0][0] == 100
    assert args[0][1] == "State 3"


def test_nested_progress():
    mock_event = MagicMock()

    progress = Progress(100)
    progress.register_updated_event(mock_event)

    sub_progress_1 = Progress(1, parent=progress, represents_progress=20)
    sub_progress_1.increment(1)

    assert mock_event.call_count == 1
    args = mock_event.call_args
    assert args[0][0] == 20
    assert args[0][1] is None

    sub_progress_2 = progress.create_child(20, 5 * 120)
    for i in range(0, 5):
        for i2 in range(0, 100):
            sub_progress_2.increment()
        sub_progress_2.increment(by=20, state="Sub progress 2 second")

    args = mock_event.call_args
    assert args[0][0] == 40
    assert args[0][1] is None

    sub_progress_3_builder = progress.create_child_builder(40)
    sub_progress_3 = ChildProgressBuilder.build(sub_progress_3_builder, 100)

    sub_progress_3_1 = sub_progress_3.create_child(10, 4)
    sub_progress_3_1.increment(by=2)
    sub_progress_3_1.increment()
    sub_progress_3_1.increment()

    args = mock_event.call_args
    assert args[0][0] == 44
    assert args[0][1] is None

    sub_progress_3_2 = sub_progress_3.create_child(10, 11)
    for i in range(0, 11):
        sub_progress_3_2.increment()

    args = mock_event.call_args
    assert args[0][0] == 48
    assert args[0][1] is None

    sub_progress_3.create_child(10, 0)
    args = mock_event.call_args
    assert args[0][0] == 52
    assert args[0][1] is None

    sub_progress_3_4_builder = sub_progress_3.create_child_builder(10)
    ChildProgressBuilder.build(sub_progress_3_4_builder, 0)
    args = mock_event.call_args
    assert args[0][0] == 56
    assert args[0][1] is None

    sub_progress_3_5 = sub_progress_3.create_child(55, 5 * 120)
    for i in range(0, 5):
        sub_progress_3_5_1 = sub_progress_3_5.create_child(100, 100)
        for i2 in range(0, 100):
            sub_progress_3_5_1.increment()
        sub_progress_3_5.increment(20)

    args = mock_event.call_args
    assert args[0][0] == 78
    assert args[0][1] is None

    sub_progress_3_6 = sub_progress_3.create_child(5, 1)
    sub_progress_3_6.increment()

    assert mock_event.call_count == 52
    args = mock_event.call_args
    assert args[0][0] == 80
    assert args[0][1] is None


def test_progress_higher_total_than_parent():
    mock_event = MagicMock()

    progress = Progress(100)
    progress.register_updated_event(mock_event)

    sub_progress = progress.create_child(100, 1000)
    sub_progress.increment()

    assert mock_event.call_count == 1
    args = mock_event.call_args
    assert args[0][0] == 1
    assert args[0][1] is None

    sub_progress.increment()

    assert mock_event.call_count == 1
    args = mock_event.call_args
    assert args[0][0] == 1
    assert args[0][1] is None

    sub_progress.increment(8)

    assert mock_event.call_count == 1
    args = mock_event.call_args
    assert args[0][0] == 1
    assert args[0][1] is None

    sub_progress.increment()

    assert mock_event.call_count == 2
    args = mock_event.call_args
    assert args[0][0] == 2
    assert args[0][1] is None
