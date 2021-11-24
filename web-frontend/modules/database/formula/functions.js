import { Registerable } from '@baserow/modules/core/registry'

export class BaserowFunctionDefinition extends Registerable {
  getDescription() {
    throw new Error(
      'Not implemented error. This method should return the functions description.'
    )
  }

  getSyntaxUsage() {
    throw new Error(
      'Not implemented error. This method should return a string showing the syntax ' +
        'of the function.'
    )
  }

  getExamples() {
    throw new Error(
      'Not implemented error. This method should return list of strings showing ' +
        'example usage of the function.'
    )
  }

  getFormulaType() {
    throw new Error(
      'Not implemented error. This method should return the baserow formula type ' +
        'string of the function.'
    )
  }

  isOperator() {
    return false
  }

  getOperator() {
    return ''
  }
}

export class BaserowUpper extends BaserowFunctionDefinition {
  static getType() {
    return 'upper'
  }

  getDescription() {
    return 'Returns its argument in upper case'
  }

  getSyntaxUsage() {
    return ['upper(text)']
  }

  getExamples() {
    return ["upper('a') = 'A'"]
  }

  getFormulaType() {
    return 'text'
  }
}
export class BaserowLower extends BaserowFunctionDefinition {
  static getType() {
    return 'lower'
  }

  getDescription() {
    return 'Returns its argument in lower case'
  }

  getSyntaxUsage() {
    return ['lower(text)']
  }

  getExamples() {
    return ["lower('A') = 'a'"]
  }

  getFormulaType() {
    return 'text'
  }
}

export class BaserowConcat extends BaserowFunctionDefinition {
  static getType() {
    return 'concat'
  }

  getDescription() {
    return 'Returns its arguments joined together as a single piece of text'
  }

  getSyntaxUsage() {
    return ['concat(any, any, ...)']
  }

  getExamples() {
    return ["concat('A', 1, 1=2) = 'A1false'"]
  }

  getFormulaType() {
    return 'text'
  }
}

export class BaserowAdd extends BaserowFunctionDefinition {
  static getType() {
    return 'add'
  }

  getDescription() {
    return 'Returns its two arguments added together'
  }

  getSyntaxUsage() {
    return [
      'number + number',
      'text + text',
      'date + date_interval',
      'date_interval + date_interval',
      'date_interval + date',
      'add(number, number)',
    ]
  }

  getExamples() {
    return ['1+1 = 2', "'a' + 'b' = 'ab'"]
  }

  getFormulaType() {
    return 'special'
  }

  isOperator() {
    return true
  }

  getOperator() {
    return '+'
  }
}

export class BaserowMinus extends BaserowFunctionDefinition {
  static getType() {
    return 'minus'
  }

  getDescription() {
    return 'Returns its two arguments subtracted'
  }

  getSyntaxUsage() {
    return [
      'number - number',
      'minus(number, number)',
      'date - date',
      'date - date_interval',
      'date_interval - date_interval',
    ]
  }

  getExamples() {
    return ['3-1 = 2']
  }

  getFormulaType() {
    return 'special'
  }

  isOperator() {
    return true
  }

  getOperator() {
    return '-'
  }
}

export class BaserowMultiply extends BaserowFunctionDefinition {
  static getType() {
    return 'multiply'
  }

  getDescription() {
    return 'Returns its two arguments multiplied together'
  }

  getSyntaxUsage() {
    return ['number * number', 'multiply(number, number)']
  }

  getExamples() {
    return ['2*5 = 10']
  }

  getFormulaType() {
    return 'number'
  }

  isOperator() {
    return true
  }

  getOperator() {
    return '*'
  }
}

export class BaserowDivide extends BaserowFunctionDefinition {
  static getType() {
    return 'divide'
  }

  getDescription() {
    return 'Returns its two arguments divided, the first divided by the second'
  }

  getSyntaxUsage() {
    return ['number / number', 'divide(number, number)']
  }

  getExamples() {
    return ['10/2 = 5']
  }

  getFormulaType() {
    return 'number'
  }

  isOperator() {
    return true
  }

  getOperator() {
    return '/'
  }
}

export class BaserowEqual extends BaserowFunctionDefinition {
  static getType() {
    return 'equal'
  }

  getDescription() {
    return 'Returns if its two arguments have the same value.'
  }

  getSyntaxUsage() {
    return ['any = any', 'equal(any, any)']
  }

  getExamples() {
    return ['1=1', "'a' = 'a'"]
  }

  getFormulaType() {
    return 'boolean'
  }

  isOperator() {
    return true
  }

  getOperator() {
    return '='
  }
}

export class BaserowIf extends BaserowFunctionDefinition {
  static getType() {
    return 'if'
  }

  getDescription() {
    return (
      'If the first argument is true then returns the second argument, otherwise ' +
      'returns the third.'
    )
  }

  getSyntaxUsage() {
    return ['if(bool, any, any)']
  }

  getExamples() {
    return ["if(field('text field') = 'on', 'it is on', 'it is off')"]
  }

  getFormulaType() {
    return 'boolean'
  }
}

export class BaserowToText extends BaserowFunctionDefinition {
  static getType() {
    return 'totext'
  }

  getDescription() {
    return 'Converts the input to text'
  }

  getSyntaxUsage() {
    return ['totext(any)']
  }

  getExamples() {
    return ["totext(10) = '10'"]
  }

  getFormulaType() {
    return 'text'
  }
}

export class BaserowDatetimeFormat extends BaserowFunctionDefinition {
  static getType() {
    return 'datetime_format'
  }

  getDescription() {
    return 'Converts the date to text given a way of formatting the date'
  }

  getSyntaxUsage() {
    return ['datetime_format(date, text)']
  }

  getExamples() {
    return ["datetime_format(field('date field'), 'YYYY')"]
  }

  getFormulaType() {
    return 'date'
  }
}

export class BaserowToNumber extends BaserowFunctionDefinition {
  static getType() {
    return 'tonumber'
  }

  getDescription() {
    return 'Converts the input to a number if possible'
  }

  getSyntaxUsage() {
    return ['tonumber(text)']
  }

  getExamples() {
    return ["tonumber('10') = 10"]
  }

  getFormulaType() {
    return 'number'
  }
}

export class BaserowField extends BaserowFunctionDefinition {
  static getType() {
    return 'field'
  }

  getDescription() {
    return 'Returns the field named by the single text argument'
  }

  getSyntaxUsage() {
    return ["field('a field name')"]
  }

  getExamples() {
    return ["field('my text field') = 'flag'"]
  }

  getFormulaType() {
    return 'special'
  }
}

export class BaserowLookup extends BaserowFunctionDefinition {
  static getType() {
    return 'lookup'
  }

  getDescription() {
    return (
      'Looks up the values from a field in another table for rows in a link row' +
      ' field. The first argument should be the name of a link row field in the' +
      ' current table and the second should be the name of a field in the linked' +
      ' table.'
    )
  }

  getSyntaxUsage() {
    return ["lookup('a link row field name', 'field name in other the table')"]
  }

  getExamples() {
    return [
      "lookup('link row field', 'first name') = lookup('link row field', 'last name')",
    ]
  }

  getFormulaType() {
    return 'special'
  }
}

export class BaserowIsBlank extends BaserowFunctionDefinition {
  static getType() {
    return 'isblank'
  }

  getDescription() {
    return 'Returns true if the argument is empty or blank, false otherwise'
  }

  getSyntaxUsage() {
    return ['isblank(any)']
  }

  getExamples() {
    return ["isblank('10') "]
  }

  getFormulaType() {
    return 'boolean'
  }
}

export class BaserowT extends BaserowFunctionDefinition {
  static getType() {
    return 't'
  }

  getDescription() {
    return 'Returns the arguments value if it is text, but otherwise '
  }

  getSyntaxUsage() {
    return ['t(any)']
  }

  getExamples() {
    return ['t(10)']
  }

  getFormulaType() {
    return 'text'
  }
}

export class BaserowNot extends BaserowFunctionDefinition {
  static getType() {
    return 'not'
  }

  getDescription() {
    return 'Returns false if the argument is true and true if the argument is false'
  }

  getSyntaxUsage() {
    return ['not(boolean)']
  }

  getExamples() {
    return ['not(true) = false', 'not(10=2) = true']
  }

  getFormulaType() {
    return 'boolean'
  }
}

export class BaserowGreaterThan extends BaserowFunctionDefinition {
  static getType() {
    return 'greater_than'
  }

  getDescription() {
    return 'Returns true if the first argument greater than the second, otherwise false'
  }

  getSyntaxUsage() {
    return ['any > any']
  }

  getExamples() {
    return [
      '1 > 2 = false',
      "if(field('a') > field('b'), 'a is bigger', 'b is bigger or equal')",
    ]
  }

  getFormulaType() {
    return 'boolean'
  }

  isOperator() {
    return true
  }

  getOperator() {
    return '>'
  }
}

export class BaserowGreaterThanOrEqual extends BaserowFunctionDefinition {
  static getType() {
    return 'greater_than_or_equal'
  }

  getDescription() {
    return 'Returns true if the first argument is greater than or equal to the second, otherwise false'
  }

  getSyntaxUsage() {
    return ['any >= any']
  }

  getExamples() {
    return [
      '1 >= 1 = true',
      "if(field('a') >= field('b'), 'a is bigger or equal', 'b is smaller')",
    ]
  }

  getFormulaType() {
    return 'boolean'
  }

  isOperator() {
    return true
  }

  getOperator() {
    return '>='
  }
}

export class BaserowLessThan extends BaserowFunctionDefinition {
  static getType() {
    return 'less_than'
  }

  getDescription() {
    return 'Returns true if the first argument less than the second, otherwise false'
  }

  getSyntaxUsage() {
    return ['any < any']
  }

  getExamples() {
    return [
      '2 < 1 = false',
      "if(field('a') < field('b'), 'a is smaller', 'b is bigger or equal')",
    ]
  }

  getFormulaType() {
    return 'boolean'
  }

  isOperator() {
    return true
  }

  getOperator() {
    return '<'
  }
}

export class BaserowLessThanOrEqual extends BaserowFunctionDefinition {
  static getType() {
    return 'less_than_or_equal'
  }

  getDescription() {
    return 'Returns true if the first argument less than or equal to the second, otherwise false'
  }

  getSyntaxUsage() {
    return ['any <= any']
  }

  getExamples() {
    return [
      '1 <= 1 = true',
      "if(field('a') <= field('b'), 'a smaller', 'b is greater than or equal')",
    ]
  }

  getFormulaType() {
    return 'boolean'
  }

  isOperator() {
    return true
  }

  getOperator() {
    return '<='
  }
}

export class BaserowToDate extends BaserowFunctionDefinition {
  static getType() {
    return 'todate'
  }

  getDescription() {
    return 'Returns the first argument converted into a date given a date format string as the second argument'
  }

  getSyntaxUsage() {
    return ['todate(text, text)']
  }

  getExamples() {
    return ["todate('20210101', 'YYYYMMDD')"]
  }

  getFormulaType() {
    return 'date'
  }
}

export class BaserowDay extends BaserowFunctionDefinition {
  static getType() {
    return 'day'
  }

  getDescription() {
    return 'Returns the day of the month as a number between 1 to 31 from the argument'
  }

  getSyntaxUsage() {
    return ['day(date)']
  }

  getExamples() {
    return ["day(todate('20210101', 'YYYYMMDD')) = 1"]
  }

  getFormulaType() {
    return 'date'
  }
}

export class BaserowDateDiff extends BaserowFunctionDefinition {
  static getType() {
    return 'date_diff'
  }

  getDescription() {
    return (
      "Given a date unit to measure in as the first argument ('year', " +
      "'month', 'week', 'day', 'hour', 'minute', 'seconds') calculates and returns " +
      'the number of units from the second argument to the third.'
    )
  }

  getSyntaxUsage() {
    return ['date_diff(text, date, date)']
  }

  getExamples() {
    return [
      "date_diff('yy', todate('2000-01-01', 'YYYY-MM-DD'), todate('2020-01-01'," +
        " 'YYYY-MM-DD')) = 20",
    ]
  }

  getFormulaType() {
    return 'date'
  }
}

export class BaserowAnd extends BaserowFunctionDefinition {
  static getType() {
    return 'and'
  }

  getDescription() {
    return (
      'Returns the logical and of the first and second argument, so if they are both' +
      'true then the result is true, otherwise it is false'
    )
  }

  getSyntaxUsage() {
    return ['and(boolean, boolean)']
  }

  getExamples() {
    return [
      'and(true, false) = false',
      'and(true, true) = true',
      "and(field('first test'), field('second test'))",
    ]
  }

  getFormulaType() {
    return 'boolean'
  }
}

export class BaserowOr extends BaserowFunctionDefinition {
  static getType() {
    return 'or'
  }

  getDescription() {
    return (
      'Returns the logical or of the first and second argument, so if either are ' +
      'true then the result is true, otherwise it is false'
    )
  }

  getSyntaxUsage() {
    return ['or(boolean, boolean)']
  }

  getExamples() {
    return [
      'or(true, false) = true',
      'and(true, true) = true',
      "or(field('first test'), field('second test'))",
    ]
  }

  getFormulaType() {
    return 'boolean'
  }
}

export class BaserowDateInterval extends BaserowFunctionDefinition {
  static getType() {
    return 'date_interval'
  }

  getDescription() {
    return 'Returns the date interval corresponding to the provided argument.'
  }

  getSyntaxUsage() {
    return ['date_interval(text)']
  }

  getExamples() {
    return ["date_interval('1 year')", "date_interval('2 seconds')"]
  }

  getFormulaType() {
    return 'date_interval'
  }
}

export class BaserowReplace extends BaserowFunctionDefinition {
  static getType() {
    return 'replace'
  }

  getDescription() {
    return (
      'Replaces all instances of the second argument in the first argument with ' +
      'the third argument'
    )
  }

  getSyntaxUsage() {
    return ['replace(text, text, text)']
  }

  getExamples() {
    return ['replace("test a b c test", "test", "1") = "1 a b c 1"']
  }

  getFormulaType() {
    return 'text'
  }
}

export class BaserowSearch extends BaserowFunctionDefinition {
  static getType() {
    return 'search'
  }

  getDescription() {
    return (
      'Returns a positive integer starting from 1 for the first ' +
      'occurrence of the second argument inside the first, or 0 if no ' +
      'occurrence is found.'
    )
  }

  getSyntaxUsage() {
    return ['search(text, text)']
  }

  getExamples() {
    return [
      'search("test a b c test", "test") = 1',
      'search("none", "test") = 0',
    ]
  }

  getFormulaType() {
    return 'text'
  }
}

export class BaserowRowId extends BaserowFunctionDefinition {
  static getType() {
    return 'row_id'
  }

  getDescription() {
    return 'Returns the rows unique identifying number'
  }

  getSyntaxUsage() {
    return ['row_id()']
  }

  getExamples() {
    return ['concat("Row ", row_id())']
  }

  getFormulaType() {
    return 'special'
  }
}

export class BaserowLength extends BaserowFunctionDefinition {
  static getType() {
    return 'length'
  }

  getDescription() {
    return 'Returns the number of characters in the first argument provided'
  }

  getSyntaxUsage() {
    return ['length(text)']
  }

  getExamples() {
    return ['length("abc") = 3']
  }

  getFormulaType() {
    return 'text'
  }
}

export class BaserowReverse extends BaserowFunctionDefinition {
  static getType() {
    return 'reverse'
  }

  getDescription() {
    return 'Returns the reversed text of the provided first argument'
  }

  getSyntaxUsage() {
    return ['reverse(text)']
  }

  getExamples() {
    return ['reverse("abc") = "cba"']
  }

  getFormulaType() {
    return 'text'
  }
}

export class BaserowNotEqual extends BaserowFunctionDefinition {
  static getType() {
    return 'not_equal'
  }

  getDescription() {
    return 'Returns if its two arguments have different values.'
  }

  getSyntaxUsage() {
    return ['any != any', 'not_equal(any, any)']
  }

  getExamples() {
    return ['1!=2', "'a' != 'b'"]
  }

  getFormulaType() {
    return 'boolean'
  }

  isOperator() {
    return true
  }

  getOperator() {
    return '!='
  }
}

export class BaserowCount extends BaserowFunctionDefinition {
  static getType() {
    return 'count'
  }

  getDescription() {
    return 'Returns the number of items in its first argument.'
  }

  getSyntaxUsage() {
    return ['count(array)']
  }

  getExamples() {
    return ["count(field('my link row field'))"]
  }

  getFormulaType() {
    return 'array'
  }
}

export class BaserowContains extends BaserowFunctionDefinition {
  static getType() {
    return 'contains'
  }

  getDescription() {
    return 'Returns true if the first piece of text contains at least once the second.'
  }

  getSyntaxUsage() {
    return ['contains(text,text)']
  }

  getExamples() {
    return ['contains("test", "e") = true']
  }

  getFormulaType() {
    return 'text'
  }
}

export class BaserowLeft extends BaserowFunctionDefinition {
  static getType() {
    return 'left'
  }

  getDescription() {
    return (
      'Extracts the left most characters from the first input, stops when it has' +
      ' extracted the number of characters specified by the second input.'
    )
  }

  getSyntaxUsage() {
    return ['left(text, number)']
  }

  getExamples() {
    return ['left("abcd", 2) = "ab"']
  }

  getFormulaType() {
    return 'text'
  }
}

export class BaserowRight extends BaserowFunctionDefinition {
  static getType() {
    return 'right'
  }

  getDescription() {
    return (
      'Extracts the right most characters from the first input, stops when it has' +
      ' extracted the number of characters specified by the second input.'
    )
  }

  getSyntaxUsage() {
    return ['right(text, number)']
  }

  getExamples() {
    return ['right("abcd", 2) = "cd"']
  }

  getFormulaType() {
    return 'text'
  }
}

export class BaserowTrim extends BaserowFunctionDefinition {
  static getType() {
    return 'trim'
  }

  getDescription() {
    return 'Removes all whitespace from the left and right sides of the input.'
  }

  getSyntaxUsage() {
    return ['trim(text)']
  }

  getExamples() {
    return ['trim("   abc   ") = "abc"']
  }

  getFormulaType() {
    return 'text'
  }
}

export class BaserowRegexReplace extends BaserowFunctionDefinition {
  static getType() {
    return 'regex_replace'
  }

  getDescription() {
    return (
      'Replaces any text in the first input which matches the regex specified by' +
      ' the second input with the text in the third input.'
    )
  }

  getSyntaxUsage() {
    return ['regex_replace(text, regex text, replacement text)']
  }

  getExamples() {
    return ['regex_replace("abc", "a", "1") = "1bc"']
  }

  getFormulaType() {
    return 'text'
  }
}

export class BaserowGreatest extends BaserowFunctionDefinition {
  static getType() {
    return 'greatest'
  }

  getDescription() {
    return 'Returns the greatest value of the two inputs.'
  }

  getSyntaxUsage() {
    return ['greatest(number, number)']
  }

  getExamples() {
    return ['greatest(1,2) = 2']
  }

  getFormulaType() {
    return 'number'
  }
}

export class BaserowLeast extends BaserowFunctionDefinition {
  static getType() {
    return 'least'
  }

  getDescription() {
    return 'Returns the smallest of the two inputs.'
  }

  getSyntaxUsage() {
    return ['least(number, number)']
  }

  getExamples() {
    return ['least(1,2) = 1']
  }

  getFormulaType() {
    return 'number'
  }
}

export class BaserowMonth extends BaserowFunctionDefinition {
  static getType() {
    return 'month'
  }

  getDescription() {
    return 'Returns the number of months in the provided date.'
  }

  getSyntaxUsage() {
    return ['month(date)']
  }

  getExamples() {
    return ['month(todate("2021-12-12", "YYYY-MM-DD")) = 12']
  }

  getFormulaType() {
    return 'date'
  }
}

export class BaserowYear extends BaserowFunctionDefinition {
  static getType() {
    return 'year'
  }

  getDescription() {
    return 'Returns the number of years in the provided date.'
  }

  getSyntaxUsage() {
    return ['year(date)']
  }

  getExamples() {
    return ['year(field("my date"))']
  }

  getFormulaType() {
    return 'date'
  }
}

export class BaserowSecond extends BaserowFunctionDefinition {
  static getType() {
    return 'second'
  }

  getDescription() {
    return 'Returns the number of seconds in the provided date.'
  }

  getSyntaxUsage() {
    return ['second(date)']
  }

  getExamples() {
    return ['second(field("dates")) == 2']
  }

  getFormulaType() {
    return 'date'
  }
}
export class BaserowWhenEmpty extends BaserowFunctionDefinition {
  static getType() {
    return 'when_empty'
  }

  getDescription() {
    return (
      'If the first input is calculated to be empty the ' +
      'second input will be returned instead, otherwise if the first input is not' +
      ' empty the first will be returned.'
    )
  }

  getSyntaxUsage() {
    return ['when_empty(any, same type as the first)']
  }

  getExamples() {
    return ['when_empty(field("a"), "default")']
  }

  getFormulaType() {
    return 'special'
  }
}

export class BaserowAny extends BaserowFunctionDefinition {
  static getType() {
    return 'any'
  }

  getDescription() {
    return (
      'Returns true if any one of the provided looked up values is true,' +
      ' false if they are all false.'
    )
  }

  getSyntaxUsage() {
    return ['any(boolean values from a lookup() or field())']
  }

  getExamples() {
    return ['any(field("my lookup") = "test")']
  }

  getFormulaType() {
    return 'array'
  }
}

export class BaserowEvery extends BaserowFunctionDefinition {
  static getType() {
    return 'every'
  }

  getDescription() {
    return (
      'Returns true if every one of the provided looked up values is true,' +
      ' false otherwise.'
    )
  }

  getSyntaxUsage() {
    return ['every(boolean values from a lookup() or field())']
  }

  getExamples() {
    return ['every(field("my lookup") = "test")']
  }

  getFormulaType() {
    return 'array'
  }
}

export class BaserowMax extends BaserowFunctionDefinition {
  static getType() {
    return 'max'
  }

  getDescription() {
    return 'Returns the largest number from all the looked up values provided'
  }

  getSyntaxUsage() {
    return ['max(numbers from a lookup() or field())']
  }

  getExamples() {
    return [
      'max(lookup("link field", "number field"))',
      'max(field("lookup field"))',
      'max(field("link field with text primary field"))',
    ]
  }

  getFormulaType() {
    return 'array'
  }
}

export class BaserowMin extends BaserowFunctionDefinition {
  static getType() {
    return 'min'
  }

  getDescription() {
    return 'Returns the smallest number from all the looked up values provided'
  }

  getSyntaxUsage() {
    return ['min(numbers from a lookup() or field())']
  }

  getExamples() {
    return [
      'min(lookup("link field", "number field"))',
      'min(field("lookup field"))',
      'min(field("link field with text primary field"))',
    ]
  }

  getFormulaType() {
    return 'array'
  }
}

export class BaserowJoin extends BaserowFunctionDefinition {
  static getType() {
    return 'join'
  }

  getDescription() {
    return (
      'Concats all of the values from the first input together using the values' +
      ' from the second input'
    )
  }

  getSyntaxUsage() {
    return ['join(text from lookup() or field(), text)']
  }

  getExamples() {
    return [
      'join(lookup("link field", "number field"), "_")',
      'join(field("lookup field"), field("different lookup field"))',
      'join(field("link field with text primary field"), ",")',
    ]
  }

  getFormulaType() {
    return 'array'
  }
}

export class BaserowStddevPop extends BaserowFunctionDefinition {
  static getType() {
    return 'stddev_pop'
  }

  getDescription() {
    return (
      'Calculates the population standard deviation of the values and returns the' +
      ' result. ' +
      'The population standard deviation should be used when the provided values' +
      ' contain a ' +
      ' value for every single piece of data in the population.'
    )
  }

  getSyntaxUsage() {
    return ['stddev_pop(numbers from lookup() or field())']
  }

  getExamples() {
    return [
      'stddev_pop(lookup("link field", "number field"))',
      'stddev_pop(field("lookup field"))',
      'stddev_pop(field("link field with number primary field"))',
    ]
  }

  getFormulaType() {
    return 'array'
  }
}

export class BaserowStddevSample extends BaserowFunctionDefinition {
  static getType() {
    return 'stddev_sample'
  }

  getDescription() {
    return (
      'Calculates the sample standard deviation of the values and returns the' +
      ' result. ' +
      'The sample deviation should be used when the provided values are only for a' +
      ' sample or subset  of values for an underlying population.'
    )
  }

  getSyntaxUsage() {
    return ['stddev_sample(numbers from lookup() or field())']
  }

  getExamples() {
    return [
      'stddev_sample(lookup("link field", "number field"))',
      'stddev_sample(field("lookup field"))',
      'stddev_sample(field("link field with number primary field"))',
    ]
  }

  getFormulaType() {
    return 'array'
  }
}

export class BaserowVarianceSample extends BaserowFunctionDefinition {
  static getType() {
    return 'variance_sample'
  }

  getDescription() {
    return (
      'Calculates the sample variance of the values and returns the result. ' +
      'The sample variance should be used when the provided values are only for a' +
      ' sample or subset of values for an underlying population.'
    )
  }

  getSyntaxUsage() {
    return ['variance_sample(numbers from lookup() or field())']
  }

  getExamples() {
    return [
      'variance_sample(lookup("link field", "number field"))',
      'variance_sample(field("lookup field"))',
      'variance_sample(field("link field with number primary field"))',
    ]
  }

  getFormulaType() {
    return 'array'
  }
}

export class BaserowVariancePop extends BaserowFunctionDefinition {
  static getType() {
    return 'variance_pop'
  }

  getDescription() {
    return (
      'Calculates the population variance of the values and returns the result. ' +
      'The population variance should be used when the provided values contain a ' +
      ' value for every single piece of data in the population.'
    )
  }

  getSyntaxUsage() {
    return ['variance_pop(numbers from lookup() or field())']
  }

  getExamples() {
    return [
      'variance_pop(lookup("link field", "number field"))',
      'variance_pop(field("lookup field"))',
      'variance_pop(field("link field with number primary field"))',
    ]
  }

  getFormulaType() {
    return 'array'
  }
}

export class BaserowAvg extends BaserowFunctionDefinition {
  static getType() {
    return 'avg'
  }

  getDescription() {
    return 'Averages all of the values and returns the result'
  }

  getSyntaxUsage() {
    return ['avg(numbers from lookup() or field())']
  }

  getExamples() {
    return [
      'avg(lookup("link field", "number field"))',
      'avg(field("lookup field"))',
      'avg(field("link field with number primary field"))',
    ]
  }

  getFormulaType() {
    return 'array'
  }
}

export class BaserowSum extends BaserowFunctionDefinition {
  static getType() {
    return 'sum'
  }

  getDescription() {
    return 'Sums all of the values and returns the result'
  }

  getSyntaxUsage() {
    return ['sum(numbers from lookup() or field())']
  }

  getExamples() {
    return [
      'sum(lookup("link field", "number field"))',
      'sum(field("lookup field"))',
      'sum(field("link field with number primary field"))',
    ]
  }

  getFormulaType() {
    return 'array'
  }
}

export class BaserowFilter extends BaserowFunctionDefinition {
  static getType() {
    return 'filter'
  }

  getDescription() {
    return (
      'Filters down an expression involving a lookup/link field reference or a' +
      ' lookup function call.'
    )
  }

  getSyntaxUsage() {
    return [
      'filter(an expression involving lookup() or field(a link/lookup field),' +
        ' boolean)',
    ]
  }

  getExamples() {
    return [
      'sum(filter(lookup("link field", "number field"), lookup("link field", "number' +
        ' field") > 10))',
      'filter(field("lookup field"), contains(field("lookup field"), "a"))',
      'filter(field("link field") + "a", length(field("link field")) > 10")',
    ]
  }

  getFormulaType() {
    return 'array'
  }
}
