from baserow_enterprise.models import Team, TeamSubject


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
