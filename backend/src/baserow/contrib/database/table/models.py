import re
from typing import Any, Dict, Type, Union

from django.apps import apps
from django.conf import settings
from django.db import models
from django.db.models import F, JSONField, Q, QuerySet

from baserow.contrib.database.fields.exceptions import (
    FilterFieldNotFound,
    OrderByFieldNotFound,
    OrderByFieldNotPossible,
)
from baserow.contrib.database.fields.field_filters import (
    FILTER_TYPE_AND,
    FILTER_TYPE_OR,
    FilterBuilder,
)
from baserow.contrib.database.fields.field_sortings import AnnotatedOrder
from baserow.contrib.database.fields.models import CreatedOnField, LastModifiedField
from baserow.contrib.database.fields.registries import field_type_registry
from baserow.contrib.database.table.cache import (
    get_cached_model_field_attrs,
    set_cached_model_field_attrs,
)
from baserow.contrib.database.views.exceptions import ViewFilterTypeNotAllowedForField
from baserow.contrib.database.views.registries import view_filter_type_registry
from baserow.core.db import specific_iterator
from baserow.core.jobs.mixins import JobWithUndoRedoIds, JobWithWebsocketId
from baserow.core.jobs.models import Job
from baserow.core.mixins import (
    CreatedAndUpdatedOnMixin,
    OrderableMixin,
    TrashableModelMixin,
)
from baserow.core.utils import split_comma_separated_string

deconstruct_filter_key_regex = re.compile(
    r"filter__field_([0-9]+|created_on|updated_on)__([a-zA-Z0-9_]*)$"
)


class TableModelQuerySet(models.QuerySet):
    def enhance_by_fields(self):
        """
        Enhances the queryset based on the `enhance_queryset` for each field in the
        table. For example the `link_row` field adds the `prefetch_related` to prevent
        N queries per row. This helper should only be used when multiple rows are going
        to be fetched.

        :return: The enhanced queryset.
        :rtype: QuerySet
        """

        for field_object in self.model._field_objects.values():
            self = field_object["type"].enhance_queryset(
                self, field_object["field"], field_object["name"]
            )
        return self

    def search_all_fields(self, search, only_search_by_field_ids=None):
        """
        Performs a very broad search across all supported fields with the given search
        query. If the primary key value matches then that result will be returned
        otherwise all field types other than link row and boolean fields are currently
        searched.

        :param search: The search query.
        :type search: str
        :param only_search_by_field_ids: Only field ids in this iterable will be
            filtered by the search term. Other fields not in the iterable will be
            ignored and not be filtered.
        :type only_search_by_field_ids: Optional[Iterable[int]]
        :return: The queryset containing the search queries.
        :rtype: QuerySet
        """

        filter_builder = FilterBuilder(filter_type=FILTER_TYPE_OR).filter(
            Q(id__contains=search)
        )
        for field_object in self.model._field_objects.values():
            if (
                only_search_by_field_ids is not None
                and field_object["field"].id not in only_search_by_field_ids
            ):
                continue
            field_name = field_object["name"]
            model_field = self.model._meta.get_field(field_name)

            try:
                sub_filter = field_object["type"].contains_query(
                    field_name, search, model_field, field_object["field"]
                )
                filter_builder.filter(sub_filter)
            except Exception:  # nosec B112
                continue

        return filter_builder.apply_to_queryset(self)

    def _get_field_name(self, field: str) -> str:
        """
        Helper method for parsing a field name from a string
        with a possible prefix.

        :param field: The string from which the field name
            should be parsed.
        :type field: str
        :return: The field without prefix.
        :rtype: str
        """

        possible_prefix = field[:1]
        if possible_prefix in {"-", "+"}:
            return field[1:]
        else:
            return field

    def _get_field_id(self, field: str) -> Union[int, None]:
        """
        Helper method for parsing a field ID from a string.

        :param field: The string from which the field id
            should be parsed.
        :type field: str
        :return: The ID of the field or None
        :rtype: int or None
        """

        try:
            field_id = int(re.sub("[^0-9]", "", str(field)))
        except ValueError:
            field_id = None

        return field_id

    def order_by_fields_string(
        self, order_string, user_field_names=False, only_order_by_field_ids=None
    ):
        """
        Orders the query by the given field order string. This string is often
        directly forwarded from a GET, POST or other user provided parameter.
        Multiple fields can be provided by separating the values by a comma. When
        user_field_names is False the order_string must contain a comma separated
        list of field ids. The field id is extracted from the string so it can either
        be provided as field_1, 1, id_1, etc. When user_field_names is True the
        order_string is treated as a comma separated list of the actual field names,
        use quotes to wrap field names containing commas.

        :param order_string: The field ids to order the queryset by separated by a
            comma. For example `field_1,2` which will order by field with id 1 first
            and then by field with id 2 second.
        :type order_string: str
        :param user_field_names: If true then the order_string is instead treated as
        a comma separated list of actual field names and not field ids.
        :type user_field_names: bool
        :param only_order_by_field_ids: Only field ids in this iterable will be
            ordered by. Other fields not in the iterable will be ignored and not be
            filtered.
        :type only_order_by_field_ids: Optional[Iterable[int]]
        :raises OrderByFieldNotFound: when the provided field id is not found in the
            model.
        :raises OrderByFieldNotPossible: when it is not possible to order by the
            field's type.
        :return: The queryset ordered by the provided order_string.
        :rtype: QuerySet
        """

        order_by = split_comma_separated_string(order_string)

        if len(order_by) == 0:
            raise ValueError("At least one field must be provided.")

        if user_field_names:
            field_object_dict = {
                o["field"].name: o for o in self.model._field_objects.values()
            }
        else:
            field_object_dict = self.model._field_objects

        annotations = {}
        for index, order in enumerate(order_by):
            if user_field_names:
                field_name_or_id = self._get_field_name(order)
            else:
                field_name_or_id = self._get_field_id(order)

            if field_name_or_id not in field_object_dict or (
                only_order_by_field_ids is not None
                and field_name_or_id not in only_order_by_field_ids
            ):
                raise OrderByFieldNotFound(order)

            order_direction = "DESC" if order[:1] == "-" else "ASC"
            field_object = field_object_dict[field_name_or_id]
            field_type = field_object["type"]
            field_name = field_object["name"]
            field = field_object["field"]
            user_field_name = field_object["field"].name
            error_display_name = user_field_name if user_field_names else field_name

            if not field_object["type"].check_can_order_by(field_object["field"]):
                raise OrderByFieldNotPossible(
                    error_display_name,
                    field_type.type,
                    f"It is not possible to order by field type {field_type.type}.",
                )

            field_order = field_type.get_order(field, field_name, order_direction)

            if isinstance(field_order, AnnotatedOrder):
                if field_order.annotation is not None:
                    annotations = {**annotations, **field_order.annotation}
                field_order = field_order.order

            if field_order:
                order_by[index] = field_order
            else:
                order_expression = F(field_name)

                if order_direction == "ASC":
                    order_expression = order_expression.asc(nulls_first=True)
                else:
                    order_expression = order_expression.desc(nulls_last=True)

                order_by[index] = order_expression

        order_by.append("order")
        order_by.append("id")

        if annotations is not None:
            return self.annotate(**annotations).order_by(*order_by)
        else:
            return self.order_by(*order_by)

    def filter_by_fields_object(
        self, filter_object, filter_type=FILTER_TYPE_AND, only_filter_by_field_ids=None
    ):
        """
        Filters the query by the provided filters in the filter_object. The following
        format `filter__field_{id}__{view_filter_type}` is expected as key and multiple
        values can be provided as a list containing strings. Only the view filter types
        are allowed.

        Example: {
            'filter__field_{id}__{view_filter_type}': {value}.
        }

        In addition to that, it's also possible to directly filter on the
        `created_on` and `updated_on` fields, even if the CreatedOn and LastModified
        fields are not created. This can be done by providing
        `filter__field_created_on__{view_filter_type}` or
        `filter__field_updated_on__{view_filter_type}` as keys in the `filter_object`.

        :param filter_object: The object containing the field and filter type as key
            and the filter value as value.
        :type filter_object: object
        :param filter_type: Indicates if the provided filters are in an AND or OR
            statement.
        :type filter_type: str
        :param only_filter_by_field_ids: Only field ids in this iterable will be
            filtered by. Other fields not in the iterable will be ignored and not be
            filtered.
        :type only_filter_by_field_ids: Optional[Iterable[int]]
        :raises ValueError: Raised when the provided filer_type isn't AND or OR.
        :raises FilterFieldNotFound: Raised when the provided field isn't found in
            the model.
        :raises ViewFilterTypeDoesNotExist: when the view filter type doesn't exist.
        :raises ViewFilterTypeNotAllowedForField: when the view filter type isn't
            compatible with field type.
        :return: The filtered queryset.
        :rtype: QuerySet
        """

        if filter_type not in [FILTER_TYPE_AND, FILTER_TYPE_OR]:
            raise ValueError(f"Unknown filter type {filter_type}.")

        filter_builder = FilterBuilder(filter_type=filter_type)

        for key, values in filter_object.items():
            matches = deconstruct_filter_key_regex.match(key)

            if not matches:
                continue

            fixed_field_instance_mapping = {
                "created_on": CreatedOnField(),
                "updated_on": LastModifiedField(),
            }

            if matches[1] in fixed_field_instance_mapping.keys():
                field_name = matches[1]
                field_instance = fixed_field_instance_mapping.get(field_name)
            else:
                field_id = int(matches[1])

                if field_id not in self.model._field_objects or (
                    only_filter_by_field_ids is not None
                    and field_id not in only_filter_by_field_ids
                ):
                    raise FilterFieldNotFound(
                        field_id, f"Field {field_id} does not exist."
                    )

                field_object = self.model._field_objects[field_id]
                field_instance = field_object["field"]
                field_name = field_object["name"]
                field_type = field_object["type"].type

            model_field = self.model._meta.get_field(field_name)
            view_filter_type = view_filter_type_registry.get(matches[2])
            if not view_filter_type.field_is_compatible(field_instance):
                raise ViewFilterTypeNotAllowedForField(
                    matches[2],
                    field_type,
                )

            if not isinstance(values, list):
                values = [values]

            for value in values:
                filter_builder.filter(
                    view_filter_type.get_filter(
                        field_name, value, model_field, field_instance
                    )
                )

        return filter_builder.apply_to_queryset(self)


class TableModelTrashAndObjectsManager(models.Manager):
    def get_queryset(self):
        return TableModelQuerySet(self.model, using=self._db)


class TableModelManager(TableModelTrashAndObjectsManager):
    def get_queryset(self):
        return TableModelQuerySet(self.model, using=self._db).filter(trashed=False)


FieldObject = Dict[str, Any]


class GeneratedTableModel(models.Model):
    """
    Mixed into Model classes which have been generated by Baserow.
    Can also be used to identify instances of generated baserow models
    like `isinstance(possible_baserow_model, GeneratedTableModel)`.
    """

    @classmethod
    def fields_requiring_refresh_after_insert(cls):
        return [
            f.attname
            for f in cls._meta.fields
            if getattr(f, "requires_refresh_after_insert", False)
            # There is a bug in Django where db_returning fields do not have their
            # from_db_value function applied after performing and INSERT .. RETURNING
            # Instead for now we force a refresh to ensure these fields are converted
            # from their db representations correctly.
            or isinstance(f, JSONField) and f.db_returning
        ]

    @classmethod
    def fields_requiring_refresh_after_update(cls):
        return [
            f.attname
            for f in cls._meta.fields
            if getattr(f, "requires_refresh_after_update", False)
        ]

    class Meta:
        abstract = True


class DefaultAppsProxy:
    """
    A proxy class to the default apps registry.
    This class is needed to make our dynamic models available in the
    options then the relation tree is built.
    """

    def __init__(self):
        self._extra_models = []

    def add_models(self, *dynamic_models):
        """
        Adds a model to the default apps registry.
        """

        self._extra_models.extend(dynamic_models)

    def get_models(self, *args, **kwargs):
        return apps.get_models(*args, **kwargs) + self._extra_models

    def __getattr__(self, attr):
        return getattr(apps, attr)


class Table(
    TrashableModelMixin, CreatedAndUpdatedOnMixin, OrderableMixin, models.Model
):
    USER_TABLE_DATABASE_NAME_PREFIX = "database_table_"
    database = models.ForeignKey("database.Database", on_delete=models.CASCADE)
    order = models.PositiveIntegerField()
    name = models.CharField(max_length=255)
    row_count = models.PositiveIntegerField(null=True)
    row_count_updated_at = models.DateTimeField(null=True)
    version = models.TextField(default="initial_version")

    class Meta:
        ordering = ("order",)

    @classmethod
    def get_last_order(cls, database):
        queryset = Table.objects.filter(database=database)
        return cls.get_highest_order_of_queryset(queryset) + 1

    def get_database_table_name(self):
        return f"{self.USER_TABLE_DATABASE_NAME_PREFIX}{self.id}"

    def get_model(
        self,
        fields=None,
        field_ids=None,
        field_names=None,
        attribute_names=False,
        manytomany_models=None,
        add_dependencies=True,
        managed=False,
        use_cache=True,
    ) -> Type[GeneratedTableModel]:
        """
        Generates a temporary Django model based on available fields that belong to
        this table. Note that the model will not be registered with the apps because
        of the `DatabaseConfig.prevent_generated_model_for_registering` hack. We do
        not want to the model cached because models with the same name can differ.

        :param fields: Extra table field instances that need to be added the model.
        :type fields: list
        :param field_ids: If provided only the fields with the ids in the list will be
            added to the model. This can be done to improve speed if for example only a
            single field needs to be mutated.
        :type field_ids: None or list
        :param field_names: If provided only the fields with the names in the list
            will be added to the model. This can be done to improve speed if for
            example only a single field needs to be mutated.
        :type field_names: None or list
        :param attribute_names: If True, the model attributes will be based on the
            field name instead of the field id.
        :type attribute_names: bool
        :param manytomany_models: In some cases with related fields a model has to be
            generated in order to generate that model. In order to prevent a
            recursion loop we cache the generated models and pass those along.
        :type manytomany_models: dict
        :param add_dependencies: When True will ensure any direct field dependencies
            are included in the model. Otherwise only the exact fields you specify will
            be added to the model.
        :param managed: Whether the created model should be managed by Django or not.
            Only in very specific limited situations should this be enabled as
            generally Baserow itself manages most aspects of returned generated models.
        :type managed: bool
        :param use_cache: Indicates whether a cached model can be used.
        :type use_cache: bool
        :return: The generated model.
        :rtype: Model
        """

        filtered = field_names is not None or field_ids is not None
        model_name = f"Table{self.pk}Model"

        if fields is None:
            fields = []

        if manytomany_models is None:
            manytomany_models = {}

        app_label = "database_table"
        meta = type(
            "Meta",
            (),
            {
                "apps": DefaultAppsProxy(),
                "managed": managed,
                "db_table": self.get_database_table_name(),
                "app_label": app_label,
                "ordering": ["order", "id"],
                "indexes": [
                    models.Index(
                        fields=["order", "id"],
                        name=self.get_collision_safe_order_id_idx_name(),
                    ),
                ],
            },
        )

        def __str__(self):
            """
            When the model instance is rendered to a string, then we want to return the
            primary field value in human readable format.
            """

            field = self._field_objects.get(self._primary_field_id, None)

            if not field:
                return f"unnamed row {self.id}"

            return field["type"].get_human_readable_value(
                getattr(self, field["name"]), field
            )

        attrs = {
            "Meta": meta,
            "__module__": "database.models",
            # An indication that the model is a generated table model.
            "_generated_table_model": True,
            "_table_id": self.id,
            # We are using our own table model manager to implement some queryset
            # helpers.
            "objects": TableModelManager(),
            "objects_and_trash": TableModelTrashAndObjectsManager(),
            # Indicates which position the row has.
            "order": models.DecimalField(
                max_digits=40,
                decimal_places=20,
                editable=False,
                default=1,
            ),
            "__str__": __str__,
        }

        use_cache = (
            use_cache
            and len(fields) == 0
            and field_ids is None
            and add_dependencies is True
            and attribute_names is False
            and not settings.BASEROW_DISABLE_MODEL_CACHE
        )

        if use_cache:
            self.refresh_from_db(fields=["version"])
            field_attrs = get_cached_model_field_attrs(self)
        else:
            field_attrs = None

        if field_attrs is None:
            field_attrs = self._fetch_and_generate_field_attrs(
                add_dependencies,
                attribute_names,
                field_ids,
                field_names,
                fields,
                filtered,
            )

            if use_cache:
                set_cached_model_field_attrs(self, field_attrs)

        attrs.update(**field_attrs)

        # Create the model class.
        model = type(
            str(model_name),
            (
                GeneratedTableModel,
                TrashableModelMixin,
                CreatedAndUpdatedOnMixin,
                models.Model,
            ),
            attrs,
        )

        # In some situations the field can only be added once the model class has been
        # generated. So for each field we will call the after_model_generation with
        # the generated model as argument in order to do this. This is for example used
        # by the link row field. It can also be used to make other changes to the
        # class.
        all_field_objects = {
            **attrs["_field_objects"],
            **attrs["_trashed_field_objects"],
        }
        for field_id, field_object in all_field_objects.items():
            field_object["type"].after_model_generation(
                field_object["field"], model, field_object["name"], manytomany_models
            )

        return model

    def _fetch_and_generate_field_attrs(
        self,
        add_dependencies,
        attribute_names,
        field_ids,
        field_names,
        fields,
        filtered,
    ):
        field_attrs = {
            "_primary_field_id": -1,
            # An object containing the table fields, field types and the chosen
            # names with the table field id as key.
            "_field_objects": {},
            # An object containing the trashed table fields, field types and the
            # chosen names with the table field id as key.
            "_trashed_field_objects": {},
        }
        # Construct a query to fetch all the fields of that table. We need to
        # include any trashed fields so the created model still has them present
        # as the column is still actually there. If the model did not have the
        # trashed field attributes then model.objects.create will fail as the
        # trashed columns will be given null values by django triggering not null
        # constraints in the database.
        fields_query = self.field_set(manager="objects_and_trash").all()

        # If the field ids are provided we must only fetch the fields of which the
        # ids are in that list.
        if isinstance(field_ids, list):
            if len(field_ids) == 0:
                fields_query = []
            else:
                fields_query = fields_query.filter(pk__in=field_ids)

        # If the field names are provided we must only fetch the fields of which the
        # user defined name is in that list.
        if isinstance(field_names, list):
            if len(field_names) == 0:
                fields_query = []
            else:
                fields_query = fields_query.filter(name__in=field_names)

        if isinstance(fields_query, QuerySet):
            fields_query = specific_iterator(fields_query)

        # Create a combined list of fields that must be added and belong to the this
        # table.
        fields = list(fields) + [field for field in fields_query]

        # If there are duplicate field names we have to store them in a list so we
        # know later which ones are duplicate.
        duplicate_field_names = []
        already_included_field_names = set([f.name for f in fields])

        # We will have to add each field to with the correct field name and model
        # field to the attribute list in order for the model to work.
        while len(fields) > 0:
            field = fields.pop(0)
            trashed = field.trashed
            field = field.specific
            field_type = field_type_registry.get_by_model(field)
            field_name = field.db_column

            if filtered and add_dependencies:
                from baserow.contrib.database.fields.dependencies.handler import (
                    FieldDependencyHandler,
                )

                direct_dependencies = (
                    FieldDependencyHandler.get_same_table_dependencies(field)
                )
                for f in direct_dependencies:
                    if f.name not in already_included_field_names:
                        fields.append(f)
                        already_included_field_names.add(f.name)

            # If attribute_names is True we will not use 'field_{id}' as attribute
            # name, but we will rather use a name the user provided.
            if attribute_names:
                field_name = field.model_attribute_name
                if trashed:
                    field_name = f"trashed_{field_name}"
                # If the field name already exists we will append '_field_{id}' to
                # each entry that is a duplicate.
                if field_name in field_attrs:
                    duplicate_field_names.append(field_name)
                    replaced_field_name = (
                        f"{field_name}_{field_attrs[field_name].db_column}"
                    )
                    field_attrs[replaced_field_name] = field_attrs.pop(field_name)
                if field_name in duplicate_field_names:
                    field_name = f"{field_name}_{field.db_column}"

            field_objects_dict = (
                "_trashed_field_objects" if trashed else "_field_objects"
            )
            # Add the generated objects and information to the dict that
            # optionally can be returned. We exclude trashed fields here so they
            # are not displayed by baserow anywhere.
            field_attrs[field_objects_dict][field.id] = {
                "field": field,
                "type": field_type,
                "name": field_name,
            }
            if field.primary:
                field_attrs["_primary_field_id"] = field.id

            # Add the field to the attribute dict that is used to generate the
            # model. All the kwargs that are passed to the `get_model_field`
            # method are going to be passed along to the model field.
            field_attrs[field_name] = field_type.get_model_field(
                field,
                db_column=field.db_column,
                verbose_name=field.name,
            )

        return field_attrs

    # Use our own custom index name as the default models.Index
    # naming scheme causes 5+ collisions on average per 1000 new
    # tables.
    def get_collision_safe_order_id_idx_name(self):
        return f"tbl_order_id_{self.id}_idx"


class DuplicateTableJob(JobWithWebsocketId, JobWithUndoRedoIds, Job):

    original_table = models.ForeignKey(
        Table,
        null=True,
        related_name="duplicated_by_jobs",
        on_delete=models.SET_NULL,
        help_text="The Baserow table to duplicate.",
    )

    duplicated_table = models.OneToOneField(
        Table,
        null=True,
        related_name="duplicated_from_jobs",
        on_delete=models.SET_NULL,
        help_text="The duplicated Baserow table.",
    )
