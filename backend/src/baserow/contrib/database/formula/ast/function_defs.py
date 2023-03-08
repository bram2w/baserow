from abc import ABC
from decimal import Decimal
from typing import List, Union

from django.contrib.postgres.aggregates import JSONBAgg
from django.db.models import (
    Avg,
    Case,
    Count,
    Expression,
    ExpressionWrapper,
    F,
    Func,
    JSONField,
    Max,
    Min,
    StdDev,
    Sum,
    Value,
    Variance,
    When,
    fields,
)
from django.db.models.functions import (
    Abs,
    Cast,
    Ceil,
    Coalesce,
    Concat,
    Exp,
    Extract,
    Floor,
    Greatest,
    JSONObject,
    Least,
    Left,
    Length,
    Ln,
    Log,
    Lower,
    Mod,
    Power,
    Replace,
    Reverse,
    Right,
    Sign,
    Sqrt,
    StrIndex,
    Upper,
)
from django.db.models.functions.datetime import TimezoneMixin

from baserow.contrib.database.fields.models import NUMBER_MAX_DECIMAL_PLACES
from baserow.contrib.database.formula.ast.function import (
    BaserowFunctionDefinition,
    NumOfArgsGreaterThan,
    OneArgumentBaserowFunction,
    ThreeArgumentBaserowFunction,
    TwoArgumentBaserowFunction,
    ZeroArgumentBaserowFunction,
    aggregate_wrapper,
)
from baserow.contrib.database.formula.ast.tree import (
    BaserowDecimalLiteral,
    BaserowExpression,
    BaserowExpressionContext,
    BaserowFunctionCall,
    BaserowIntegerLiteral,
)
from baserow.contrib.database.formula.expression_generator.django_expressions import (
    AndExpr,
    BaserowStringAgg,
    EqualsExpr,
    GreaterThanExpr,
    GreaterThanOrEqualExpr,
    IsNullExpr,
    LessThanEqualOrExpr,
    LessThanExpr,
    NotEqualsExpr,
    NotExpr,
    OrExpr,
)
from baserow.contrib.database.formula.expression_generator.exceptions import (
    BaserowToDjangoExpressionGenerationError,
)
from baserow.contrib.database.formula.expression_generator.generator import (
    JoinIdsType,
    WrappedExpressionWithMetadata,
)
from baserow.contrib.database.formula.types.formula_type import (
    BaserowFormulaType,
    BaserowFormulaValidType,
    UnTyped,
)
from baserow.contrib.database.formula.types.formula_types import (
    BaserowFormulaArrayType,
    BaserowFormulaBooleanType,
    BaserowFormulaCharType,
    BaserowFormulaDateIntervalType,
    BaserowFormulaDateType,
    BaserowFormulaLinkType,
    BaserowFormulaNumberType,
    BaserowFormulaSingleSelectType,
    BaserowFormulaTextType,
    calculate_number_type,
    literal,
)
from baserow.contrib.database.formula.types.type_checker import (
    BaserowArgumentTypeChecker,
    MustBeManyExprChecker,
)


class BaserowTimezoneMixinOverride(TimezoneMixin):
    def get_tzname(self):
        return None


class BaserowExtract(BaserowTimezoneMixinOverride, Extract):
    pass


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
    registry.register(BaserowMod())
    registry.register(BaserowRound())
    registry.register(BaserowInt())
    registry.register(BaserowEven())
    registry.register(BaserowOdd())
    registry.register(BaserowTrunc())
    registry.register(BaserowLn())
    registry.register(BaserowExp())
    registry.register(BaserowLog())
    registry.register(BaserowSqrt())
    registry.register(BaserowPower())
    registry.register(BaserowAbs())
    registry.register(BaserowCeil())
    registry.register(BaserowFloor())
    registry.register(BaserowSign())
    registry.register(BaserowIsNaN())
    registry.register(BaserowWhenNan())
    # Boolean functions
    registry.register(BaserowIf())
    registry.register(BaserowEqual())
    registry.register(BaserowIsBlank())
    registry.register(BaserowIsNull())
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
    registry.register(BaserowBcToNull())
    registry.register(BaserowNow())
    registry.register(BaserowToday())
    registry.register(BaserowToDateTz())
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
    # Link functions
    registry.register(BaserowLink())
    registry.register(BaserowButton())
    registry.register(BaserowGetLinkUrl())
    registry.register(BaserowGetLinkLabel())


class BaserowUpper(OneArgumentBaserowFunction):

    type = "upper"
    arg_type = [BaserowFormulaTextType]

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
        arg: BaserowExpression[BaserowFormulaValidType],
    ) -> BaserowExpression[BaserowFormulaType]:
        return func_call.with_valid_type(
            BaserowFormulaTextType(nullable=arg.expression_type.nullable)
        )

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
        return func_call.with_valid_type(
            BaserowFormulaTextType(nullable=arg.expression_type.nullable)
        )

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
        return func_call.with_valid_type(
            BaserowFormulaTextType(nullable=arg1.expression_type.nullable)
        )

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
    try_coerce_nullable_args_to_not_null = False

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
        arg: BaserowExpression[BaserowFormulaValidType],
    ) -> BaserowExpression[BaserowFormulaType]:
        return arg.expression_type.cast_to_text(func_call, arg).with_valid_type(
            BaserowFormulaTextType()
        )

    def to_django_expression(self, arg: Expression) -> Expression:
        return Coalesce(
            Cast(arg, output_field=fields.TextField()),
            Value(""),
            output_field=fields.TextField(),
        )


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
            return func_call.with_valid_type(
                BaserowFormulaTextType(nullable=arg.expression_type.nullable)
            )

    def to_django_expression(self, arg: Expression) -> Expression:
        return Cast(Value(""), output_field=fields.TextField())


class BaserowConcat(BaserowFunctionDefinition):
    type = "concat"
    num_args = NumOfArgsGreaterThan(1)
    try_coerce_nullable_args_to_not_null = False

    @property
    def arg_types(self) -> BaserowArgumentTypeChecker:
        return lambda _, _2: [BaserowFormulaValidType]

    def type_function_given_valid_args(
        self,
        args: List[BaserowExpression[BaserowFormulaValidType]],
        expression: "BaserowFunctionCall[UnTyped]",
    ) -> BaserowExpression[BaserowFormulaType]:
        typed_args = [BaserowToText()(a) for a in args]
        return expression.with_args(typed_args).with_valid_type(
            BaserowFormulaTextType()
        )

    def to_django_expression_given_args(
        self, expr_args: List[WrappedExpressionWithMetadata], *args, **kwargs
    ) -> WrappedExpressionWithMetadata:
        return WrappedExpressionWithMetadata.from_args(
            Concat(*[e.expression for e in expr_args], output_field=fields.TextField()),
            expr_args,
        )


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
    try_coerce_nullable_args_to_not_null = False

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
        arg1: BaserowExpression[BaserowFormulaNumberType],
        arg2: BaserowExpression[BaserowFormulaNumberType],
    ) -> BaserowExpression[BaserowFormulaType]:
        return func_call.with_valid_type(
            calculate_number_type([arg1.expression_type, arg2.expression_type]),
            nullable=arg1.expression_type.nullable and arg2.expression_type.nullable,
        )

    def to_django_expression(self, arg1: Expression, arg2: Expression) -> Expression:
        return Greatest(arg1, arg2, output_field=arg1.output_field)


class BaserowLeast(TwoArgumentBaserowFunction):
    type = "least"
    arg1_type = [BaserowFormulaNumberType]
    arg2_type = [BaserowFormulaNumberType]
    try_coerce_nullable_args_to_not_null = False

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
        arg1: BaserowExpression[BaserowFormulaNumberType],
        arg2: BaserowExpression[BaserowFormulaNumberType],
    ) -> BaserowExpression[BaserowFormulaType]:
        return func_call.with_valid_type(
            calculate_number_type([arg1.expression_type, arg2.expression_type]),
            nullable=arg1.expression_type.nullable and arg2.expression_type.nullable,
        )

    def to_django_expression(self, arg1: Expression, arg2: Expression) -> Expression:
        return Least(arg1, arg2, output_field=arg1.output_field)


class BaserowRound(TwoArgumentBaserowFunction):
    type = "round"
    arg1_type = [BaserowFormulaNumberType]
    arg2_type = [BaserowFormulaNumberType]

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
        arg1: BaserowExpression[BaserowFormulaNumberType],
        arg2: BaserowExpression[BaserowFormulaNumberType],
    ) -> BaserowExpression[BaserowFormulaType]:
        if isinstance(arg2, BaserowIntegerLiteral):
            guessed_number_decimal_places = arg2.literal
        elif isinstance(arg2, BaserowDecimalLiteral):
            guessed_number_decimal_places = int(arg2.literal)
        else:
            guessed_number_decimal_places = NUMBER_MAX_DECIMAL_PLACES

        return func_call.with_valid_type(
            BaserowFormulaNumberType(
                number_decimal_places=min(
                    max(guessed_number_decimal_places, 0), NUMBER_MAX_DECIMAL_PLACES
                )
            )
        )

    def to_django_expression(self, arg1: Expression, arg2: Expression) -> Expression:
        return handle_arg_being_nan(
            arg_to_check_if_nan=arg2,
            when_nan=Value(Decimal("NaN")),
            when_not_nan=(
                Func(
                    arg1,
                    # The round function requires an integer input.
                    trunc_numeric_to_int(arg2),
                    function="round",
                    output_field=arg1.output_field,
                )
            ),
        )


class BaserowMod(TwoArgumentBaserowFunction):
    type = "mod"
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
        return Case(
            When(
                condition=(
                    EqualsExpr(arg2, Value(0), output_field=fields.BooleanField())
                ),
                then=Value(Decimal("NaN")),
            ),
            default=Mod(arg1, arg2, output_field=arg1.output_field),
            output_field=arg1.output_field,
        )


class BaserowPower(TwoArgumentBaserowFunction):
    type = "power"
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
        return Power(arg1, arg2, output_field=arg1.output_field)


class BaserowLog(TwoArgumentBaserowFunction):
    type = "log"
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
        return Case(
            When(
                condition=(
                    LessThanEqualOrExpr(
                        arg1, Value(0), output_field=fields.BooleanField()
                    )
                ),
                then=Value(Decimal("NaN")),
            ),
            When(
                condition=(
                    LessThanEqualOrExpr(
                        arg2, Value(0), output_field=fields.BooleanField()
                    )
                ),
                then=Value(Decimal("NaN")),
            ),
            default=Log(arg1, arg2, output_field=arg1.output_field),
            output_field=arg1.output_field,
        )


class BaserowAbs(OneArgumentBaserowFunction):
    type = "abs"
    arg_type = [BaserowFormulaNumberType]

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
        arg: BaserowExpression[BaserowFormulaNumberType],
    ) -> BaserowExpression[BaserowFormulaType]:
        return func_call.with_valid_type(arg.expression_type)

    def to_django_expression(self, arg: Expression) -> Expression:
        return Abs(arg, output_field=arg.output_field)


class BaserowExp(OneArgumentBaserowFunction):
    type = "exp"
    arg_type = [BaserowFormulaNumberType]

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
        arg: BaserowExpression[BaserowFormulaNumberType],
    ) -> BaserowExpression[BaserowFormulaType]:
        return func_call.with_valid_type(arg.expression_type)

    def to_django_expression(self, arg: Expression) -> Expression:
        return Exp(arg, output_field=arg.output_field)


class BaserowEven(OneArgumentBaserowFunction):
    type = "even"
    arg_type = [BaserowFormulaNumberType]

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
        arg: BaserowExpression[BaserowFormulaNumberType],
    ) -> BaserowExpression[BaserowFormulaType]:
        return func_call.with_valid_type(BaserowFormulaBooleanType())

    def to_django_expression(self, arg: Expression) -> Expression:
        return EqualsExpr(
            Mod(arg, Value(2), output_field=arg.output_field),
            Value(0),
            output_field=fields.BooleanField(),
        )


class BaserowOdd(OneArgumentBaserowFunction):
    type = "odd"
    arg_type = [BaserowFormulaNumberType]

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
        arg: BaserowExpression[BaserowFormulaNumberType],
    ) -> BaserowExpression[BaserowFormulaType]:
        return func_call.with_valid_type(BaserowFormulaBooleanType())

    def to_django_expression(self, arg: Expression) -> Expression:
        return EqualsExpr(
            Mod(arg, Value(2), output_field=arg.output_field),
            Value(1),
            output_field=fields.BooleanField(),
        )


class BaserowLn(OneArgumentBaserowFunction):
    type = "ln"
    arg_type = [BaserowFormulaNumberType]

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
        arg: BaserowExpression[BaserowFormulaNumberType],
    ) -> BaserowExpression[BaserowFormulaType]:
        return func_call.with_valid_type(arg.expression_type)

    def to_django_expression(self, arg: Expression) -> Expression:
        # If we get given a negative number ln will crash, instead just return NaN.
        return Case(
            When(
                condition=(
                    LessThanEqualOrExpr(
                        arg, Value(0), output_field=fields.BooleanField()
                    )
                ),
                then=Value(Decimal("NaN")),
            ),
            default=Ln(arg, output_field=arg.output_field),
            output_field=arg.output_field,
        )


class BaserowSqrt(OneArgumentBaserowFunction):
    type = "sqrt"
    arg_type = [BaserowFormulaNumberType]

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
        arg: BaserowExpression[BaserowFormulaNumberType],
    ) -> BaserowExpression[BaserowFormulaType]:
        return func_call.with_valid_type(arg.expression_type)

    def to_django_expression(self, arg: Expression) -> Expression:
        # If we get given a negative number sqrt will crash, instead just return NaN.
        return Case(
            When(
                condition=(
                    LessThanExpr(arg, Value(0), output_field=fields.BooleanField())
                ),
                then=Value(Decimal("NaN")),
            ),
            default=Sqrt(arg, output_field=arg.output_field),
            output_field=arg.output_field,
        )


class BaserowSign(OneArgumentBaserowFunction):
    type = "sign"
    arg_type = [BaserowFormulaNumberType]

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
        arg: BaserowExpression[BaserowFormulaNumberType],
    ) -> BaserowExpression[BaserowFormulaType]:
        return func_call.with_valid_type(
            BaserowFormulaNumberType(number_decimal_places=0)
        )

    def to_django_expression(self, arg: Expression) -> Expression:
        return Sign(arg, output_field=int_like_numeric_output_field())


class BaserowCeil(OneArgumentBaserowFunction):
    type = "ceil"
    arg_type = [BaserowFormulaNumberType]

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
        arg: BaserowExpression[BaserowFormulaNumberType],
    ) -> BaserowExpression[BaserowFormulaType]:
        return func_call.with_valid_type(
            BaserowFormulaNumberType(number_decimal_places=0)
        )

    def to_django_expression(self, arg: Expression) -> Expression:
        return Ceil(arg, output_field=int_like_numeric_output_field())


class BaserowFloor(OneArgumentBaserowFunction):
    type = "floor"
    arg_type = [BaserowFormulaNumberType]

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
        arg: BaserowExpression[BaserowFormulaNumberType],
    ) -> BaserowExpression[BaserowFormulaType]:
        return func_call.with_valid_type(
            BaserowFormulaNumberType(number_decimal_places=0)
        )

    def to_django_expression(self, arg: Expression) -> Expression:
        return Floor(arg, output_field=int_like_numeric_output_field())


class BaserowTrunc(OneArgumentBaserowFunction):
    type = "trunc"
    arg_type = [BaserowFormulaNumberType]

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
        arg: BaserowExpression[BaserowFormulaNumberType],
    ) -> BaserowExpression[BaserowFormulaType]:
        return func_call.with_valid_type(
            BaserowFormulaNumberType(
                number_decimal_places=0, nullable=arg.expression_type.nullable
            )
        )

    def to_django_expression(self, arg: Expression) -> Expression:
        return Func(arg, function="trunc", output_field=int_like_numeric_output_field())


def int_like_numeric_output_field() -> fields.DecimalField:
    return fields.DecimalField(
        max_digits=BaserowFormulaNumberType.MAX_DIGITS, decimal_places=0
    )


class BaserowIsNaN(OneArgumentBaserowFunction):
    type = "is_nan"
    arg_type = [BaserowFormulaNumberType]

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
        arg: Union[BaserowExpression[BaserowFormulaNumberType]],
    ) -> BaserowExpression[BaserowFormulaType]:
        return func_call.with_valid_type(
            BaserowFormulaBooleanType(nullable=arg.expression_type.nullable)
        )

    def to_django_expression(self, arg: Expression) -> Expression:
        return EqualsExpr(
            arg, Value(Decimal("NaN")), output_field=fields.BooleanField()
        )


class BaserowWhenNan(TwoArgumentBaserowFunction):
    type = "when_nan"
    arg1_type = [BaserowFormulaNumberType]
    arg2_type = [BaserowFormulaNumberType]

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
        arg1: Union[BaserowExpression[BaserowFormulaNumberType]],
        arg2: Union[BaserowExpression[BaserowFormulaNumberType]],
    ) -> BaserowExpression[BaserowFormulaType]:
        return func_call.with_valid_type(
            calculate_number_type([arg1.expression_type, arg2.expression_type]),
        )

    def to_django_expression(self, arg1: Expression, arg2: Expression) -> Expression:
        return handle_arg_being_nan(arg1, arg2, arg1)


class BaserowInt(BaserowTrunc):
    """
    Kept for backwards compatability as was introduced in v3 of formula language but
    renamed to trunc in v4.
    """

    type = "int"


def trunc_numeric_to_int(expr: Expression) -> Expression:
    return Cast(
        Func(expr, function="trunc", output_field=expr.output_field),
        output_field=fields.IntegerField(),
    )


def handle_arg_being_nan(
    arg_to_check_if_nan: Expression,
    when_nan: Expression,
    when_not_nan: Expression,
) -> Expression:
    return Case(
        When(
            condition=(
                EqualsExpr(
                    arg_to_check_if_nan,
                    Value(Decimal("Nan")),
                    output_field=fields.BooleanField(),
                )
            ),
            then=when_nan,
        ),
        default=when_not_nan,
        output_field=when_not_nan.output_field,
    )


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
        max_dp_output = fields.DecimalField(
            max_digits=BaserowFormulaNumberType.MAX_DIGITS,
            decimal_places=NUMBER_MAX_DECIMAL_PLACES,
        )
        return ExpressionWrapper(
            arg1
            / Case(
                When(
                    condition=(
                        EqualsExpr(arg2, Value(0), output_field=fields.BooleanField())
                    ),
                    then=Value(Decimal("NaN")),
                ),
                default=arg2,
                output_field=max_dp_output,
            ),
            output_field=max_dp_output,
        )


class BaserowEqual(TwoArgumentBaserowFunction):
    type = "equal"
    operator = "="
    try_coerce_nullable_args_to_not_null = False

    # Overridden by the arg_types property below
    arg1_type = [BaserowFormulaValidType]
    arg2_type = [BaserowFormulaValidType]

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

            return self.__class__()(
                BaserowToText()(arg1),
                BaserowToText()(arg2),
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
    try_coerce_nullable_args_to_not_null = False

    arg1_type = [BaserowFormulaBooleanType]
    # Overridden by the type function property below
    arg2_type = [BaserowFormulaValidType]
    arg3_type = [BaserowFormulaValidType]

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
            return BaserowIf()(
                arg1,
                BaserowToText()(arg2),
                BaserowToText()(arg3),
            )
        else:
            if isinstance(arg2_type, BaserowFormulaNumberType) and isinstance(
                arg3_type, BaserowFormulaNumberType
            ):
                resulting_type = calculate_number_type([arg2_type, arg3_type])
            else:
                resulting_type = arg2_type

            return func_call.with_valid_type(
                resulting_type,
                nullable=arg2_type.nullable or arg3_type.nullable,
            )

    def to_django_expression(
        self, arg1: Expression, arg2: Expression, arg3: Expression
    ) -> Expression:
        return Case(
            When(condition=arg1, then=arg2),
            default=arg3,
            output_field=arg2.output_field,
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
            BaserowFormulaNumberType(number_decimal_places=NUMBER_MAX_DECIMAL_PLACES)
        )

    def to_django_expression(self, arg: Expression) -> Expression:
        return Func(
            arg,
            function="try_cast_to_numeric",
            output_field=int_like_numeric_output_field(),
        )


class BaserowErrorToNan(OneArgumentBaserowFunction):
    type = "error_to_nan"
    arg_type = [BaserowFormulaNumberType]
    is_wrapper = True

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
    is_wrapper = True

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
        arg: BaserowExpression[BaserowFormulaValidType],
    ) -> BaserowExpression[BaserowFormulaType]:

        # FIXME: This function should set `nullable=True` on the resulting type,
        # but since this is used as the most external wrapper function, don't
        # want to loose the real nullable state of the expression. This should
        # be fixed in the future (e.g. saving only the inner expression and wrapping
        # at runtime somehow).

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
        return arg.expression_type.is_blank(func_call, arg)

    def to_django_expression(self, arg: Expression) -> Expression:
        return EqualsExpr(
            Coalesce(
                arg,
                Value(""),
            ),
            Value(""),
            output_field=fields.BooleanField(),
        )


class BaserowIsNull(OneArgumentBaserowFunction):
    type = "is_null"
    arg_type = [BaserowFormulaValidType]
    try_coerce_nullable_args_to_not_null = False

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
        arg: BaserowExpression[BaserowFormulaValidType],
    ) -> BaserowExpression[BaserowFormulaType]:
        return func_call.with_valid_type(BaserowFormulaBooleanType())

    def to_django_expression(self, arg: Expression) -> Expression:
        return IsNullExpr(arg, output_field=fields.BooleanField())


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
    # Overridden by the arg_types property below
    arg1_type = [BaserowFormulaValidType]
    arg2_type = [BaserowFormulaValidType]

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


class BaserowNow(ZeroArgumentBaserowFunction):
    type = "now"
    needs_periodic_update = True

    def type_function(
        self, func_call: BaserowFunctionCall[UnTyped]
    ) -> BaserowExpression[BaserowFormulaType]:
        return func_call.with_valid_type(
            BaserowFormulaDateType(
                date_format="ISO", date_include_time=True, date_time_format="24"
            )
        )

    def to_django_expression(self) -> Expression:
        pass

    def to_django_expression_given_args(
        self,
        args: List["WrappedExpressionWithMetadata"],
        context: BaserowExpressionContext,
    ) -> "WrappedExpressionWithMetadata":

        return WrappedExpressionWithMetadata(
            Value(context.get_utc_now(), output_field=fields.DateTimeField()),
        )


class BaserowToday(ZeroArgumentBaserowFunction):
    type = "today"
    needs_periodic_update = True

    def type_function(
        self, func_call: BaserowFunctionCall[UnTyped]
    ) -> BaserowExpression[BaserowFormulaType]:
        return func_call.with_valid_type(
            BaserowFormulaDateType(
                date_format="ISO",
                date_include_time=False,
                date_time_format="24",
                date_force_timezone="UTC",
            )
        )

    def to_django_expression(self) -> Expression:
        pass

    def to_django_expression_given_args(
        self,
        args: List["WrappedExpressionWithMetadata"],
        context: BaserowExpressionContext,
    ) -> "WrappedExpressionWithMetadata":

        return WrappedExpressionWithMetadata(
            Value(context.get_utc_now(), output_field=fields.DateField()),
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
                date_format="ISO",
                date_include_time=False,
                date_time_format="24",
                nullable=True,
            )
        )

    def to_django_expression(self, arg1: Expression, arg2: Expression) -> Expression:
        return Func(
            arg1,
            arg2,
            function="try_cast_to_date",
            output_field=fields.DateTimeField(),
        )


class BaserowToDateTz(ThreeArgumentBaserowFunction):
    type = "todate_tz"
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
        return func_call.with_valid_type(
            BaserowFormulaDateType(
                date_format="ISO",
                date_include_time=True,
                date_time_format="24",
                date_show_tzinfo=True,
                date_force_timezone=getattr(arg3, "literal", None),
                nullable=True,
            )
        )

    def to_django_expression(
        self, arg1: Expression, arg2: Expression, arg3: Expression
    ) -> Expression:

        return Func(
            arg1,
            arg2,
            arg3,
            function="try_cast_to_date_tz",
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
            BaserowFormulaNumberType(
                number_decimal_places=0, nullable=arg.expression_type.nullable
            )
        )

    def to_django_expression(self, arg: Expression) -> Expression:
        return BaserowExtract(arg, "day", output_field=int_like_numeric_output_field())


class BaserowMonth(OneArgumentBaserowFunction):
    type = "month"
    arg_type = [BaserowFormulaDateType]

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
        arg: BaserowExpression[BaserowFormulaValidType],
    ) -> BaserowExpression[BaserowFormulaType]:
        return func_call.with_valid_type(
            BaserowFormulaNumberType(
                number_decimal_places=0, nullable=arg.expression_type.nullable
            )
        )

    def to_django_expression(self, arg: Expression) -> Expression:
        return BaserowExtract(
            arg, "month", output_field=int_like_numeric_output_field()
        )


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
        nullable = arg2.expression_type.nullable or arg3.expression_type.nullable
        return func_call.with_valid_type(
            BaserowFormulaNumberType(number_decimal_places=0, nullable=nullable)
        )

    def to_django_expression(
        self, arg1: Expression, arg2: Expression, arg3: Expression
    ) -> Expression:
        return Func(
            arg1,
            arg2,
            arg3,
            function="date_diff",
            output_field=int_like_numeric_output_field(),
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

        return func_call.with_valid_type(BaserowFormulaDateIntervalType(nullable=True))

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
        return func_call.with_valid_type(BaserowFormulaTextType(nullable=False))

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
        return StrIndex(arg1, arg2, output_field=int_like_numeric_output_field())


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
        args: List["WrappedExpressionWithMetadata"],
        context: BaserowExpressionContext,
    ) -> "WrappedExpressionWithMetadata":
        if context.model_instance is None:
            return WrappedExpressionWithMetadata(
                ExpressionWrapper(F("id"), output_field=int_like_numeric_output_field())
            )
        else:
            # noinspection PyUnresolvedReferences
            return WrappedExpressionWithMetadata(
                Cast(
                    Value(context.model_instance.id),
                    output_field=fields.IntegerField(),
                )
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
        return Length(arg, output_field=int_like_numeric_output_field())


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
    arg1_type = [BaserowFormulaValidType]
    arg2_type = [BaserowFormulaValidType]
    try_coerce_nullable_args_to_not_null = False

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
        arg1: BaserowExpression[BaserowFormulaValidType],
        arg2: BaserowExpression[BaserowFormulaValidType],
    ) -> BaserowExpression[BaserowFormulaType]:
        if arg1.expression_type.type != arg2.expression_type.type:
            return func_call.with_invalid_type(
                "both inputs for when_empty must be the same type"
            )
        return func_call.with_valid_type(
            arg1.expression_type, nullable=arg2.expression_type.nullable
        )

    def to_django_expression(self, arg1: Expression, arg2: Expression) -> Expression:
        return Coalesce(arg1, arg2, output_field=arg2.output_field)


def _calculate_aggregate_orders(join_ids: JoinIdsType):
    orders = []
    for join in reversed(join_ids):
        orders.append(join[0] + "__order")
        orders.append(join[0] + "__id")
    return orders


class BaserowArrayAgg(OneArgumentBaserowFunction):
    type = "array_agg"
    arg_type = [MustBeManyExprChecker(BaserowFormulaValidType)]
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
        args: List["WrappedExpressionWithMetadata"],
        context: BaserowExpressionContext,
    ) -> "WrappedExpressionWithMetadata":
        pre_annotations = dict()
        aggregate_filters = []
        join_ids = []
        for child in args:
            pre_annotations.update(child.pre_annotations)
            aggregate_filters.extend(child.aggregate_filters)
            join_ids.extend(child.join_ids)

        json_builder_args = {"value": args[0].expression}

        # Remove any duplicates from join_ids
        join_ids = list(dict.fromkeys(join_ids))
        if len(join_ids) > 1:
            json_builder_args["ids"] = JSONObject(
                **{tbl: F(i + "__id") for i, tbl in join_ids}
            )
        else:
            json_builder_args["id"] = F(join_ids[0][0] + "__id")

        orders = _calculate_aggregate_orders(join_ids)

        expr = JSONBAgg(JSONObject(**json_builder_args), ordering=orders)
        wrapped_expr = aggregate_wrapper(
            WrappedExpressionWithMetadata(
                expr, pre_annotations, aggregate_filters, join_ids
            ),
            context.model,
        ).expression
        return WrappedExpressionWithMetadata(
            Coalesce(
                wrapped_expr,
                Value([], output_field=JSONField()),
                output_field=JSONField(),
            )
        )


class Baserow2dArrayAgg(OneArgumentBaserowFunction):
    type = "array_agg_unnesting"
    arg_type = [MustBeManyExprChecker(BaserowFormulaArrayType)]
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
        args: List["WrappedExpressionWithMetadata"],
        context: BaserowExpressionContext,
    ) -> "WrappedExpressionWithMetadata":
        subquery = super().to_django_expression_given_args(args, context)
        return WrappedExpressionWithMetadata(
            Func(Func(subquery.expression, function="array"), function="to_jsonb")
        )


class BaserowCount(OneArgumentBaserowFunction):
    type = "count"
    arg_type = [MustBeManyExprChecker(BaserowFormulaValidType)]
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
        return Count(arg, output_field=int_like_numeric_output_field())


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
        args: List["WrappedExpressionWithMetadata"],
        context: BaserowExpressionContext,
    ) -> "WrappedExpressionWithMetadata":
        result = super().to_django_expression_given_args(args, context)
        return WrappedExpressionWithMetadata(
            result.expression,
            result.pre_annotations,
            result.aggregate_filters + [args[1].expression],
            result.join_ids,
        )


class BaserowAny(OneArgumentBaserowFunction):
    type = "any"
    arg_type = [MustBeManyExprChecker(BaserowFormulaBooleanType)]
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
    arg_type = [MustBeManyExprChecker(BaserowFormulaBooleanType)]
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
        MustBeManyExprChecker(
            BaserowFormulaTextType, BaserowFormulaNumberType, BaserowFormulaCharType
        ),
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
        MustBeManyExprChecker(
            BaserowFormulaTextType, BaserowFormulaNumberType, BaserowFormulaCharType
        ),
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
        MustBeManyExprChecker(BaserowFormulaNumberType),
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
    arg_type = [MustBeManyExprChecker(BaserowFormulaNumberType)]
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
    arg_type = [MustBeManyExprChecker(BaserowFormulaNumberType)]
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
    arg1_type = [MustBeManyExprChecker(BaserowFormulaTextType)]
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
        args: List["WrappedExpressionWithMetadata"],
        context: BaserowExpressionContext,
    ) -> "WrappedExpressionWithMetadata":
        pre_annotations = {}
        aggregate_filters = []
        join_ids = []
        for child in args:
            pre_annotations.update(child.pre_annotations)
            aggregate_filters.extend(child.aggregate_filters)
            join_ids.extend(child.join_ids)

        # Remove any duplicates from join_ids
        join_ids = list(dict.fromkeys(join_ids))
        orders = _calculate_aggregate_orders(join_ids)
        return aggregate_wrapper(
            WrappedExpressionWithMetadata(
                BaserowStringAgg(
                    args[0].expression,
                    args[1].expression,
                    ordering=orders,
                    output_field=fields.TextField(),
                ),
                pre_annotations,
                aggregate_filters,
                join_ids,
            ),
            context.model,
        )


class BaserowSum(OneArgumentBaserowFunction):
    type = "sum"
    aggregate = True
    arg_type = [MustBeManyExprChecker(BaserowFormulaNumberType)]

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
    arg_type = [MustBeManyExprChecker(BaserowFormulaNumberType)]

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
    arg_type = [MustBeManyExprChecker(BaserowFormulaNumberType)]

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
        return func_call.with_valid_type(
            BaserowFormulaTextType(nullable=arg.expression_type.nullable)
        )

    def to_django_expression(self, arg: Expression) -> Expression:
        return Func(
            arg,
            Value("value"),
            function="jsonb_extract_path_text",
            output_field=fields.TextField(),
        )


class BaserowGetLinkUrl(OneArgumentBaserowFunction):
    type = "get_link_url"
    arg_type = [BaserowFormulaLinkType]

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
        arg: BaserowExpression[BaserowFormulaValidType],
    ) -> BaserowExpression[BaserowFormulaType]:
        return func_call.with_valid_type(
            BaserowFormulaTextType(nullable=arg.expression_type.nullable)
        )

    def to_django_expression(self, arg: Expression) -> Expression:
        return Func(
            arg,
            Value("url"),
            function="jsonb_extract_path_text",
            output_field=fields.TextField(),
        )


class BaserowGetLinkLabel(OneArgumentBaserowFunction):
    type = "get_link_label"
    arg_type = [BaserowFormulaLinkType]

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
        arg: BaserowExpression[BaserowFormulaValidType],
    ) -> BaserowExpression[BaserowFormulaType]:
        return func_call.with_valid_type(
            BaserowFormulaTextType(nullable=arg.expression_type.nullable)
        )

    def to_django_expression(self, arg: Expression) -> Expression:
        return Func(
            arg,
            Value("label"),
            function="jsonb_extract_path_text",
            output_field=fields.TextField(),
        )


class BaserowLeft(TwoArgumentBaserowFunction):
    type = "left"
    arg1_type = [BaserowFormulaTextType]
    arg2_type = [BaserowFormulaNumberType]

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
        arg1: BaserowExpression[BaserowFormulaValidType],
        arg2: BaserowExpression[BaserowFormulaNumberType],
    ) -> BaserowExpression[BaserowFormulaType]:
        return func_call.with_valid_type(arg1.expression_type, nullable=True)

    def to_django_expression(self, arg1: Expression, arg2: Expression) -> Expression:
        return handle_arg_being_nan(
            arg_to_check_if_nan=arg2,
            when_nan=Value(None),
            when_not_nan=(
                Left(arg1, trunc_numeric_to_int(arg2), output_field=fields.TextField())
            ),
        )


class BaserowRight(TwoArgumentBaserowFunction):
    type = "right"
    arg1_type = [BaserowFormulaTextType]
    arg2_type = [BaserowFormulaNumberType]

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
        arg1: BaserowExpression[BaserowFormulaValidType],
        arg2: BaserowExpression[BaserowFormulaNumberType],
    ) -> BaserowExpression[BaserowFormulaType]:
        return func_call.with_valid_type(arg1.expression_type, nullable=True)

    def to_django_expression(self, arg1: Expression, arg2: Expression) -> Expression:
        return handle_arg_being_nan(
            arg_to_check_if_nan=arg2,
            when_nan=Value(None),
            when_not_nan=(
                Right(
                    arg1,
                    trunc_numeric_to_int(arg2),
                    output_field=fields.TextField(),
                )
            ),
        )


class BaserowRegexReplace(ThreeArgumentBaserowFunction):

    type = "regex_replace"
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


class BaserowLink(OneArgumentBaserowFunction):
    type = "link"
    arg_type = [BaserowFormulaTextType]

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
        arg: BaserowExpression[BaserowFormulaValidType],
    ) -> BaserowExpression[BaserowFormulaType]:
        return func_call.with_valid_type(
            BaserowFormulaLinkType(nullable=arg.expression_type.nullable)
        )

    def to_django_expression(self, arg: Expression) -> Expression:
        return JSONObject(url=arg)


class BaserowButton(TwoArgumentBaserowFunction):
    type = "button"
    arg1_type = [BaserowFormulaTextType]
    arg2_type = [BaserowFormulaTextType]

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
        arg1: BaserowExpression[BaserowFormulaValidType],
        arg2: BaserowExpression[BaserowFormulaValidType],
    ) -> BaserowExpression[BaserowFormulaType]:
        return func_call.with_valid_type(
            BaserowFormulaLinkType(nullable=arg1.expression_type.nullable)
        )

    def to_django_expression(self, arg1: Expression, arg2: Expression) -> Expression:
        return JSONObject(url=arg1, label=arg2)


class BaserowTrim(OneArgumentBaserowFunction):

    type = "trim"
    arg_type = [BaserowFormulaTextType]

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
        arg: BaserowExpression[BaserowFormulaValidType],
    ) -> BaserowExpression[BaserowFormulaType]:
        return BaserowRegexReplace()(arg, literal("(^\\s+|\\s+$)"), literal(""))

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
            BaserowFormulaNumberType(
                number_decimal_places=0, nullable=arg.expression_type.nullable
            )
        )

    def to_django_expression(self, arg: Expression) -> Expression:
        return BaserowExtract(arg, "year", output_field=int_like_numeric_output_field())


class BaserowSecond(OneArgumentBaserowFunction):
    type = "second"
    arg_type = [BaserowFormulaDateType]

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
        arg: BaserowExpression[BaserowFormulaValidType],
    ) -> BaserowExpression[BaserowFormulaType]:
        return func_call.with_valid_type(
            BaserowFormulaNumberType(
                number_decimal_places=0, nullable=arg.expression_type.nullable
            )
        )

    def to_django_expression(self, arg: Expression) -> Expression:
        return BaserowExtract(
            arg, "second", output_field=int_like_numeric_output_field()
        )


class BaserowBcToNull(OneArgumentBaserowFunction):
    type = "bc_to_null"
    arg_type = [BaserowFormulaDateType]
    is_wrapper = True

    def type_function(
        self,
        func_call: BaserowFunctionCall[UnTyped],
        arg: BaserowExpression[BaserowFormulaValidType],
    ) -> BaserowExpression[BaserowFormulaType]:
        return func_call.with_valid_type(arg.expression_type, nullable=True)

    def to_django_expression(self, arg: Expression) -> Expression:
        expr_to_get_year = BaserowExtract(
            arg, "year", output_field=int_like_numeric_output_field()
        )
        return Case(
            When(
                condition=LessThanExpr(
                    expr_to_get_year, Value(0), output_field=fields.BooleanField()
                ),
                then=Value(None, output_field=arg.output_field),
            ),
            default=arg,
        )
