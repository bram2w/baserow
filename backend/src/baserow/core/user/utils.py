import unicodedata


def normalize_email_address(email):
    """
    Normalizes an email address by stripping the whitespace, converting to lowercase
    and by normlizing the unicode.

    :param email: The email address that needs to be normalized.
    :type email: str
    :return: The normalized email address.
    :rtype: str
    """

    return unicodedata.normalize("NFKC", email).strip().lower()
