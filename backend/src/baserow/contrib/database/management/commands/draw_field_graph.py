from django.core.management.base import BaseCommand

import graphviz
from tqdm import tqdm

from baserow.contrib.database.fields.dependencies.models import FieldDependency
from baserow.contrib.database.fields.models import Field, LinkRowField
from baserow.contrib.database.fields.registries import field_type_registry
from baserow.contrib.database.models import Database
from baserow.contrib.database.table.models import Table


class Command(BaseCommand):
    help = (
        "Generates an image showing the field dependency graph for a database or "
        "all databases."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "database_id",
            type=str,
            help="The database to generate the field dependency graph for or all to "
            "generate for all databases.",
        )
        parser.add_argument(
            "--output-dir",
            default="field-diagrams",
            help="The folder to write field diagrams to",
        )
        parser.add_argument(
            "--gv-files-only",
            action="store_true",
            help="When provided only gv files will be output and no png files",
        )
        parser.add_argument(
            "--disable-m2m-boxes",
            action="store_true",
            help="When provided no m2m boxes will be drawn",
        )

    def handle(self, *args, **options):
        database_id = options["database_id"]
        output_dir = options["output_dir"]
        gv_files_only = options["gv_files_only"]
        draw_m2m_boxes = not options["disable_m2m_boxes"]
        if database_id == "all":
            databases = Database.objects.all()
            for db in tqdm(databases, desc="Drawing graphs for all databases"):
                draw_field_graph(
                    db,
                    output_dir=output_dir,
                    gv_files_only=gv_files_only,
                    draw_m2m_boxes=draw_m2m_boxes,
                )

            self.stdout.write(self.style.SUCCESS(f"Graphs written to {output_dir}."))
        else:
            database_id = int(database_id)
            databases = Database.objects.filter(pk=database_id)

            output_image_file = draw_field_graph(
                databases.get(),
                output_dir=output_dir,
                gv_files_only=gv_files_only,
                draw_m2m_boxes=draw_m2m_boxes,
            )

            self.stdout.write(
                self.style.SUCCESS(f"Graph written to {output_image_file}.")
            )


def draw_field_graph(
    database: Database, output_dir: str, gv_files_only: bool, draw_m2m_boxes: bool
):
    kwargs = {"format": "png"} if not gv_files_only else {"format": "gv"}
    dot = graphviz.Digraph(
        f"database-{database.id}-graph",
        comment=f"Field dependencies for the database {database.name}",
        **kwargs,
    )

    tables = Table.objects.filter(database=database)
    for table in tables:
        with dot.subgraph(name=f"cluster_{table.id}_{table.name}") as c:
            c.attr(label=f"{table.name} (table_{table.id})")
            c.attr(style="filled", color="lightgrey")
            c.node_attr.update(style="filled", color="white")
            for field in Field.objects.filter(table=table):
                field_type_name = field_type_registry.get_by_model(
                    field.specific_class
                ).type
                if field.dependencies.exists() or field.dependants.exists():
                    c.node(
                        field_node(field),
                        f"{field.name} (field_{field.id})\n{field_type_name}",
                        color="darkseagreen3" if field.primary else "white",
                    )

    if draw_m2m_boxes:
        for relation_id in (
            LinkRowField.objects.filter(table__database=database)
            .values_list("link_row_relation_id", flat=True)
            .distinct()
        ):
            with dot.subgraph(name=f"cluster_rel_{relation_id}") as c:
                c.attr(label=f"link row (rel_{relation_id})")
                c.attr(style="filled", color="lightgrey")
                c.node_attr.update(shape="point", color="black")
                for via_dep in FieldDependency.objects.filter(
                    via__link_row_relation_id=relation_id
                ):
                    c.node(via_node_name_func(via_dep), f"")

    for table in tables:
        fields_in_table = Field.objects.filter(table=table)
        for field in fields_in_table:
            for dependency in field.dependencies.all():
                field_node_name = field_node(field)
                if dependency.broken_reference_field_name:
                    dep_node = f"broken_{dependency.broken_reference_field_name}"
                else:
                    dep_node = field_node(dependency.dependency)
                if dependency.via is not None and draw_m2m_boxes:
                    dot.edge(
                        field_node_name,
                        via_node_name_func(dependency),
                        arrowhead="none",
                    )
                    dot.edge(
                        via_node_name_func(dependency),
                        dep_node,
                    )
                else:
                    dot.edge(field_node_name, dep_node)

    return dot.render(directory=output_dir)


def field_node(field):
    return f"{field.name}_AT_{field.table.name}".lower().replace(" ", "_")


def via_node_name_func(via_dep):
    dep_name = (
        via_dep.dependency.name + "_AT_" + via_dep.dependency.table.name
        if via_dep.dependency
        else f"broken_{via_dep.broken_reference_field_name}"
    )
    return (
        f"{via_dep.dependant.name}"
        f"_AT_{via_dep.via.table.name}"
        f"__via_{via_dep.via.name}_AT_{via_dep.via.table.name}__"
        f"{dep_name}".lower().replace(" ", "_")
    )
