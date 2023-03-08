import datetime
from decimal import Decimal
from typing import Any, List, Optional, Type, Union

from django.db import models
from django.db.models import JSONField, Q, Value
from django.utils import timezone

from dateutil import parser
from rest_framework import serializers
from rest_framework.fields import Field

from baserow.contrib.database.fields.mixins import get_date_time_format
from baserow.contrib.database.formula.ast.tree import (
    BaserowBooleanLiteral,
    BaserowDecimalLiteral,
    BaserowExpression,
    BaserowFunctionCall,
    BaserowIntegerLiteral,
    BaserowStringLiteral,
)
from baserow.contrib.database.formula.registries import formula_function_registry
from baserow.contrib.database.formula.types.exceptions import UnknownFormulaType
from baserow.contrib.database.formula.types.formula_type import (
    BaserowFormulaInvalidType,
    BaserowFormulaType,
    BaserowFormulaTypeHasEmptyBaserowExpression,
    BaserowFormulaValidType,
    UnTyped,
)
from baserow.contrib.database.formula.types.serializers import LinkSerializer
from baserow.core.utils import list_to_comma_separated_string


class BaserowFormulaBaseTextType(BaserowFormulaTypeHasEmptyBaserowExpression):
    @property
    def comparable_types(self) -> List[Type["BaserowFormulaValidType"]]:
        return [
            BaserowFormulaTextType,
            BaserowFormulaDateType,
            BaserowFormulaNumberType,
            BaserowFormulaBooleanType,
            BaserowFormulaCharType,
            BaserowFormulaLinkType,
        ]

    @property
    def limit_comparable_types(self) -> List[Type["BaserowFormulaValidType"]]:
        # Force users to explicitly convert to text before doing any limit comparison
        # operators as lexicographical comparison can be surprising and so should be opt
        # in
        return [BaserowFormulaTextType, BaserowFormulaCharType, BaserowFormulaLinkType]

    @property
    def addable_types(self) -> List[Type["BaserowFormulaValidType"]]:
        return [BaserowFormulaTextType, BaserowFormulaCharType, BaserowFormulaLinkType]

    def add(
        self,
        add_func_call: "BaserowFunctionCall[UnTyped]",
        arg1: "BaserowExpression[BaserowFormulaTextType]",
        arg2: "BaserowExpression[BaserowFormulaTextType]",
    ):
        return formula_function_registry.get("concat").call_and_type_with_args(
            [arg1, arg2]
        )

    def placeholder_empty_value(self):
        return Value("", output_field=models.TextField())

    def placeholder_empty_baserow_expression(
        self,
    ) -> "BaserowExpression[BaserowFormulaValidType]":
        return literal("")


class BaserowFormulaTextType(
    BaserowFormulaBaseTextType,
    BaserowFormulaTypeHasEmptyBaserowExpression,
    BaserowFormulaValidType,
):
    type = "text"
    baserow_field_type = "text"

    def cast_to_text(
        self,
        to_text_func_call: "BaserowFunctionCall[UnTyped]",
        arg: "BaserowExpression[BaserowFormulaValidType]",
    ) -> "BaserowExpression[BaserowFormulaType]":
        # Explicitly unwrap the func_call here and just return the arg as it is already
        # in the text type and we don't want to return to_text(arg) but instead just
        # arg.
        return arg


class BaserowFormulaCharType(BaserowFormulaBaseTextType, BaserowFormulaValidType):
    type = "char"
    baserow_field_type = "text"


class BaserowFormulaLinkType(BaserowFormulaTextType):
    type = "link"
    baserow_field_type = None
    can_order_by = False

    @property
    def comparable_types(self) -> List[Type["BaserowFormulaValidType"]]:
        return [
            type(self),
        ]

    @property
    def limit_comparable_types(self) -> List[Type["BaserowFormulaValidType"]]:
        return []

    @property
    def addable_types(self) -> List[Type["BaserowFormulaValidType"]]:
        return []

    @property
    def subtractable_types(self) -> List[Type["BaserowFormulaValidType"]]:
        return []

    def cast_to_text(
        self,
        to_text_func_call: "BaserowFunctionCall[UnTyped]",
        arg: "BaserowExpression[BaserowFormulaValidType]",
    ) -> "BaserowExpression[BaserowFormulaType]":
        return formula_function_registry.get("get_link_label")(arg)

    def get_baserow_field_instance_and_type(self):
        return self, self

    def get_model_field(self, instance, **kwargs) -> models.Field:
        kwargs["null"] = True
        kwargs["blank"] = True

        return JSONField(default=dict, **kwargs)

    def get_response_serializer_field(self, instance, **kwargs) -> Optional[Field]:
        return self.get_serializer_field(instance, **kwargs)

    def get_serializer_field(self, instance, **kwargs) -> Optional[Field]:
        required = kwargs.get("required", False)

        return LinkSerializer(
            **{"required": required, "allow_null": not required, **kwargs}
        )

    def get_export_value(self, value, field_object, rich_value=False) -> Any:
        if rich_value:
            return value
        elif value is not None:
            if "label" in value:
                return f"{value['label']} ({value['url']})"
            else:
                return f"{value['url']}"
        else:
            return ""

    def contains_query(self, field_name, value, model_field, field):
        value = value.strip()
        # If an empty value has been provided we do not want to filter at all.
        if value == "":
            return Q()
        return Q(**{f"{field_name}__url__icontains": value}) | Q(
            **{f"{field_name}__label__icontains": value}
        )

    def get_alter_column_prepare_old_value(self, connection, from_field, to_field):
        sql = f"""
            p_in = p_in->'label' + ' (' + p_in->'url' + ')';
        """
        return sql, {}

    def get_human_readable_value(self, value: Any, field_object) -> str:
        human_readable_value = self.get_export_value(
            value, field_object, rich_value=False
        )
        if human_readable_value is None:
            return ""
        else:
            return str(human_readable_value)

    def placeholder_empty_value(self):
        return Value({}, output_field=JSONField())

    def placeholder_empty_baserow_expression(
        self,
    ) -> "BaserowExpression[BaserowFormulaValidType]":
        return formula_function_registry.get("link")(literal(""))


class BaserowFormulaNumberType(
    BaserowFormulaTypeHasEmptyBaserowExpression, BaserowFormulaValidType
):
    type = "number"
    baserow_field_type = "number"
    user_overridable_formatting_option_fields = ["number_decimal_places"]
    MAX_DIGITS = 50

    def __init__(self, number_decimal_places: int, **kwargs):
        super().__init__(**kwargs)
        self.number_decimal_places = number_decimal_places

    @property
    def comparable_types(self) -> List[Type["BaserowFormulaValidType"]]:
        return [
            type(self),
            BaserowFormulaTextType,
        ]

    @property
    def limit_comparable_types(self) -> List[Type["BaserowFormulaValidType"]]:
        return [type(self)]

    @property
    def addable_types(self) -> List[Type["BaserowFormulaValidType"]]:
        return [type(self)]

    @property
    def subtractable_types(self) -> List[Type["BaserowFormulaValidType"]]:
        return [type(self)]

    def add(
        self,
        add_func_call: "BaserowFunctionCall[UnTyped]",
        arg1: "BaserowExpression[BaserowFormulaNumberType]",
        arg2: "BaserowExpression[BaserowFormulaNumberType]",
    ):
        return add_func_call.with_valid_type(
            calculate_number_type([arg1.expression_type, arg2.expression_type])
        )

    def minus(
        self,
        minus_func_call: "BaserowFunctionCall[UnTyped]",
        arg1: "BaserowExpression[BaserowFormulaNumberType]",
        arg2: "BaserowExpression[BaserowFormulaNumberType]",
    ):
        return minus_func_call.with_valid_type(
            calculate_number_type([arg1.expression_type, arg2.expression_type])
        )

    def should_recreate_when_old_type_was(self, old_type: "BaserowFormulaType") -> bool:
        if isinstance(old_type, BaserowFormulaNumberType):
            return self.number_decimal_places != old_type.number_decimal_places
        else:
            return True

    def wrap_at_field_level(self, expr: "BaserowExpression[BaserowFormulaType]"):
        return formula_function_registry.get("error_to_nan")(expr)

    def unwrap_at_field_level(self, expr: "BaserowFunctionCall[BaserowFormulaType]"):
        return expr.args[0].with_valid_type(expr.expression_type)

    def placeholder_empty_value(self):
        return Value(
            0, output_field=models.DecimalField(max_digits=50, decimal_places=0)
        )

    def placeholder_empty_baserow_expression(
        self,
    ) -> "BaserowExpression[BaserowFormulaValidType]":
        return literal(0)

    def __str__(self) -> str:
        return f"number({self.number_decimal_places})"


class BaserowFormulaBooleanType(
    BaserowFormulaTypeHasEmptyBaserowExpression, BaserowFormulaValidType
):
    type = "boolean"
    baserow_field_type = "boolean"

    @property
    def comparable_types(self) -> List[Type["BaserowFormulaValidType"]]:
        return [
            type(self),
            BaserowFormulaTextType,
        ]

    @property
    def limit_comparable_types(self) -> List[Type["BaserowFormulaValidType"]]:
        # true > true makes no sense
        return []

    def placeholder_empty_value(self):
        return Value(False, output_field=models.BooleanField())

    def placeholder_empty_baserow_expression(
        self,
    ) -> "BaserowExpression[BaserowFormulaValidType]":
        return literal(False)

    def try_coerce_to_not_null(
        self, expr: "BaserowExpression[BaserowFormulaValidType]"
    ):
        return expr


def _calculate_addition_interval_type(
    arg1: BaserowExpression[BaserowFormulaValidType],
    arg2: BaserowExpression[BaserowFormulaValidType],
) -> BaserowFormulaValidType:
    arg1_type = arg1.expression_type
    arg2_type = arg2.expression_type
    if isinstance(arg1_type, BaserowFormulaDateIntervalType) and isinstance(
        arg2_type, BaserowFormulaDateIntervalType
    ):
        # interval + interval = interval
        resulting_type = arg1_type
    elif isinstance(arg1_type, BaserowFormulaDateIntervalType):
        # interval + date = date
        resulting_type = arg2_type
    else:
        # date + interval = date
        resulting_type = arg1_type
    resulting_type.nullable = arg1_type.nullable or arg2_type.nullable
    return resulting_type


# noinspection PyMethodMayBeStatic
class BaserowFormulaDateIntervalType(
    BaserowFormulaTypeHasEmptyBaserowExpression, BaserowFormulaValidType
):
    type = "date_interval"
    baserow_field_type = None

    @property
    def comparable_types(self) -> List[Type["BaserowFormulaValidType"]]:
        return [type(self)]

    @property
    def limit_comparable_types(self) -> List[Type["BaserowFormulaValidType"]]:
        return [type(self)]

    @property
    def addable_types(self) -> List[Type["BaserowFormulaValidType"]]:
        return [type(self), BaserowFormulaDateType]

    @property
    def subtractable_types(self) -> List[Type["BaserowFormulaValidType"]]:
        return [type(self)]

    def add(
        self,
        add_func_call: "BaserowFunctionCall[UnTyped]",
        arg1: "BaserowExpression[BaserowFormulaValidType]",
        arg2: "BaserowExpression[BaserowFormulaValidType]",
    ):
        return add_func_call.with_valid_type(
            _calculate_addition_interval_type(arg1, arg2)
        )

    def minus(
        self,
        minus_func_call: "BaserowFunctionCall[UnTyped]",
        arg1: "BaserowExpression[BaserowFormulaValidType]",
        arg2: "BaserowExpression[BaserowFormulaValidType]",
    ):
        return minus_func_call.with_valid_type(
            BaserowFormulaDateIntervalType(
                nullable=arg1.expression_type.nullable or arg2.expression_type.nullable
            )
        )

    def get_baserow_field_instance_and_type(self):
        # Until Baserow has a duration field type implement the required methods below
        return self, self

    def get_model_field(self, instance, **kwargs) -> models.Field:
        from baserow.contrib.database.fields.fields import (
            DurationFieldUsingPostgresFormatting,
        )

        kwargs["null"] = True
        kwargs["blank"] = True

        return DurationFieldUsingPostgresFormatting(**kwargs)

    def get_response_serializer_field(self, instance, **kwargs) -> Optional[Field]:
        return self.get_serializer_field(instance, **kwargs)

    def get_serializer_field(self, instance, **kwargs) -> Optional[Field]:
        required = kwargs.get("required", False)

        return serializers.CharField(
            **{"required": required, "allow_null": not required, **kwargs}
        )

    def get_export_value(self, value, field_object, rich_value=False) -> Any:
        if rich_value:
            return value
        else:
            return value if value is not None else ""

    def contains_query(self, field_name, value, model_field, field):
        return Q()

    def get_alter_column_prepare_old_value(self, connection, from_field, to_field):
        return None

    def get_human_readable_value(self, value: Any, field_object) -> str:
        human_readable_value = self.get_export_value(
            value, field_object, rich_value=False
        )
        if human_readable_value is None:
            return ""
        else:
            return str(human_readable_value)

    def placeholder_empty_value(self):
        return Value(datetime.timedelta(hours=0), output_field=models.DurationField())

    def placeholder_empty_baserow_expression(
        self,
    ) -> "BaserowExpression[BaserowFormulaValidType]":
        return literal(datetime.timedelta(hours=0))


class BaserowFormulaDateType(BaserowFormulaValidType):
    type = "date"
    baserow_field_type = "date"
    user_overridable_formatting_option_fields = [
        "date_format",
        "date_include_time",
        "date_time_format",
        "date_show_tzinfo",
        "date_force_timezone",
    ]
    nullable_option_fields = ["date_force_timezone"]

    def __init__(
        self,
        date_format: str,
        date_include_time: bool,
        date_time_format: str,
        date_show_tzinfo: bool = False,
        date_force_timezone: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.date_format = date_format
        self.date_include_time = date_include_time
        self.date_time_format = date_time_format
        self.date_show_tzinfo = date_show_tzinfo
        self.date_force_timezone = date_force_timezone

    @property
    def comparable_types(self) -> List[Type["BaserowFormulaValidType"]]:
        return [
            type(self),
            BaserowFormulaTextType,
        ]

    @property
    def limit_comparable_types(self) -> List[Type["BaserowFormulaValidType"]]:
        return [type(self)]

    @property
    def addable_types(self) -> List[Type["BaserowFormulaValidType"]]:
        return [BaserowFormulaDateIntervalType]

    @property
    def subtractable_types(self) -> List[Type["BaserowFormulaValidType"]]:
        return [type(self), BaserowFormulaDateIntervalType]

    def add(
        self,
        add_func_call: "BaserowFunctionCall[UnTyped]",
        arg1: "BaserowExpression[BaserowFormulaValidType]",
        arg2: "BaserowExpression[BaserowFormulaValidType]",
    ):
        return add_func_call.with_valid_type(
            _calculate_addition_interval_type(arg1, arg2)
        )

    def minus(
        self,
        minus_func_call: "BaserowFunctionCall[UnTyped]",
        arg1: "BaserowExpression[BaserowFormulaValidType]",
        arg2: "BaserowExpression[BaserowFormulaValidType]",
    ):
        arg1_type = arg1.expression_type
        arg2_type = arg2.expression_type
        if isinstance(arg2_type, BaserowFormulaDateType):
            # date - date = interval
            resulting_type = BaserowFormulaDateIntervalType(
                nullable=arg1_type.nullable or arg2_type.nullable
            )
        else:
            # date - interval = date
            resulting_type = arg1_type
        return minus_func_call.with_valid_type(resulting_type)

    def should_recreate_when_old_type_was(self, old_type: "BaserowFormulaType") -> bool:
        if isinstance(old_type, BaserowFormulaDateType):
            return self.date_include_time != old_type.date_include_time
        else:
            return True

    def wrap_at_field_level(self, expr: "BaserowExpression[BaserowFormulaType]"):
        wrapped = formula_function_registry.get("bc_to_null")(expr)
        return super().wrap_at_field_level(wrapped)

    def unwrap_at_field_level(self, expr: "BaserowFunctionCall[BaserowFormulaType]"):
        unwrapped = super().unwrap_at_field_level(expr)
        return expr.args[0].with_valid_type(unwrapped.expression_type)

    def cast_to_text(
        self,
        to_text_func_call: BaserowFunctionCall[UnTyped],
        arg: BaserowExpression[BaserowFormulaValidType],
    ) -> BaserowExpression[BaserowFormulaValidType]:
        when_empty_func = formula_function_registry.get("when_empty")
        datetime_fmt_func = formula_function_registry.get("datetime_format")
        datetime_text_literal = datetime_fmt_func(
            arg, literal(get_date_time_format(self, "sql"))
        )
        return when_empty_func(datetime_text_literal, literal(""))

    def placeholder_empty_value(self):
        if self.date_include_time:
            field = models.DateTimeField()
        else:
            field = models.DateField()

        return Value(timezone.now(), output_field=field)

    def __str__(self) -> str:
        date_or_datetime = "datetime" if self.date_include_time else "date"
        optional_time_format = (
            f", {self.date_time_format}" if self.date_include_time else ""
        )
        return f"{date_or_datetime}({self.date_format}{optional_time_format})"


class BaserowFormulaArrayType(BaserowFormulaValidType):
    type = "array"
    user_overridable_formatting_option_fields = [
        "array_formula_type",
    ]
    can_order_by = False

    def __init__(self, sub_type: BaserowFormulaValidType, **kwargs):
        super().__init__(**kwargs)
        self.array_formula_type = sub_type.type
        self.sub_type = sub_type

    @classmethod
    def construct_type_from_formula_field(cls, formula_field):
        sub_type_cls = _lookup_formula_type_from_string(
            formula_field.array_formula_type
        )
        sub_type = sub_type_cls.construct_type_from_formula_field(formula_field)
        return cls(sub_type)

    def persist_onto_formula_field(self, formula_field):
        self.sub_type.persist_onto_formula_field(formula_field)
        formula_field.array_formula_type = self.sub_type.type
        formula_field.formula_type = self.type

    def new_type_with_user_and_calculated_options_merged(self, formula_field):
        new_sub_type = self.sub_type.new_type_with_user_and_calculated_options_merged(
            formula_field
        )
        return self.__class__(new_sub_type)

    def collapse_many(self, expr: "BaserowExpression[BaserowFormulaType]"):
        func = formula_function_registry.get("array_agg_unnesting")
        return func(expr)

    def placeholder_empty_value(self):
        """
        The use of `array_agg_unnesting` in `self.collapse_many` above means that we can
        never have null values inserted into array fields but instead they should be
        empty lists.

        This is because during template imports we can run update statements using
        `array_agg_unnesting` over array fields which have just been filled with empty
        data and not had their actual values calculated yet. If they instead defaulted
        to Value(None) (null) these update statements would fail as the use of
        `jsonb_array_elements` by `array_agg_unnesting` crashes if you give in null
        instead of [] with
        `django.db.utils.DataError: cannot extract elements from a scalar`
        """

        return Value([], output_field=JSONField())

    def wrap_at_field_level(self, expr: "BaserowExpression[BaserowFormulaType]"):
        return formula_function_registry.get("error_to_null")(expr)

    def unwrap_at_field_level(self, expr: "BaserowFunctionCall[BaserowFormulaType]"):
        arg = expr.args[0]
        # By unwrapping a field's array_agg we can then use our own aggregate
        # functions or apply our own transformations on the underlying many
        # expression.
        single_unnest = formula_function_registry.get("array_agg")
        double_unnest = formula_function_registry.get("array_agg_unnesting")

        sub_type = expr.expression_type.sub_type
        if isinstance(arg, BaserowFunctionCall):
            if arg.function_def.type == single_unnest.type:
                arg = arg.args[0]
            elif arg.function_def.type == double_unnest.type:
                arg = arg.args[0]
                sub_type = BaserowFormulaArrayType(sub_type)

        return arg.with_valid_type(sub_type)

    @property
    def baserow_field_type(self) -> str:
        return "unknown"

    @property
    def comparable_types(self) -> List[Type["BaserowFormulaValidType"]]:
        return []

    @property
    def limit_comparable_types(self) -> List[Type["BaserowFormulaValidType"]]:
        return []

    def get_baserow_field_instance_and_type(self):
        # Until Baserow has a array field type implement the required methods below
        return self, self

    def get_model_field(self, instance, **kwargs) -> models.Field:
        return JSONField(default=list, **kwargs)

    def get_response_serializer_field(self, instance, **kwargs) -> Optional[Field]:
        return self.get_serializer_field(instance, **kwargs)

    def get_serializer_field(self, instance, **kwargs) -> Optional[Field]:
        required = kwargs.get("required", False)

        from baserow.contrib.database.api.fields.serializers import ArrayValueSerializer

        (
            instance,
            field_type,
        ) = self.sub_type.get_baserow_field_instance_and_type()
        return serializers.ListSerializer(
            **{
                "required": required,
                "allow_null": not required,
                "child": ArrayValueSerializer(
                    field_type.get_response_serializer_field(instance)
                ),
                **kwargs,
            }
        )

    def get_export_value(self, value, field_object, rich_value=False) -> Any:
        if value is None:
            return [] if rich_value else ""

        field_instance, field_type = self.sub_type.get_baserow_field_instance_and_type()
        field_obj = {
            "field": field_instance,
            "type": field_type,
            "name": field_object["name"],
        }

        result = self._map_safely_across_lookup_json_value_list(
            lambda safe_value: field_type.get_export_value(
                safe_value, field_obj, rich_value=rich_value
            ),
            value,
        )

        if rich_value:
            return result
        else:
            return list_to_comma_separated_string(result)

    def contains_query(self, field_name, value, model_field, field):
        return Q()

    def get_alter_column_prepare_old_value(self, connection, from_field, to_field):
        return "p_in = '';"

    def get_human_readable_value(self, value: Any, field_object) -> str:
        if value is None:
            return ""

        field_instance, field_type = self.sub_type.get_baserow_field_instance_and_type()
        field_obj = {
            "field": field_instance,
            "type": field_type,
            "name": field_object["name"],
        }

        human_readable_values = self._map_safely_across_lookup_json_value_list(
            lambda safe_value: field_type.get_human_readable_value(
                safe_value, field_obj
            ),
            value,
        )

        return ", ".join(human_readable_values)

    def _map_safely_across_lookup_json_value_list(
        self, map_func, lookup_json_value_list
    ):
        human_readable_values = []
        for v in lookup_json_value_list:
            lookup_json_value_list = v["value"]
            if lookup_json_value_list is not None and self.sub_type.type == "date":
                # Arrays are stored as JSON which means the dates are converted to
                # strings, we need to reparse them back first before giving it to
                # the date field type.
                lookup_json_value_list = parser.isoparse(lookup_json_value_list)
            export_value = map_func(lookup_json_value_list)
            if export_value is None:
                export_value = ""
            human_readable_values.append(export_value)
        return human_readable_values

    def __str__(self) -> str:
        return f"array({self.sub_type})"


class BaserowFormulaSingleSelectType(BaserowFormulaValidType):
    type = "single_select"
    baserow_field_type = "single_select"
    can_order_by = False

    @property
    def comparable_types(self) -> List[Type["BaserowFormulaValidType"]]:
        return [
            type(self),
        ]

    @property
    def limit_comparable_types(self) -> List[Type["BaserowFormulaValidType"]]:
        # true > true makes no sense
        return []

    def get_baserow_field_instance_and_type(self):
        # Until Baserow has a array field type implement the required methods below
        return self, self

    def get_model_field(self, instance, **kwargs) -> models.Field:
        return JSONField(default=dict, **kwargs)

    def get_response_serializer_field(self, instance, **kwargs) -> Optional[Field]:
        instance, field_type = super().get_baserow_field_instance_and_type()
        return field_type.get_response_serializer_field(instance, **kwargs)

    def get_serializer_field(self, *args, **kwargs) -> Optional[Field]:
        instance, field_type = super().get_baserow_field_instance_and_type()
        return field_type.get_response_serializer_field(instance, **kwargs)

    def get_export_value(self, value, field_object, rich_value=False) -> Any:
        if value is None:
            return value if rich_value else ""
        return value["value"]

    def contains_query(self, field_name, value, model_field, field):
        value = value.strip()
        # If an empty value has been provided we do not want to filter at all.
        if value == "":
            return Q()
        return Q(**{f"{field_name}__value__icontains": value})

    def get_alter_column_prepare_old_value(self, connection, from_field, to_field):
        sql = f"""
            p_in = p_in->'value';
        """
        return sql, {}

    def get_human_readable_value(self, value, field_object) -> str:
        if value is None:
            return ""
        return self.get_export_value(value, field_object, rich_value=False)

    def cast_to_text(
        self,
        to_text_func_call: "BaserowFunctionCall[UnTyped]",
        arg: "BaserowExpression[BaserowFormulaValidType]",
    ) -> "BaserowExpression[BaserowFormulaType]":
        single_select_value = formula_function_registry.get("get_single_select_value")(
            arg
        )
        return formula_function_registry.get("when_empty")(
            single_select_value, literal("")
        )


BASEROW_FORMULA_TYPES = [
    BaserowFormulaInvalidType,
    BaserowFormulaTextType,
    BaserowFormulaCharType,
    BaserowFormulaLinkType,
    BaserowFormulaDateIntervalType,
    BaserowFormulaDateType,
    BaserowFormulaBooleanType,
    BaserowFormulaNumberType,
    BaserowFormulaArrayType,
    BaserowFormulaSingleSelectType,
]

BASEROW_FORMULA_TYPE_ALLOWED_FIELDS = list(
    set(
        allowed_field for f in BASEROW_FORMULA_TYPES for allowed_field in f.all_fields()
    )
)

BASEROW_FORMULA_TYPE_CHOICES = [(f.type, f.type) for f in BASEROW_FORMULA_TYPES]
BASEROW_FORMULA_ARRAY_TYPE_CHOICES = [
    (f.type, f.type)
    for f in BASEROW_FORMULA_TYPES
    if f.type != BaserowFormulaArrayType.type
]


def calculate_number_type(
    arg_types: List[BaserowFormulaNumberType], min_decimal_places=0
):
    max_number_decimal_places = min_decimal_places
    for a in arg_types:
        max_number_decimal_places = max(
            max_number_decimal_places, a.number_decimal_places
        )

    return BaserowFormulaNumberType(number_decimal_places=max_number_decimal_places)


def _lookup_formula_type_from_string(formula_type_string):
    for possible_type in BASEROW_FORMULA_TYPES:
        if formula_type_string == possible_type.type:
            return possible_type
    raise UnknownFormulaType(formula_type_string)


def literal(
    arg: Union[str, int, bool, Decimal, datetime.timedelta]
) -> BaserowExpression[BaserowFormulaValidType]:
    """
    A helper function for building BaserowExpressions with literals
    :param arg: The literal
    :return: The literal wrapped in the corresponding valid typed BaserowExpression
        literal.
    """

    if isinstance(arg, str):
        return BaserowStringLiteral(arg, BaserowFormulaTextType())
    elif isinstance(arg, bool):
        return BaserowBooleanLiteral(arg, BaserowFormulaBooleanType())
    elif isinstance(arg, int):
        return BaserowIntegerLiteral(
            arg, BaserowFormulaNumberType(number_decimal_places=0)
        )
    elif isinstance(arg, Decimal):
        decimal_literal_expr = BaserowDecimalLiteral(arg, None)
        return decimal_literal_expr.with_valid_type(
            BaserowFormulaNumberType(decimal_literal_expr.num_decimal_places())
        )
    elif isinstance(arg, datetime.timedelta):
        return formula_function_registry.get("date_interval")(literal("0 hours"))

    raise TypeError(f"Unknown literal type {type(arg)}")
