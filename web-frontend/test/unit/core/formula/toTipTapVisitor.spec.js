import { TestApp } from '@baserow/test/helpers/testApp'
import { RuntimeFunctionCollection } from '@baserow/modules/core/functionCollection'
import { ToTipTapVisitor } from '@baserow/modules/core/formula/toTipTapVisitor'
import parseBaserowFormula from '@baserow/formula/parser/parser'
import testCases from '@baserow_test_cases/tip_tap_visitor_cases.json'

describe('toTipTapVisitor', () => {
  let testApp = null
  beforeAll(() => {
    testApp = new TestApp()
  })

  testCases.forEach(({ formula, content }) => {
    it('should return the expected formula', () => {
      const functionCollection = new RuntimeFunctionCollection(
        testApp.store.$registry
      )
      const tree = parseBaserowFormula(formula)
      const result = new ToTipTapVisitor(functionCollection).visit(tree)
      expect(result).toEqual(content)
    })
  })
})
