from abc import ABC
from decimal import Decimal
from typing import List, Optional, Type, Dict, Set

from django.contrib.postgres.aggregates import JSONBAgg
from django.db.models import (
    Expression,
    Value,
    Case,
    When,
    fields,
    Func,
    F,
    ExpressionWrapper,
    Model,
    Count,
    Sum,
    JSONField,
    Variance,
    Max,
    Min,
    Avg,
    StdDev,
)
from django.db.models.functions import (
    Upper,
    Lower,
    Concat,
    Coalesce,
    Cast,
    Greatest,
    Extract,
    Replace,
    StrIndex,
    Length,
    Reverse,
    JSONObject,
    Least,
    Left,
    Right,
)

from baserow.contrib.database.fields.models import (
    NUMBER_MAX_DECIMAL_PLACES,
)
from baserow.contrib.database.formula.ast.function import (
    BaserowFunctionDefinition,
    NumOfArgsGreaterThan,
    OneArgumentBaserowFunction,
    TwoArgumentBaserowFunction,
    ThreeArgumentBaserowFunction,
    ZeroArgumentBaserowFunction,
    aggregate_wrapper,
)
from baserow.contrib.database.formula.ast.tree import (
    BaserowFunctionCall,
    BaserowExpression,
)
from baserow.contrib.database.formula.expression_generator.django_expressions import (
    EqualsExpr,
    NotExpr,
    NotEqualsExpr,
    GreaterThanExpr,
    GreaterThanOrEqualExpr,
    LessThanExpr,
    LessThanEqualOrExpr,
    AndExpr,
    OrExpr,
    BaserowStringAgg,
)
from baserow.contrib.database.formula.expression_generator.exceptions import (
    BaserowToDjangoExpressionGenerationError,
)
from baserow.contrib.database.formula.types.formula_type import (
    BaserowFormulaType,
    BaserowFormulaValidType,
    UnTyped,
    BaserowArgumentTypeChecker,
)
from baserow.contrib.database.formula.types.formula_types import (
    BaserowFormulaTextType,
    BaserowFormulaDateType,
    BaserowFormulaNumberType,
    BaserowFormulaBooleanType,
    calculate_number_type,
    BaserowFormulaDateIntervalType,
    BaserowFormulaArrayType,
    BaserowFormulaSingleSelectType,
    BaserowFormulaCharType,
    literal,
)
from baserow.contrib.database.formula.types.type_checkers import OnlyIntegerNumberTypes


def register_formula_functions(registry):
    # Text functions
    registry.register(BaserowUpper())
    registry.register(BaserowLower())
    registry.register(BaserowConcat())
    registry.register(BaserowToText())
    registry.register(BaserowT())
    registry.register(BaserowReplace())
    registry.register(BaserowSearch())
    registry.register(BaserowLength())
    registry.register(BaserowReverse())
    registry.register(BaserowContains())
    registry.register(BaserowLeft())
    registry.register(BaserowRight())
    registry.register(BaserowTrim())
    registry.register(BaserowRegexReplace())
    # Number functions
    registry.register(BaserowMultiply())
    registry.register(BaserowDivide())
    registry.register(BaserowToNumber())
    registry.register(BaserowErrorToNan())
    registry.register(BaserowGreatest())
    registry.register(BaserowLeast())
    # Boolean functions
    registry.register(BaserowIf())
    registry.register(BaserowEqual())
    registry.register(BaserowIsBlank())
    registry.register(BaserowNot())
    registry.register(BaserowNotEqual())
    registry.register(BaserowGreaterThan())
    registry.register(BaserowGreaterThanOrEqual())
    registry.register(BaserowLessThan())
    registry.register(BaserowLessThanOrEqual())
    registry.register(BaserowAnd())
    registry.register(BaserowOr())
    # Date functions
    registry.register(BaserowDatetimeFormat())
    registry.register(BaserowDay())
    registry.register(BaserowMonth())
    registry.register(BaserowYear())
    registry.register(BaserowSecond())
    registry.register(BaserowToDate())
    registry.register(BaserowDateDiff())
    # Date interval functions
    registry.register(BaserowDateInterval())
    # Special functions
    registry.register(BaserowAdd())
    registry.register(BaserowMinus())
    registry.register(BaserowErrorToNull())
    registry.register(BaserowRowId())
    registry.register(BaserowWhenEmpty())
    # Array functions
    registry.register(BaserowArrayAgg())
    registry.register(Baserow2dArrayAgg())
    registry.register(BaserowAny())
    registry.register(BaserowEvery())
    registry.register(BaserowMax())
    registry.register(BaserowMin())
    registry.register(BaserowCount())
    registry.register(BaserowFilter())
    registry.register(BaserowAggJoin())
    registry.register(BaserowStdDevPop())
    registry.register(BaserowStdDevSample())
    registry.register(BaserowVarianceSample())
    registry.register(BaserowVariancePop())
    registry.register(BaserowAvg())
    registry.register(BaserowSum())
    # Single Select functions
    registry.register(BaserowGetSingleSelectValue())


class BaserowUpper(OneArgumentBaserowFunction):

    type = "upper"
    arg_type = [BaserowFormulaTextType]

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
        arg: BaserowExpression[BaserowFormulaValidType],
    ) -> BaserowExpression[BaserowFormulaType]:
        return func_call.with_valid_type(BaserowFormulaTextType())

    def to_django_expression(self, arg: Expression) -> Expression:
        return Upper(arg, output_field=fields.TextField())


class BaserowLower(OneArgumentBaserowFunction):
    type = "lower"
    arg_type = [BaserowFormulaTextType]

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
        arg: BaserowExpression[BaserowFormulaValidType],
    ) -> BaserowExpression[BaserowFormulaType]:
        return func_call.with_valid_type(BaserowFormulaTextType())

    def to_django_expression(self, arg: Expression) -> Expression:
        return Lower(arg, output_field=fields.TextField())


class BaserowDatetimeFormat(TwoArgumentBaserowFunction):
    type = "datetime_format"
    arg1_type = [BaserowFormulaDateType]
    arg2_type = [BaserowFormulaTextType]

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
        arg1: BaserowExpression[BaserowFormulaValidType],
        arg2: BaserowExpression[BaserowFormulaValidType],
    ) -> BaserowExpression[BaserowFormulaType]:
        return func_call.with_valid_type(BaserowFormulaTextType())

    def to_django_expression(self, arg1: Expression, arg2: Expression) -> Expression:
        if isinstance(arg1, Value) and arg1.value is None:
            return Value("")
        return Coalesce(
            Func(
                arg1,
                arg2,
                function="to_char",
                output_field=fields.TextField(),
            ),
            Value(""),
            output_field=fields.TextField(),
        )


class BaserowToText(OneArgumentBaserowFunction):
    type = "totext"
    arg_type = [BaserowFormulaValidType]

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
        arg: BaserowExpression[BaserowFormulaValidType],
    ) -> BaserowExpression[BaserowFormulaType]:
        return arg.expression_type.cast_to_text(func_call, arg)

    def to_django_expression(self, arg: Expression) -> Expression:
        return Cast(arg, output_field=fields.TextField())


class BaserowT(OneArgumentBaserowFunction):
    type = "t"
    arg_type = [BaserowFormulaValidType]

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
        arg: BaserowExpression[BaserowFormulaValidType],
    ) -> BaserowExpression[BaserowFormulaType]:
        if isinstance(arg.expression_type, BaserowFormulaTextType):
            return arg
        else:
            return func_call.with_valid_type(BaserowFormulaTextType())

    def to_django_expression(self, arg: Expression) -> Expression:
        return Cast(Value(""), output_field=fields.TextField())


class BaserowConcat(BaserowFunctionDefinition):
    type = "concat"
    num_args = NumOfArgsGreaterThan(1)

    @property
    def arg_types(self) -> BaserowArgumentTypeChecker:
        return lambda _, _2: [BaserowFormulaValidType]

    def type_function_given_valid_args(
        self,
        args: List[BaserowExpression[BaserowFormulaValidType]],
        expression: "BaserowFunctionCall[UnTyped]",
    ) -> BaserowExpression[BaserowFormulaType]:
        return expression.with_args(
            [BaserowToText().call_and_type_with(a) for a in args]
        ).with_valid_type(BaserowFormulaTextType())

    def to_django_expression_given_args(
        self, expr_args: List[Expression], *args, **kwargs
    ) -> Expression:
        return Concat(*expr_args, output_field=fields.TextField())


class BaserowAdd(TwoArgumentBaserowFunction):
    type = "add"
    operator = "+"
    arg1_type = [BaserowFormulaNumberType]
    arg2_type = [BaserowFormulaNumberType]

    @property
    def arg_types(self) -> BaserowArgumentTypeChecker:
        def type_checker(arg_index: int, arg_types: List[BaserowFormulaType]):
            if arg_index == 1:
                return arg_types[0].addable_types
            else:
                return [BaserowFormulaValidType]

        return type_checker

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
        arg1: BaserowExpression[BaserowFormulaValidType],
        arg2: BaserowExpression[BaserowFormulaValidType],
    ) -> BaserowExpression[BaserowFormulaType]:
        return arg1.expression_type.add(func_call, arg1, arg2)

    def to_django_expression(self, arg1: Expression, arg2: Expression) -> Expression:
        # date + interval = date
        # non date/interval types + non date/interval types = first arg type always
        output_field = arg1.output_field
        if isinstance(arg1.output_field, fields.DurationField):
            # interval + interval = interval
            # interval + date = date
            output_field = arg2.output_field
        return ExpressionWrapper(arg1 + arg2, output_field=output_field)


class BaserowMultiply(TwoArgumentBaserowFunction):
    type = "multiply"
    operator = "*"
    arg1_type = [BaserowFormulaNumberType]
    arg2_type = [BaserowFormulaNumberType]

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
        arg1: BaserowExpression[BaserowFormulaNumberType],
        arg2: BaserowExpression[BaserowFormulaNumberType],
    ) -> BaserowExpression[BaserowFormulaType]:
        return func_call.with_valid_type(
            calculate_number_type([arg1.expression_type, arg2.expression_type])
        )

    def to_django_expression(self, arg1: Expression, arg2: Expression) -> Expression:
        return ExpressionWrapper(arg1 * arg2, output_field=arg1.output_field)


class BaserowMinus(TwoArgumentBaserowFunction):
    type = "minus"
    operator = "-"
    arg1_type = [BaserowFormulaNumberType]
    arg2_type = [BaserowFormulaNumberType]

    @property
    def arg_types(self) -> BaserowArgumentTypeChecker:
        def type_checker(arg_index: int, arg_types: List[BaserowFormulaType]):
            if arg_index == 1:
                # Only type check the left hand side is one of the subtractable types
                # of the right hand side argument.
                return arg_types[0].subtractable_types
            else:
                return [BaserowFormulaValidType]

        return type_checker

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
        arg1: BaserowExpression[BaserowFormulaValidType],
        arg2: BaserowExpression[BaserowFormulaValidType],
    ) -> BaserowExpression[BaserowFormulaType]:
        return arg1.expression_type.minus(func_call, arg1, arg2)

    def to_django_expression(self, arg1: Expression, arg2: Expression) -> Expression:
        output_field = arg1.output_field
        if isinstance(arg1.output_field, fields.DateField) and isinstance(
            arg2.output_field, fields.DateField
        ):
            output_field = fields.DurationField()
        return ExpressionWrapper(arg1 - arg2, output_field=output_field)


class BaserowGreatest(TwoArgumentBaserowFunction):
    type = "greatest"
    arg1_type = [BaserowFormulaNumberType]
    arg2_type = [BaserowFormulaNumberType]

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
        arg1: BaserowExpression[BaserowFormulaNumberType],
        arg2: BaserowExpression[BaserowFormulaNumberType],
    ) -> BaserowExpression[BaserowFormulaType]:
        return func_call.with_valid_type(
            calculate_number_type([arg1.expression_type, arg2.expression_type])
        )

    def to_django_expression(self, arg1: Expression, arg2: Expression) -> Expression:
        return Greatest(arg1, arg2, output_field=arg1.output_field)


class BaserowLeast(TwoArgumentBaserowFunction):
    type = "least"
    arg1_type = [BaserowFormulaNumberType]
    arg2_type = [BaserowFormulaNumberType]

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
        arg1: BaserowExpression[BaserowFormulaNumberType],
        arg2: BaserowExpression[BaserowFormulaNumberType],
    ) -> BaserowExpression[BaserowFormulaType]:
        return func_call.with_valid_type(
            calculate_number_type([arg1.expression_type, arg2.expression_type])
        )

    def to_django_expression(self, arg1: Expression, arg2: Expression) -> Expression:
        return Least(arg1, arg2, output_field=arg1.output_field)


class BaserowDivide(TwoArgumentBaserowFunction):
    type = "divide"
    operator = "/"

    arg1_type = [BaserowFormulaNumberType]
    arg2_type = [BaserowFormulaNumberType]

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
        arg1: BaserowExpression[BaserowFormulaNumberType],
        arg2: BaserowExpression[BaserowFormulaNumberType],
    ) -> BaserowExpression[BaserowFormulaType]:
        # Show all the decimal places we can by default if the user makes a formula
        # with a division to prevent weird results like `1/3=0`
        return func_call.with_valid_type(
            BaserowFormulaNumberType(NUMBER_MAX_DECIMAL_PLACES)
        )

    def to_django_expression(self, arg1: Expression, arg2: Expression) -> Expression:
        # Prevent divide by zero's by swapping 0 for NaN causing the entire expression
        # to evaluate to NaN. The front-end then treats NaN values as a per cell error
        # to display to the user.
        return ExpressionWrapper(
            arg1
            / Case(
                When(
                    condition=(EqualsExpr(arg2, 0, output_field=fields.BooleanField())),
                    then=Value(Decimal("NaN")),
                ),
                default=arg2,
            ),
            output_field=fields.DecimalField(decimal_places=NUMBER_MAX_DECIMAL_PLACES),
        )


class BaserowEqual(TwoArgumentBaserowFunction):
    type = "equal"
    operator = "="

    @property
    def arg_types(self) -> BaserowArgumentTypeChecker:
        def type_checker(arg_index: int, arg_types: List[BaserowFormulaType]):
            if arg_index == 1:
                return arg_types[0].comparable_types
            else:
                return [BaserowFormulaValidType]

        return type_checker

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
        arg1: BaserowExpression[BaserowFormulaValidType],
        arg2: BaserowExpression[BaserowFormulaValidType],
    ) -> BaserowExpression[BaserowFormulaType]:
        arg1_type = arg1.expression_type
        arg2_type = arg2.expression_type
        if not (type(arg1_type) is type(arg2_type)):
            # If trying to compare two types which can be compared, but are of different
            # types, then first cast them to text and then compare.
            # We to ourselves via the __class__ property here so subtypes of this type
            # use themselves here instead of us!
            return self.__class__().call_and_type_with(
                BaserowToText().call_and_type_with(arg1),
                BaserowToText().call_and_type_with(arg2),
            )
        else:
            return func_call.with_valid_type(BaserowFormulaBooleanType())

    def to_django_expression(self, arg1: Expression, arg2: Expression) -> Expression:
        return EqualsExpr(
            arg1,
            arg2,
            output_field=fields.BooleanField(),
        )


class BaserowIf(ThreeArgumentBaserowFunction):
    type = "if"

    arg1_type = [BaserowFormulaBooleanType]

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
        arg1: BaserowExpression[BaserowFormulaValidType],
        arg2: BaserowExpression[BaserowFormulaValidType],
        arg3: BaserowExpression[BaserowFormulaValidType],
    ) -> BaserowExpression[BaserowFormulaType]:
        arg2_type = arg2.expression_type
        arg3_type = arg3.expression_type
        if not (type(arg2_type) is type(arg3_type)):
            # Replace the current if func_call with one which casts both args to text
            # if they are of different types as PostgreSQL requires all cases of a case
            # statement to be of the same type.
            return BaserowIf().call_and_type_with(
                arg1,
                BaserowToText().call_and_type_with(arg2),
                BaserowToText().call_and_type_with(arg3),
            )
        else:
            if isinstance(arg2_type, BaserowFormulaNumberType) and isinstance(
                arg3_type, BaserowFormulaNumberType
            ):
                resulting_type = calculate_number_type([arg2_type, arg3_type])
            else:
                resulting_type = arg2_type

            return func_call.with_valid_type(resulting_type)

    def to_django_expression(
        self, arg1: Expression, arg2: Expression, arg3: Expression
    ) -> Expression:
        return Case(
            When(condition=arg1, then=arg2),
            default=arg3,
            output_field=arg1.output_field,
        )


class BaserowToNumber(OneArgumentBaserowFunction):
    type = "tonumber"
    arg_type = [BaserowFormulaTextType]

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
        arg: BaserowExpression[BaserowFormulaValidType],
    ) -> BaserowExpression[BaserowFormulaType]:
        return func_call.with_valid_type(
            BaserowFormulaNumberType(number_decimal_places=5)
        )

    def to_django_expression(self, arg: Expression) -> Expression:
        return Func(
            arg,
            function="try_cast_to_numeric",
            output_field=fields.DecimalField(decimal_places=0),
        )


class BaserowErrorToNan(OneArgumentBaserowFunction):
    type = "error_to_nan"
    arg_type = [BaserowFormulaNumberType]

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
        arg: BaserowExpression[BaserowFormulaValidType],
    ) -> BaserowExpression[BaserowFormulaType]:
        return func_call.with_valid_type(arg.expression_type)

    def to_django_expression(self, arg: Expression) -> Expression:
        return Func(
            arg, function="replace_errors_with_nan", output_field=arg.output_field
        )


class BaserowErrorToNull(OneArgumentBaserowFunction):
    type = "error_to_null"
    arg_type = [BaserowFormulaValidType]

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
        arg: BaserowExpression[BaserowFormulaValidType],
    ) -> BaserowExpression[BaserowFormulaType]:
        return func_call.with_valid_type(arg.expression_type)

    def to_django_expression(self, arg: Expression) -> Expression:
        return Func(
            arg, function="replace_errors_with_null", output_field=arg.output_field
        )


class BaserowIsBlank(OneArgumentBaserowFunction):
    type = "isblank"
    arg_type = [BaserowFormulaValidType]

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
        arg: BaserowExpression[BaserowFormulaValidType],
    ) -> BaserowExpression[BaserowFormulaType]:
        return func_call.with_args(
            [BaserowToText().call_and_type_with(arg)]
        ).with_valid_type(BaserowFormulaBooleanType())

    def to_django_expression(self, arg: Expression) -> Expression:
        return EqualsExpr(
            Coalesce(
                arg,
                Value(""),
            ),
            Value(""),
            output_field=fields.BooleanField(),
        )


class BaserowNot(OneArgumentBaserowFunction):
    type = "not"
    arg_type = [BaserowFormulaBooleanType]

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
        arg: BaserowExpression[BaserowFormulaBooleanType],
    ) -> BaserowExpression[BaserowFormulaType]:
        return func_call.with_valid_type(BaserowFormulaBooleanType())

    def to_django_expression(self, arg: Expression) -> Expression:
        return NotExpr(arg, output_field=fields.BooleanField())


class BaserowNotEqual(BaserowEqual):
    type = "not_equal"
    operator = "!="

    def to_django_expression(self, arg1: Expression, arg2: Expression) -> Expression:
        return NotEqualsExpr(
            arg1,
            arg2,
            output_field=fields.BooleanField(),
        )


class BaseLimitComparableFunction(TwoArgumentBaserowFunction, ABC):
    @property
    def arg_types(self) -> BaserowArgumentTypeChecker:
        def type_checker(arg_index: int, arg_types: List[BaserowFormulaType]):
            if arg_index == 1:
                return arg_types[0].limit_comparable_types
            else:
                return [BaserowFormulaValidType]

        return type_checker

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
        arg1: BaserowExpression[BaserowFormulaValidType],
        arg2: BaserowExpression[BaserowFormulaValidType],
    ) -> BaserowExpression[BaserowFormulaType]:
        return func_call.with_valid_type(BaserowFormulaBooleanType())


class BaserowGreaterThan(BaseLimitComparableFunction):
    type = "greater_than"
    operator = ">"

    def to_django_expression(self, arg1: Expression, arg2: Expression) -> Expression:
        return GreaterThanExpr(
            arg1,
            arg2,
            output_field=fields.BooleanField(),
        )


class BaserowGreaterThanOrEqual(BaseLimitComparableFunction):
    type = "greater_than_or_equal"
    operator = ">="

    def to_django_expression(self, arg1: Expression, arg2: Expression) -> Expression:
        return GreaterThanOrEqualExpr(
            arg1,
            arg2,
            output_field=fields.BooleanField(),
        )


class BaserowLessThan(BaseLimitComparableFunction):
    type = "less_than"
    operator = "<"

    def to_django_expression(self, arg1: Expression, arg2: Expression) -> Expression:
        return LessThanExpr(
            arg1,
            arg2,
            output_field=fields.BooleanField(),
        )


class BaserowLessThanOrEqual(BaseLimitComparableFunction):
    type = "less_than_or_equal"
    operator = "<="

    def to_django_expression(self, arg1: Expression, arg2: Expression) -> Expression:
        return LessThanEqualOrExpr(
            arg1,
            arg2,
            output_field=fields.BooleanField(),
        )


class BaserowToDate(TwoArgumentBaserowFunction):
    type = "todate"
    arg1_type = [BaserowFormulaTextType]
    arg2_type = [BaserowFormulaTextType]

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
        arg1: BaserowExpression[BaserowFormulaValidType],
        arg2: BaserowExpression[BaserowFormulaValidType],
    ) -> BaserowExpression[BaserowFormulaType]:
        return func_call.with_valid_type(
            BaserowFormulaDateType(
                date_format="ISO", date_include_time=False, date_time_format="24"
            )
        )

    def to_django_expression(self, arg1: Expression, arg2: Expression) -> Expression:
        return Func(
            arg1,
            arg2,
            function="try_cast_to_date",
            output_field=fields.DateTimeField(),
        )


class BaserowDay(OneArgumentBaserowFunction):
    type = "day"
    arg_type = [BaserowFormulaDateType]

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
        arg: BaserowExpression[BaserowFormulaValidType],
    ) -> BaserowExpression[BaserowFormulaType]:
        return func_call.with_valid_type(
            BaserowFormulaNumberType(number_decimal_places=0)
        )

    def to_django_expression(self, arg: Expression) -> Expression:
        return Extract(arg, "day", output_field=fields.DecimalField(decimal_places=0))


class BaserowMonth(OneArgumentBaserowFunction):
    type = "month"
    arg_type = [BaserowFormulaDateType]

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
        arg: BaserowExpression[BaserowFormulaValidType],
    ) -> BaserowExpression[BaserowFormulaType]:
        return func_call.with_valid_type(
            BaserowFormulaNumberType(number_decimal_places=0)
        )

    def to_django_expression(self, arg: Expression) -> Expression:
        return Extract(arg, "month", output_field=fields.DecimalField(decimal_places=0))


class BaserowDateDiff(ThreeArgumentBaserowFunction):
    type = "date_diff"

    arg1_type = [BaserowFormulaTextType]
    arg2_type = [BaserowFormulaDateType]
    arg3_type = [BaserowFormulaDateType]

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
        arg1: BaserowExpression[BaserowFormulaValidType],
        arg2: BaserowExpression[BaserowFormulaValidType],
        arg3: BaserowExpression[BaserowFormulaValidType],
    ) -> BaserowExpression[BaserowFormulaType]:
        return func_call.with_valid_type(
            BaserowFormulaNumberType(number_decimal_places=0)
        )

    def to_django_expression(
        self, arg1: Expression, arg2: Expression, arg3: Expression
    ) -> Expression:
        return Func(
            arg1,
            arg2,
            arg3,
            function="date_diff",
            output_field=fields.DecimalField(decimal_places=0),
        )


class BaserowAnd(TwoArgumentBaserowFunction):
    type = "and"
    arg1_type = [BaserowFormulaBooleanType]
    arg2_type = [BaserowFormulaBooleanType]

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
        arg1: BaserowExpression[BaserowFormulaValidType],
        arg2: BaserowExpression[BaserowFormulaValidType],
    ) -> BaserowExpression[BaserowFormulaType]:
        return func_call.with_valid_type(BaserowFormulaBooleanType())

    def to_django_expression(self, arg1: Expression, arg2: Expression) -> Expression:
        return AndExpr(arg1, arg2, output_field=fields.BooleanField())


class BaserowOr(TwoArgumentBaserowFunction):
    type = "or"
    arg1_type = [BaserowFormulaBooleanType]
    arg2_type = [BaserowFormulaBooleanType]

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
        arg1: BaserowExpression[BaserowFormulaValidType],
        arg2: BaserowExpression[BaserowFormulaValidType],
    ) -> BaserowExpression[BaserowFormulaType]:
        return func_call.with_valid_type(BaserowFormulaBooleanType())

    def to_django_expression(self, arg1: Expression, arg2: Expression) -> Expression:
        return OrExpr(arg1, arg2, output_field=fields.BooleanField())


class BaserowDateInterval(OneArgumentBaserowFunction):
    type = "date_interval"
    arg_type = [BaserowFormulaTextType]

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
        arg: BaserowExpression[BaserowFormulaValidType],
    ) -> BaserowExpression[BaserowFormulaType]:
        return func_call.with_valid_type(BaserowFormulaDateIntervalType())

    def to_django_expression(self, arg: Expression) -> Expression:
        return Func(
            arg, function="try_cast_to_interval", output_field=fields.DurationField()
        )


class BaserowReplace(ThreeArgumentBaserowFunction):
    type = "replace"
    arg1_type = [BaserowFormulaTextType]
    arg2_type = [BaserowFormulaTextType]
    arg3_type = [BaserowFormulaTextType]

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
        arg1: BaserowExpression[BaserowFormulaValidType],
        arg2: BaserowExpression[BaserowFormulaValidType],
        arg3: BaserowExpression[BaserowFormulaValidType],
    ) -> BaserowExpression[BaserowFormulaType]:
        return func_call.with_valid_type(BaserowFormulaTextType())

    def to_django_expression(
        self, arg1: Expression, arg2: Expression, arg3: Expression
    ) -> Expression:
        return Replace(arg1, arg2, arg3, output_field=fields.TextField())


class BaserowSearch(TwoArgumentBaserowFunction):
    type = "search"
    arg1_type = [BaserowFormulaTextType]
    arg2_type = [BaserowFormulaTextType]

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
        arg1: BaserowExpression[BaserowFormulaValidType],
        arg2: BaserowExpression[BaserowFormulaValidType],
    ) -> BaserowExpression[BaserowFormulaType]:
        return func_call.with_valid_type(
            BaserowFormulaNumberType(number_decimal_places=0)
        )

    def to_django_expression(self, arg1: Expression, arg2: Expression) -> Expression:
        return StrIndex(arg1, arg2, output_field=fields.DecimalField(decimal_places=0))


class BaserowContains(TwoArgumentBaserowFunction):
    type = "contains"
    arg1_type = [BaserowFormulaTextType]
    arg2_type = [BaserowFormulaTextType]

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
        arg1: BaserowExpression[BaserowFormulaValidType],
        arg2: BaserowExpression[BaserowFormulaValidType],
    ) -> BaserowExpression[BaserowFormulaType]:
        return func_call.with_valid_type(BaserowFormulaBooleanType())

    def to_django_expression(self, arg1: Expression, arg2: Expression) -> Expression:
        return NotEqualsExpr(
            StrIndex(arg1, arg2), Value(0), output_field=fields.BooleanField()
        )


class BaserowRowId(ZeroArgumentBaserowFunction):
    type = "row_id"
    requires_refresh_after_insert = True

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
    ) -> BaserowExpression[BaserowFormulaType]:
        return func_call.with_valid_type(
            BaserowFormulaNumberType(number_decimal_places=0)
        )

    def to_django_expression(self) -> Expression:
        pass

    def to_django_expression_given_args(
        self,
        args: List[Expression],
        model: Type[Model],
        model_instance: Optional[Model],
        pre_annotations: Dict[str, Expression],
        aggregate_filters: List[Expression],
        join_ids: Set[str],
    ) -> Expression:
        if model_instance is None:
            return ExpressionWrapper(
                F("id"), output_field=fields.DecimalField(decimal_places=0)
            )
        else:
            # noinspection PyUnresolvedReferences
            return Cast(
                Value(model_instance.id),
                output_field=fields.DecimalField(
                    max_digits=BaserowFormulaNumberType.MAX_DIGITS, decimal_places=0
                ),
            )


class BaserowLength(OneArgumentBaserowFunction):

    type = "length"
    arg_type = [BaserowFormulaTextType]

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
        arg: BaserowExpression[BaserowFormulaValidType],
    ) -> BaserowExpression[BaserowFormulaType]:
        return func_call.with_valid_type(
            BaserowFormulaNumberType(number_decimal_places=0)
        )

    def to_django_expression(self, arg: Expression) -> Expression:
        return Length(arg, output_field=fields.DecimalField(decimal_places=0))


class BaserowReverse(OneArgumentBaserowFunction):

    type = "reverse"
    arg_type = [BaserowFormulaTextType]

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
        arg: BaserowExpression[BaserowFormulaValidType],
    ) -> BaserowExpression[BaserowFormulaType]:
        return func_call.with_valid_type(arg.expression_type)

    def to_django_expression(self, arg: Expression) -> Expression:
        return Reverse(arg, output_field=fields.TextField())


class BaserowWhenEmpty(TwoArgumentBaserowFunction):

    type = "when_empty"
    arg_type = [BaserowFormulaValidType]

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
        arg1: BaserowExpression[BaserowFormulaValidType],
        arg2: BaserowExpression[BaserowFormulaValidType],
    ) -> BaserowExpression[BaserowFormulaType]:
        if arg1.expression_type.type != arg2.expression_type.type:
            func_call.with_invalid_type(
                "both inputs for when_empty must be the same type"
            )
        return func_call.with_valid_type(arg1.expression_type)

    def to_django_expression(self, arg1: Expression, arg2: Expression) -> Expression:
        return Coalesce(arg1, arg2, output_field=arg1.output_field)


def _calculate_aggregate_orders(join_ids):
    orders = []
    for join in reversed(join_ids):
        orders.append(join[0] + "__order")
        orders.append(join[0] + "__id")
    return orders


class BaserowArrayAgg(OneArgumentBaserowFunction):
    type = "array_agg"
    arg_type = [BaserowFormulaValidType]
    aggregate = True

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
        arg: BaserowExpression[BaserowFormulaValidType],
    ) -> BaserowExpression[BaserowFormulaType]:
        return func_call.with_valid_type(BaserowFormulaArrayType(arg.expression_type))

    def to_django_expression(self, arg: Expression) -> Expression:
        pass

    def to_django_expression_given_args(
        self,
        args: List[Expression],
        model: Type[Model],
        model_instance: Optional[Model],
        pre_annotations: Dict[str, Expression],
        aggregate_filters: List[Expression],
        join_ids: Set[str],
    ) -> Expression:
        join_ids = list(join_ids)
        json_builder_args = {"value": args[0]}
        if len(join_ids) > 1:
            json_builder_args["ids"] = JSONObject(
                **{tbl: F(i + "__id") for i, tbl in join_ids}
            )
        else:
            json_builder_args["id"] = F(join_ids[0][0] + "__id")

        orders = _calculate_aggregate_orders(join_ids)

        expr = JSONBAgg(JSONObject(**json_builder_args), ordering=orders)
        return Coalesce(
            aggregate_wrapper(
                expr, model, pre_annotations, aggregate_filters, join_ids
            ),
            Value([], output_field=JSONField()),
            output_field=JSONField(),
        )


class Baserow2dArrayAgg(OneArgumentBaserowFunction):
    type = "array_agg_unnesting"
    arg_type = [BaserowFormulaArrayType]
    aggregate = True

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
        arg: BaserowExpression[BaserowFormulaValidType],
    ) -> BaserowExpression[BaserowFormulaType]:
        return func_call.with_valid_type(arg.expression_type)

    def to_django_expression(self, arg: Expression) -> Expression:
        return Func(
            Func(JSONBAgg(arg), function="jsonb_array_elements"),
            function="jsonb_array_elements",
            output_field=JSONField(),
        )

    def to_django_expression_given_args(
        self,
        args: List[Expression],
        model: Type[Model],
        model_instance: Optional[Model],
        pre_annotations: Dict[str, Expression],
        aggregate_filters: List[Expression],
        join_ids: Set[str],
    ) -> Expression:
        subquery = super().to_django_expression_given_args(
            args, model, model_instance, pre_annotations, aggregate_filters, join_ids
        )
        return Func(Func(subquery, function="array"), function="to_jsonb")


class BaserowCount(OneArgumentBaserowFunction):
    type = "count"
    arg_type = [BaserowFormulaValidType]
    aggregate = True

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
        arg: BaserowExpression[BaserowFormulaValidType],
    ) -> BaserowExpression[BaserowFormulaType]:
        return func_call.with_valid_type(
            BaserowFormulaNumberType(number_decimal_places=0)
        )

    def to_django_expression(self, arg: Expression) -> Expression:
        return Count(arg, output_field=fields.DecimalField(decimal_places=0))


class BaserowFilter(TwoArgumentBaserowFunction):
    type = "filter"
    arg1_type = [BaserowFormulaValidType]
    arg2_type = [BaserowFormulaBooleanType]

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
        arg1: BaserowExpression[BaserowFormulaValidType],
        arg2: BaserowExpression[BaserowFormulaValidType],
    ) -> BaserowExpression[BaserowFormulaType]:
        if not arg1.many:
            return func_call.with_invalid_type(
                "first input to filter must be an expression of many values ("
                "a lookup function call or a field reference to a lookup/link "
                "field)"
            )
        valid_type = func_call.with_valid_type(arg1.expression_type)
        # Force all usages of filter to be immediately wrapped by an aggregate call
        # otherwise formula behaviour when filtering is odd.
        valid_type.requires_aggregate_wrapper = True
        return valid_type

    def to_django_expression(self, arg1: Expression, arg2: Expression) -> Expression:
        return arg1

    def to_django_expression_given_args(
        self,
        args: List[Expression],
        model: Type[Model],
        model_instance: Optional[Model],
        pre_annotations: Dict[str, Expression],
        aggregate_filters: List[Expression],
        join_ids: Set[str],
    ) -> Expression:
        result = super().to_django_expression_given_args(
            args, model, model_instance, pre_annotations, aggregate_filters, join_ids
        )
        aggregate_filters.append(args[1])
        return result


class BaserowAny(OneArgumentBaserowFunction):
    type = "any"
    arg_type = [BaserowFormulaBooleanType]
    aggregate = True

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
        arg: BaserowExpression[BaserowFormulaValidType],
    ) -> BaserowExpression[BaserowFormulaType]:
        return func_call.with_valid_type(arg.expression_type)

    def to_django_expression(self, arg: Expression) -> Expression:
        return Func(arg, function="bool_or", output_field=fields.BooleanField())


class BaserowEvery(OneArgumentBaserowFunction):
    type = "every"
    arg_type = [BaserowFormulaBooleanType]
    aggregate = True

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
        arg: BaserowExpression[BaserowFormulaValidType],
    ) -> BaserowExpression[BaserowFormulaType]:
        return func_call.with_valid_type(arg.expression_type)

    def to_django_expression(self, arg: Expression) -> Expression:
        return Func(arg, function="every", output_field=fields.BooleanField())


class BaserowMax(OneArgumentBaserowFunction):
    type = "max"
    arg_type = [
        BaserowFormulaTextType,
        BaserowFormulaNumberType,
        BaserowFormulaCharType,
    ]
    aggregate = True

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
        arg: BaserowExpression[BaserowFormulaValidType],
    ) -> BaserowExpression[BaserowFormulaType]:
        return func_call.with_valid_type(arg.expression_type)

    def to_django_expression(self, arg: Expression) -> Expression:
        return Max(arg, output_field=arg.output_field)


class BaserowMin(OneArgumentBaserowFunction):
    type = "min"
    arg_type = [
        BaserowFormulaTextType,
        BaserowFormulaNumberType,
        BaserowFormulaCharType,
    ]
    aggregate = True

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
        arg: BaserowExpression[BaserowFormulaValidType],
    ) -> BaserowExpression[BaserowFormulaType]:
        return func_call.with_valid_type(arg.expression_type)

    def to_django_expression(self, arg: Expression) -> Expression:
        return Min(arg, output_field=arg.output_field)


class BaserowAvg(OneArgumentBaserowFunction):
    type = "avg"
    arg_type = [
        BaserowFormulaNumberType,
    ]
    aggregate = True

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
        arg: BaserowExpression[BaserowFormulaValidType],
    ) -> BaserowExpression[BaserowFormulaType]:
        return func_call.with_valid_type(arg.expression_type)

    def to_django_expression(self, arg: Expression) -> Expression:
        return Avg(arg, output_field=arg.output_field)


class BaserowStdDevPop(OneArgumentBaserowFunction):
    type = "stddev_pop"
    arg_type = [BaserowFormulaNumberType]
    aggregate = True

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
        arg: BaserowExpression[BaserowFormulaValidType],
    ) -> BaserowExpression[BaserowFormulaType]:
        return func_call.with_valid_type(arg.expression_type)

    def to_django_expression(self, arg: Expression) -> Expression:
        return StdDev(arg, sample=False, output_field=arg.output_field)


class BaserowStdDevSample(OneArgumentBaserowFunction):
    type = "stddev_sample"
    arg_type = [BaserowFormulaNumberType]
    aggregate = True

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
        arg: BaserowExpression[BaserowFormulaValidType],
    ) -> BaserowExpression[BaserowFormulaType]:
        return func_call.with_valid_type(arg.expression_type)

    def to_django_expression(self, arg: Expression) -> Expression:
        return StdDev(arg, sample=True, output_field=arg.output_field)


class BaserowAggJoin(TwoArgumentBaserowFunction):
    type = "join"
    arg1_type = [BaserowFormulaTextType]
    arg2_type = [BaserowFormulaTextType]
    aggregate = True

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
        arg1: BaserowExpression[BaserowFormulaValidType],
        arg2: BaserowExpression[BaserowFormulaValidType],
    ) -> BaserowExpression[BaserowFormulaType]:
        return func_call.with_valid_type(BaserowFormulaTextType())

    def to_django_expression(self, arg1: Expression, arg2: Expression) -> Expression:
        pass

    def to_django_expression_given_args(
        self,
        args: List[Expression],
        model: Type[Model],
        model_instance: Optional[Model],
        pre_annotations: Dict[str, Expression],
        aggregate_filters: List[Expression],
        join_ids: Set[str],
    ) -> Expression:
        join_ids = list(join_ids)
        orders = _calculate_aggregate_orders(join_ids)
        join_ids.clear()
        return aggregate_wrapper(
            BaserowStringAgg(
                args[0], args[1], ordering=orders, output_field=fields.TextField()
            ),
            model,
            pre_annotations,
            aggregate_filters,
            join_ids,
        )


class BaserowSum(OneArgumentBaserowFunction):
    type = "sum"
    aggregate = True
    arg_type = [BaserowFormulaNumberType]

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
        arg: BaserowExpression[BaserowFormulaValidType],
    ) -> BaserowExpression[BaserowFormulaType]:
        return func_call.with_valid_type(arg.expression_type)

    def to_django_expression(self, arg: Expression) -> Expression:
        return Sum(arg, output_field=arg.output_field)


class BaserowVarianceSample(OneArgumentBaserowFunction):
    type = "variance_sample"
    aggregate = True
    arg_type = [BaserowFormulaNumberType]

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
        arg: BaserowExpression[BaserowFormulaValidType],
    ) -> BaserowExpression[BaserowFormulaType]:
        return func_call.with_valid_type(arg.expression_type)

    def to_django_expression(self, arg: Expression) -> Expression:
        return Variance(arg, sample=True, output_field=arg.output_field)


class BaserowVariancePop(OneArgumentBaserowFunction):
    type = "variance_pop"
    aggregate = True
    arg_type = [BaserowFormulaNumberType]

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
        arg: BaserowExpression[BaserowFormulaValidType],
    ) -> BaserowExpression[BaserowFormulaType]:
        return func_call.with_valid_type(arg.expression_type)

    def to_django_expression(self, arg: Expression) -> Expression:
        return Variance(arg, sample=False, output_field=arg.output_field)


class BaserowGetSingleSelectValue(OneArgumentBaserowFunction):
    type = "get_single_select_value"
    arg_type = [BaserowFormulaSingleSelectType]

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
        arg: BaserowExpression[BaserowFormulaValidType],
    ) -> BaserowExpression[BaserowFormulaType]:
        return func_call.with_valid_type(BaserowFormulaTextType())

    def to_django_expression(self, arg: Expression) -> Expression:
        return Func(
            arg,
            Value("value"),
            function="jsonb_extract_path_text",
            output_field=fields.TextField(),
        )


class BaserowLeft(TwoArgumentBaserowFunction):
    type = "left"
    arg1_type = [BaserowFormulaTextType]
    arg2_type = [OnlyIntegerNumberTypes()]

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
        arg1: BaserowExpression[BaserowFormulaValidType],
        arg2: BaserowExpression[BaserowFormulaNumberType],
    ) -> BaserowExpression[BaserowFormulaType]:
        return func_call.with_valid_type(arg1.expression_type)

    def to_django_expression(self, arg1: Expression, arg2: Expression) -> Expression:
        return Left(arg1, arg2, output_field=fields.TextField())


class BaserowRight(TwoArgumentBaserowFunction):
    type = "right"
    arg1_type = [BaserowFormulaTextType]
    arg2_type = [OnlyIntegerNumberTypes()]

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
        arg1: BaserowExpression[BaserowFormulaValidType],
        arg2: BaserowExpression[BaserowFormulaNumberType],
    ) -> BaserowExpression[BaserowFormulaType]:
        return func_call.with_valid_type(arg1.expression_type)

    def to_django_expression(self, arg1: Expression, arg2: Expression) -> Expression:
        return Right(arg1, arg2, output_field=fields.TextField())


class BaserowRegexReplace(ThreeArgumentBaserowFunction):

    type = "regex_replace"
    arg_type1 = [BaserowFormulaTextType]
    arg_type2 = [BaserowFormulaTextType]
    arg_type3 = [BaserowFormulaTextType]

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
        arg1: BaserowExpression[BaserowFormulaValidType],
        arg2: BaserowExpression[BaserowFormulaValidType],
        arg3: BaserowExpression[BaserowFormulaValidType],
    ) -> BaserowExpression[BaserowFormulaType]:
        return func_call.with_valid_type(arg1.expression_type)

    def to_django_expression(
        self, arg1: Expression, arg2: Expression, arg3: Expression
    ) -> Expression:
        return Func(
            arg1,
            arg2,
            arg3,
            Value("g", output_field=fields.TextField()),
            function="regexp_replace",
            output_field=fields.TextField(),
        )


class BaserowTrim(OneArgumentBaserowFunction):

    type = "trim"
    arg_type = [BaserowFormulaTextType]

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
        arg: BaserowExpression[BaserowFormulaValidType],
    ) -> BaserowExpression[BaserowFormulaType]:
        return BaserowRegexReplace().call_and_type_with(
            arg, literal("(^\\s+|\\s+$)"), literal("")
        )

    def to_django_expression(self, arg: Expression) -> Expression:
        # This function should always be completely substituted when typing and replaced
        # with BaserowRegexReplace and hence this should never be called.
        raise BaserowToDjangoExpressionGenerationError()


class BaserowYear(OneArgumentBaserowFunction):
    type = "year"
    arg_type = [BaserowFormulaDateType]

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
        arg: BaserowExpression[BaserowFormulaValidType],
    ) -> BaserowExpression[BaserowFormulaType]:
        return func_call.with_valid_type(
            BaserowFormulaNumberType(number_decimal_places=0)
        )

    def to_django_expression(self, arg: Expression) -> Expression:
        return Extract(arg, "year", output_field=fields.DecimalField(decimal_places=0))


class BaserowSecond(OneArgumentBaserowFunction):
    type = "second"
    arg_type = [BaserowFormulaDateType]

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
        arg: BaserowExpression[BaserowFormulaValidType],
    ) -> BaserowExpression[BaserowFormulaType]:
        return func_call.with_valid_type(
            BaserowFormulaNumberType(number_decimal_places=0)
        )

    def to_django_expression(self, arg: Expression) -> Expression:
        return Extract(
            arg, "second", output_field=fields.DecimalField(decimal_places=0)
        )
