from typing import List, Type, Optional, Any

from django.db import models
from django.db.models import Q
from rest_framework import serializers
from rest_framework.fields import Field

from baserow.contrib.database.fields.mixins import (
    get_date_time_format,
)
from baserow.contrib.database.formula.ast.tree import (
    BaserowExpression,
    BaserowFunctionCall,
    BaserowStringLiteral,
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


def construct_type_from_formula_field(
    formula_field: "models.FormulaField",
) -> BaserowFormulaType:
    """
    Gets the BaserowFormulaType the provided formula field currently has. This will
    vary depending on the formula of the field.

    :param formula_field: An instance of a formula field.
    :return: The BaserowFormulaType of the formula field instance.
    """

    for formula_type in BASEROW_FORMULA_TYPES:
        if formula_field.formula_type == formula_type.type:
            return formula_type.construct_type_from_formula_field(formula_field)
    raise UnknownFormulaType(formula_field.formula_type)


BASEROW_FORMULA_TYPES = [
    BaserowFormulaInvalidType,
    BaserowFormulaTextType,
    BaserowFormulaCharType,
    BaserowFormulaDateIntervalType,
    BaserowFormulaDateType,
    BaserowFormulaBooleanType,
    BaserowFormulaNumberType,
]

BASEROW_FORMULA_TYPE_ALLOWED_FIELDS = [
    allowed_field for f in BASEROW_FORMULA_TYPES for allowed_field in f.all_fields()
]

BASEROW_FORMULA_TYPE_CHOICES = [(f.type, f.type) for f in BASEROW_FORMULA_TYPES]


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
