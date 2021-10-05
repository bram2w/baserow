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
    return 'upper(text)'
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
    return 'lower(text)'
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
    return 'concat(any, any, ...)'
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
    return 'datediff'
  }

  getDescription() {
    return (
      "Given a date unit to measure in as the first argument ('year', " +
      "'month', 'week', 'day', 'hour', 'minute', 'seconds') calculates and returns " +
      'the number of units from the second argument to the third.'
    )
  }

  getSyntaxUsage() {
    return ['daydiff(text, date, date)']
  }

  getExamples() {
    return [
      "datediff('yy', todate('2000-01-01', 'YYYY-MM-DD'), todate('2020-01-01', 'YYYY-MM-DD')) = 20",
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
