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
