from baserow.core.models import Group, GroupUser, GroupInvitation


class GroupFixtures:
    def create_group(self, **kwargs):
        user = kwargs.pop("user", None)
        users = kwargs.pop("users", [])

        if user:
            users.insert(0, user)

        if "name" not in kwargs:
            kwargs["name"] = self.fake.name()

        group = Group.objects.create(**kwargs)

        for user in users:
            self.create_user_group(group=group, user=user, order=0)

        return group

    def create_user_group(self, **kwargs):
        if "group" not in kwargs:
            kwargs["group"] = self.create_group()

        if "user" not in kwargs:
            kwargs["user"] = self.create_user()

        if "order" not in kwargs:
            kwargs["order"] = 0

        if "permissions" not in kwargs:
            kwargs["permissions"] = "ADMIN"

        return GroupUser.objects.create(**kwargs)

    def create_group_invitation(self, **kwargs):
        if "invited_by" not in kwargs:
            kwargs["invited_by"] = self.create_user()

        if "group" not in kwargs:
            kwargs["group"] = self.create_group(user=kwargs["invited_by"])

        if "email" not in kwargs:
            kwargs["email"] = self.fake.email()

        if "permissions" not in kwargs:
            kwargs["permissions"] = "ADMIN"

        if "message" not in kwargs:
            kwargs["message"] = self.fake.name()

        return GroupInvitation.objects.create(**kwargs)
