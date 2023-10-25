from baserow.contrib.builder.domains.models import CustomDomain, SubDomain


class DomainFixtures:
    def create_builder_custom_domain(self, user=None, **kwargs):
        return self.create_builder_domain(CustomDomain, user, **kwargs)

    def create_builder_sub_domain(self, user=None, **kwargs):
        return self.create_builder_domain(SubDomain, user, **kwargs)

    def create_builder_domain(self, model_class, user=None, **kwargs):
        if user is None:
            user = self.create_user()

        if "builder" not in kwargs:
            kwargs["builder"] = self.create_builder_application(user=user)

        if "domain_name" not in kwargs:
            kwargs["domain_name"] = self.fake.unique.domain_name()

        if "order" not in kwargs:
            kwargs["order"] = 0

        domain = model_class.objects.create(**kwargs)

        return domain
