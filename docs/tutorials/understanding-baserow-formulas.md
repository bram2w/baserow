# Understanding Baserow Formulas

Baserow formula fields allow you to dynamically calculate values for each cell in the
field based on a formula. These formulas are similar to those found in other spreadsheet
tools, have a growing collection of functions available and are lightning fast.

This guide will first explain what Baserow formulas are and how to use them. See the
[baserow formula technical guide](../technical/formula-technical-guide.md) if you are a
looking for a technical understanding of how formulas are implemented within Baserow.

## What a Baserow Formula Field is

A Baserow Formula field lets you create a field whose contents are calculated based on a
Baserow Formula you've provided. A Baserow Formula is simply some text written in a
particular way such that Baserow can understand it, for example the text `1+1` is a
Baserow formula which will calculate the result `2` for every row.

### A Simple Formula Example

Imagine you have a table with a normal text field called `text field` with 3 rows
containing the text `one`,`two` and `three` respectively. If you then create a formula
field with the formula `concat('Number', field('text field'))` the resulting table would
look like:

| text field | formula field |
|------------|---------------|
| one        | Number one    |
| two        | Number two    |
| three      | Number three  |

As you can see the formula field cells are calculated using the text field cell for each
row.

In the next section we break down the formula bit by bit. If you are familiar with
formulas already feel free to skip to the section after.

### Breaking down a simple formula

Let's split apart the formula `concat('Number', field('text field'))` to understand what
is going on:

* `concat`
    * Concat is one of many formula functions you can use. It will join together all the
      inputs you give to it into one single piece of text.
* `(`
    * To give inputs to a formula function you first have to write an opening
      parenthesis indicating the inputs will follow.
* `'Number'`
    * This is the first input we are giving to `concat` and it is literally just the
      text `Number`. When writing literal pieces of text in a formula you need to
      surround them with quotes.
* `,`
    * As we are giving multiple inputs to `concat` we need to separate each input with a
      comma.
* `field('text field')`
    * This is the second and final input we are giving to `concat`. We could keep on
      adding however many inputs as we wanted however as long as each was separated by a
      comma.
    * This second input is a reference to the field in the same table with the name
      `text field`. For each cell in the formula field this reference will be replaced
      by whatever the value in the `text field` field is for that row.
* `)`
    * Finally, we need to tell Baserow we've finished giving inputs to the `concat`
      function, we do this with a matching closing parenthesis.

#### What is a formula function?

A function in a formula takes a number of inputs depending on the type of the function.
It does some calculation using those inputs and produces an output. Functions also
sometimes only take specific types of inputs. For example the `datetime_format`
only accepts two inputs, the first must be a date (either a field reference to a date
field Or a sub formula which calculates a date) and the second must be some text.

All the available functions for you to use are shown in the expanded formula edit box
which appears when you click on the formula whilst editing a formula field.

### Using numbers in formulas

Formulas can be used to do numerical calculations. The standard maths operators exist
like `+`,`-`,`*` and `/`. You can use whole numbers or decimal numbers directly in your
formula like so `(field('number field') + 10.005)/10`

#### Invalid Number Error

If you see an `Invalid Number` in a formula cell it means that your formula for that row
has tried to do one of the following invalid operations:

* Divide a number by zero.
* Convert text to a number using the `tonumber` function and failed because the text
  wasn't a valid number.
* Calculate a number which is larger than `10^50`, the maximum value allowed.

### Conditional calculations

If you need to do a calculation conditionally then the `if` function and comparison
operators will let you do this. For example the following formula calculates whether a
date field is the first day of a month, `IF(day(field('some date')) = 1, true, false)`.

You can compare fields and sub-formulas using the `>`, `>=` `<=`, `<`, `=` and `!=`
operators.

### Using Dates

Use the `todate` function to create a constant date inside a formula like so:
`todate('2020-01-01 10:20:30', 'YYYY-MM-DD HH:MI:SS')`. The first argument is the date
you want in text form and the second is the format of the date text.

### Using Date intervals

Subtracting two dates returns the difference in time between the two dates:
`field('date a') - field('date b')`. The `date_interval` function lets you create
intervals inside the formula to work with.

Need to calculate a new date based on a date/time interval? Use the `date_interval`
function like so:
`field('my date column') - date_interval('1 year')`

## FAQ

### Why can't I change the value of a formula fields cell?

You cannot change the value of a formula field cell. This is because a formula field has
one formula for the entire field which is used to calculate the individual cells values.
Try converting the formula field back to a normal field if you are done with your
calculation and now want to make specific edits to the results.

### What happens when I delete a field referenced by formula field?

If you reference a field in a formula, if you then delete the referenced field, your
formula field will become invalid and an error will be shown. To fix this you can either
restore the deleted field, create a new field with the same name, change the formula to
no longer reference the deleted field or rename another field.

## Future Formula Functionality

### Extra Functions

Many more functions will be coming soon, please let us know which in particular are most
important for you on our [community forum](https://community.baserow.io/).

### Unsupported Field Types

It is not currently possible to reference and use the following fields in a formula:

* Collaborators
* Created by
* Last modified by
* Password
* AI Prompt
