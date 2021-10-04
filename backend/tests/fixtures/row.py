from baserow.contrib.database.rows.handler import RowHandler


class RowFixture:
    def create_row_for_many_to_many_field(
        self, table, field, values, user, model=None, **kwargs
    ):
        """
        This is a helper function for creating a row with a many-to-many field that
        preserves the order of the elements that are being passed in as a list. This is
        done by creating the row with the first element in the list and successively
        updating the row for each additional element in the list, mimicking how the
        relationships would be added when using the frontend.

        Iteration steps:

        Example list: [1, 2, 3]

        First = create the row with: [1]
        Second = update the row with: [1, 2]
        Final = update the row with: [1, 2, 3]
        """

        field_id = f"field_{field.id}"
        row_handler = RowHandler()

        if model is None:
            model = table.get_model()

        # If the values list is empty, we create an empty row and return that row.
        if len(values) == 0:
            return row_handler.create_row(
                user=user, table=table, model=model, values={field_id: values}
            )

        row = None
        for index, value in enumerate(values):
            values_to_update = values[: index + 1]
            if index == 0:
                row = row_handler.create_row(
                    user=user,
                    table=table,
                    model=model,
                    values={field_id: values_to_update},
                )
            else:
                row = row_handler.update_row(
                    user=user,
                    table=table,
                    model=model,
                    row_id=row.id,
                    values={field_id: values_to_update},
                )

        return row
