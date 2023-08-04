import BaserowFormulaVisitor from '@baserow/formula/parser/generated/BaserowFormulaVisitor'
import { UnknownOperatorError } from '@baserow/formula/parser/errors'

export class FunctionCollection {
  get(name) {
    throw new Error('needs to be implemented')
  }
}

export default class JavascriptExecutor extends BaserowFormulaVisitor {
  constructor(functions, context = {}) {
    super()
    this.functions = functions
    this.context = context
  }

  visitRoot(ctx) {
    return ctx.expr().accept(this)
  }

  visitStringLiteral(ctx) {
    return this.processString(ctx)
  }

  visitDecimalLiteral(ctx) {
    return parseFloat(ctx.getText())
  }

  visitBooleanLiteral(ctx) {
    return ctx.TRUE() !== null
  }

  visitBrackets(ctx) {
    return ctx.expr().accept(this)
  }

  processString(ctx) {
    const literalWithoutOuterQuotes = ctx.getText().slice(1, -1)
    let literal

    if (ctx.SINGLEQ_STRING_LITERAL() !== null) {
      literal = literalWithoutOuterQuotes.replace("\\'", "'")
    } else {
      literal = literalWithoutOuterQuotes.replace('\\"', '"')
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

    formulaFunctionType.validateArgs(args)

    const argsParsed = formulaFunctionType.parseArgs(args)

    return formulaFunctionType.execute(this.context, argsParsed)
  }

  visitBinaryOp(ctx) {
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
    return ctx.getText()
  }

  visitIdentifier(ctx) {
    return ctx.getText()
  }

  visitIntegerLiteral(ctx) {
    return parseInt(ctx.getText())
  }

  visitLeftWhitespaceOrComments(ctx) {
    return ctx.expr().accept(this)
  }

  visitRightWhitespaceOrComments(ctx) {
    return ctx.expr().accept(this)
  }
}
