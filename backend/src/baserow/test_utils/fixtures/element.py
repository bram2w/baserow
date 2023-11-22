from copy import deepcopy

from baserow.contrib.builder.elements.models import (
    ButtonElement,
    CollectionField,
    ColumnElement,
    HeadingElement,
    ImageElement,
    LinkElement,
    ParagraphElement,
    TableElement,
)


class ElementFixtures:
    def create_builder_heading_element(self, user=None, page=None, **kwargs):
        element = self.create_builder_element(HeadingElement, user, page, **kwargs)
        return element

    def create_builder_paragraph_element(self, user=None, page=None, **kwargs):
        element = self.create_builder_element(ParagraphElement, user, page, **kwargs)
        return element

    def create_builder_image_element(self, user=None, page=None, **kwargs):
        element = self.create_builder_element(ImageElement, user, page, **kwargs)
        return element

    def create_builder_column_element(self, user=None, page=None, **kwargs):
        element = self.create_builder_element(ColumnElement, user, page, **kwargs)
        return element

    def create_builder_link_element(self, user=None, page=None, **kwargs):
        element = self.create_builder_element(LinkElement, user, page, **kwargs)
        return element

    def create_builder_table_element(self, user=None, page=None, **kwargs):
        fields = kwargs.pop(
            "fields",
            deepcopy(
                [
                    {
                        "name": "Field 1",
                        "type": "text",
                        "config": {"value": "get('test1')"},
                    },
                    {
                        "name": "Field 2",
                        "type": "text",
                        "config": {"value": "get('test2')"},
                    },
                    {
                        "name": "Field 3",
                        "type": "text",
                        "config": {"value": "get('test3')"},
                    },
                ]
            ),
        )

        if "data_source" not in kwargs:
            kwargs[
                "data_source"
            ] = self.create_builder_local_baserow_list_rows_data_source(page=page)

        element = self.create_builder_element(TableElement, user, page, **kwargs)

        if fields:
            created_fields = CollectionField.objects.bulk_create(
                [
                    CollectionField(**field, order=index)
                    for index, field in enumerate(fields)
                ]
            )
            element.fields.add(*created_fields)

        return element

    def create_builder_button_element(self, user=None, page=None, **kwargs):
        element = self.create_builder_element(ButtonElement, user, page, **kwargs)
        return element

    def create_builder_element(self, model_class, user=None, page=None, **kwargs):
        if user is None:
            user = self.create_user()

        if not page:
            builder = kwargs.pop("builder", None)
            page_args = kwargs.pop("page_args", {})
            page = self.create_builder_page(user=user, builder=builder, **page_args)

        if "order" not in kwargs:
            kwargs["order"] = model_class.get_last_order(page)

        element = model_class.objects.create(page=page, **kwargs)

        return element
