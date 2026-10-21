import parseBaserowFormula from '@baserow/modules/core/formula/parser/parser'
import BaserowFormula from '@baserow/modules/core/formula/parser/generated/BaserowFormula'
import BaserowFormulaVisitor from '@baserow/modules/core/formula/parser/generated/BaserowFormulaVisitor'

export const filterHasValue = (filter) =>
  !['empty', 'not_empty'].includes(filter.operator)

export const filterHasOptions = (filter) =>
  filter.mode === 'dropdown' && filterHasValue(filter)

export function shouldResetFilterValues(previous, next) {
  return (
    previous != null &&
    (previous.mode !== next.mode ||
      filterHasValue(previous) !== filterHasValue(next) ||
      (next.mode === 'dropdown' && previous.multiple !== next.multiple))
  )
}

function unwrapExpression(expression) {
  const wrappers = [
    BaserowFormula.BracketsContext,
    BaserowFormula.LeftWhitespaceOrCommentsContext,
    BaserowFormula.RightWhitespaceOrCommentsContext,
  ]
  while (wrappers.some((type) => expression instanceof type)) {
    expression = expression.expr()
  }
  return expression
}

function getDashboardFilterPath(expression) {
  expression = unwrapExpression(expression)
  if (
    !(expression instanceof BaserowFormula.FunctionCallContext) ||
    expression.func_name().getText().toLowerCase() !== 'get' ||
    expression.expr().length !== 1
  )
    return null
  const argument = unwrapExpression(expression.expr(0))
  if (!(argument instanceof BaserowFormula.StringLiteralContext)) return null
  const path = argument.getText().slice(1, -1)
  const match = /^dashboard_filter\.([1-9][0-9]*)(?:\.(\*|[0-9]+))?$/.exec(path)
  return match ? { filterId: Number(match[1]), index: match[2] } : null
}

export function getReferencedDashboardFilterId(formula) {
  if (!formula?.formula || formula.mode === 'raw') return null
  try {
    return (
      getDashboardFilterPath(parseBaserowFormula(formula.formula).expr())
        ?.filterId ?? null
    )
  } catch {
    // Incomplete expressions are still editable in the formula input.
    return null
  }
}

class DashboardFilterReferenceVisitor extends BaserowFormulaVisitor {
  constructor() {
    super()
    this.references = []
  }

  visitFunctionCall(ctx) {
    const reference = getDashboardFilterPath(ctx)
    if (reference) this.references.push(reference)
    return this.visitChildren(ctx)
  }
}

export function hasActiveDashboardFilter(formula, filters, appliedValues) {
  if (!formula?.formula || formula.mode === 'raw') return false
  try {
    const visitor = new DashboardFilterReferenceVisitor()
    visitor.visit(parseBaserowFormula(formula.formula))
    return visitor.references.some(({ filterId, index }) => {
      const filter = filters.find(({ id }) => id === filterId)
      if (!filter) return false
      let values = appliedValues[filterId] ?? []
      if (filter.mode !== 'dropdown' || !filter.multiple) {
        if (index !== undefined) return false
        values = values.slice(0, 1)
      } else if (index !== undefined && index !== '*') {
        values = values.slice(Number(index), Number(index) + 1)
      }
      return values.some((value) => value.trim() !== '')
    })
  } catch {
    return false
  }
}
