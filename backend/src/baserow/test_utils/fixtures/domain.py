from baserow.contrib.builder.domains.models import Domain


class DomainFixtures:
    def create_builder_domain(self, user=None, **kwargs):
        if user is None:
            user = self.create_user()

        if "builder" not in kwargs:
            kwargs["builder"] = self.create_builder_application(user=user)

        if "domain_name" not in kwargs:
            kwargs["domain_name"] = self.fake.domain_name()

        if "order" not in kwargs:
            kwargs["order"] = 0

        domain = Domain.objects.create(**kwargs)

        return domain
