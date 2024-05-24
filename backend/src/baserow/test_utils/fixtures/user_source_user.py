from types import SimpleNamespace

from baserow.core.user_sources.user_source_user import UserSourceUser


class UserSourceUserFixtures:
    def create_user_source_user(
        self,
        user=None,
        user_source=None,
        user_id=None,
        username=None,
        email=None,
        user_source_args=None,
        **kwargs,
    ) -> UserSourceUser:
        if user_id is None:
            user_id = self.fake.unique.random_int()

        if email is None:
            email = self.fake.unique.email()

        if username is None:
            username = self.fake.name()

        if user_source is None:
            user_source = self.create_user_source_with_first_type(
                **(user_source_args or {})
            )

        user = SimpleNamespace(username=username, email=email, id=user_id)
        return UserSourceUser(user_source, user, user_id, username, email, **kwargs)
