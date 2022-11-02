from baserow_premium.license.models import License, LicenseUser
from baserow_premium.views.models import KanbanView, KanbanViewFieldOptions

from baserow.contrib.database.fields.models import Field

VALID_ONE_SEAT_LICENSE = (
    # id: "1", instance_id: "1"
    b"eyJ2ZXJzaW9uIjogMSwgImlkIjogIjEiLCAidmFsaWRfZnJvbSI6ICIyMDIxLTA4LTI5VDE5OjUyOjU3"
    b"Ljg0MjY5NiIsICJ2YWxpZF90aHJvdWdoIjogIjIwMjEtMDktMjlUMTk6NTI6NTcuODQyNjk2IiwgInBy"
    b"b2R1Y3RfY29kZSI6ICJwcmVtaXVtIiwgInNlYXRzIjogMSwgImlzc3VlZF9vbiI6ICIyMDIxLTA4LTI5"
    b"VDE5OjUyOjU3Ljg0MjY5NiIsICJpc3N1ZWRfdG9fZW1haWwiOiAiYnJhbUBiYXNlcm93LmlvIiwgImlz"
    b"c3VlZF90b19uYW1lIjogIkJyYW0iLCAiaW5zdGFuY2VfaWQiOiAiMSJ9.e33Z4CxLSmD-R55Es24P3mR"
    b"8Oqn3LpaXvgYLzF63oFHat3paon7IBjBmOX3eyd8KjirVf3empJds4uUw2Nn2m7TVvRAtJ8XzNl-8ytf"
    b"2RLtmjMx1Xkgp5VZ8S7UqJ_cKLyl76eVRtGEA1DH2HdPKu1vBPJ4bzDfnhDPYl4k5z9XSSgqAbQ9WO0U"
    b"5kiI3BYjVRZSKnZMeguAGZ47ezDj_WArGcHAB8Pa2v3HFp5Y34DMJ8r3_hD5hxCKgoNx4AHx1Q-hRDqp"
    b"Aroj-4jl7KWvlP-OJNc1BgH2wnhFmeKHotv-Iumi83JQohyceUbG6j8rDDQvJfcn0W2_ebmUH3TKr-w="
    b"="
)
VALID_100_SEAT_LICENSE_UNTIL_YEAR_2099 = (
    # id: "test-license", instance_id: "1"
    # valid from the year 1000 through the year 2099
    b"eyJ2ZXJzaW9uIjogMSwgImlkIjogInRlc3QtbGljZW5zZSIsICJ2YWxpZF9mcm9tIjogIjEwMDAtMDEt"
    b"MDFUMTI6MDA6MDAuMDAwMDAwIiwgInZhbGlkX3Rocm91Z2giOiAiMjA5OS0wMS0wMVQxMjowMDowMC4w"
    b"MDAwMDAiLCAicHJvZHVjdF9jb2RlIjogInByZW1pdW0iLCAic2VhdHMiOiAxMDAsICJpc3N1ZWRfb24i"
    b"OiAiMjAyMS0wOC0yOVQxOTo1Mjo1Ny44NDI2OTYiLCAiaXNzdWVkX3RvX2VtYWlsIjogImJyYW1AYmFz"
    b"ZXJvdy5pbyIsICJpc3N1ZWRfdG9fbmFtZSI6ICJCcmFtIiwgImluc3RhbmNlX2lkIjogIjEifQ==.SoF"
    b"QKxwNjNM-lvJ4iy7d8dc4EmWZagMBzgAmQgUJoGo6FtXaTOILOnc3Tm2uSwZ2MImBeehIff8GPE521-k"
    b"a9-0DDYEX4BYVgpLxLF3gFZxgX0QJgsNsauOjEZH8IGFGX1Asdsll2rNbzYDKz68jG7GgK04Lfn19cQ-"
    b"Qg0Qlgq0gB_7CoUulo73fhCjOZHoH1HAzxh77SbgXxJbDQOYlXqortVvl5vDpNcPTbar4IihBJRgaFTM"
    b"7DjR0On8GCX7j944VkXguiGPdglBXTcqRbPf1qqmZ8jaHrKX6wHYysBJs10OqWqT5p_s8cuRrr0IzLDz"
    b"Ss-q11zuFn-ekeJzo5A=="
)


class PremiumFixtures:
    def create_user(self, *args, **kwargs):
        has_active_premium_license = kwargs.pop("has_active_premium_license", False)
        user = super().create_user(*args, **kwargs)

        if has_active_premium_license:
            self.create_active_premium_license_for_user(user)

        return user

    def create_active_premium_license_for_user(self, user):
        test_license, created = License.objects.get_or_create(
            license=VALID_100_SEAT_LICENSE_UNTIL_YEAR_2099.decode()
        )
        LicenseUser.objects.get_or_create(user=user, license=test_license)

    def remove_all_active_premium_licenses(self, user):
        LicenseUser.objects.filter(user=user).delete()

    def create_premium_license(self, **kwargs):
        if "license" not in kwargs:
            kwargs["license"] = VALID_100_SEAT_LICENSE_UNTIL_YEAR_2099.decode()

        return License.objects.create(**kwargs)

    def create_premium_license_user(self, **kwargs):
        if "user" not in kwargs:
            kwargs["user"] = self.create_user()

        if "license" not in kwargs:
            kwargs["license"] = self.create_premium_license()

        return LicenseUser.objects.create(**kwargs)

    def create_kanban_view(self, user=None, **kwargs):
        if "table" not in kwargs:
            kwargs["table"] = self.create_database_table(user=user)

        if "name" not in kwargs:
            kwargs["name"] = self.fake.name()

        if "order" not in kwargs:
            kwargs["order"] = 0

        if "single_select_field" not in kwargs:
            kwargs["single_select_field"] = self.create_single_select_field(
                table=kwargs["table"],
            )

        kanban_view = KanbanView.objects.create(**kwargs)
        self.create_kanban_view_field_options(kanban_view)
        return kanban_view

    def create_kanban_view_field_options(self, kanban_view, **kwargs):
        return [
            self.create_kanban_view_field_option(kanban_view, field, **kwargs)
            for field in Field.objects.filter(table=kanban_view.table)
        ]

    def create_kanban_view_field_option(self, kanban_view, field, **kwargs):
        return KanbanViewFieldOptions.objects.create(
            kanban_view=kanban_view, field=field, **kwargs
        )
