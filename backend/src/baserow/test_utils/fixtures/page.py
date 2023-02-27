from baserow.contrib.builder.pages.models import Page


class PageFixtures:
    def create_builder_page(self, user=None, **kwargs):
        if user is None:
            user = self.create_user()

        if "builder" not in kwargs:
            kwargs["builder"] = self.create_builder_application(user=user)

        if "name" not in kwargs:
            kwargs["name"] = self.fake.name()

        if "order" not in kwargs:
            kwargs["order"] = 0

        page = Page.objects.create(**kwargs)

        return page
