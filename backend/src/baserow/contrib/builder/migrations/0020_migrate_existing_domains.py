from django.db import migrations, transaction

from baserow.contrib.builder.domains.models import CustomDomain, Domain


def forward(apps, schema_editor):
    """
    This migration introduces polymorphism, so we need to decide which type of
    domain all the existing domains now become. In this case we are turning
    all the existing domains into custom domains.
    """

    with transaction.atomic():
        domains = Domain.objects.all()

        for domain in domains:
            domain.delete()
            CustomDomain.objects.create(
                domain_name=domain.domain_name,
                order=domain.order,
                builder=domain.builder,
            )


def reverse(apps, schema_editor):
    ...


class Migration(migrations.Migration):
    dependencies = [("builder", "0019_sub_domains")]

    operations = [
        migrations.RunPython(forward, reverse),
    ]
