from datetime import datetime

import pytest
from freezegun import freeze_time
from rest_framework_simplejwt.tokens import RefreshToken

from baserow.core.models import BlacklistedToken
from baserow.core.user.handler import UserHandler
from baserow.core.user.tasks import flush_expired_tokens


@pytest.mark.django_db
def test_flush_expired_tokens(data_fixture):
    with freeze_time("2020-01-01 12:00"):
        user = data_fixture.create_user(
            email="test@test.nl", password="password", first_name="Test1"
        )
        token_1 = str(RefreshToken.for_user(user))
        UserHandler().blacklist_refresh_token(token_1, datetime(2020, 1, 1, 13, 00))
        token_2 = str(RefreshToken.for_user(user))
        UserHandler().blacklist_refresh_token(token_2, datetime(2020, 1, 2, 13, 00))
        token_3 = str(RefreshToken.for_user(user))
        UserHandler().blacklist_refresh_token(token_3, datetime(2020, 1, 9, 13, 00))
        token_4 = str(RefreshToken.for_user(user))
        UserHandler().blacklist_refresh_token(token_4, datetime(2020, 1, 10, 13, 00))
        token_5 = str(RefreshToken.for_user(user))
        UserHandler().blacklist_refresh_token(token_5, datetime(2020, 1, 11, 13, 00))

    assert BlacklistedToken.objects.all().count() == 5

    with freeze_time("2020-01-10 12:01"):
        flush_expired_tokens()

    blacklisted = BlacklistedToken.objects.all()
    assert len(blacklisted) == 2

    assert UserHandler().refresh_token_is_blacklisted(token_1) is False
    assert UserHandler().refresh_token_is_blacklisted(token_2) is False
    assert UserHandler().refresh_token_is_blacklisted(token_3) is False
    assert UserHandler().refresh_token_is_blacklisted(token_4) is True
    assert UserHandler().refresh_token_is_blacklisted(token_5) is True
