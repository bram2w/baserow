# Generated from BaserowFormula.g4 by ANTLR 4.8
from antlr4 import *
if __name__ is not None and "." in __name__:
    from .BaserowFormula import BaserowFormula
else:
    from BaserowFormula import BaserowFormula

# This class defines a complete generic visitor for a parse tree produced by BaserowFormula.

class BaserowFormulaVisitor(ParseTreeVisitor):

    # Visit a parse tree produced by BaserowFormula#root.
    def visitRoot(self, ctx:BaserowFormula.RootContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by BaserowFormula#FieldReference.
    def visitFieldReference(self, ctx:BaserowFormula.FieldReferenceContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by BaserowFormula#StringLiteral.
    def visitStringLiteral(self, ctx:BaserowFormula.StringLiteralContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by BaserowFormula#Brackets.
    def visitBrackets(self, ctx:BaserowFormula.BracketsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by BaserowFormula#BooleanLiteral.
    def visitBooleanLiteral(self, ctx:BaserowFormula.BooleanLiteralContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by BaserowFormula#RightWhitespaceOrComments.
    def visitRightWhitespaceOrComments(self, ctx:BaserowFormula.RightWhitespaceOrCommentsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by BaserowFormula#DecimalLiteral.
    def visitDecimalLiteral(self, ctx:BaserowFormula.DecimalLiteralContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by BaserowFormula#LeftWhitespaceOrComments.
    def visitLeftWhitespaceOrComments(self, ctx:BaserowFormula.LeftWhitespaceOrCommentsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by BaserowFormula#FunctionCall.
    def visitFunctionCall(self, ctx:BaserowFormula.FunctionCallContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by BaserowFormula#FieldByIdReference.
    def visitFieldByIdReference(self, ctx:BaserowFormula.FieldByIdReferenceContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by BaserowFormula#LookupFieldReference.
    def visitLookupFieldReference(self, ctx:BaserowFormula.LookupFieldReferenceContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by BaserowFormula#IntegerLiteral.
    def visitIntegerLiteral(self, ctx:BaserowFormula.IntegerLiteralContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by BaserowFormula#BinaryOp.
    def visitBinaryOp(self, ctx:BaserowFormula.BinaryOpContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by BaserowFormula#ws_or_comment.
    def visitWs_or_comment(self, ctx:BaserowFormula.Ws_or_commentContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by BaserowFormula#func_name.
    def visitFunc_name(self, ctx:BaserowFormula.Func_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by BaserowFormula#field_reference.
    def visitField_reference(self, ctx:BaserowFormula.Field_referenceContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by BaserowFormula#identifier.
    def visitIdentifier(self, ctx:BaserowFormula.IdentifierContext):
        return self.visitChildren(ctx)



del BaserowFormula