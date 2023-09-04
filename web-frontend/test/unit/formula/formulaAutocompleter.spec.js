import {
  autocompleteFormula,
  calculateFilteredFunctionsAndFieldsBasedOnCursorLocation,
} from '@baserow/modules/core/formula/autocompleter/formulaAutocompleter'

function wrap(fields) {
  return fields.map((f) => ({
    value: f,
  }))
}

function unwrap(fields) {
  return fields.map((f) => f.value)
}

const ALL_FIELDS = ['field name a', 'double quoted "a"', "single quoted '"]
const ALL_FUNCTIONS = ['field', 'upper', 'lower', 'length']

describe('Tests checking the formula autocomplete logic', () => {
  const functionFieldFilterTests = [
    ['fi$', ['field'], [], true],
    ['l$', ['lower', 'length'], [], true],
    ['field("$', [], ALL_FIELDS, true],
    ['field("f$', [], ['field name a'], true],
    ['field("f$")', [], ['field name a'], true],
    ['field("d$")', [], ['double quoted "a"'], true],
    ['field("s$")', [], ["single quoted '"], true],
    ['lower()$', ALL_FUNCTIONS, ALL_FIELDS, false],
    ['$', ALL_FUNCTIONS, ALL_FIELDS, false],
  ]
  test.each(functionFieldFilterTests)(
    'for formula %s it filters fields and functions correctly',
    (
      startingFormulaWithCursor,
      expectedFilteredFunctions,
      expectedFilteredFields,
      expectedIsFiltered
    ) => {
      const startingCursorPosition = startingFormulaWithCursor.indexOf('$')
      const formulaWithoutCursorMarker = startingFormulaWithCursor.replace(
        '$',
        ''
      )
      const { filteredFunctions, filteredFields, filtered } =
        calculateFilteredFunctionsAndFieldsBasedOnCursorLocation(
          formulaWithoutCursorMarker,
          startingCursorPosition,
          wrap(ALL_FIELDS),
          wrap(ALL_FUNCTIONS)
        )
      expect(unwrap(filteredFunctions)).toEqual(expectedFilteredFunctions)
      expect(unwrap(filteredFields)).toEqual(expectedFilteredFields)
      expect(filtered).toEqual(expectedIsFiltered)
    }
  )
  const autocompleteTestsWhereDollarIsCursorLocation = [
    ['fi$', "field('$')"],
    ['fie$', "field('$')"],
    ['fiel$', "field('$')"],
    ['field$', "field('$')"],
    ['field($', "field('field name a')$"],
    ["field('$", "field('field name a')$"],
    ["field(''$", "field('field name a')$"],
    ["field('')$", "field('')field('field name a')$"],
    ['fie$)', "field('$'))"],
    ['f$i', "field('$'i"],
    ["field2('$", "field2('field('field name a')$"],
    ["field('$')", "field('field name a')$"],
    ['field("$")', 'field("field name a")$'],
    ['field("field na$me a")', 'field("field na$me a")'],
    ['field("field na$")', 'field("field name a")$'],
    ["field('field na$')", "field('field name a')$"],
    ['field("d$")', 'field("double quoted \\"a\\"")$'],
    ['field("s$")', 'field("single quoted \'")$'],
    ["field('d$')", 'field(\'double quoted "a"\')$'],
    ["field('s$')", "field('single quoted \\'')$"],
    ['field("d$', 'field("double quoted \\"a\\"")$'],
    ['field("s$', 'field("single quoted \'")$'],
    ["field('d$", 'field(\'double quoted "a"\')$'],
    ["field('s$", "field('single quoted \\'')$"],
    ['u$', 'upper($)'],
    ['l$', 'lower($)'],
    ['le$', 'length($)'],
    ['u($', "u(field('field name a')$"],
    ['u$)', 'upper($))'],
    ['upper(f$)', "upper(field('$'))"],
    ['lower(upper(field("$")', 'lower(upper(field("field name a")$)'],
    ['upper(f$', "upper(field('$')"],
    ['upper(l$)', 'upper(lower($))'],
    ['upper(l$', 'upper(lower($)'],
    ['up$field("a")', 'upper($field("a")'],
  ]
  test.each(autocompleteTestsWhereDollarIsCursorLocation)(
    'autocomplete test for %s where dollar is cursor location',
    (startingFormulaWithCursor, expectedResultingFormulaWithCursor) => {
      const startingCursorPosition = startingFormulaWithCursor.indexOf('$')
      const formulaWithoutCursorMarker = startingFormulaWithCursor.replace(
        '$',
        ''
      )
      const { filteredFunctions, filteredFields } =
        calculateFilteredFunctionsAndFieldsBasedOnCursorLocation(
          formulaWithoutCursorMarker,
          startingCursorPosition,
          wrap(ALL_FIELDS),
          wrap(ALL_FUNCTIONS)
        )
      const { autocompletedFormula, newCursorPosition } = autocompleteFormula(
        formulaWithoutCursorMarker,
        startingCursorPosition,
        filteredFunctions[0],
        filteredFields[0]
      )
      const resultingFormulaWithCursor = [
        autocompletedFormula.slice(0, newCursorPosition),
        '$',
        autocompletedFormula.slice(newCursorPosition),
      ].join('')
      expect(resultingFormulaWithCursor).toStrictEqual(
        expectedResultingFormulaWithCursor
      )
    }
  )
})
