from baserow_premium.export.utils import get_unique_name, safe_xml_tag_name, to_xml


def test_get_unique_name():
    assert get_unique_name({"name": ""}, "name") == "name_2"
    assert get_unique_name({"name": ""}, "name", separator=" ") == "name 2"
    assert get_unique_name({"name": "", "name_2": "", "name_4": ""}, "name") == "name_3"
    assert (
        get_unique_name({"name": "", "name_2": "", "name_3": "", "name_4": ""}, "name")
        == "name_5"
    )
    assert (
        get_unique_name({"name": "", "name_2": "", "name_3": "", "name_4": ""}, "else")
        == "else"
    )


def test_safe_xml_tag_name():
    assert safe_xml_tag_name("name") == "name"
    assert safe_xml_tag_name("/name<>") == "name"
    assert safe_xml_tag_name("/name<>test") == "name-test"
    assert safe_xml_tag_name("Test 1 // <> @#$$%&%*$^%&%") == "Test-1"
    assert safe_xml_tag_name("123") == "tag-123"
    assert safe_xml_tag_name("123", "prefix-") == "prefix-123"
    assert safe_xml_tag_name("/", "prefix-", "empty") == "empty"


def test_to_xml():
    xml = to_xml(
        {
            "name": "<value>",
            "name2": ["<value1>", "value2"],
            "name3": {"<key1>": "<value1>", "key2": "value2"},
        }
    )
    assert (
        xml == "<name>&lt;value&gt;</name><name2><item>&lt;value1&gt;</item>"
        "<item>value2</item></name2><name3><<key1>>&lt;value1&gt;</<key1>>"
        "<key2>value2</key2></name3>"
    )
