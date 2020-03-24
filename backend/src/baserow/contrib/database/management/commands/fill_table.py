import sys

from django.core.management.base import BaseCommand

from faker import Faker

from baserow.contrib.database.table.models import Table


class Command(BaseCommand):
    help = 'Fills a table with random data.'

    def add_arguments(self, parser):
        parser.add_argument('table_id', type=int, help='The table that needs to be '
                                                       'filled.')
        parser.add_argument('limit', type=int, help='Amount of rows that need to be '
                                                    'inserted.')

    def handle(self, *args, **options):
        table_id = options['table_id']
        limit = options['limit']
        fake = Faker()

        try:
            table = Table.objects.get(pk=table_id)
        except Table.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"The table with id {table_id} was not "
                                               f"found."))
            sys.exit(1)

        model = table.get_model()

        for i in range(0, limit):
            # Based on the random_value function we have for each type we can
            # build a dict with a random value for each field.
            values = {
                f'field_{field_id}': field_object['type'].random_value(
                    field_object['field'],
                    fake
                )
                for field_id, field_object in model._field_objects.items()
            }

            # Insert the row with the randomly created values.
            model.objects.create(**values)

        self.stdout.write(self.style.SUCCESS(f"{limit} rows have been inserted."))
