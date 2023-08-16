import BaserowFormulaVisitor from '@baserow/formula/parser/generated/BaserowFormulaVisitor'
import { UnknownOperatorError } from '@baserow/formula/parser/errors'
import _ from 'lodash'

export class ToTipTapVisitor extends BaserowFormulaVisitor {
  constructor(functions) {
    super()
    this.functions = functions
  }

  visitRoot(ctx) {
    const result = ctx.expr().accept(this)
    return _.isArray(result) ? result : [result]
  }

  visitStringLiteral(ctx) {
    switch (ctx.getText()) {
      case "'\n'":
        return { type: 'hardBreak' }
      default:
        return { type: 'text', text: this.processString(ctx) }
    }
  }

  visitDecimalLiteral(ctx) {
    // TODO
    return parseFloat(ctx.getText())
  }

  visitBooleanLiteral(ctx) {
    // TODO
    return ctx.TRUE() !== null
  }

  visitBrackets(ctx) {
    // TODO
    return ctx.expr().accept(this)
  }

  processString(ctx) {
    const literalWithoutOuterQuotes = ctx.getText().slice(1, -1)
    let literal

    if (ctx.SINGLEQ_STRING_LITERAL() !== null) {
      literal = literalWithoutOuterQuotes.replace(/\\'/g, "'")
    } else {
      literal = literalWithoutOuterQuotes.replace(/\\"/g, '"')
    }

    return literal
  }

  visitFunctionCall(ctx) {
    const functionName = this.visitFuncName(ctx.func_name()).toLowerCase()
    const functionArgumentExpressions = ctx.expr()

    return this.doFunc(functionArgumentExpressions, functionName)
  }

  doFunc(functionArgumentExpressions, functionName) {
    const args = Array.from(functionArgumentExpressions, (expr) =>
      expr.accept(this)
    )

    const formulaFunctionType = this.functions.get(functionName)

    return formulaFunctionType.toNode(args)
  }

  visitBinaryOp(ctx) {
    // TODO
    let op

    if (ctx.PLUS()) {
      op = 'add'
    } else if (ctx.MINUS()) {
      op = 'minus'
    } else if (ctx.SLASH()) {
      op = 'divide'
    } else if (ctx.EQUAL()) {
      op = 'equal'
    } else if (ctx.BANG_EQUAL()) {
      op = 'not_equal'
    } else if (ctx.STAR()) {
      op = 'multiply'
    } else if (ctx.GT()) {
      op = 'greater_than'
    } else if (ctx.LT()) {
      op = 'less_than'
    } else if (ctx.GTE()) {
      op = 'greater_than_or_equal'
    } else if (ctx.LTE()) {
      op = 'less_than_or_equal'
    } else {
      throw new UnknownOperatorError(ctx.getText())
    }

    return this.doFunc(ctx.expr(), op)
  }

  visitFuncName(ctx) {
    // TODO
    return ctx.getText()
  }

  visitIdentifier(ctx) {
    // TODO
    return ctx.getText()
  }

  visitIntegerLiteral(ctx) {
    // TODO
    return parseInt(ctx.getText())
  }

  visitLeftWhitespaceOrComments(ctx) {
    // TODO
    return ctx.expr().accept(this)
  }

  visitRightWhitespaceOrComments(ctx) {
    // TODO
    return ctx.expr().accept(this)
  }
}
