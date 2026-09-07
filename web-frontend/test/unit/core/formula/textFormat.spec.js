import { isFormulaValid, resolveFormula } from '@baserow/modules/core/formula'
import {
  MARKDOWN_PREFIX,
  TEXT_FORMATS,
  addPrefix,
  getFormat,
  getFormulaFormat,
  setFormat,
  setFormulaFormat,
  splitFormat,
  stripFormat,
} from '@baserow/modules/core/formula/textFormat'

describe('textFormat helpers', () => {
  test.each([
    [`${MARKDOWN_PREFIX}get('a.b')`, TEXT_FORMATS.MARKDOWN, "get('a.b')"],
    [MARKDOWN_PREFIX, TEXT_FORMATS.MARKDOWN, ''],
    ["get('a.b')", TEXT_FORMATS.PLAIN, "get('a.b')"],
    // Only a leading marker counts, a marker inside a literal is text.
    [
      `'${MARKDOWN_PREFIX}**a**'`,
      TEXT_FORMATS.PLAIN,
      `'${MARKDOWN_PREFIX}**a**'`,
    ],
    ['', TEXT_FORMATS.PLAIN, ''],
    [undefined, TEXT_FORMATS.PLAIN, undefined],
    [null, TEXT_FORMATS.PLAIN, null],
    [5, TEXT_FORMATS.PLAIN, 5],
  ])('splits %p', (value, format, bare) => {
    expect(splitFormat(value)).toEqual({ format, value: bare })
    expect(getFormat(value)).toBe(format)
    expect(stripFormat(value)).toBe(bare)
  })

  test('adds and changes the format of a string', () => {
    expect(addPrefix("get('a')")).toBe(`${MARKDOWN_PREFIX}get('a')`)
    expect(addPrefix("get('a')", TEXT_FORMATS.PLAIN)).toBe("get('a')")
    expect(addPrefix('', TEXT_FORMATS.MARKDOWN)).toBe(MARKDOWN_PREFIX)
    expect(addPrefix(undefined, TEXT_FORMATS.MARKDOWN)).toBe(MARKDOWN_PREFIX)
    expect(setFormat(`${MARKDOWN_PREFIX}Name`, TEXT_FORMATS.PLAIN)).toBe('Name')
    expect(setFormat('Name', TEXT_FORMATS.MARKDOWN)).toBe(
      `${MARKDOWN_PREFIX}Name`
    )
    expect(setFormat(`${MARKDOWN_PREFIX}Name`, TEXT_FORMATS.MARKDOWN)).toBe(
      `${MARKDOWN_PREFIX}Name`
    )
  })

  test('reads and writes the format of a formula object', () => {
    const formula = { formula: "get('a')", mode: 'simple', version: '0.1' }

    expect(getFormulaFormat(formula)).toBe(TEXT_FORMATS.PLAIN)
    expect(getFormulaFormat({})).toBe(TEXT_FORMATS.PLAIN)
    expect(getFormulaFormat(undefined)).toBe(TEXT_FORMATS.PLAIN)

    const markdown = setFormulaFormat(formula, TEXT_FORMATS.MARKDOWN)
    expect(markdown).toEqual({
      formula: `${MARKDOWN_PREFIX}get('a')`,
      mode: 'simple',
      version: '0.1',
    })
    // The input is left untouched.
    expect(formula.formula).toBe("get('a')")
    expect(getFormulaFormat(markdown)).toBe(TEXT_FORMATS.MARKDOWN)
    expect(setFormulaFormat(markdown, TEXT_FORMATS.PLAIN)).toEqual(formula)
    expect(setFormulaFormat({}, TEXT_FORMATS.MARKDOWN)).toEqual({
      formula: MARKDOWN_PREFIX,
    })
  })
})

describe('resolveFormula with the text format marker', () => {
  const resolve = (formulaCtx) => resolveFormula(formulaCtx, {}, {})

  test.each([
    ["'**a**'", 'simple', '**a**'],
    [`${MARKDOWN_PREFIX}'**a**'`, 'simple', '**a**'],
    // A marker inside the resolved output is just text.
    [`'${MARKDOWN_PREFIX}**a**'`, 'simple', `${MARKDOWN_PREFIX}**a**`],
    ['**a**', 'raw', '**a**'],
    [`${MARKDOWN_PREFIX}**a**`, 'raw', '**a**'],
    ['', 'simple', ''],
    [MARKDOWN_PREFIX, 'simple', ''],
    [MARKDOWN_PREFIX, 'raw', ''],
  ])('resolves %p in %s mode to %p', (formula, mode, expected) => {
    expect(resolve({ formula, mode })).toBe(expected)
  })
})

describe('isFormulaValid with the text format marker', () => {
  test('validates the formula behind the marker', () => {
    expect(isFormulaValid(`${MARKDOWN_PREFIX}'a'`, {}).valid).toBe(true)
    expect(isFormulaValid(MARKDOWN_PREFIX, {}).valid).toBe(true)
    expect(isFormulaValid(`${MARKDOWN_PREFIX}'a`, {}).valid).toBe(false)
    expect(isFormulaValid("'a", {}).valid).toBe(false)
  })
})
