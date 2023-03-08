from django.contrib.auth import get_user_model
from django.db import transaction

from baserow.contrib.database.fields.models import Field, SelectOption
from baserow.contrib.database.models import Database
from baserow.contrib.database.rows.handler import RowHandler
from baserow.contrib.database.table.handler import TableHandler
from baserow.contrib.database.table.models import Table
from baserow.core.handler import CoreHandler

User = get_user_model()


@transaction.atomic
def load_test_data():

    print("Add basic data...")

    user = User.objects.get(email="admin@baserow.io")
    group = user.groupuser_set.get(group__name="Acme Corp").group

    try:
        database = Database.objects.get(name="Back to local")
    except Database.DoesNotExist:
        database = CoreHandler().create_application(
            user, group, "database", name="Back to local"
        )

    try:
        products_table = Table.objects.get(name="Products", database=database)
    except Table.DoesNotExist:
        products_table = TableHandler().create_table_and_fields(
            user,
            database,
            name="Products",
            fields=[
                ("Name", "text", {}),
                (
                    "Category",
                    "single_select",
                    {},
                ),
                ("Notes", "long_text", {"field_options": {"width": 400}}),
            ],
        )

        select_field = Field.objects.get(table=products_table, name="Category")
        select_by_name = {}

        for order, option in enumerate(
            [
                {"color": "dark-green", "value": "Fruit & Vegetable"},
                {"color": "light-orange", "value": "Dairy"},
                {"color": "dark-red", "value": "Meat"},
                {"color": "blue", "value": "Fish"},
                {"color": "dark-gray", "value": "Bakery"},
                {"color": "dark-blue", "value": "Beverage"},
                {"color": "light-green", "value": "Grocery"},
            ]
        ):

            select_option = SelectOption.objects.create(
                field=select_field,
                order=order,
                value=option["value"],
                color=option["color"],
            )
            select_by_name[select_option.value] = select_option.id

        data = [
            ("Bread", select_by_name["Bakery"], ""),
            ("Croissant", select_by_name["Bakery"], ""),
            ("Vine", select_by_name["Beverage"], ""),
            ("Beer", select_by_name["Beverage"], ""),
            ("Milk", select_by_name["Dairy"], ""),
            ("Cheese", select_by_name["Dairy"], ""),
            ("Butter", select_by_name["Dairy"], ""),
            ("Fish", select_by_name["Fish"], ""),
            ("Apple", select_by_name["Fruit & Vegetable"], ""),
            ("Grapes", select_by_name["Fruit & Vegetable"], ""),
            ("Carrot", select_by_name["Fruit & Vegetable"], ""),
            ("Onion", select_by_name["Fruit & Vegetable"], ""),
            ("Flour", select_by_name["Grocery"], ""),
            ("Honey", select_by_name["Grocery"], ""),
            ("Oil", select_by_name["Grocery"], ""),
            ("Pork", select_by_name["Meat"], ""),
            ("Beef", select_by_name["Meat"], ""),
            ("Chicken", select_by_name["Meat"], ""),
            ("Rabbit", select_by_name["Meat"], ""),
        ]

        RowHandler().import_rows(user, products_table, data, send_signal=False)

    try:
        suppliers_table = Table.objects.get(name="Suppliers", database=database)
    except Table.DoesNotExist:
        suppliers_table = TableHandler().create_table_and_fields(
            user,
            database,
            name="Suppliers",
            fields=[
                ("Name", "text", {}),
                ("Products", "link_row", {"link_row_table": products_table}),
                ("Production", "rating", {}),
                ("Certification", "multiple_select", {}),
                ("Notes", "long_text", {"field_options": {"width": 400}}),
            ],
        )

        products = products_table.get_model(attribute_names=True)

        select_field = Field.objects.get(table=suppliers_table, name="Certification")
        for order, option in enumerate(
            [
                {"color": "dark-green", "value": "Organic"},
                {"color": "light-orange", "value": "Fair trade"},
                {"color": "light-green", "value": "Natural"},
                {"color": "light-blue", "value": "Animal protection"},
                {"color": "blue", "value": "Eco"},
                {"color": "dark-blue", "value": "Equitable"},
            ]
        ):

            select_option = SelectOption.objects.create(
                field=select_field,
                order=order,
                value=option["value"],
                color=option["color"],
            )
            select_by_name[select_option.value] = select_option.id

        products_by_name = {p.name: p.id for p in products.objects.all()}
        certif_by_name = {p.value: p.id for p in select_field.select_options.all()}

        data = [
            (
                "The happy cow",
                [products_by_name["Milk"], products_by_name["Butter"]],
                3,
                [certif_by_name["Animal protection"]],
                "Animals here are happy.",
            ),
            (
                "Jack's farm",
                [
                    products_by_name["Carrot"],
                    products_by_name["Onion"],
                    products_by_name["Chicken"],
                ],
                5,
                [certif_by_name["Organic"], certif_by_name["Equitable"]],
                "Good guy.",
            ),
            (
                "Horse & crocodile",
                [products_by_name["Beef"]],
                2,
                [certif_by_name["Fair trade"]],
                "",
            ),
            (
                "Vines LTD",
                [products_by_name["Vine"], products_by_name["Grapes"]],
                4,
                [
                    certif_by_name["Organic"],
                    certif_by_name["Natural"],
                ],
                "Excellent white & red wines.",
            ),
        ]

        RowHandler().import_rows(user, suppliers_table, data, send_signal=False)

    try:
        retailers_table = Table.objects.get(name="Retailers", database=database)
    except Table.DoesNotExist:
        retailers_table = TableHandler().create_table_and_fields(
            user,
            database,
            name="Retailers",
            fields=[
                ("Name", "text", {}),
                ("Suppliers", "link_row", {"link_row_table": suppliers_table}),
                ("Rating", "rating", {}),
                ("Notes", "long_text", {"field_options": {"width": 400}}),
            ],
        )

        suppliers = suppliers_table.get_model(attribute_names=True)
        suppliers_by_name = {p.name: p.id for p in suppliers.objects.all()}

        data = [
            (
                "All from the farm",
                [suppliers_by_name["The happy cow"], suppliers_by_name["Jack's farm"]],
                3,
                "",
            ),
            ("My little supermarket", [suppliers_by_name["Vines LTD"]], 1, ""),
            ("Organic4U", [suppliers_by_name["The happy cow"]], 5, ""),
            (
                "Ecomarket",
                [
                    suppliers_by_name["Horse & crocodile"],
                    suppliers_by_name["Jack's farm"],
                ],
                3,
                "",
            ),
            ("Welcome to the farm", [suppliers_by_name["The happy cow"]], 4, ""),
        ]

        RowHandler().import_rows(user, retailers_table, data, send_signal=False)
