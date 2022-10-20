from baserow_enterprise.models import Role, RoleAssignment, Team, TeamSubject


class EnterpriseFixtures:
    def create_user(self, *args, **kwargs):
        user = super().create_user(*args, **kwargs)
        return user

    def create_team(self, **kwargs):
        if "name" not in kwargs:
            kwargs["name"] = self.fake.name()
        team = Team.objects.create(**kwargs)
        return team

    def create_subject(self, **kwargs):
        if "subject" not in kwargs:
            kwargs["subject"] = self.create_user()
        subject = TeamSubject.objects.create(**kwargs)
        return subject

    def create_role_assignment(self, **kwargs):
        user = kwargs.get("user", None)
        role_uid = kwargs.get("role_uid", "builder")
        group = kwargs.get("group", None)
        scope = kwargs.get("scope", None)

        if "user" not in kwargs:
            user = super().create_user()

        if group is None:
            group = super().create_group(user=user)

        if scope is None:
            scope = group

        role = Role.objects.get(uid=role_uid)

        return RoleAssignment.objects.create(
            subject=user, role=role, group=group, scope=scope
        )
