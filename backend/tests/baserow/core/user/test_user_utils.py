from baserow.core.user.utils import normalize_email_address


def test_normalize_email_address():
    assert normalize_email_address(" test@test.nl ") == "test@test.nl"
    assert normalize_email_address("TeST@TEST.nl") == "test@test.nl"
