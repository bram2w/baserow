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
        extract_share_id_from_url("https://airtable.com/appxxxxxxxxxxxxxx")
        == "appxxxxxxxxxxxxxx"
    )
    assert (
        extract_share_id_from_url("https://airtable.com/shrXxmp0WmqsTkFWTzv")
        == "shrXxmp0WmqsTkFWTzv"
    )

    long_share_id = (
        "shr22aXe5Hj32sPJB/tblU0bav59SSEyOkU/"
        "viwyUDJYyQPYuFj1F?blocks=bipEYER8Qq7fLoPbr"
    )
    assert (
        extract_share_id_from_url(f"https://airtable.com/{long_share_id}")
        == long_share_id
    )
