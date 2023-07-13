export class BaserowFormulaParserError extends Error {
  constructor(offendingSymbol, line, character, message) {
    super()
    this.offendingSymbol = offendingSymbol
    this.line = line
    this.character = character
    this.message = message
  }
}

export class UnknownOperatorError extends Error {
  constructor(operatorName) {
    super()
    this.operatorName = operatorName
  }
}

export class InvalidNumberOfArguments extends Error {
  constructor(formulaFunctionType, args) {
    super()
    this.formulaFunctionType = formulaFunctionType
    this.args = args
  }
}

export class InvalidFormulaArgumentType extends Error {
  constructor(formulaFunctionType, arg) {
    super()
    this.formulaFunctionType = formulaFunctionType
    this.arg = arg
  }
}
