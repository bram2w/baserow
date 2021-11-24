// Generated from BaserowFormula.g4 by ANTLR 4.8
// jshint ignore: start
var antlr4 = require('antlr4/index');

// This class defines a complete generic visitor for a parse tree produced by BaserowFormula.

function BaserowFormulaVisitor() {
	antlr4.tree.ParseTreeVisitor.call(this);
	return this;
}

BaserowFormulaVisitor.prototype = Object.create(antlr4.tree.ParseTreeVisitor.prototype);
BaserowFormulaVisitor.prototype.constructor = BaserowFormulaVisitor;

// Visit a parse tree produced by BaserowFormula#root.
BaserowFormulaVisitor.prototype.visitRoot = function(ctx) {
  return this.visitChildren(ctx);
};


// Visit a parse tree produced by BaserowFormula#FieldReference.
BaserowFormulaVisitor.prototype.visitFieldReference = function(ctx) {
  return this.visitChildren(ctx);
};


// Visit a parse tree produced by BaserowFormula#StringLiteral.
BaserowFormulaVisitor.prototype.visitStringLiteral = function(ctx) {
  return this.visitChildren(ctx);
};


// Visit a parse tree produced by BaserowFormula#Brackets.
BaserowFormulaVisitor.prototype.visitBrackets = function(ctx) {
  return this.visitChildren(ctx);
};


// Visit a parse tree produced by BaserowFormula#BooleanLiteral.
BaserowFormulaVisitor.prototype.visitBooleanLiteral = function(ctx) {
  return this.visitChildren(ctx);
};


// Visit a parse tree produced by BaserowFormula#RightWhitespaceOrComments.
BaserowFormulaVisitor.prototype.visitRightWhitespaceOrComments = function(ctx) {
  return this.visitChildren(ctx);
};


// Visit a parse tree produced by BaserowFormula#DecimalLiteral.
BaserowFormulaVisitor.prototype.visitDecimalLiteral = function(ctx) {
  return this.visitChildren(ctx);
};


// Visit a parse tree produced by BaserowFormula#LeftWhitespaceOrComments.
BaserowFormulaVisitor.prototype.visitLeftWhitespaceOrComments = function(ctx) {
  return this.visitChildren(ctx);
};


// Visit a parse tree produced by BaserowFormula#FunctionCall.
BaserowFormulaVisitor.prototype.visitFunctionCall = function(ctx) {
  return this.visitChildren(ctx);
};


// Visit a parse tree produced by BaserowFormula#FieldByIdReference.
BaserowFormulaVisitor.prototype.visitFieldByIdReference = function(ctx) {
  return this.visitChildren(ctx);
};


// Visit a parse tree produced by BaserowFormula#LookupFieldReference.
BaserowFormulaVisitor.prototype.visitLookupFieldReference = function(ctx) {
  return this.visitChildren(ctx);
};


// Visit a parse tree produced by BaserowFormula#IntegerLiteral.
BaserowFormulaVisitor.prototype.visitIntegerLiteral = function(ctx) {
  return this.visitChildren(ctx);
};


// Visit a parse tree produced by BaserowFormula#BinaryOp.
BaserowFormulaVisitor.prototype.visitBinaryOp = function(ctx) {
  return this.visitChildren(ctx);
};


// Visit a parse tree produced by BaserowFormula#ws_or_comment.
BaserowFormulaVisitor.prototype.visitWs_or_comment = function(ctx) {
  return this.visitChildren(ctx);
};


// Visit a parse tree produced by BaserowFormula#func_name.
BaserowFormulaVisitor.prototype.visitFunc_name = function(ctx) {
  return this.visitChildren(ctx);
};


// Visit a parse tree produced by BaserowFormula#field_reference.
BaserowFormulaVisitor.prototype.visitField_reference = function(ctx) {
  return this.visitChildren(ctx);
};


// Visit a parse tree produced by BaserowFormula#identifier.
BaserowFormulaVisitor.prototype.visitIdentifier = function(ctx) {
  return this.visitChildren(ctx);
};



exports.BaserowFormulaVisitor = BaserowFormulaVisitor;