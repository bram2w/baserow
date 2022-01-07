from decimal import Decimal
from typing import List, Type, Optional, Any, Union

from dateutil import parser
from django.db import models
from django.db.models import Q, JSONField
from rest_framework import serializers
from rest_framework.fields import Field

from baserow.contrib.database.fields.mixins import (
    get_date_time_format,
)
from baserow.contrib.database.formula.ast.tree import (
    BaserowExpression,
    BaserowFunctionCall,
    BaserowStringLiteral,
    BaserowIntegerLiteral,
    BaserowBooleanLiteral,
    BaserowDecimalLiteral,
)
from baserow.contrib.database.formula.registries import (
    formula_function_registry,
)
from baserow.contrib.database.formula.types.exceptions import UnknownFormulaType
from baserow.contrib.database.formula.types.formula_type import (
    BaserowFormulaValidType,
    UnTyped,
    BaserowFormulaType,
    BaserowFormulaInvalidType,
)


class BaserowFormulaTextType(BaserowFormulaValidType):
    type = "text"
    baserow_field_type = "text"

    @property
    def comparable_types(self) -> List[Type["BaserowFormulaValidType"]]:
        return [
            BaserowFormulaTextType,
            BaserowFormulaDateType,
            BaserowFormulaNumberType,
            BaserowFormulaBooleanType,
            BaserowFormulaCharType,
        ]

    @property
    def limit_comparable_types(self) -> List[Type["BaserowFormulaValidType"]]:
        # Force users to explicitly convert to text before doing any limit comparison
        # operators as lexicographical comparison can be surprising and so should be opt
        # in
        return [BaserowFormulaTextType, BaserowFormulaCharType]

    @property
    def addable_types(self) -> List[Type["BaserowFormulaValidType"]]:
        return [BaserowFormulaTextType, BaserowFormulaCharType]

    def add(
        self,
        add_func_call: "BaserowFunctionCall[UnTyped]",
        arg1: "BaserowExpression[BaserowFormulaTextType]",
        arg2: "BaserowExpression[BaserowFormulaTextType]",
    ):
        return formula_function_registry.get("concat").call_and_type_with_args(
            [arg1, arg2]
        )

    def cast_to_text(
        self,
        to_text_func_call: "BaserowFunctionCall[UnTyped]",
        arg: "BaserowExpression[BaserowFormulaValidType]",
    ) -> "BaserowExpression[BaserowFormulaType]":
        # Explicitly unwrap the func_call here and just return the arg as it is already
        # in the text type and we don't want to return to_text(arg) but instead just
        # arg.
        return arg


class BaserowFormulaCharType(BaserowFormulaTextType):
    type = "char"
    baserow_field_type = "text"

    def cast_to_text(
        self,
        to_text_func_call: "BaserowFunctionCall[UnTyped]",
        arg: "BaserowExpression[BaserowFormulaValidType]",
    ) -> "BaserowExpression[BaserowFormulaType]":
        # Force char fields to be casted to text so Django does not complain
        return to_text_func_call.with_valid_type(BaserowFormulaTextType())


class BaserowFormulaNumberType(BaserowFormulaValidType):
    type = "number"
    baserow_field_type = "number"
    user_overridable_formatting_option_fields = ["number_decimal_places"]
    MAX_DIGITS = 50

    def __init__(self, number_decimal_places: int):
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
        return formula_function_registry.get("error_to_nan").call_and_type_with(expr)

    def unwrap_at_field_level(self, expr: "BaserowFunctionCall[BaserowFormulaType]"):
        return expr.args[0].with_valid_type(expr.expression_type)

    def __str__(self) -> str:
        return f"number({self.number_decimal_places})"


class BaserowFormulaBooleanType(BaserowFormulaValidType):
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
    return resulting_type


# noinspection PyMethodMayBeStatic
class BaserowFormulaDateIntervalType(BaserowFormulaValidType):
    type = "date_interval"
    baserow_field_type = None

    @property
    def comparable_types(self) -> List[Type["BaserowFormulaValidType"]]:
        return [
            type(self),
        ]

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
        return minus_func_call.with_valid_type(BaserowFormulaDateIntervalType())

    def get_baserow_field_instance_and_type(self):
        # Until Baserow has a duration field type implement the required methods below
        return self, self

    def get_model_field(self, instance, **kwargs) -> models.Field:
        kwargs["null"] = True
        kwargs["blank"] = True
        return models.DurationField()

    def get_response_serializer_field(self, instance, **kwargs) -> Optional[Field]:
        return self.get_serializer_field(instance, **kwargs)

    def get_serializer_field(self, instance, **kwargs) -> Optional[Field]:
        required = kwargs.get("required", False)

        return serializers.DurationField(
            **{"required": required, "allow_null": not required, **kwargs}
        )

    def get_export_value(self, value, field_object) -> Any:
        return value

    def contains_query(self, field_name, value, model_field, field):
        return Q()

    def get_alter_column_prepare_old_value(self, connection, from_field, to_field):
        return None

    def get_human_readable_value(self, value: Any, field_object) -> str:
        human_readable_value = self.get_export_value(value, field_object)
        if human_readable_value is None:
            return ""
        else:
            return str(human_readable_value)


class BaserowFormulaDateType(BaserowFormulaValidType):
    type = "date"
    baserow_field_type = "date"
    user_overridable_formatting_option_fields = [
        "date_format",
        "date_include_time",
        "date_time_format",
    ]

    def __init__(
        self, date_format: str, date_include_time: bool, date_time_format: str
    ):
        self.date_format = date_format
        self.date_include_time = date_include_time
        self.date_time_format = date_time_format

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
            resulting_type = BaserowFormulaDateIntervalType()
        else:
            # date - interval = date
            resulting_type = arg1_type
        return minus_func_call.with_valid_type(resulting_type)

    def should_recreate_when_old_type_was(self, old_type: "BaserowFormulaType") -> bool:
        if isinstance(old_type, BaserowFormulaDateType):
            return self.date_include_time != old_type.date_include_time
        else:
            return True

    def cast_to_text(
        self,
        to_text_func_call: BaserowFunctionCall[UnTyped],
        arg: BaserowExpression[BaserowFormulaValidType],
    ) -> BaserowExpression[BaserowFormulaValidType]:
        return BaserowFunctionCall[BaserowFormulaValidType](
            formula_function_registry.get("datetime_format"),
            [
                arg,
                BaserowStringLiteral(
                    get_date_time_format(self, "sql"), BaserowFormulaTextType()
                ),
            ],
            BaserowFormulaTextType(),
        )

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

    def __init__(self, sub_type: BaserowFormulaValidType):
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
        return func.call_and_type_with(expr)

    def wrap_at_field_level(self, expr: "BaserowExpression[BaserowFormulaType]"):
        return formula_function_registry.get("error_to_null").call_and_type_with(expr)

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

    def get_export_value(self, value, field_object) -> Any:
        if value is None:
            return []

        i, field_type = self.sub_type.get_baserow_field_instance_and_type()

        field_obj = {"field": i, "type": field_type, "name": field_object["name"]}
        result = []
        for v in value:
            value = v["value"]
            if value is not None and self.sub_type.type == "date":
                # Arrays are stored as JSON which means the dates are converted to
                # strings, we need to reparse them back first before giving it to
                # the date field type.
                value = parser.isoparse(value)
            export_value = field_type.get_export_value(value, field_obj)
            if export_value is None:
                export_value = ""
            result.append(export_value)
        return result

    def contains_query(self, field_name, value, model_field, field):
        return Q()

    def get_alter_column_prepare_old_value(self, connection, from_field, to_field):
        return "p_in = '';"

    def get_human_readable_value(self, value: Any, field_object) -> str:
        if value is None:
            return ""

        i, field_type = self.sub_type.get_baserow_field_instance_and_type()

        export_values = self.get_export_value(value, field_object)
        field_obj = {"field": i, "type": field_type, "name": field_object["name"]}
        return ", ".join(
            [field_type.get_human_readable_value(v, field_obj) for v in export_values]
        )

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
        return models.JSONField(default=dict, **kwargs)

    def get_response_serializer_field(self, instance, **kwargs) -> Optional[Field]:
        instance, field_type = super().get_baserow_field_instance_and_type()
        return field_type.get_response_serializer_field(instance, **kwargs)

    def get_serializer_field(self, *args, **kwargs) -> Optional[Field]:
        instance, field_type = super().get_baserow_field_instance_and_type()
        return field_type.get_response_serializer_field(instance, **kwargs)

    def get_export_value(self, value, field_object) -> Any:
        if value is None:
            return value
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
        return self.get_export_value(value, field_object)

    def cast_to_text(
        self,
        to_text_func_call: "BaserowFunctionCall[UnTyped]",
        arg: "BaserowExpression[BaserowFormulaValidType]",
    ) -> "BaserowExpression[BaserowFormulaType]":
        get_value_func = formula_function_registry.get("get_single_select_value")
        return get_value_func.call_and_type_with(arg)


BASEROW_FORMULA_TYPES = [
    BaserowFormulaInvalidType,
    BaserowFormulaTextType,
    BaserowFormulaCharType,
    BaserowFormulaDateIntervalType,
    BaserowFormulaDateType,
    BaserowFormulaBooleanType,
    BaserowFormulaNumberType,
    BaserowFormulaArrayType,
    BaserowFormulaSingleSelectType,
]

BASEROW_FORMULA_TYPE_ALLOWED_FIELDS = [
    allowed_field for f in BASEROW_FORMULA_TYPES for allowed_field in f.all_fields()
]

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

    return BaserowFormulaNumberType(
        number_decimal_places=max_number_decimal_places,
    )


def _lookup_formula_type_from_string(formula_type_string):
    for possible_type in BASEROW_FORMULA_TYPES:
        if formula_type_string == possible_type.type:
            return possible_type
    raise UnknownFormulaType(formula_type_string)


def literal(
    arg: Union[str, int, bool, Decimal]
) -> BaserowExpression[BaserowFormulaValidType]:
    """
    A helper function for building BaserowExpressions with literals
    :param arg: The literal
    :return: The literal wrapped in the corrosponding valid typed BaserowExpression
        literal.
    """

    if isinstance(arg, str):
        return BaserowStringLiteral(arg, BaserowFormulaTextType())
    elif isinstance(arg, int):
        return BaserowIntegerLiteral(
            arg, BaserowFormulaNumberType(number_decimal_places=0)
        )
    elif isinstance(arg, bool):
        return BaserowBooleanLiteral(arg, BaserowFormulaBooleanType())
    elif isinstance(arg, Decimal):
        decimal_literal_expr = BaserowDecimalLiteral(arg, None)
        return decimal_literal_expr.with_valid_type(
            BaserowFormulaNumberType(decimal_literal_expr.num_decimal_places())
        )
