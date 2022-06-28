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
    const { i18n } = this.app
    return i18n.t('formulaFunctions.upperDescription')
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
    const { i18n } = this.app
    return i18n.t('formulaFunctions.lowerDescription')
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
    const { i18n } = this.app
    return i18n.t('formulaFunctions.concatDescription')
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
    const { i18n } = this.app
    return i18n.t('formulaFunctions.addDescription')
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
    const { i18n } = this.app
    return i18n.t('formulaFunctions.minusDescription')
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
    const { i18n } = this.app
    return i18n.t('formulaFunctions.multiplyDescription')
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
    const { i18n } = this.app
    return i18n.t('formulaFunctions.divideDescription')
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
    const { i18n } = this.app
    return i18n.t('formulaFunctions.equalDescription')
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
    const { i18n } = this.app
    return i18n.t('formulaFunctions.ifDescription')
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
    const { i18n } = this.app
    return i18n.t('formulaFunctions.toTextDescription')
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
    const { i18n } = this.app
    return i18n.t('formulaFunctions.datetimeFormatDescription')
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
    const { i18n } = this.app
    return i18n.t('formulaFunctions.toNumberDescription')
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
    const { i18n } = this.app
    return i18n.t('formulaFunctions.fieldDescription')
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
    const { i18n } = this.app
    return i18n.t('formulaFunctions.lookupDescription')
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
    const { i18n } = this.app
    return i18n.t('formulaFunctions.isBlankDescription')
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
    const { i18n } = this.app
    return i18n.t('formulaFunctions.tDescription')
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
    const { i18n } = this.app
    return i18n.t('formulaFunctions.notDescription')
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
    const { i18n } = this.app
    return i18n.t('formulaFunctions.greaterThanDescription')
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
    const { i18n } = this.app
    return i18n.t('formulaFunctions.greaterThanOrEqualDescription')
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
    const { i18n } = this.app
    return i18n.t('formulaFunctions.lessThanDescription')
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
    const { i18n } = this.app
    return i18n.t('formulaFunctions.lessThanOrEqualDescription')
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
    const { i18n } = this.app
    return i18n.t('formulaFunctions.toDateDescription')
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
    const { i18n } = this.app
    return i18n.t('formulaFunctions.dayDescription')
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
    const { i18n } = this.app
    return i18n.t('formulaFunctions.dateDiffDescription')
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
    const { i18n } = this.app
    return i18n.t('formulaFunctions.andDescription')
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
    const { i18n } = this.app
    return i18n.t('formulaFunctions.orDescription')
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
    const { i18n } = this.app
    return i18n.t('formulaFunctions.dateIntervalDescription')
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
    const { i18n } = this.app
    return i18n.t('formulaFunctions.replaceDescription')
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
    const { i18n } = this.app
    return i18n.t('formulaFunctions.searchDescription')
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
    const { i18n } = this.app
    return i18n.t('formulaFunctions.rowIdDescription')
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
    const { i18n } = this.app
    return i18n.t('formulaFunctions.lengthDescription')
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
    const { i18n } = this.app
    return i18n.t('formulaFunctions.reverseDescription')
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
    const { i18n } = this.app
    return i18n.t('formulaFunctions.notEqualDescription')
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
    const { i18n } = this.app
    return i18n.t('formulaFunctions.countDescription')
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
    const { i18n } = this.app
    return i18n.t('formulaFunctions.containsDescription')
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
    const { i18n } = this.app
    return i18n.t('formulaFunctions.leftDescription')
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
    const { i18n } = this.app
    return i18n.t('formulaFunctions.rightDescription')
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
    const { i18n } = this.app
    return i18n.t('formulaFunctions.trimDescription')
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
    const { i18n } = this.app
    return i18n.t('formulaFunctions.regexReplaceDescription')
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
    const { i18n } = this.app
    return i18n.t('formulaFunctions.greatestDescription')
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
export class BaserowRound extends BaserowFunctionDefinition {
  static getType() {
    return 'round'
  }

  getDescription() {
    const { i18n } = this.app
    return i18n.t('formulaFunctions.roundDescription')
  }

  getSyntaxUsage() {
    return ['round(number, number)']
  }

  getExamples() {
    return ['round(1.12345,2) = 1.12']
  }

  getFormulaType() {
    return 'number'
  }
}

export class BaserowInt extends BaserowFunctionDefinition {
  static getType() {
    return 'int'
  }

  getDescription() {
    const { i18n } = this.app
    return i18n.t('formulaFunctions.intDescription')
  }

  getSyntaxUsage() {
    return ['round(int)']
  }

  getExamples() {
    return ['int(1.49) = 1']
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
    const { i18n } = this.app
    return i18n.t('formulaFunctions.leastDescription')
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
    const { i18n } = this.app
    return i18n.t('formulaFunctions.monthDescription')
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
    const { i18n } = this.app
    return i18n.t('formulaFunctions.yearDescription')
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
    const { i18n } = this.app
    return i18n.t('formulaFunctions.secondDescription')
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
    const { i18n } = this.app
    return i18n.t('formulaFunctions.whenEmptyDescription')
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
    const { i18n } = this.app
    return i18n.t('formulaFunctions.anyDescription')
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
    const { i18n } = this.app
    return i18n.t('formulaFunctions.everyDescription')
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
    const { i18n } = this.app
    return i18n.t('formulaFunctions.maxDescription')
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
    const { i18n } = this.app
    return i18n.t('formulaFunctions.minDescription')
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
    const { i18n } = this.app
    return i18n.t('formulaFunctions.joinDescription')
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
    const { i18n } = this.app
    return i18n.t('formulaFunctions.stddevPopDescription')
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
    const { i18n } = this.app
    return i18n.t('formulaFunctions.stddevSampleDescription')
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
    const { i18n } = this.app
    return i18n.t('formulaFunctions.varianceSampleDescription')
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
    const { i18n } = this.app
    return i18n.t('formulaFunctions.variancePopDescription')
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
    const { i18n } = this.app
    return i18n.t('formulaFunctions.avgDescription')
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
    const { i18n } = this.app
    return i18n.t('formulaFunctions.sumDescription')
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
    const { i18n } = this.app
    return i18n.t('formulaFunctions.filterDescription')
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
