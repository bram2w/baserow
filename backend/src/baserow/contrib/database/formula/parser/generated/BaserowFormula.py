# Generated from BaserowFormula.g4 by ANTLR 4.8
# encoding: utf-8
from antlr4 import *
from io import StringIO
import sys
if sys.version_info[1] > 5:
	from typing import TextIO
else:
	from typing.io import TextIO


def serializedATN():
    with StringIO() as buf:
        buf.write("\3\u608b\ua72a\u8133\ub9ed\u417c\u3be7\u7786\u5964\3T")
        buf.write("J\4\2\t\2\4\3\t\3\4\4\t\4\4\5\t\5\4\6\t\6\3\2\3\2\3\2")
        buf.write("\3\3\3\3\3\3\3\3\3\3\3\3\3\3\3\3\3\3\3\3\3\3\3\3\3\3\3")
        buf.write("\3\3\3\3\3\3\3\3\3\3\3\3\3\3\3\3\3\3\3\3\3\7\3(\n\3\f")
        buf.write("\3\16\3+\13\3\5\3-\n\3\3\3\3\3\5\3\61\n\3\3\3\3\3\3\3")
        buf.write("\3\3\3\3\3\3\3\3\3\3\3\3\3\3\3\3\3\3\7\3?\n\3\f\3\16\3")
        buf.write("B\13\3\3\4\3\4\3\5\3\5\3\6\3\6\3\6\2\3\4\7\2\4\6\b\n\2")
        buf.write("\t\3\2\6\7\4\2\17\17JJ\4\2>>DD\4\2*+\65\66\4\2&&((\3\2")
        buf.write("\32\33\3\2\34\35\2R\2\f\3\2\2\2\4\60\3\2\2\2\6C\3\2\2")
        buf.write("\2\bE\3\2\2\2\nG\3\2\2\2\f\r\5\4\3\2\r\16\7\2\2\3\16\3")
        buf.write("\3\2\2\2\17\20\b\3\1\2\20\61\7\32\2\2\21\61\7\33\2\2\22")
        buf.write("\61\7\27\2\2\23\61\7\26\2\2\24\61\t\2\2\2\25\26\7\20\2")
        buf.write("\2\26\27\5\4\3\2\27\30\7\21\2\2\30\61\3\2\2\2\31\32\7")
        buf.write("\b\2\2\32\33\7\20\2\2\33\34\5\b\5\2\34\35\7\21\2\2\35")
        buf.write("\61\3\2\2\2\36\37\7\t\2\2\37 \7\20\2\2 !\7\27\2\2!\61")
        buf.write("\7\21\2\2\"#\5\6\4\2#,\7\20\2\2$)\5\4\3\2%&\7\n\2\2&(")
        buf.write("\5\4\3\2\'%\3\2\2\2(+\3\2\2\2)\'\3\2\2\2)*\3\2\2\2*-\3")
        buf.write("\2\2\2+)\3\2\2\2,$\3\2\2\2,-\3\2\2\2-.\3\2\2\2./\7\21")
        buf.write("\2\2/\61\3\2\2\2\60\17\3\2\2\2\60\21\3\2\2\2\60\22\3\2")
        buf.write("\2\2\60\23\3\2\2\2\60\24\3\2\2\2\60\25\3\2\2\2\60\31\3")
        buf.write("\2\2\2\60\36\3\2\2\2\60\"\3\2\2\2\61@\3\2\2\2\62\63\f")
        buf.write("\t\2\2\63\64\t\3\2\2\64?\5\4\3\n\65\66\f\b\2\2\66\67\t")
        buf.write("\4\2\2\67?\5\4\3\t89\f\7\2\29:\t\5\2\2:?\5\4\3\b;<\f\6")
        buf.write("\2\2<=\t\6\2\2=?\5\4\3\7>\62\3\2\2\2>\65\3\2\2\2>8\3\2")
        buf.write("\2\2>;\3\2\2\2?B\3\2\2\2@>\3\2\2\2@A\3\2\2\2A\5\3\2\2")
        buf.write("\2B@\3\2\2\2CD\5\n\6\2D\7\3\2\2\2EF\t\7\2\2F\t\3\2\2\2")
        buf.write("GH\t\b\2\2H\13\3\2\2\2\7),\60>@")
        return buf.getvalue()


class BaserowFormula ( Parser ):

    grammarFileName = "BaserowFormula.g4"

    atn = ATNDeserializer().deserialize(serializedATN())

    decisionsToDFA = [ DFA(ds, i) for i, ds in enumerate(atn.decisionToState) ]

    sharedContextCache = PredictionContextCache()

    literalNames = [ "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                     "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                     "','", "':'", "'::'", "'$'", "'$$'", "'*'", "'('", 
                     "')'", "'['", "']'", "<INVALID>", "<INVALID>", "<INVALID>", 
                     "<INVALID>", "<INVALID>", "'.'", "<INVALID>", "<INVALID>", 
                     "<INVALID>", "<INVALID>", "'&'", "'&&'", "'&<'", "'@@'", 
                     "'@>'", "'@'", "'!'", "'!!'", "'!='", "'^'", "'='", 
                     "'=>'", "'>'", "'>='", "'>>'", "'#'", "'#='", "'#>'", 
                     "'#>>'", "'##'", "'->'", "'->>'", "'-|-'", "'<'", "'<='", 
                     "'<@'", "'<^'", "'<>'", "'<->'", "'<<'", "'<<='", "'<?>'", 
                     "'-'", "'%'", "'|'", "'||'", "'||/'", "'|/'", "'+'", 
                     "'?'", "'?&'", "'?#'", "'?-'", "'?|'", "'/'", "'~'", 
                     "'~='", "'~>=~'", "'~>~'", "'~<=~'", "'~<~'", "'~*'", 
                     "'~~'", "';'" ]

    symbolicNames = [ "<INVALID>", "WHITESPACE", "BLOCK_COMMENT", "LINE_COMMENT", 
                      "TRUE", "FALSE", "FIELD", "FIELDBYID", "COMMA", "COLON", 
                      "COLON_COLON", "DOLLAR", "DOLLAR_DOLLAR", "STAR", 
                      "OPEN_PAREN", "CLOSE_PAREN", "OPEN_BRACKET", "CLOSE_BRACKET", 
                      "BIT_STRING", "REGEX_STRING", "NUMERIC_LITERAL", "INTEGER_LITERAL", 
                      "HEX_INTEGER_LITERAL", "DOT", "SINGLEQ_STRING_LITERAL", 
                      "DOUBLEQ_STRING_LITERAL", "IDENTIFIER", "IDENTIFIER_UNICODE", 
                      "AMP", "AMP_AMP", "AMP_LT", "AT_AT", "AT_GT", "AT_SIGN", 
                      "BANG", "BANG_BANG", "BANG_EQUAL", "CARET", "EQUAL", 
                      "EQUAL_GT", "GT", "GTE", "GT_GT", "HASH", "HASH_EQ", 
                      "HASH_GT", "HASH_GT_GT", "HASH_HASH", "HYPHEN_GT", 
                      "HYPHEN_GT_GT", "HYPHEN_PIPE_HYPHEN", "LT", "LTE", 
                      "LT_AT", "LT_CARET", "LT_GT", "LT_HYPHEN_GT", "LT_LT", 
                      "LT_LT_EQ", "LT_QMARK_GT", "MINUS", "PERCENT", "PIPE", 
                      "PIPE_PIPE", "PIPE_PIPE_SLASH", "PIPE_SLASH", "PLUS", 
                      "QMARK", "QMARK_AMP", "QMARK_HASH", "QMARK_HYPHEN", 
                      "QMARK_PIPE", "SLASH", "TIL", "TIL_EQ", "TIL_GTE_TIL", 
                      "TIL_GT_TIL", "TIL_LTE_TIL", "TIL_LT_TIL", "TIL_STAR", 
                      "TIL_TIL", "SEMI", "ErrorCharacter" ]

    RULE_root = 0
    RULE_expr = 1
    RULE_func_name = 2
    RULE_field_reference = 3
    RULE_identifier = 4

    ruleNames =  [ "root", "expr", "func_name", "field_reference", "identifier" ]

    EOF = Token.EOF
    WHITESPACE=1
    BLOCK_COMMENT=2
    LINE_COMMENT=3
    TRUE=4
    FALSE=5
    FIELD=6
    FIELDBYID=7
    COMMA=8
    COLON=9
    COLON_COLON=10
    DOLLAR=11
    DOLLAR_DOLLAR=12
    STAR=13
    OPEN_PAREN=14
    CLOSE_PAREN=15
    OPEN_BRACKET=16
    CLOSE_BRACKET=17
    BIT_STRING=18
    REGEX_STRING=19
    NUMERIC_LITERAL=20
    INTEGER_LITERAL=21
    HEX_INTEGER_LITERAL=22
    DOT=23
    SINGLEQ_STRING_LITERAL=24
    DOUBLEQ_STRING_LITERAL=25
    IDENTIFIER=26
    IDENTIFIER_UNICODE=27
    AMP=28
    AMP_AMP=29
    AMP_LT=30
    AT_AT=31
    AT_GT=32
    AT_SIGN=33
    BANG=34
    BANG_BANG=35
    BANG_EQUAL=36
    CARET=37
    EQUAL=38
    EQUAL_GT=39
    GT=40
    GTE=41
    GT_GT=42
    HASH=43
    HASH_EQ=44
    HASH_GT=45
    HASH_GT_GT=46
    HASH_HASH=47
    HYPHEN_GT=48
    HYPHEN_GT_GT=49
    HYPHEN_PIPE_HYPHEN=50
    LT=51
    LTE=52
    LT_AT=53
    LT_CARET=54
    LT_GT=55
    LT_HYPHEN_GT=56
    LT_LT=57
    LT_LT_EQ=58
    LT_QMARK_GT=59
    MINUS=60
    PERCENT=61
    PIPE=62
    PIPE_PIPE=63
    PIPE_PIPE_SLASH=64
    PIPE_SLASH=65
    PLUS=66
    QMARK=67
    QMARK_AMP=68
    QMARK_HASH=69
    QMARK_HYPHEN=70
    QMARK_PIPE=71
    SLASH=72
    TIL=73
    TIL_EQ=74
    TIL_GTE_TIL=75
    TIL_GT_TIL=76
    TIL_LTE_TIL=77
    TIL_LT_TIL=78
    TIL_STAR=79
    TIL_TIL=80
    SEMI=81
    ErrorCharacter=82

    def __init__(self, input:TokenStream, output:TextIO = sys.stdout):
        super().__init__(input, output)
        self.checkVersion("4.8")
        self._interp = ParserATNSimulator(self, self.atn, self.decisionsToDFA, self.sharedContextCache)
        self._predicates = None




    class RootContext(ParserRuleContext):

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def expr(self):
            return self.getTypedRuleContext(BaserowFormula.ExprContext,0)


        def EOF(self):
            return self.getToken(BaserowFormula.EOF, 0)

        def getRuleIndex(self):
            return BaserowFormula.RULE_root

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterRoot" ):
                listener.enterRoot(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitRoot" ):
                listener.exitRoot(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitRoot" ):
                return visitor.visitRoot(self)
            else:
                return visitor.visitChildren(self)




    def root(self):

        localctx = BaserowFormula.RootContext(self, self._ctx, self.state)
        self.enterRule(localctx, 0, self.RULE_root)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 10
            self.expr(0)
            self.state = 11
            self.match(BaserowFormula.EOF)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ExprContext(ParserRuleContext):

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser


        def getRuleIndex(self):
            return BaserowFormula.RULE_expr

     
        def copyFrom(self, ctx:ParserRuleContext):
            super().copyFrom(ctx)


    class FieldReferenceContext(ExprContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a BaserowFormula.ExprContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def FIELD(self):
            return self.getToken(BaserowFormula.FIELD, 0)
        def OPEN_PAREN(self):
            return self.getToken(BaserowFormula.OPEN_PAREN, 0)
        def field_reference(self):
            return self.getTypedRuleContext(BaserowFormula.Field_referenceContext,0)

        def CLOSE_PAREN(self):
            return self.getToken(BaserowFormula.CLOSE_PAREN, 0)

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterFieldReference" ):
                listener.enterFieldReference(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitFieldReference" ):
                listener.exitFieldReference(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitFieldReference" ):
                return visitor.visitFieldReference(self)
            else:
                return visitor.visitChildren(self)


    class StringLiteralContext(ExprContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a BaserowFormula.ExprContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def SINGLEQ_STRING_LITERAL(self):
            return self.getToken(BaserowFormula.SINGLEQ_STRING_LITERAL, 0)
        def DOUBLEQ_STRING_LITERAL(self):
            return self.getToken(BaserowFormula.DOUBLEQ_STRING_LITERAL, 0)

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterStringLiteral" ):
                listener.enterStringLiteral(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitStringLiteral" ):
                listener.exitStringLiteral(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitStringLiteral" ):
                return visitor.visitStringLiteral(self)
            else:
                return visitor.visitChildren(self)


    class BracketsContext(ExprContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a BaserowFormula.ExprContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def OPEN_PAREN(self):
            return self.getToken(BaserowFormula.OPEN_PAREN, 0)
        def expr(self):
            return self.getTypedRuleContext(BaserowFormula.ExprContext,0)

        def CLOSE_PAREN(self):
            return self.getToken(BaserowFormula.CLOSE_PAREN, 0)

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterBrackets" ):
                listener.enterBrackets(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitBrackets" ):
                listener.exitBrackets(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitBrackets" ):
                return visitor.visitBrackets(self)
            else:
                return visitor.visitChildren(self)


    class BooleanLiteralContext(ExprContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a BaserowFormula.ExprContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def TRUE(self):
            return self.getToken(BaserowFormula.TRUE, 0)
        def FALSE(self):
            return self.getToken(BaserowFormula.FALSE, 0)

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterBooleanLiteral" ):
                listener.enterBooleanLiteral(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitBooleanLiteral" ):
                listener.exitBooleanLiteral(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitBooleanLiteral" ):
                return visitor.visitBooleanLiteral(self)
            else:
                return visitor.visitChildren(self)


    class DecimalLiteralContext(ExprContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a BaserowFormula.ExprContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def NUMERIC_LITERAL(self):
            return self.getToken(BaserowFormula.NUMERIC_LITERAL, 0)

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterDecimalLiteral" ):
                listener.enterDecimalLiteral(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitDecimalLiteral" ):
                listener.exitDecimalLiteral(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitDecimalLiteral" ):
                return visitor.visitDecimalLiteral(self)
            else:
                return visitor.visitChildren(self)


    class FunctionCallContext(ExprContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a BaserowFormula.ExprContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def func_name(self):
            return self.getTypedRuleContext(BaserowFormula.Func_nameContext,0)

        def OPEN_PAREN(self):
            return self.getToken(BaserowFormula.OPEN_PAREN, 0)
        def CLOSE_PAREN(self):
            return self.getToken(BaserowFormula.CLOSE_PAREN, 0)
        def expr(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(BaserowFormula.ExprContext)
            else:
                return self.getTypedRuleContext(BaserowFormula.ExprContext,i)

        def COMMA(self, i:int=None):
            if i is None:
                return self.getTokens(BaserowFormula.COMMA)
            else:
                return self.getToken(BaserowFormula.COMMA, i)

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterFunctionCall" ):
                listener.enterFunctionCall(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitFunctionCall" ):
                listener.exitFunctionCall(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitFunctionCall" ):
                return visitor.visitFunctionCall(self)
            else:
                return visitor.visitChildren(self)


    class FieldByIdReferenceContext(ExprContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a BaserowFormula.ExprContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def FIELDBYID(self):
            return self.getToken(BaserowFormula.FIELDBYID, 0)
        def OPEN_PAREN(self):
            return self.getToken(BaserowFormula.OPEN_PAREN, 0)
        def INTEGER_LITERAL(self):
            return self.getToken(BaserowFormula.INTEGER_LITERAL, 0)
        def CLOSE_PAREN(self):
            return self.getToken(BaserowFormula.CLOSE_PAREN, 0)

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterFieldByIdReference" ):
                listener.enterFieldByIdReference(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitFieldByIdReference" ):
                listener.exitFieldByIdReference(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitFieldByIdReference" ):
                return visitor.visitFieldByIdReference(self)
            else:
                return visitor.visitChildren(self)


    class IntegerLiteralContext(ExprContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a BaserowFormula.ExprContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def INTEGER_LITERAL(self):
            return self.getToken(BaserowFormula.INTEGER_LITERAL, 0)

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterIntegerLiteral" ):
                listener.enterIntegerLiteral(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitIntegerLiteral" ):
                listener.exitIntegerLiteral(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitIntegerLiteral" ):
                return visitor.visitIntegerLiteral(self)
            else:
                return visitor.visitChildren(self)


    class BinaryOpContext(ExprContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a BaserowFormula.ExprContext
            super().__init__(parser)
            self.op = None # Token
            self.copyFrom(ctx)

        def expr(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(BaserowFormula.ExprContext)
            else:
                return self.getTypedRuleContext(BaserowFormula.ExprContext,i)

        def SLASH(self):
            return self.getToken(BaserowFormula.SLASH, 0)
        def STAR(self):
            return self.getToken(BaserowFormula.STAR, 0)
        def PLUS(self):
            return self.getToken(BaserowFormula.PLUS, 0)
        def MINUS(self):
            return self.getToken(BaserowFormula.MINUS, 0)
        def GT(self):
            return self.getToken(BaserowFormula.GT, 0)
        def LT(self):
            return self.getToken(BaserowFormula.LT, 0)
        def GTE(self):
            return self.getToken(BaserowFormula.GTE, 0)
        def LTE(self):
            return self.getToken(BaserowFormula.LTE, 0)
        def EQUAL(self):
            return self.getToken(BaserowFormula.EQUAL, 0)
        def BANG_EQUAL(self):
            return self.getToken(BaserowFormula.BANG_EQUAL, 0)

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterBinaryOp" ):
                listener.enterBinaryOp(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitBinaryOp" ):
                listener.exitBinaryOp(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitBinaryOp" ):
                return visitor.visitBinaryOp(self)
            else:
                return visitor.visitChildren(self)



    def expr(self, _p:int=0):
        _parentctx = self._ctx
        _parentState = self.state
        localctx = BaserowFormula.ExprContext(self, self._ctx, _parentState)
        _prevctx = localctx
        _startState = 2
        self.enterRecursionRule(localctx, 2, self.RULE_expr, _p)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 46
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [BaserowFormula.SINGLEQ_STRING_LITERAL]:
                localctx = BaserowFormula.StringLiteralContext(self, localctx)
                self._ctx = localctx
                _prevctx = localctx

                self.state = 14
                self.match(BaserowFormula.SINGLEQ_STRING_LITERAL)
                pass
            elif token in [BaserowFormula.DOUBLEQ_STRING_LITERAL]:
                localctx = BaserowFormula.StringLiteralContext(self, localctx)
                self._ctx = localctx
                _prevctx = localctx
                self.state = 15
                self.match(BaserowFormula.DOUBLEQ_STRING_LITERAL)
                pass
            elif token in [BaserowFormula.INTEGER_LITERAL]:
                localctx = BaserowFormula.IntegerLiteralContext(self, localctx)
                self._ctx = localctx
                _prevctx = localctx
                self.state = 16
                self.match(BaserowFormula.INTEGER_LITERAL)
                pass
            elif token in [BaserowFormula.NUMERIC_LITERAL]:
                localctx = BaserowFormula.DecimalLiteralContext(self, localctx)
                self._ctx = localctx
                _prevctx = localctx
                self.state = 17
                self.match(BaserowFormula.NUMERIC_LITERAL)
                pass
            elif token in [BaserowFormula.TRUE, BaserowFormula.FALSE]:
                localctx = BaserowFormula.BooleanLiteralContext(self, localctx)
                self._ctx = localctx
                _prevctx = localctx
                self.state = 18
                _la = self._input.LA(1)
                if not(_la==BaserowFormula.TRUE or _la==BaserowFormula.FALSE):
                    self._errHandler.recoverInline(self)
                else:
                    self._errHandler.reportMatch(self)
                    self.consume()
                pass
            elif token in [BaserowFormula.OPEN_PAREN]:
                localctx = BaserowFormula.BracketsContext(self, localctx)
                self._ctx = localctx
                _prevctx = localctx
                self.state = 19
                self.match(BaserowFormula.OPEN_PAREN)
                self.state = 20
                self.expr(0)
                self.state = 21
                self.match(BaserowFormula.CLOSE_PAREN)
                pass
            elif token in [BaserowFormula.FIELD]:
                localctx = BaserowFormula.FieldReferenceContext(self, localctx)
                self._ctx = localctx
                _prevctx = localctx
                self.state = 23
                self.match(BaserowFormula.FIELD)
                self.state = 24
                self.match(BaserowFormula.OPEN_PAREN)
                self.state = 25
                self.field_reference()
                self.state = 26
                self.match(BaserowFormula.CLOSE_PAREN)
                pass
            elif token in [BaserowFormula.FIELDBYID]:
                localctx = BaserowFormula.FieldByIdReferenceContext(self, localctx)
                self._ctx = localctx
                _prevctx = localctx
                self.state = 28
                self.match(BaserowFormula.FIELDBYID)
                self.state = 29
                self.match(BaserowFormula.OPEN_PAREN)
                self.state = 30
                self.match(BaserowFormula.INTEGER_LITERAL)
                self.state = 31
                self.match(BaserowFormula.CLOSE_PAREN)
                pass
            elif token in [BaserowFormula.IDENTIFIER, BaserowFormula.IDENTIFIER_UNICODE]:
                localctx = BaserowFormula.FunctionCallContext(self, localctx)
                self._ctx = localctx
                _prevctx = localctx
                self.state = 32
                self.func_name()
                self.state = 33
                self.match(BaserowFormula.OPEN_PAREN)
                self.state = 42
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if (((_la) & ~0x3f) == 0 and ((1 << _la) & ((1 << BaserowFormula.TRUE) | (1 << BaserowFormula.FALSE) | (1 << BaserowFormula.FIELD) | (1 << BaserowFormula.FIELDBYID) | (1 << BaserowFormula.OPEN_PAREN) | (1 << BaserowFormula.NUMERIC_LITERAL) | (1 << BaserowFormula.INTEGER_LITERAL) | (1 << BaserowFormula.SINGLEQ_STRING_LITERAL) | (1 << BaserowFormula.DOUBLEQ_STRING_LITERAL) | (1 << BaserowFormula.IDENTIFIER) | (1 << BaserowFormula.IDENTIFIER_UNICODE))) != 0):
                    self.state = 34
                    self.expr(0)
                    self.state = 39
                    self._errHandler.sync(self)
                    _la = self._input.LA(1)
                    while _la==BaserowFormula.COMMA:
                        self.state = 35
                        self.match(BaserowFormula.COMMA)
                        self.state = 36
                        self.expr(0)
                        self.state = 41
                        self._errHandler.sync(self)
                        _la = self._input.LA(1)



                self.state = 44
                self.match(BaserowFormula.CLOSE_PAREN)
                pass
            else:
                raise NoViableAltException(self)

            self._ctx.stop = self._input.LT(-1)
            self.state = 62
            self._errHandler.sync(self)
            _alt = self._interp.adaptivePredict(self._input,4,self._ctx)
            while _alt!=2 and _alt!=ATN.INVALID_ALT_NUMBER:
                if _alt==1:
                    if self._parseListeners is not None:
                        self.triggerExitRuleEvent()
                    _prevctx = localctx
                    self.state = 60
                    self._errHandler.sync(self)
                    la_ = self._interp.adaptivePredict(self._input,3,self._ctx)
                    if la_ == 1:
                        localctx = BaserowFormula.BinaryOpContext(self, BaserowFormula.ExprContext(self, _parentctx, _parentState))
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_expr)
                        self.state = 48
                        if not self.precpred(self._ctx, 7):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 7)")
                        self.state = 49
                        localctx.op = self._input.LT(1)
                        _la = self._input.LA(1)
                        if not(_la==BaserowFormula.STAR or _la==BaserowFormula.SLASH):
                            localctx.op = self._errHandler.recoverInline(self)
                        else:
                            self._errHandler.reportMatch(self)
                            self.consume()
                        self.state = 50
                        self.expr(8)
                        pass

                    elif la_ == 2:
                        localctx = BaserowFormula.BinaryOpContext(self, BaserowFormula.ExprContext(self, _parentctx, _parentState))
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_expr)
                        self.state = 51
                        if not self.precpred(self._ctx, 6):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 6)")
                        self.state = 52
                        localctx.op = self._input.LT(1)
                        _la = self._input.LA(1)
                        if not(_la==BaserowFormula.MINUS or _la==BaserowFormula.PLUS):
                            localctx.op = self._errHandler.recoverInline(self)
                        else:
                            self._errHandler.reportMatch(self)
                            self.consume()
                        self.state = 53
                        self.expr(7)
                        pass

                    elif la_ == 3:
                        localctx = BaserowFormula.BinaryOpContext(self, BaserowFormula.ExprContext(self, _parentctx, _parentState))
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_expr)
                        self.state = 54
                        if not self.precpred(self._ctx, 5):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 5)")
                        self.state = 55
                        localctx.op = self._input.LT(1)
                        _la = self._input.LA(1)
                        if not((((_la) & ~0x3f) == 0 and ((1 << _la) & ((1 << BaserowFormula.GT) | (1 << BaserowFormula.GTE) | (1 << BaserowFormula.LT) | (1 << BaserowFormula.LTE))) != 0)):
                            localctx.op = self._errHandler.recoverInline(self)
                        else:
                            self._errHandler.reportMatch(self)
                            self.consume()
                        self.state = 56
                        self.expr(6)
                        pass

                    elif la_ == 4:
                        localctx = BaserowFormula.BinaryOpContext(self, BaserowFormula.ExprContext(self, _parentctx, _parentState))
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_expr)
                        self.state = 57
                        if not self.precpred(self._ctx, 4):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 4)")
                        self.state = 58
                        localctx.op = self._input.LT(1)
                        _la = self._input.LA(1)
                        if not(_la==BaserowFormula.BANG_EQUAL or _la==BaserowFormula.EQUAL):
                            localctx.op = self._errHandler.recoverInline(self)
                        else:
                            self._errHandler.reportMatch(self)
                            self.consume()
                        self.state = 59
                        self.expr(5)
                        pass

             
                self.state = 64
                self._errHandler.sync(self)
                _alt = self._interp.adaptivePredict(self._input,4,self._ctx)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.unrollRecursionContexts(_parentctx)
        return localctx


    class Func_nameContext(ParserRuleContext):

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def identifier(self):
            return self.getTypedRuleContext(BaserowFormula.IdentifierContext,0)


        def getRuleIndex(self):
            return BaserowFormula.RULE_func_name

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterFunc_name" ):
                listener.enterFunc_name(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitFunc_name" ):
                listener.exitFunc_name(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitFunc_name" ):
                return visitor.visitFunc_name(self)
            else:
                return visitor.visitChildren(self)




    def func_name(self):

        localctx = BaserowFormula.Func_nameContext(self, self._ctx, self.state)
        self.enterRule(localctx, 4, self.RULE_func_name)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 65
            self.identifier()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class Field_referenceContext(ParserRuleContext):

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def SINGLEQ_STRING_LITERAL(self):
            return self.getToken(BaserowFormula.SINGLEQ_STRING_LITERAL, 0)

        def DOUBLEQ_STRING_LITERAL(self):
            return self.getToken(BaserowFormula.DOUBLEQ_STRING_LITERAL, 0)

        def getRuleIndex(self):
            return BaserowFormula.RULE_field_reference

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterField_reference" ):
                listener.enterField_reference(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitField_reference" ):
                listener.exitField_reference(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitField_reference" ):
                return visitor.visitField_reference(self)
            else:
                return visitor.visitChildren(self)




    def field_reference(self):

        localctx = BaserowFormula.Field_referenceContext(self, self._ctx, self.state)
        self.enterRule(localctx, 6, self.RULE_field_reference)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 67
            _la = self._input.LA(1)
            if not(_la==BaserowFormula.SINGLEQ_STRING_LITERAL or _la==BaserowFormula.DOUBLEQ_STRING_LITERAL):
                self._errHandler.recoverInline(self)
            else:
                self._errHandler.reportMatch(self)
                self.consume()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class IdentifierContext(ParserRuleContext):

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def IDENTIFIER(self):
            return self.getToken(BaserowFormula.IDENTIFIER, 0)

        def IDENTIFIER_UNICODE(self):
            return self.getToken(BaserowFormula.IDENTIFIER_UNICODE, 0)

        def getRuleIndex(self):
            return BaserowFormula.RULE_identifier

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterIdentifier" ):
                listener.enterIdentifier(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitIdentifier" ):
                listener.exitIdentifier(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitIdentifier" ):
                return visitor.visitIdentifier(self)
            else:
                return visitor.visitChildren(self)




    def identifier(self):

        localctx = BaserowFormula.IdentifierContext(self, self._ctx, self.state)
        self.enterRule(localctx, 8, self.RULE_identifier)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 69
            _la = self._input.LA(1)
            if not(_la==BaserowFormula.IDENTIFIER or _la==BaserowFormula.IDENTIFIER_UNICODE):
                self._errHandler.recoverInline(self)
            else:
                self._errHandler.reportMatch(self)
                self.consume()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx



    def sempred(self, localctx:RuleContext, ruleIndex:int, predIndex:int):
        if self._predicates == None:
            self._predicates = dict()
        self._predicates[1] = self.expr_sempred
        pred = self._predicates.get(ruleIndex, None)
        if pred is None:
            raise Exception("No predicate with index:" + str(ruleIndex))
        else:
            return pred(localctx, predIndex)

    def expr_sempred(self, localctx:ExprContext, predIndex:int):
            if predIndex == 0:
                return self.precpred(self._ctx, 7)
         

            if predIndex == 1:
                return self.precpred(self._ctx, 6)
         

            if predIndex == 2:
                return self.precpred(self._ctx, 5)
         

            if predIndex == 3:
                return self.precpred(self._ctx, 4)
         




