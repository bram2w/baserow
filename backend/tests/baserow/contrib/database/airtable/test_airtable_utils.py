import pytest

from baserow.contrib.database.airtable.utils import extract_share_id_from_url


def test_extract_share_id_from_url():
    with pytest.raises(ValueError):
        extract_share_id_from_url("test")

    assert (
        extract_share_id_from_url("https://airtable.com/shrxxxxxxxxxxxxxx")
        == "shrxxxxxxxxxxxxxx"
    )
    assert (
        extract_share_id_from_url("https://airtable.com/shrXxmp0WmqsTkFWTzv")
        == "shrXxmp0WmqsTkFWTzv"
    )
