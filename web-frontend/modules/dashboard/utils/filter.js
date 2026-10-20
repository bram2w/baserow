import parseBaserowFormula from '@baserow/modules/core/formula/parser/parser'
import BaserowFormula from '@baserow/modules/core/formula/parser/generated/BaserowFormula'

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

export function getReferencedDashboardFilterId(formula) {
  if (!formula?.formula || formula.mode === 'raw') return null
  try {
    const expression = unwrapExpression(
      parseBaserowFormula(formula.formula).expr()
    )
    if (
      !(expression instanceof BaserowFormula.FunctionCallContext) ||
      expression.func_name().getText().toLowerCase() !== 'get' ||
      expression.expr().length !== 1
    )
      return null
    const argument = unwrapExpression(expression.expr(0))
    if (!(argument instanceof BaserowFormula.StringLiteralContext)) return null
    const path = argument.getText().slice(1, -1)
    const match = /^dashboard_filter\.([1-9][0-9]*)(?:\.(?:\*|[0-9]+))?$/.exec(
      path
    )
    return match ? Number(match[1]) : null
  } catch {
    // Incomplete expressions are still editable in the formula input.
    return null
  }
}
