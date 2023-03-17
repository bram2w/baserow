from baserow.contrib.builder.pages.models import Page


class PageFixtures:
    def create_builder_page(self, user=None, **kwargs):
        if user is None:
            user = self.create_user()

        if not kwargs.get("builder", None):
            kwargs["builder"] = self.create_builder_application(user=user)

        if "name" not in kwargs:
            kwargs["name"] = self.fake.unique.uri_page()

        if "order" not in kwargs:
            kwargs["order"] = Page.get_last_order(kwargs["builder"])

        page = Page.objects.create(**kwargs)

        return page
