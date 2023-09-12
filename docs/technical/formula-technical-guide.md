# Baserow Formula Technical Guide

This guide explains the inner workings of Baserow formulas for developers.

See the [understanding baserow formulas guide](../tutorials/understanding-baserow-formulas.md) if
you instead want a general guide of how to use formulas as a user within Baserow.

## Technical Overview

In Baserow there is a special formula field type. The user enters a single formula for a
whole formula field which is then used to calculate every cell in the formula field.

Baserow formulas are written in the open source Baserow Formula language which is a
simple expression based language similar to formulas you will find in other spreadsheet
tools. The Baserow Formula language itself is a fully functioning programming language
with a :

* A language syntax/grammar definition.
    * See `{git repo root}/formulas/*.g4`.
* Lexers and parsers generated using ANTLR4 from the grammar.
    * See `{git repo root}/formulas/build.sh` for the script that generates these using
      docker.
    * A generated parser used for checking formula validity in the browser can be found
      in
      `web-frontend/modules/database/formula/parser`.
    * A generated parser used for checking formula validity and constructing the python
      AST in the backend can be found
      in `backend/src/baserow/core/formulas/parser/generated`.
* A python abstract syntax tree used internally in the backend.
    * See `backend/src/baserow/core/formulas/ast/tree.py`.
* A typing algorithm that is capable of typing a given formula.
    * See the formula types module found
      in `backend/src/baserow/core/formulas/types`.
* Finally, a generator which coverts a typed formula into a Django expression for safe
  evaluation.
    * see the expression generator module found
      in `backend/src/baserow/core/formulas/expression_generator`.

## Formula Features from a technical perspective

A Formula is just a single expression which can consist of literals (string, int,
decimal), functions, operators and nested formulas.

### Formula Functions

Functions are defined by implementing a BaserowFunctionDefinition and storing it in
the `formula_function_registry` (which allows plugins to trivially add their own custom
functions)

Functions have specific or unlimited number of arguments. These arguments can be type
checked and forced to have specific types otherwise an error is shown. The function
itself has a return type.

A function can change its behaviour at type checking time, for example if a function is
given two arguments of different types it could first choose to wrap them in a
BaserowToText function call.

Functions define how to transform themselves into a Django Expression to calculate their
result.

### Extending Baserow Formulas using plugins

Plugins can easily add new Baserow formula functions and types by implementing
a `BaserowFunctionDefinition` and registering it in the `formula_function_registry`.
Hint: Use the various `{Zero/One/Two/Three}ArgumentBaserowFunctionDefinition` sub-classes
get a nicer set of functions to implement corresponding to the arguments.

### Formula Operators

Operators are implemented as a mapping from an operator to a `BaserowFunctionDefinition`
. So the `+` operator is just a fancy way of calling the `BaserowAdd` function.
Operators have precedence as defined by the rule ordering in the BaserowParser.g4
grammar file.

### Operator Overloading

Operators can have different implementations depending on the input types. For example
`'a'+'b'` concatenates the two strings together, whereas `1+2` performs numeric
addition.

### Calculating the result of a Formula

Formulas ultimately compile down to a prepared SQL statement which is used to  
calculate and store the formula results in a PostgreSQL column.

To generate the SQL we transform a baserow formula into
a [Django Expression](https://docs.djangoproject.com/en/3.2/ref/models/expressions/)
and then rely on Django to generate the SQL for us.

### Field References

Formulas can reference other fields including other formula fields. They cannot
reference themselves and circular references are disallowed.

Because formula fields can reference other fields, now whenever a field is edited,
deleted, restored or created it might also affect other fields which depend on it. In
these situations we construct the reference tree of all fields in a table, recalculate
what each fields type is and if it has changed refresh that formula fields values.

### User configurable type/formatting options

Formula types can have their options override by user configurable formatting options.

For example:

* A formula field `1+1` is initially calculated to have the type of
  `BaserowFormulaNumberType(num_decimal_places=0)`.
* This calculated type is stored on the `FormulaField` model by setting
  its `formula_type` field to `number`, it's `num_decimal_places` field to `0` and
  setting all other type option fields to null.
* Then all cells for this field will be displayed as `1`.
* The user however can then edit these persisted type options themselves to change the
  type and hence how the field is displayed.
* For example the user could then change `num_decimal_places` to `2`, which changes the
  corresponding field on the model and also changes the type of that field to
  `BaserowFormulaNumberType(num_decimal_places=2)`.
* Now the cells will be shown as `1.00`

These user supplied type/formatting options will be reset when the overall type of a
formula field changes, otherwise they will stick around.

### The Invalid Formula Type

There is an invalid type which stores an error on the `FormulaField` model for formulas
which have an invalid type such as `(1+'a')` etc.

### Type Coercion

Generally functions prefer to coerce types in sensible ways that a non-technical user
might expect. For example, `CONCAT(field('a date field'),field('a boolean field'))`
should work without having to use a function to cast each to text. * However we don't
allow users to do odd things like compare a boolean to a date and instead provide a type
error rather than always returning false or something.

### Field Renaming

Renaming a field will rename any references to that field in a formula. This is achieved
by the following process:

* Updating all formulas referencing that field to reference the new name 
* Returning these updated fields to the browser.

When deleting a field we:
* Mark the formulas which referenced it as broken with an error.
* This then lets the user create a new field called `'name'` which will then fix those
  broken formulas. 

This also can happen when a field is restored from deletion or a field is renamed.

Importantly this means creating, restoring or renaming fields can cause any number of
other fields in the same table to go from the invalid type to a valid type and hence we
need to check and re-type the table in these situations.

### Sorting and Filtering Formula Fields

Formula fields can be sorted and filtered using Baserow's existing view filters based on
the BaserowFormulaType of the field. Simply using
the `FormulaFieldType.compatible_with_formula_types`
helper function when defining your view filters `compatible_field_types` to say which of
the Formula Types work with your view filter.
