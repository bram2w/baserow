from django.db.models import Max

from baserow.core.models import Template, TemplateCategory


class TemplateFixtures:
    def create_template_category(self, template=None, templates=None, **kwargs):
        if "name" not in kwargs:
            kwargs["name"] = self.fake.name()

        category = TemplateCategory.objects.create(**kwargs)

        if not templates:
            templates = []

        if template:
            templates.append(template)

        category.templates.add(*templates)

        return category

    def create_template(self, category=None, categories=None, **kwargs):
        if "name" not in kwargs:
            kwargs["name"] = self.fake.name()

        if "slug" not in kwargs:
            kwargs["slug"] = self.fake.unique.slug()

        if "icon" not in kwargs:
            kwargs["icon"] = "document"

        if "workspace" not in kwargs:
            kwargs["workspace"] = self.create_workspace()

        if "type" not in kwargs:
            kwargs["type"] = Template.Type.OFFICIAL

        template = Template.objects.create(**kwargs)
        # Like the handlers, so that the cached template types of the workspace are
        # read again.
        template.workspace.save(update_fields=["updated_on"])

        if not categories:
            categories = []

        if category:
            categories.append(category)

        if len(categories) == 0:
            categories.append(self.create_template_category())

        template.categories.add(*categories)

        return template

    def create_user_template(self, user=None, **kwargs):
        if user is None:
            user = self.create_user()

        kwargs.setdefault("owner", user)
        kwargs.setdefault("author", user)

        return self.create_template(type=Template.Type.USER, **kwargs)

    def create_user_template_revision(self, root, **kwargs):
        if "version" not in kwargs:
            kwargs["version"] = (
                root.revisions.aggregate(version=Max("version"))["version"] or 1
            ) + 1

        return self.create_template(type=root.type, root=root, slug="", **kwargs)
