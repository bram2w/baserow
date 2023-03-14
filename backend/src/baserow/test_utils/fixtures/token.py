from baserow.contrib.database.tokens.models import Token
from baserow.core.utils import random_string


class TokenFixtures:
    def create_token(self, **kwargs):
        if "key" not in kwargs:
            kwargs["key"] = random_string(32)

        if "name" not in kwargs:
            kwargs["name"] = self.fake.name()

        if "user" not in kwargs:
            kwargs["user"] = self.create_user()

        if "workspace" not in kwargs:
            kwargs["workspace"] = self.create_workspace(user=kwargs["user"])

        return Token.objects.create(**kwargs)
