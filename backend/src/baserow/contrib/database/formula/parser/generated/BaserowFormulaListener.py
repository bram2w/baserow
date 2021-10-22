# Generated from BaserowFormula.g4 by ANTLR 4.8
from antlr4 import *

if __name__ is not None and "." in __name__:
    from .BaserowFormula import BaserowFormula
else:
    from BaserowFormula import BaserowFormula

# This class defines a complete listener for a parse tree produced by BaserowFormula.
class BaserowFormulaListener(ParseTreeListener):

    # Enter a parse tree produced by BaserowFormula#root.
    def enterRoot(self, ctx: BaserowFormula.RootContext):
        pass

    # Exit a parse tree produced by BaserowFormula#root.
    def exitRoot(self, ctx: BaserowFormula.RootContext):
        pass

    # Enter a parse tree produced by BaserowFormula#FieldReference.
    def enterFieldReference(self, ctx: BaserowFormula.FieldReferenceContext):
        pass

    # Exit a parse tree produced by BaserowFormula#FieldReference.
    def exitFieldReference(self, ctx: BaserowFormula.FieldReferenceContext):
        pass

    # Enter a parse tree produced by BaserowFormula#StringLiteral.
    def enterStringLiteral(self, ctx: BaserowFormula.StringLiteralContext):
        pass

    # Exit a parse tree produced by BaserowFormula#StringLiteral.
    def exitStringLiteral(self, ctx: BaserowFormula.StringLiteralContext):
        pass

    # Enter a parse tree produced by BaserowFormula#Brackets.
    def enterBrackets(self, ctx: BaserowFormula.BracketsContext):
        pass

    # Exit a parse tree produced by BaserowFormula#Brackets.
    def exitBrackets(self, ctx: BaserowFormula.BracketsContext):
        pass

    # Enter a parse tree produced by BaserowFormula#BooleanLiteral.
    def enterBooleanLiteral(self, ctx: BaserowFormula.BooleanLiteralContext):
        pass

    # Exit a parse tree produced by BaserowFormula#BooleanLiteral.
    def exitBooleanLiteral(self, ctx: BaserowFormula.BooleanLiteralContext):
        pass

    # Enter a parse tree produced by BaserowFormula#RightWhitespaceOrComments.
    def enterRightWhitespaceOrComments(
        self, ctx: BaserowFormula.RightWhitespaceOrCommentsContext
    ):
        pass

    # Exit a parse tree produced by BaserowFormula#RightWhitespaceOrComments.
    def exitRightWhitespaceOrComments(
        self, ctx: BaserowFormula.RightWhitespaceOrCommentsContext
    ):
        pass

    # Enter a parse tree produced by BaserowFormula#DecimalLiteral.
    def enterDecimalLiteral(self, ctx: BaserowFormula.DecimalLiteralContext):
        pass

    # Exit a parse tree produced by BaserowFormula#DecimalLiteral.
    def exitDecimalLiteral(self, ctx: BaserowFormula.DecimalLiteralContext):
        pass

    # Enter a parse tree produced by BaserowFormula#LeftWhitespaceOrComments.
    def enterLeftWhitespaceOrComments(
        self, ctx: BaserowFormula.LeftWhitespaceOrCommentsContext
    ):
        pass

    # Exit a parse tree produced by BaserowFormula#LeftWhitespaceOrComments.
    def exitLeftWhitespaceOrComments(
        self, ctx: BaserowFormula.LeftWhitespaceOrCommentsContext
    ):
        pass

    # Enter a parse tree produced by BaserowFormula#FunctionCall.
    def enterFunctionCall(self, ctx: BaserowFormula.FunctionCallContext):
        pass

    # Exit a parse tree produced by BaserowFormula#FunctionCall.
    def exitFunctionCall(self, ctx: BaserowFormula.FunctionCallContext):
        pass

    # Enter a parse tree produced by BaserowFormula#FieldByIdReference.
    def enterFieldByIdReference(self, ctx: BaserowFormula.FieldByIdReferenceContext):
        pass

    # Exit a parse tree produced by BaserowFormula#FieldByIdReference.
    def exitFieldByIdReference(self, ctx: BaserowFormula.FieldByIdReferenceContext):
        pass

    # Enter a parse tree produced by BaserowFormula#IntegerLiteral.
    def enterIntegerLiteral(self, ctx: BaserowFormula.IntegerLiteralContext):
        pass

    # Exit a parse tree produced by BaserowFormula#IntegerLiteral.
    def exitIntegerLiteral(self, ctx: BaserowFormula.IntegerLiteralContext):
        pass

    # Enter a parse tree produced by BaserowFormula#BinaryOp.
    def enterBinaryOp(self, ctx: BaserowFormula.BinaryOpContext):
        pass

    # Exit a parse tree produced by BaserowFormula#BinaryOp.
    def exitBinaryOp(self, ctx: BaserowFormula.BinaryOpContext):
        pass

    # Enter a parse tree produced by BaserowFormula#ws_or_comment.
    def enterWs_or_comment(self, ctx: BaserowFormula.Ws_or_commentContext):
        pass

    # Exit a parse tree produced by BaserowFormula#ws_or_comment.
    def exitWs_or_comment(self, ctx: BaserowFormula.Ws_or_commentContext):
        pass

    # Enter a parse tree produced by BaserowFormula#func_name.
    def enterFunc_name(self, ctx: BaserowFormula.Func_nameContext):
        pass

    # Exit a parse tree produced by BaserowFormula#func_name.
    def exitFunc_name(self, ctx: BaserowFormula.Func_nameContext):
        pass

    # Enter a parse tree produced by BaserowFormula#field_reference.
    def enterField_reference(self, ctx: BaserowFormula.Field_referenceContext):
        pass

    # Exit a parse tree produced by BaserowFormula#field_reference.
    def exitField_reference(self, ctx: BaserowFormula.Field_referenceContext):
        pass

    # Enter a parse tree produced by BaserowFormula#identifier.
    def enterIdentifier(self, ctx: BaserowFormula.IdentifierContext):
        pass

    # Exit a parse tree produced by BaserowFormula#identifier.
    def exitIdentifier(self, ctx: BaserowFormula.IdentifierContext):
        pass


del BaserowFormula
