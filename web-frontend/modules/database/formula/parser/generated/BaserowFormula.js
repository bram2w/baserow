// Generated from BaserowFormula.g4 by ANTLR 4.8
// jshint ignore: start
var antlr4 = require('antlr4/index');
var BaserowFormulaListener = require('./BaserowFormulaListener').BaserowFormulaListener;
var BaserowFormulaVisitor = require('./BaserowFormulaVisitor').BaserowFormulaVisitor;

var grammarFileName = "BaserowFormula.g4";


var serializedATN = ["\u0003\u608b\ua72a\u8133\ub9ed\u417c\u3be7\u7786\u5964",
    "\u0003U]\u0004\u0002\t\u0002\u0004\u0003\t\u0003\u0004\u0004\t\u0004",
    "\u0004\u0005\t\u0005\u0004\u0006\t\u0006\u0004\u0007\t\u0007\u0003\u0002",
    "\u0003\u0002\u0003\u0002\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003",
    "\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003",
    "\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003",
    "\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003",
    "\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0005\u0003",
    "-\n\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003",
    "\u0003\u0003\u0003\u0003\u0003\u0003\u0007\u00037\n\u0003\f\u0003\u000e",
    "\u0003:\u000b\u0003\u0005\u0003<\n\u0003\u0003\u0003\u0003\u0003\u0005",
    "\u0003@\n\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003",
    "\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003",
    "\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0007\u0003P\n\u0003\f\u0003",
    "\u000e\u0003S\u000b\u0003\u0003\u0004\u0003\u0004\u0003\u0005\u0003",
    "\u0005\u0003\u0006\u0003\u0006\u0003\u0007\u0003\u0007\u0003\u0007\u0002",
    "\u0003\u0004\b\u0002\u0004\u0006\b\n\f\u0002\n\u0003\u0002\u0006\u0007",
    "\u0004\u0002\u0010\u0010KK\u0004\u0002??EE\u0004\u0002+,67\u0004\u0002",
    "\'\'))\u0003\u0002\u0003\u0005\u0003\u0002\u001b\u001c\u0003\u0002\u001d",
    "\u001e\u0002h\u0002\u000e\u0003\u0002\u0002\u0002\u0004?\u0003\u0002",
    "\u0002\u0002\u0006T\u0003\u0002\u0002\u0002\bV\u0003\u0002\u0002\u0002",
    "\nX\u0003\u0002\u0002\u0002\fZ\u0003\u0002\u0002\u0002\u000e\u000f\u0005",
    "\u0004\u0003\u0002\u000f\u0010\u0007\u0002\u0002\u0003\u0010\u0003\u0003",
    "\u0002\u0002\u0002\u0011\u0012\b\u0003\u0001\u0002\u0012@\u0007\u001b",
    "\u0002\u0002\u0013@\u0007\u001c\u0002\u0002\u0014@\u0007\u0018\u0002",
    "\u0002\u0015@\u0007\u0017\u0002\u0002\u0016@\t\u0002\u0002\u0002\u0017",
    "\u0018\u0005\u0006\u0004\u0002\u0018\u0019\u0005\u0004\u0003\r\u0019",
    "@\u0003\u0002\u0002\u0002\u001a\u001b\u0007\u0011\u0002\u0002\u001b",
    "\u001c\u0005\u0004\u0003\u0002\u001c\u001d\u0007\u0012\u0002\u0002\u001d",
    "@\u0003\u0002\u0002\u0002\u001e\u001f\u0007\b\u0002\u0002\u001f \u0007",
    "\u0011\u0002\u0002 !\u0005\n\u0006\u0002!\"\u0007\u0012\u0002\u0002",
    "\"@\u0003\u0002\u0002\u0002#$\u0007\t\u0002\u0002$%\u0007\u0011\u0002",
    "\u0002%&\u0007\u0018\u0002\u0002&@\u0007\u0012\u0002\u0002\'(\u0007",
    "\n\u0002\u0002()\u0007\u0011\u0002\u0002)*\u0005\n\u0006\u0002*,\u0007",
    "\u000b\u0002\u0002+-\u0007\u0005\u0002\u0002,+\u0003\u0002\u0002\u0002",
    ",-\u0003\u0002\u0002\u0002-.\u0003\u0002\u0002\u0002./\u0005\n\u0006",
    "\u0002/0\u0007\u0012\u0002\u00020@\u0003\u0002\u0002\u000212\u0005\b",
    "\u0005\u00022;\u0007\u0011\u0002\u000238\u0005\u0004\u0003\u000245\u0007",
    "\u000b\u0002\u000257\u0005\u0004\u0003\u000264\u0003\u0002\u0002\u0002",
    "7:\u0003\u0002\u0002\u000286\u0003\u0002\u0002\u000289\u0003\u0002\u0002",
    "\u00029<\u0003\u0002\u0002\u0002:8\u0003\u0002\u0002\u0002;3\u0003\u0002",
    "\u0002\u0002;<\u0003\u0002\u0002\u0002<=\u0003\u0002\u0002\u0002=>\u0007",
    "\u0012\u0002\u0002>@\u0003\u0002\u0002\u0002?\u0011\u0003\u0002\u0002",
    "\u0002?\u0013\u0003\u0002\u0002\u0002?\u0014\u0003\u0002\u0002\u0002",
    "?\u0015\u0003\u0002\u0002\u0002?\u0016\u0003\u0002\u0002\u0002?\u0017",
    "\u0003\u0002\u0002\u0002?\u001a\u0003\u0002\u0002\u0002?\u001e\u0003",
    "\u0002\u0002\u0002?#\u0003\u0002\u0002\u0002?\'\u0003\u0002\u0002\u0002",
    "?1\u0003\u0002\u0002\u0002@Q\u0003\u0002\u0002\u0002AB\f\n\u0002\u0002",
    "BC\t\u0003\u0002\u0002CP\u0005\u0004\u0003\u000bDE\f\t\u0002\u0002E",
    "F\t\u0004\u0002\u0002FP\u0005\u0004\u0003\nGH\f\b\u0002\u0002HI\t\u0005",
    "\u0002\u0002IP\u0005\u0004\u0003\tJK\f\u0007\u0002\u0002KL\t\u0006\u0002",
    "\u0002LP\u0005\u0004\u0003\bMN\f\f\u0002\u0002NP\u0005\u0006\u0004\u0002",
    "OA\u0003\u0002\u0002\u0002OD\u0003\u0002\u0002\u0002OG\u0003\u0002\u0002",
    "\u0002OJ\u0003\u0002\u0002\u0002OM\u0003\u0002\u0002\u0002PS\u0003\u0002",
    "\u0002\u0002QO\u0003\u0002\u0002\u0002QR\u0003\u0002\u0002\u0002R\u0005",
    "\u0003\u0002\u0002\u0002SQ\u0003\u0002\u0002\u0002TU\t\u0007\u0002\u0002",
    "U\u0007\u0003\u0002\u0002\u0002VW\u0005\f\u0007\u0002W\t\u0003\u0002",
    "\u0002\u0002XY\t\b\u0002\u0002Y\u000b\u0003\u0002\u0002\u0002Z[\t\t",
    "\u0002\u0002[\r\u0003\u0002\u0002\u0002\b,8;?OQ"].join("");


var atn = new antlr4.atn.ATNDeserializer().deserialize(serializedATN);

var decisionsToDFA = atn.decisionToState.map( function(ds, index) { return new antlr4.dfa.DFA(ds, index); });

var sharedContextCache = new antlr4.PredictionContextCache();

var literalNames = [ null, null, null, null, null, null, null, null, null, 
                     "','", "':'", "'::'", "'$'", "'$$'", "'*'", "'('", 
                     "')'", "'['", "']'", null, null, null, null, null, 
                     "'.'", null, null, null, null, "'&'", "'&&'", "'&<'", 
                     "'@@'", "'@>'", "'@'", "'!'", "'!!'", "'!='", "'^'", 
                     "'='", "'=>'", "'>'", "'>='", "'>>'", "'#'", "'#='", 
                     "'#>'", "'#>>'", "'##'", "'->'", "'->>'", "'-|-'", 
                     "'<'", "'<='", "'<@'", "'<^'", "'<>'", "'<->'", "'<<'", 
                     "'<<='", "'<?>'", "'-'", "'%'", "'|'", "'||'", "'||/'", 
                     "'|/'", "'+'", "'?'", "'?&'", "'?#'", "'?-'", "'?|'", 
                     "'/'", "'~'", "'~='", "'~>=~'", "'~>~'", "'~<=~'", 
                     "'~<~'", "'~*'", "'~~'", "';'" ];

var symbolicNames = [ null, "BLOCK_COMMENT", "LINE_COMMENT", "WHITESPACE", 
                      "TRUE", "FALSE", "FIELD", "FIELDBYID", "LOOKUP", "COMMA", 
                      "COLON", "COLON_COLON", "DOLLAR", "DOLLAR_DOLLAR", 
                      "STAR", "OPEN_PAREN", "CLOSE_PAREN", "OPEN_BRACKET", 
                      "CLOSE_BRACKET", "BIT_STRING", "REGEX_STRING", "NUMERIC_LITERAL", 
                      "INTEGER_LITERAL", "HEX_INTEGER_LITERAL", "DOT", "SINGLEQ_STRING_LITERAL", 
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
                      "TIL_TIL", "SEMI", "ErrorCharacter" ];

var ruleNames =  [ "root", "expr", "ws_or_comment", "func_name", "field_reference", 
                   "identifier" ];

function BaserowFormula (input) {
	antlr4.Parser.call(this, input);
    this._interp = new antlr4.atn.ParserATNSimulator(this, atn, decisionsToDFA, sharedContextCache);
    this.ruleNames = ruleNames;
    this.literalNames = literalNames;
    this.symbolicNames = symbolicNames;
    return this;
}

BaserowFormula.prototype = Object.create(antlr4.Parser.prototype);
BaserowFormula.prototype.constructor = BaserowFormula;

Object.defineProperty(BaserowFormula.prototype, "atn", {
	get : function() {
		return atn;
	}
});

BaserowFormula.EOF = antlr4.Token.EOF;
BaserowFormula.BLOCK_COMMENT = 1;
BaserowFormula.LINE_COMMENT = 2;
BaserowFormula.WHITESPACE = 3;
BaserowFormula.TRUE = 4;
BaserowFormula.FALSE = 5;
BaserowFormula.FIELD = 6;
BaserowFormula.FIELDBYID = 7;
BaserowFormula.LOOKUP = 8;
BaserowFormula.COMMA = 9;
BaserowFormula.COLON = 10;
BaserowFormula.COLON_COLON = 11;
BaserowFormula.DOLLAR = 12;
BaserowFormula.DOLLAR_DOLLAR = 13;
BaserowFormula.STAR = 14;
BaserowFormula.OPEN_PAREN = 15;
BaserowFormula.CLOSE_PAREN = 16;
BaserowFormula.OPEN_BRACKET = 17;
BaserowFormula.CLOSE_BRACKET = 18;
BaserowFormula.BIT_STRING = 19;
BaserowFormula.REGEX_STRING = 20;
BaserowFormula.NUMERIC_LITERAL = 21;
BaserowFormula.INTEGER_LITERAL = 22;
BaserowFormula.HEX_INTEGER_LITERAL = 23;
BaserowFormula.DOT = 24;
BaserowFormula.SINGLEQ_STRING_LITERAL = 25;
BaserowFormula.DOUBLEQ_STRING_LITERAL = 26;
BaserowFormula.IDENTIFIER = 27;
BaserowFormula.IDENTIFIER_UNICODE = 28;
BaserowFormula.AMP = 29;
BaserowFormula.AMP_AMP = 30;
BaserowFormula.AMP_LT = 31;
BaserowFormula.AT_AT = 32;
BaserowFormula.AT_GT = 33;
BaserowFormula.AT_SIGN = 34;
BaserowFormula.BANG = 35;
BaserowFormula.BANG_BANG = 36;
BaserowFormula.BANG_EQUAL = 37;
BaserowFormula.CARET = 38;
BaserowFormula.EQUAL = 39;
BaserowFormula.EQUAL_GT = 40;
BaserowFormula.GT = 41;
BaserowFormula.GTE = 42;
BaserowFormula.GT_GT = 43;
BaserowFormula.HASH = 44;
BaserowFormula.HASH_EQ = 45;
BaserowFormula.HASH_GT = 46;
BaserowFormula.HASH_GT_GT = 47;
BaserowFormula.HASH_HASH = 48;
BaserowFormula.HYPHEN_GT = 49;
BaserowFormula.HYPHEN_GT_GT = 50;
BaserowFormula.HYPHEN_PIPE_HYPHEN = 51;
BaserowFormula.LT = 52;
BaserowFormula.LTE = 53;
BaserowFormula.LT_AT = 54;
BaserowFormula.LT_CARET = 55;
BaserowFormula.LT_GT = 56;
BaserowFormula.LT_HYPHEN_GT = 57;
BaserowFormula.LT_LT = 58;
BaserowFormula.LT_LT_EQ = 59;
BaserowFormula.LT_QMARK_GT = 60;
BaserowFormula.MINUS = 61;
BaserowFormula.PERCENT = 62;
BaserowFormula.PIPE = 63;
BaserowFormula.PIPE_PIPE = 64;
BaserowFormula.PIPE_PIPE_SLASH = 65;
BaserowFormula.PIPE_SLASH = 66;
BaserowFormula.PLUS = 67;
BaserowFormula.QMARK = 68;
BaserowFormula.QMARK_AMP = 69;
BaserowFormula.QMARK_HASH = 70;
BaserowFormula.QMARK_HYPHEN = 71;
BaserowFormula.QMARK_PIPE = 72;
BaserowFormula.SLASH = 73;
BaserowFormula.TIL = 74;
BaserowFormula.TIL_EQ = 75;
BaserowFormula.TIL_GTE_TIL = 76;
BaserowFormula.TIL_GT_TIL = 77;
BaserowFormula.TIL_LTE_TIL = 78;
BaserowFormula.TIL_LT_TIL = 79;
BaserowFormula.TIL_STAR = 80;
BaserowFormula.TIL_TIL = 81;
BaserowFormula.SEMI = 82;
BaserowFormula.ErrorCharacter = 83;

BaserowFormula.RULE_root = 0;
BaserowFormula.RULE_expr = 1;
BaserowFormula.RULE_ws_or_comment = 2;
BaserowFormula.RULE_func_name = 3;
BaserowFormula.RULE_field_reference = 4;
BaserowFormula.RULE_identifier = 5;


function RootContext(parser, parent, invokingState) {
	if(parent===undefined) {
	    parent = null;
	}
	if(invokingState===undefined || invokingState===null) {
		invokingState = -1;
	}
	antlr4.ParserRuleContext.call(this, parent, invokingState);
    this.parser = parser;
    this.ruleIndex = BaserowFormula.RULE_root;
    return this;
}

RootContext.prototype = Object.create(antlr4.ParserRuleContext.prototype);
RootContext.prototype.constructor = RootContext;

RootContext.prototype.expr = function() {
    return this.getTypedRuleContext(ExprContext,0);
};

RootContext.prototype.EOF = function() {
    return this.getToken(BaserowFormula.EOF, 0);
};

RootContext.prototype.enterRule = function(listener) {
    if(listener instanceof BaserowFormulaListener ) {
        listener.enterRoot(this);
	}
};

RootContext.prototype.exitRule = function(listener) {
    if(listener instanceof BaserowFormulaListener ) {
        listener.exitRoot(this);
	}
};

RootContext.prototype.accept = function(visitor) {
    if ( visitor instanceof BaserowFormulaVisitor ) {
        return visitor.visitRoot(this);
    } else {
        return visitor.visitChildren(this);
    }
};




BaserowFormula.RootContext = RootContext;

BaserowFormula.prototype.root = function() {

    var localctx = new RootContext(this, this._ctx, this.state);
    this.enterRule(localctx, 0, BaserowFormula.RULE_root);
    try {
        this.enterOuterAlt(localctx, 1);
        this.state = 12;
        this.expr(0);
        this.state = 13;
        this.match(BaserowFormula.EOF);
    } catch (re) {
    	if(re instanceof antlr4.error.RecognitionException) {
	        localctx.exception = re;
	        this._errHandler.reportError(this, re);
	        this._errHandler.recover(this, re);
	    } else {
	    	throw re;
	    }
    } finally {
        this.exitRule();
    }
    return localctx;
};


function ExprContext(parser, parent, invokingState) {
	if(parent===undefined) {
	    parent = null;
	}
	if(invokingState===undefined || invokingState===null) {
		invokingState = -1;
	}
	antlr4.ParserRuleContext.call(this, parent, invokingState);
    this.parser = parser;
    this.ruleIndex = BaserowFormula.RULE_expr;
    return this;
}

ExprContext.prototype = Object.create(antlr4.ParserRuleContext.prototype);
ExprContext.prototype.constructor = ExprContext;


 
ExprContext.prototype.copyFrom = function(ctx) {
    antlr4.ParserRuleContext.prototype.copyFrom.call(this, ctx);
};

function FieldReferenceContext(parser, ctx) {
	ExprContext.call(this, parser);
    ExprContext.prototype.copyFrom.call(this, ctx);
    return this;
}

FieldReferenceContext.prototype = Object.create(ExprContext.prototype);
FieldReferenceContext.prototype.constructor = FieldReferenceContext;

BaserowFormula.FieldReferenceContext = FieldReferenceContext;

FieldReferenceContext.prototype.FIELD = function() {
    return this.getToken(BaserowFormula.FIELD, 0);
};

FieldReferenceContext.prototype.OPEN_PAREN = function() {
    return this.getToken(BaserowFormula.OPEN_PAREN, 0);
};

FieldReferenceContext.prototype.field_reference = function() {
    return this.getTypedRuleContext(Field_referenceContext,0);
};

FieldReferenceContext.prototype.CLOSE_PAREN = function() {
    return this.getToken(BaserowFormula.CLOSE_PAREN, 0);
};
FieldReferenceContext.prototype.enterRule = function(listener) {
    if(listener instanceof BaserowFormulaListener ) {
        listener.enterFieldReference(this);
	}
};

FieldReferenceContext.prototype.exitRule = function(listener) {
    if(listener instanceof BaserowFormulaListener ) {
        listener.exitFieldReference(this);
	}
};

FieldReferenceContext.prototype.accept = function(visitor) {
    if ( visitor instanceof BaserowFormulaVisitor ) {
        return visitor.visitFieldReference(this);
    } else {
        return visitor.visitChildren(this);
    }
};


function StringLiteralContext(parser, ctx) {
	ExprContext.call(this, parser);
    ExprContext.prototype.copyFrom.call(this, ctx);
    return this;
}

StringLiteralContext.prototype = Object.create(ExprContext.prototype);
StringLiteralContext.prototype.constructor = StringLiteralContext;

BaserowFormula.StringLiteralContext = StringLiteralContext;

StringLiteralContext.prototype.SINGLEQ_STRING_LITERAL = function() {
    return this.getToken(BaserowFormula.SINGLEQ_STRING_LITERAL, 0);
};

StringLiteralContext.prototype.DOUBLEQ_STRING_LITERAL = function() {
    return this.getToken(BaserowFormula.DOUBLEQ_STRING_LITERAL, 0);
};
StringLiteralContext.prototype.enterRule = function(listener) {
    if(listener instanceof BaserowFormulaListener ) {
        listener.enterStringLiteral(this);
	}
};

StringLiteralContext.prototype.exitRule = function(listener) {
    if(listener instanceof BaserowFormulaListener ) {
        listener.exitStringLiteral(this);
	}
};

StringLiteralContext.prototype.accept = function(visitor) {
    if ( visitor instanceof BaserowFormulaVisitor ) {
        return visitor.visitStringLiteral(this);
    } else {
        return visitor.visitChildren(this);
    }
};


function BracketsContext(parser, ctx) {
	ExprContext.call(this, parser);
    ExprContext.prototype.copyFrom.call(this, ctx);
    return this;
}

BracketsContext.prototype = Object.create(ExprContext.prototype);
BracketsContext.prototype.constructor = BracketsContext;

BaserowFormula.BracketsContext = BracketsContext;

BracketsContext.prototype.OPEN_PAREN = function() {
    return this.getToken(BaserowFormula.OPEN_PAREN, 0);
};

BracketsContext.prototype.expr = function() {
    return this.getTypedRuleContext(ExprContext,0);
};

BracketsContext.prototype.CLOSE_PAREN = function() {
    return this.getToken(BaserowFormula.CLOSE_PAREN, 0);
};
BracketsContext.prototype.enterRule = function(listener) {
    if(listener instanceof BaserowFormulaListener ) {
        listener.enterBrackets(this);
	}
};

BracketsContext.prototype.exitRule = function(listener) {
    if(listener instanceof BaserowFormulaListener ) {
        listener.exitBrackets(this);
	}
};

BracketsContext.prototype.accept = function(visitor) {
    if ( visitor instanceof BaserowFormulaVisitor ) {
        return visitor.visitBrackets(this);
    } else {
        return visitor.visitChildren(this);
    }
};


function BooleanLiteralContext(parser, ctx) {
	ExprContext.call(this, parser);
    ExprContext.prototype.copyFrom.call(this, ctx);
    return this;
}

BooleanLiteralContext.prototype = Object.create(ExprContext.prototype);
BooleanLiteralContext.prototype.constructor = BooleanLiteralContext;

BaserowFormula.BooleanLiteralContext = BooleanLiteralContext;

BooleanLiteralContext.prototype.TRUE = function() {
    return this.getToken(BaserowFormula.TRUE, 0);
};

BooleanLiteralContext.prototype.FALSE = function() {
    return this.getToken(BaserowFormula.FALSE, 0);
};
BooleanLiteralContext.prototype.enterRule = function(listener) {
    if(listener instanceof BaserowFormulaListener ) {
        listener.enterBooleanLiteral(this);
	}
};

BooleanLiteralContext.prototype.exitRule = function(listener) {
    if(listener instanceof BaserowFormulaListener ) {
        listener.exitBooleanLiteral(this);
	}
};

BooleanLiteralContext.prototype.accept = function(visitor) {
    if ( visitor instanceof BaserowFormulaVisitor ) {
        return visitor.visitBooleanLiteral(this);
    } else {
        return visitor.visitChildren(this);
    }
};


function RightWhitespaceOrCommentsContext(parser, ctx) {
	ExprContext.call(this, parser);
    ExprContext.prototype.copyFrom.call(this, ctx);
    return this;
}

RightWhitespaceOrCommentsContext.prototype = Object.create(ExprContext.prototype);
RightWhitespaceOrCommentsContext.prototype.constructor = RightWhitespaceOrCommentsContext;

BaserowFormula.RightWhitespaceOrCommentsContext = RightWhitespaceOrCommentsContext;

RightWhitespaceOrCommentsContext.prototype.expr = function() {
    return this.getTypedRuleContext(ExprContext,0);
};

RightWhitespaceOrCommentsContext.prototype.ws_or_comment = function() {
    return this.getTypedRuleContext(Ws_or_commentContext,0);
};
RightWhitespaceOrCommentsContext.prototype.enterRule = function(listener) {
    if(listener instanceof BaserowFormulaListener ) {
        listener.enterRightWhitespaceOrComments(this);
	}
};

RightWhitespaceOrCommentsContext.prototype.exitRule = function(listener) {
    if(listener instanceof BaserowFormulaListener ) {
        listener.exitRightWhitespaceOrComments(this);
	}
};

RightWhitespaceOrCommentsContext.prototype.accept = function(visitor) {
    if ( visitor instanceof BaserowFormulaVisitor ) {
        return visitor.visitRightWhitespaceOrComments(this);
    } else {
        return visitor.visitChildren(this);
    }
};


function DecimalLiteralContext(parser, ctx) {
	ExprContext.call(this, parser);
    ExprContext.prototype.copyFrom.call(this, ctx);
    return this;
}

DecimalLiteralContext.prototype = Object.create(ExprContext.prototype);
DecimalLiteralContext.prototype.constructor = DecimalLiteralContext;

BaserowFormula.DecimalLiteralContext = DecimalLiteralContext;

DecimalLiteralContext.prototype.NUMERIC_LITERAL = function() {
    return this.getToken(BaserowFormula.NUMERIC_LITERAL, 0);
};
DecimalLiteralContext.prototype.enterRule = function(listener) {
    if(listener instanceof BaserowFormulaListener ) {
        listener.enterDecimalLiteral(this);
	}
};

DecimalLiteralContext.prototype.exitRule = function(listener) {
    if(listener instanceof BaserowFormulaListener ) {
        listener.exitDecimalLiteral(this);
	}
};

DecimalLiteralContext.prototype.accept = function(visitor) {
    if ( visitor instanceof BaserowFormulaVisitor ) {
        return visitor.visitDecimalLiteral(this);
    } else {
        return visitor.visitChildren(this);
    }
};


function LeftWhitespaceOrCommentsContext(parser, ctx) {
	ExprContext.call(this, parser);
    ExprContext.prototype.copyFrom.call(this, ctx);
    return this;
}

LeftWhitespaceOrCommentsContext.prototype = Object.create(ExprContext.prototype);
LeftWhitespaceOrCommentsContext.prototype.constructor = LeftWhitespaceOrCommentsContext;

BaserowFormula.LeftWhitespaceOrCommentsContext = LeftWhitespaceOrCommentsContext;

LeftWhitespaceOrCommentsContext.prototype.ws_or_comment = function() {
    return this.getTypedRuleContext(Ws_or_commentContext,0);
};

LeftWhitespaceOrCommentsContext.prototype.expr = function() {
    return this.getTypedRuleContext(ExprContext,0);
};
LeftWhitespaceOrCommentsContext.prototype.enterRule = function(listener) {
    if(listener instanceof BaserowFormulaListener ) {
        listener.enterLeftWhitespaceOrComments(this);
	}
};

LeftWhitespaceOrCommentsContext.prototype.exitRule = function(listener) {
    if(listener instanceof BaserowFormulaListener ) {
        listener.exitLeftWhitespaceOrComments(this);
	}
};

LeftWhitespaceOrCommentsContext.prototype.accept = function(visitor) {
    if ( visitor instanceof BaserowFormulaVisitor ) {
        return visitor.visitLeftWhitespaceOrComments(this);
    } else {
        return visitor.visitChildren(this);
    }
};


function FunctionCallContext(parser, ctx) {
	ExprContext.call(this, parser);
    ExprContext.prototype.copyFrom.call(this, ctx);
    return this;
}

FunctionCallContext.prototype = Object.create(ExprContext.prototype);
FunctionCallContext.prototype.constructor = FunctionCallContext;

BaserowFormula.FunctionCallContext = FunctionCallContext;

FunctionCallContext.prototype.func_name = function() {
    return this.getTypedRuleContext(Func_nameContext,0);
};

FunctionCallContext.prototype.OPEN_PAREN = function() {
    return this.getToken(BaserowFormula.OPEN_PAREN, 0);
};

FunctionCallContext.prototype.CLOSE_PAREN = function() {
    return this.getToken(BaserowFormula.CLOSE_PAREN, 0);
};

FunctionCallContext.prototype.expr = function(i) {
    if(i===undefined) {
        i = null;
    }
    if(i===null) {
        return this.getTypedRuleContexts(ExprContext);
    } else {
        return this.getTypedRuleContext(ExprContext,i);
    }
};

FunctionCallContext.prototype.COMMA = function(i) {
	if(i===undefined) {
		i = null;
	}
    if(i===null) {
        return this.getTokens(BaserowFormula.COMMA);
    } else {
        return this.getToken(BaserowFormula.COMMA, i);
    }
};

FunctionCallContext.prototype.enterRule = function(listener) {
    if(listener instanceof BaserowFormulaListener ) {
        listener.enterFunctionCall(this);
	}
};

FunctionCallContext.prototype.exitRule = function(listener) {
    if(listener instanceof BaserowFormulaListener ) {
        listener.exitFunctionCall(this);
	}
};

FunctionCallContext.prototype.accept = function(visitor) {
    if ( visitor instanceof BaserowFormulaVisitor ) {
        return visitor.visitFunctionCall(this);
    } else {
        return visitor.visitChildren(this);
    }
};


function FieldByIdReferenceContext(parser, ctx) {
	ExprContext.call(this, parser);
    ExprContext.prototype.copyFrom.call(this, ctx);
    return this;
}

FieldByIdReferenceContext.prototype = Object.create(ExprContext.prototype);
FieldByIdReferenceContext.prototype.constructor = FieldByIdReferenceContext;

BaserowFormula.FieldByIdReferenceContext = FieldByIdReferenceContext;

FieldByIdReferenceContext.prototype.FIELDBYID = function() {
    return this.getToken(BaserowFormula.FIELDBYID, 0);
};

FieldByIdReferenceContext.prototype.OPEN_PAREN = function() {
    return this.getToken(BaserowFormula.OPEN_PAREN, 0);
};

FieldByIdReferenceContext.prototype.INTEGER_LITERAL = function() {
    return this.getToken(BaserowFormula.INTEGER_LITERAL, 0);
};

FieldByIdReferenceContext.prototype.CLOSE_PAREN = function() {
    return this.getToken(BaserowFormula.CLOSE_PAREN, 0);
};
FieldByIdReferenceContext.prototype.enterRule = function(listener) {
    if(listener instanceof BaserowFormulaListener ) {
        listener.enterFieldByIdReference(this);
	}
};

FieldByIdReferenceContext.prototype.exitRule = function(listener) {
    if(listener instanceof BaserowFormulaListener ) {
        listener.exitFieldByIdReference(this);
	}
};

FieldByIdReferenceContext.prototype.accept = function(visitor) {
    if ( visitor instanceof BaserowFormulaVisitor ) {
        return visitor.visitFieldByIdReference(this);
    } else {
        return visitor.visitChildren(this);
    }
};


function LookupFieldReferenceContext(parser, ctx) {
	ExprContext.call(this, parser);
    ExprContext.prototype.copyFrom.call(this, ctx);
    return this;
}

LookupFieldReferenceContext.prototype = Object.create(ExprContext.prototype);
LookupFieldReferenceContext.prototype.constructor = LookupFieldReferenceContext;

BaserowFormula.LookupFieldReferenceContext = LookupFieldReferenceContext;

LookupFieldReferenceContext.prototype.LOOKUP = function() {
    return this.getToken(BaserowFormula.LOOKUP, 0);
};

LookupFieldReferenceContext.prototype.OPEN_PAREN = function() {
    return this.getToken(BaserowFormula.OPEN_PAREN, 0);
};

LookupFieldReferenceContext.prototype.field_reference = function(i) {
    if(i===undefined) {
        i = null;
    }
    if(i===null) {
        return this.getTypedRuleContexts(Field_referenceContext);
    } else {
        return this.getTypedRuleContext(Field_referenceContext,i);
    }
};

LookupFieldReferenceContext.prototype.COMMA = function() {
    return this.getToken(BaserowFormula.COMMA, 0);
};

LookupFieldReferenceContext.prototype.CLOSE_PAREN = function() {
    return this.getToken(BaserowFormula.CLOSE_PAREN, 0);
};

LookupFieldReferenceContext.prototype.WHITESPACE = function() {
    return this.getToken(BaserowFormula.WHITESPACE, 0);
};
LookupFieldReferenceContext.prototype.enterRule = function(listener) {
    if(listener instanceof BaserowFormulaListener ) {
        listener.enterLookupFieldReference(this);
	}
};

LookupFieldReferenceContext.prototype.exitRule = function(listener) {
    if(listener instanceof BaserowFormulaListener ) {
        listener.exitLookupFieldReference(this);
	}
};

LookupFieldReferenceContext.prototype.accept = function(visitor) {
    if ( visitor instanceof BaserowFormulaVisitor ) {
        return visitor.visitLookupFieldReference(this);
    } else {
        return visitor.visitChildren(this);
    }
};


function IntegerLiteralContext(parser, ctx) {
	ExprContext.call(this, parser);
    ExprContext.prototype.copyFrom.call(this, ctx);
    return this;
}

IntegerLiteralContext.prototype = Object.create(ExprContext.prototype);
IntegerLiteralContext.prototype.constructor = IntegerLiteralContext;

BaserowFormula.IntegerLiteralContext = IntegerLiteralContext;

IntegerLiteralContext.prototype.INTEGER_LITERAL = function() {
    return this.getToken(BaserowFormula.INTEGER_LITERAL, 0);
};
IntegerLiteralContext.prototype.enterRule = function(listener) {
    if(listener instanceof BaserowFormulaListener ) {
        listener.enterIntegerLiteral(this);
	}
};

IntegerLiteralContext.prototype.exitRule = function(listener) {
    if(listener instanceof BaserowFormulaListener ) {
        listener.exitIntegerLiteral(this);
	}
};

IntegerLiteralContext.prototype.accept = function(visitor) {
    if ( visitor instanceof BaserowFormulaVisitor ) {
        return visitor.visitIntegerLiteral(this);
    } else {
        return visitor.visitChildren(this);
    }
};


function BinaryOpContext(parser, ctx) {
	ExprContext.call(this, parser);
    this.op = null; // Token;
    ExprContext.prototype.copyFrom.call(this, ctx);
    return this;
}

BinaryOpContext.prototype = Object.create(ExprContext.prototype);
BinaryOpContext.prototype.constructor = BinaryOpContext;

BaserowFormula.BinaryOpContext = BinaryOpContext;

BinaryOpContext.prototype.expr = function(i) {
    if(i===undefined) {
        i = null;
    }
    if(i===null) {
        return this.getTypedRuleContexts(ExprContext);
    } else {
        return this.getTypedRuleContext(ExprContext,i);
    }
};

BinaryOpContext.prototype.SLASH = function() {
    return this.getToken(BaserowFormula.SLASH, 0);
};

BinaryOpContext.prototype.STAR = function() {
    return this.getToken(BaserowFormula.STAR, 0);
};

BinaryOpContext.prototype.PLUS = function() {
    return this.getToken(BaserowFormula.PLUS, 0);
};

BinaryOpContext.prototype.MINUS = function() {
    return this.getToken(BaserowFormula.MINUS, 0);
};

BinaryOpContext.prototype.GT = function() {
    return this.getToken(BaserowFormula.GT, 0);
};

BinaryOpContext.prototype.LT = function() {
    return this.getToken(BaserowFormula.LT, 0);
};

BinaryOpContext.prototype.GTE = function() {
    return this.getToken(BaserowFormula.GTE, 0);
};

BinaryOpContext.prototype.LTE = function() {
    return this.getToken(BaserowFormula.LTE, 0);
};

BinaryOpContext.prototype.EQUAL = function() {
    return this.getToken(BaserowFormula.EQUAL, 0);
};

BinaryOpContext.prototype.BANG_EQUAL = function() {
    return this.getToken(BaserowFormula.BANG_EQUAL, 0);
};
BinaryOpContext.prototype.enterRule = function(listener) {
    if(listener instanceof BaserowFormulaListener ) {
        listener.enterBinaryOp(this);
	}
};

BinaryOpContext.prototype.exitRule = function(listener) {
    if(listener instanceof BaserowFormulaListener ) {
        listener.exitBinaryOp(this);
	}
};

BinaryOpContext.prototype.accept = function(visitor) {
    if ( visitor instanceof BaserowFormulaVisitor ) {
        return visitor.visitBinaryOp(this);
    } else {
        return visitor.visitChildren(this);
    }
};



BaserowFormula.prototype.expr = function(_p) {
	if(_p===undefined) {
	    _p = 0;
	}
    var _parentctx = this._ctx;
    var _parentState = this.state;
    var localctx = new ExprContext(this, this._ctx, _parentState);
    var _prevctx = localctx;
    var _startState = 2;
    this.enterRecursionRule(localctx, 2, BaserowFormula.RULE_expr, _p);
    var _la = 0; // Token type
    try {
        this.enterOuterAlt(localctx, 1);
        this.state = 61;
        this._errHandler.sync(this);
        switch(this._input.LA(1)) {
        case BaserowFormula.SINGLEQ_STRING_LITERAL:
            localctx = new StringLiteralContext(this, localctx);
            this._ctx = localctx;
            _prevctx = localctx;

            this.state = 16;
            this.match(BaserowFormula.SINGLEQ_STRING_LITERAL);
            break;
        case BaserowFormula.DOUBLEQ_STRING_LITERAL:
            localctx = new StringLiteralContext(this, localctx);
            this._ctx = localctx;
            _prevctx = localctx;
            this.state = 17;
            this.match(BaserowFormula.DOUBLEQ_STRING_LITERAL);
            break;
        case BaserowFormula.INTEGER_LITERAL:
            localctx = new IntegerLiteralContext(this, localctx);
            this._ctx = localctx;
            _prevctx = localctx;
            this.state = 18;
            this.match(BaserowFormula.INTEGER_LITERAL);
            break;
        case BaserowFormula.NUMERIC_LITERAL:
            localctx = new DecimalLiteralContext(this, localctx);
            this._ctx = localctx;
            _prevctx = localctx;
            this.state = 19;
            this.match(BaserowFormula.NUMERIC_LITERAL);
            break;
        case BaserowFormula.TRUE:
        case BaserowFormula.FALSE:
            localctx = new BooleanLiteralContext(this, localctx);
            this._ctx = localctx;
            _prevctx = localctx;
            this.state = 20;
            _la = this._input.LA(1);
            if(!(_la===BaserowFormula.TRUE || _la===BaserowFormula.FALSE)) {
            this._errHandler.recoverInline(this);
            }
            else {
            	this._errHandler.reportMatch(this);
                this.consume();
            }
            break;
        case BaserowFormula.BLOCK_COMMENT:
        case BaserowFormula.LINE_COMMENT:
        case BaserowFormula.WHITESPACE:
            localctx = new LeftWhitespaceOrCommentsContext(this, localctx);
            this._ctx = localctx;
            _prevctx = localctx;
            this.state = 21;
            this.ws_or_comment();
            this.state = 22;
            this.expr(11);
            break;
        case BaserowFormula.OPEN_PAREN:
            localctx = new BracketsContext(this, localctx);
            this._ctx = localctx;
            _prevctx = localctx;
            this.state = 24;
            this.match(BaserowFormula.OPEN_PAREN);
            this.state = 25;
            this.expr(0);
            this.state = 26;
            this.match(BaserowFormula.CLOSE_PAREN);
            break;
        case BaserowFormula.FIELD:
            localctx = new FieldReferenceContext(this, localctx);
            this._ctx = localctx;
            _prevctx = localctx;
            this.state = 28;
            this.match(BaserowFormula.FIELD);
            this.state = 29;
            this.match(BaserowFormula.OPEN_PAREN);
            this.state = 30;
            this.field_reference();
            this.state = 31;
            this.match(BaserowFormula.CLOSE_PAREN);
            break;
        case BaserowFormula.FIELDBYID:
            localctx = new FieldByIdReferenceContext(this, localctx);
            this._ctx = localctx;
            _prevctx = localctx;
            this.state = 33;
            this.match(BaserowFormula.FIELDBYID);
            this.state = 34;
            this.match(BaserowFormula.OPEN_PAREN);
            this.state = 35;
            this.match(BaserowFormula.INTEGER_LITERAL);
            this.state = 36;
            this.match(BaserowFormula.CLOSE_PAREN);
            break;
        case BaserowFormula.LOOKUP:
            localctx = new LookupFieldReferenceContext(this, localctx);
            this._ctx = localctx;
            _prevctx = localctx;
            this.state = 37;
            this.match(BaserowFormula.LOOKUP);
            this.state = 38;
            this.match(BaserowFormula.OPEN_PAREN);
            this.state = 39;
            this.field_reference();
            this.state = 40;
            this.match(BaserowFormula.COMMA);
            this.state = 42;
            this._errHandler.sync(this);
            _la = this._input.LA(1);
            if(_la===BaserowFormula.WHITESPACE) {
                this.state = 41;
                this.match(BaserowFormula.WHITESPACE);
            }

            this.state = 44;
            this.field_reference();
            this.state = 45;
            this.match(BaserowFormula.CLOSE_PAREN);
            break;
        case BaserowFormula.IDENTIFIER:
        case BaserowFormula.IDENTIFIER_UNICODE:
            localctx = new FunctionCallContext(this, localctx);
            this._ctx = localctx;
            _prevctx = localctx;
            this.state = 47;
            this.func_name();
            this.state = 48;
            this.match(BaserowFormula.OPEN_PAREN);
            this.state = 57;
            this._errHandler.sync(this);
            _la = this._input.LA(1);
            if((((_la) & ~0x1f) == 0 && ((1 << _la) & ((1 << BaserowFormula.BLOCK_COMMENT) | (1 << BaserowFormula.LINE_COMMENT) | (1 << BaserowFormula.WHITESPACE) | (1 << BaserowFormula.TRUE) | (1 << BaserowFormula.FALSE) | (1 << BaserowFormula.FIELD) | (1 << BaserowFormula.FIELDBYID) | (1 << BaserowFormula.LOOKUP) | (1 << BaserowFormula.OPEN_PAREN) | (1 << BaserowFormula.NUMERIC_LITERAL) | (1 << BaserowFormula.INTEGER_LITERAL) | (1 << BaserowFormula.SINGLEQ_STRING_LITERAL) | (1 << BaserowFormula.DOUBLEQ_STRING_LITERAL) | (1 << BaserowFormula.IDENTIFIER) | (1 << BaserowFormula.IDENTIFIER_UNICODE))) !== 0)) {
                this.state = 49;
                this.expr(0);
                this.state = 54;
                this._errHandler.sync(this);
                _la = this._input.LA(1);
                while(_la===BaserowFormula.COMMA) {
                    this.state = 50;
                    this.match(BaserowFormula.COMMA);
                    this.state = 51;
                    this.expr(0);
                    this.state = 56;
                    this._errHandler.sync(this);
                    _la = this._input.LA(1);
                }
            }

            this.state = 59;
            this.match(BaserowFormula.CLOSE_PAREN);
            break;
        default:
            throw new antlr4.error.NoViableAltException(this);
        }
        this._ctx.stop = this._input.LT(-1);
        this.state = 79;
        this._errHandler.sync(this);
        var _alt = this._interp.adaptivePredict(this._input,5,this._ctx)
        while(_alt!=2 && _alt!=antlr4.atn.ATN.INVALID_ALT_NUMBER) {
            if(_alt===1) {
                if(this._parseListeners!==null) {
                    this.triggerExitRuleEvent();
                }
                _prevctx = localctx;
                this.state = 77;
                this._errHandler.sync(this);
                var la_ = this._interp.adaptivePredict(this._input,4,this._ctx);
                switch(la_) {
                case 1:
                    localctx = new BinaryOpContext(this, new ExprContext(this, _parentctx, _parentState));
                    this.pushNewRecursionContext(localctx, _startState, BaserowFormula.RULE_expr);
                    this.state = 63;
                    if (!( this.precpred(this._ctx, 8))) {
                        throw new antlr4.error.FailedPredicateException(this, "this.precpred(this._ctx, 8)");
                    }
                    this.state = 64;
                    localctx.op = this._input.LT(1);
                    _la = this._input.LA(1);
                    if(!(_la===BaserowFormula.STAR || _la===BaserowFormula.SLASH)) {
                        localctx.op = this._errHandler.recoverInline(this);
                    }
                    else {
                    	this._errHandler.reportMatch(this);
                        this.consume();
                    }
                    this.state = 65;
                    this.expr(9);
                    break;

                case 2:
                    localctx = new BinaryOpContext(this, new ExprContext(this, _parentctx, _parentState));
                    this.pushNewRecursionContext(localctx, _startState, BaserowFormula.RULE_expr);
                    this.state = 66;
                    if (!( this.precpred(this._ctx, 7))) {
                        throw new antlr4.error.FailedPredicateException(this, "this.precpred(this._ctx, 7)");
                    }
                    this.state = 67;
                    localctx.op = this._input.LT(1);
                    _la = this._input.LA(1);
                    if(!(_la===BaserowFormula.MINUS || _la===BaserowFormula.PLUS)) {
                        localctx.op = this._errHandler.recoverInline(this);
                    }
                    else {
                    	this._errHandler.reportMatch(this);
                        this.consume();
                    }
                    this.state = 68;
                    this.expr(8);
                    break;

                case 3:
                    localctx = new BinaryOpContext(this, new ExprContext(this, _parentctx, _parentState));
                    this.pushNewRecursionContext(localctx, _startState, BaserowFormula.RULE_expr);
                    this.state = 69;
                    if (!( this.precpred(this._ctx, 6))) {
                        throw new antlr4.error.FailedPredicateException(this, "this.precpred(this._ctx, 6)");
                    }
                    this.state = 70;
                    localctx.op = this._input.LT(1);
                    _la = this._input.LA(1);
                    if(!(((((_la - 41)) & ~0x1f) == 0 && ((1 << (_la - 41)) & ((1 << (BaserowFormula.GT - 41)) | (1 << (BaserowFormula.GTE - 41)) | (1 << (BaserowFormula.LT - 41)) | (1 << (BaserowFormula.LTE - 41)))) !== 0))) {
                        localctx.op = this._errHandler.recoverInline(this);
                    }
                    else {
                    	this._errHandler.reportMatch(this);
                        this.consume();
                    }
                    this.state = 71;
                    this.expr(7);
                    break;

                case 4:
                    localctx = new BinaryOpContext(this, new ExprContext(this, _parentctx, _parentState));
                    this.pushNewRecursionContext(localctx, _startState, BaserowFormula.RULE_expr);
                    this.state = 72;
                    if (!( this.precpred(this._ctx, 5))) {
                        throw new antlr4.error.FailedPredicateException(this, "this.precpred(this._ctx, 5)");
                    }
                    this.state = 73;
                    localctx.op = this._input.LT(1);
                    _la = this._input.LA(1);
                    if(!(_la===BaserowFormula.BANG_EQUAL || _la===BaserowFormula.EQUAL)) {
                        localctx.op = this._errHandler.recoverInline(this);
                    }
                    else {
                    	this._errHandler.reportMatch(this);
                        this.consume();
                    }
                    this.state = 74;
                    this.expr(6);
                    break;

                case 5:
                    localctx = new RightWhitespaceOrCommentsContext(this, new ExprContext(this, _parentctx, _parentState));
                    this.pushNewRecursionContext(localctx, _startState, BaserowFormula.RULE_expr);
                    this.state = 75;
                    if (!( this.precpred(this._ctx, 10))) {
                        throw new antlr4.error.FailedPredicateException(this, "this.precpred(this._ctx, 10)");
                    }
                    this.state = 76;
                    this.ws_or_comment();
                    break;

                } 
            }
            this.state = 81;
            this._errHandler.sync(this);
            _alt = this._interp.adaptivePredict(this._input,5,this._ctx);
        }

    } catch( error) {
        if(error instanceof antlr4.error.RecognitionException) {
	        localctx.exception = error;
	        this._errHandler.reportError(this, error);
	        this._errHandler.recover(this, error);
	    } else {
	    	throw error;
	    }
    } finally {
        this.unrollRecursionContexts(_parentctx)
    }
    return localctx;
};


function Ws_or_commentContext(parser, parent, invokingState) {
	if(parent===undefined) {
	    parent = null;
	}
	if(invokingState===undefined || invokingState===null) {
		invokingState = -1;
	}
	antlr4.ParserRuleContext.call(this, parent, invokingState);
    this.parser = parser;
    this.ruleIndex = BaserowFormula.RULE_ws_or_comment;
    return this;
}

Ws_or_commentContext.prototype = Object.create(antlr4.ParserRuleContext.prototype);
Ws_or_commentContext.prototype.constructor = Ws_or_commentContext;

Ws_or_commentContext.prototype.BLOCK_COMMENT = function() {
    return this.getToken(BaserowFormula.BLOCK_COMMENT, 0);
};

Ws_or_commentContext.prototype.LINE_COMMENT = function() {
    return this.getToken(BaserowFormula.LINE_COMMENT, 0);
};

Ws_or_commentContext.prototype.WHITESPACE = function() {
    return this.getToken(BaserowFormula.WHITESPACE, 0);
};

Ws_or_commentContext.prototype.enterRule = function(listener) {
    if(listener instanceof BaserowFormulaListener ) {
        listener.enterWs_or_comment(this);
	}
};

Ws_or_commentContext.prototype.exitRule = function(listener) {
    if(listener instanceof BaserowFormulaListener ) {
        listener.exitWs_or_comment(this);
	}
};

Ws_or_commentContext.prototype.accept = function(visitor) {
    if ( visitor instanceof BaserowFormulaVisitor ) {
        return visitor.visitWs_or_comment(this);
    } else {
        return visitor.visitChildren(this);
    }
};




BaserowFormula.Ws_or_commentContext = Ws_or_commentContext;

BaserowFormula.prototype.ws_or_comment = function() {

    var localctx = new Ws_or_commentContext(this, this._ctx, this.state);
    this.enterRule(localctx, 4, BaserowFormula.RULE_ws_or_comment);
    var _la = 0; // Token type
    try {
        this.enterOuterAlt(localctx, 1);
        this.state = 82;
        _la = this._input.LA(1);
        if(!((((_la) & ~0x1f) == 0 && ((1 << _la) & ((1 << BaserowFormula.BLOCK_COMMENT) | (1 << BaserowFormula.LINE_COMMENT) | (1 << BaserowFormula.WHITESPACE))) !== 0))) {
        this._errHandler.recoverInline(this);
        }
        else {
        	this._errHandler.reportMatch(this);
            this.consume();
        }
    } catch (re) {
    	if(re instanceof antlr4.error.RecognitionException) {
	        localctx.exception = re;
	        this._errHandler.reportError(this, re);
	        this._errHandler.recover(this, re);
	    } else {
	    	throw re;
	    }
    } finally {
        this.exitRule();
    }
    return localctx;
};


function Func_nameContext(parser, parent, invokingState) {
	if(parent===undefined) {
	    parent = null;
	}
	if(invokingState===undefined || invokingState===null) {
		invokingState = -1;
	}
	antlr4.ParserRuleContext.call(this, parent, invokingState);
    this.parser = parser;
    this.ruleIndex = BaserowFormula.RULE_func_name;
    return this;
}

Func_nameContext.prototype = Object.create(antlr4.ParserRuleContext.prototype);
Func_nameContext.prototype.constructor = Func_nameContext;

Func_nameContext.prototype.identifier = function() {
    return this.getTypedRuleContext(IdentifierContext,0);
};

Func_nameContext.prototype.enterRule = function(listener) {
    if(listener instanceof BaserowFormulaListener ) {
        listener.enterFunc_name(this);
	}
};

Func_nameContext.prototype.exitRule = function(listener) {
    if(listener instanceof BaserowFormulaListener ) {
        listener.exitFunc_name(this);
	}
};

Func_nameContext.prototype.accept = function(visitor) {
    if ( visitor instanceof BaserowFormulaVisitor ) {
        return visitor.visitFunc_name(this);
    } else {
        return visitor.visitChildren(this);
    }
};




BaserowFormula.Func_nameContext = Func_nameContext;

BaserowFormula.prototype.func_name = function() {

    var localctx = new Func_nameContext(this, this._ctx, this.state);
    this.enterRule(localctx, 6, BaserowFormula.RULE_func_name);
    try {
        this.enterOuterAlt(localctx, 1);
        this.state = 84;
        this.identifier();
    } catch (re) {
    	if(re instanceof antlr4.error.RecognitionException) {
	        localctx.exception = re;
	        this._errHandler.reportError(this, re);
	        this._errHandler.recover(this, re);
	    } else {
	    	throw re;
	    }
    } finally {
        this.exitRule();
    }
    return localctx;
};


function Field_referenceContext(parser, parent, invokingState) {
	if(parent===undefined) {
	    parent = null;
	}
	if(invokingState===undefined || invokingState===null) {
		invokingState = -1;
	}
	antlr4.ParserRuleContext.call(this, parent, invokingState);
    this.parser = parser;
    this.ruleIndex = BaserowFormula.RULE_field_reference;
    return this;
}

Field_referenceContext.prototype = Object.create(antlr4.ParserRuleContext.prototype);
Field_referenceContext.prototype.constructor = Field_referenceContext;

Field_referenceContext.prototype.SINGLEQ_STRING_LITERAL = function() {
    return this.getToken(BaserowFormula.SINGLEQ_STRING_LITERAL, 0);
};

Field_referenceContext.prototype.DOUBLEQ_STRING_LITERAL = function() {
    return this.getToken(BaserowFormula.DOUBLEQ_STRING_LITERAL, 0);
};

Field_referenceContext.prototype.enterRule = function(listener) {
    if(listener instanceof BaserowFormulaListener ) {
        listener.enterField_reference(this);
	}
};

Field_referenceContext.prototype.exitRule = function(listener) {
    if(listener instanceof BaserowFormulaListener ) {
        listener.exitField_reference(this);
	}
};

Field_referenceContext.prototype.accept = function(visitor) {
    if ( visitor instanceof BaserowFormulaVisitor ) {
        return visitor.visitField_reference(this);
    } else {
        return visitor.visitChildren(this);
    }
};




BaserowFormula.Field_referenceContext = Field_referenceContext;

BaserowFormula.prototype.field_reference = function() {

    var localctx = new Field_referenceContext(this, this._ctx, this.state);
    this.enterRule(localctx, 8, BaserowFormula.RULE_field_reference);
    var _la = 0; // Token type
    try {
        this.enterOuterAlt(localctx, 1);
        this.state = 86;
        _la = this._input.LA(1);
        if(!(_la===BaserowFormula.SINGLEQ_STRING_LITERAL || _la===BaserowFormula.DOUBLEQ_STRING_LITERAL)) {
        this._errHandler.recoverInline(this);
        }
        else {
        	this._errHandler.reportMatch(this);
            this.consume();
        }
    } catch (re) {
    	if(re instanceof antlr4.error.RecognitionException) {
	        localctx.exception = re;
	        this._errHandler.reportError(this, re);
	        this._errHandler.recover(this, re);
	    } else {
	    	throw re;
	    }
    } finally {
        this.exitRule();
    }
    return localctx;
};


function IdentifierContext(parser, parent, invokingState) {
	if(parent===undefined) {
	    parent = null;
	}
	if(invokingState===undefined || invokingState===null) {
		invokingState = -1;
	}
	antlr4.ParserRuleContext.call(this, parent, invokingState);
    this.parser = parser;
    this.ruleIndex = BaserowFormula.RULE_identifier;
    return this;
}

IdentifierContext.prototype = Object.create(antlr4.ParserRuleContext.prototype);
IdentifierContext.prototype.constructor = IdentifierContext;

IdentifierContext.prototype.IDENTIFIER = function() {
    return this.getToken(BaserowFormula.IDENTIFIER, 0);
};

IdentifierContext.prototype.IDENTIFIER_UNICODE = function() {
    return this.getToken(BaserowFormula.IDENTIFIER_UNICODE, 0);
};

IdentifierContext.prototype.enterRule = function(listener) {
    if(listener instanceof BaserowFormulaListener ) {
        listener.enterIdentifier(this);
	}
};

IdentifierContext.prototype.exitRule = function(listener) {
    if(listener instanceof BaserowFormulaListener ) {
        listener.exitIdentifier(this);
	}
};

IdentifierContext.prototype.accept = function(visitor) {
    if ( visitor instanceof BaserowFormulaVisitor ) {
        return visitor.visitIdentifier(this);
    } else {
        return visitor.visitChildren(this);
    }
};




BaserowFormula.IdentifierContext = IdentifierContext;

BaserowFormula.prototype.identifier = function() {

    var localctx = new IdentifierContext(this, this._ctx, this.state);
    this.enterRule(localctx, 10, BaserowFormula.RULE_identifier);
    var _la = 0; // Token type
    try {
        this.enterOuterAlt(localctx, 1);
        this.state = 88;
        _la = this._input.LA(1);
        if(!(_la===BaserowFormula.IDENTIFIER || _la===BaserowFormula.IDENTIFIER_UNICODE)) {
        this._errHandler.recoverInline(this);
        }
        else {
        	this._errHandler.reportMatch(this);
            this.consume();
        }
    } catch (re) {
    	if(re instanceof antlr4.error.RecognitionException) {
	        localctx.exception = re;
	        this._errHandler.reportError(this, re);
	        this._errHandler.recover(this, re);
	    } else {
	    	throw re;
	    }
    } finally {
        this.exitRule();
    }
    return localctx;
};


BaserowFormula.prototype.sempred = function(localctx, ruleIndex, predIndex) {
	switch(ruleIndex) {
	case 1:
			return this.expr_sempred(localctx, predIndex);
    default:
        throw "No predicate with index:" + ruleIndex;
   }
};

BaserowFormula.prototype.expr_sempred = function(localctx, predIndex) {
	switch(predIndex) {
		case 0:
			return this.precpred(this._ctx, 8);
		case 1:
			return this.precpred(this._ctx, 7);
		case 2:
			return this.precpred(this._ctx, 6);
		case 3:
			return this.precpred(this._ctx, 5);
		case 4:
			return this.precpred(this._ctx, 10);
		default:
			throw "No predicate with index:" + predIndex;
	}
};


exports.BaserowFormula = BaserowFormula;
