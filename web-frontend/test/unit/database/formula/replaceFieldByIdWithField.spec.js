import { replaceFieldByIdWithField } from '@baserow/modules/database/formula/parser/replaceFieldByIdWithField'

function _assertReturnsSame(formula) {
  const newFormula = replaceFieldByIdWithField(formula, {
    22: 'newName',
  })
  expect(newFormula).toStrictEqual(formula)
}

describe('Tests checking the replaceFieldByIdWithField formula parsing function', () => {
  test('can replace a single quoted field by id', () => {
    const newFormula = replaceFieldByIdWithField('field_by_id(1)', {
      1: 'newName',
    })
    expect(newFormula).toStrictEqual("field('newName')")
  })
  test('can replace a field by id reference keeping whitespace', () => {
    const newFormula = replaceFieldByIdWithField('field_by_id( \n \n1  )', {
      1: 'newName',
    })
    expect(newFormula).toStrictEqual("field( \n \n'newName'  )")
  })
  test('can replace a field by id with a name containing single quotes', () => {
    const newFormula = replaceFieldByIdWithField('field_by_id(1)', {
      1: "newName with '",
    })
    expect(newFormula).toStrictEqual("field('newName with \\'')")
  })
  test('can replace a field by id with a name containing double quotes', () => {
    const newFormula = replaceFieldByIdWithField('field_by_id(1)', {
      1: 'newName with "',
    })
    expect(newFormula).toStrictEqual("field('newName with \"')")
  })
  test('can replace a field by id keeping whitespace and comments', () => {
    const newFormula = replaceFieldByIdWithField(
      '/* comment */field_by_id(/* comment */ \n \n1  /* a comment */)',
      {
        1: 'newName',
      }
    )
    expect(newFormula).toStrictEqual(
      "/* comment */field(/* comment */ \n \n'newName'  /* a comment */)"
    )
  })
  test('can replace multiple different field by ids ', () => {
    const newFormula = replaceFieldByIdWithField(
      'concat(field_by_id(1), field_by_id(1), field_by_id(2))',
      {
        1: 'newName',
        2: 'newOther',
      }
    )
    expect(newFormula).toStrictEqual(
      "concat(field('newName'), field('newName'), field('newOther'))"
    )
  })
  test('doesnt change field by id not in dict', () => {
    const newFormula = replaceFieldByIdWithField('field_by_id(2)', {
      1: 'newName',
    })
    expect(newFormula).toStrictEqual('field_by_id(2)')
  })
  test('returns same formula for invalid syntax', () => {
    _assertReturnsSame('field_by_id(2')
    _assertReturnsSame("field_by_id('test')")
    _assertReturnsSame('field_by_id(test)')
    _assertReturnsSame('field_by_id((test))')
    _assertReturnsSame("field_by_id('''test'')")
    _assertReturnsSame(
      'field_by_id(111111111111111111111111111111111111111111111111111111111111111)'
    )
  })
})
