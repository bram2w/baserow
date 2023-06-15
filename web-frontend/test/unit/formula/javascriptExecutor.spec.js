import parseBaserowFormula from '@baserow/formula/parser/parser'
import JavascriptExecutor from '@baserow/formula/parser/javascriptExecutor'
import {
  VALID_FORMULA_TESTS,
  INVALID_FORMULA_TESTS,
} from '@baserow_test_cases/formula_runtime_cases'

describe('JavascriptExecutor', () => {
  test.each(VALID_FORMULA_TESTS)(
    'should correctly resolve the formula %s',
    ({ formula, result, context }) => {
      const tree = parseBaserowFormula(formula)
      expect(new JavascriptExecutor(context).visit(tree)).toEqual(result)
    }
  )

  test.each(INVALID_FORMULA_TESTS)(
    'should correctly raise an error for formula %s',
    ({ formula, context }) => {
      const tree = parseBaserowFormula(formula)
      expect(() => new JavascriptExecutor(context).visit(tree)).toThrow()
    }
  )
})
