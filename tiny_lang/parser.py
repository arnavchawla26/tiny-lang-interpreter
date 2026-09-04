"""Recursive-descent parser for Toy.

Grammar (roughly, lowest to highest precedence):

    program     -> declaration* EOF
    declaration -> varDecl | funDecl | statement
    varDecl     -> "let" IDENTIFIER ( "=" expression )? ";"
    funDecl     -> "fn" IDENTIFIER "(" params? ")" block
    statement   -> exprStmt | printStmt | block | ifStmt | whileStmt
                 | returnStmt
    exprStmt    -> expression ";"
    printStmt   -> "print" expression ";"
    block       -> "{" declaration* "}"
    ifStmt      -> "if" "(" expression ")" statement ( "else" statement )?
    whileStmt   -> "while" "(" expression ")" statement
    returnStmt  -> "return" expression? ";"

    expression  -> assignment
    assignment  -> IDENTIFIER "=" assignment | logic_or
    logic_or    -> logic_and ( "||" logic_and )*
    logic_and   -> equality ( "&&" equality )*
    equality    -> comparison ( ( "==" | "!=" ) comparison )*
    comparison  -> term ( ( "<" | "<=" | ">" | ">=" ) term )*
    term        -> factor ( ( "+" | "-" ) factor )*
    factor      -> unary ( ( "*" | "/" | "%" ) unary )*
    unary       -> ( "!" | "-" ) unary | call
    call        -> primary ( "(" arguments? ")" )*
    primary     -> NUMBER | STRING | "true" | "false" | "nil"
                 | IDENTIFIER | "(" expression ")"
"""

from __future__ import annotations

from .ast_nodes import (
    Assign,
    Binary,
    Block,
    Call,
    ExpressionStatement,
    FunctionDecl,
    IfStatement,
    Literal,
    Logical,
    Node,
    PrintStatement,
    Program,
    ReturnStatement,
    Unary,
    VarDecl,
    Variable,
    WhileStatement,
)
from .errors import ParseError
from .lexer import Token, TokenType

_COMPARISON = (TokenType.LESS, TokenType.LESS_EQUAL, TokenType.GREATER, TokenType.GREATER_EQUAL)
_EQUALITY = (TokenType.EQUAL_EQUAL, TokenType.BANG_EQUAL)
_TERM = (TokenType.PLUS, TokenType.MINUS)
_FACTOR = (TokenType.STAR, TokenType.SLASH, TokenType.PERCENT)

_OP_LEXEME = {
    TokenType.PLUS: "+",
    TokenType.MINUS: "-",
    TokenType.STAR: "*",
    TokenType.SLASH: "/",
    TokenType.PERCENT: "%",
    TokenType.EQUAL_EQUAL: "==",
    TokenType.BANG_EQUAL: "!=",
    TokenType.LESS: "<",
    TokenType.LESS_EQUAL: "<=",
    TokenType.GREATER: ">",
    TokenType.GREATER_EQUAL: ">=",
    TokenType.BANG: "!",
}


class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0

    def parse(self) -> Program:
        statements = []
        while not self._at_end():
            statements.append(self._declaration())
        return Program(statements)

    # -- declarations ----------------------------------------------------

    def _declaration(self) -> Node:
        if self._match(TokenType.LET):
            return self._var_decl()
        if self._match(TokenType.FN):
            return self._function_decl()
        return self._statement()

    def _var_decl(self) -> Node:
        line = self._previous().line
        name = self._consume(TokenType.IDENTIFIER, "Expected variable name after 'let'").lexeme
        initializer = None
        if self._match(TokenType.EQUAL):
            initializer = self._expression()
        self._consume(TokenType.SEMICOLON, "Expected ';' after variable declaration")
        return VarDecl(name, initializer, line)

    def _function_decl(self) -> Node:
        line = self._previous().line
        name = self._consume(TokenType.IDENTIFIER, "Expected function name after 'fn'").lexeme
        self._consume(TokenType.LPAREN, "Expected '(' after function name")
        params: list[str] = []
        if not self._check(TokenType.RPAREN):
            params.append(self._consume(TokenType.IDENTIFIER, "Expected parameter name").lexeme)
            while self._match(TokenType.COMMA):
                params.append(self._consume(TokenType.IDENTIFIER, "Expected parameter name").lexeme)
        self._consume(TokenType.RPAREN, "Expected ')' after parameters")
        self._consume(TokenType.LBRACE, "Expected '{' to begin function body")
        body = self._block_statements()
        return FunctionDecl(name, params, body, line)

    # -- statements --------------------------------------------------------

    def _statement(self) -> Node:
        if self._match(TokenType.PRINT):
            return self._print_statement()
        if self._match(TokenType.LBRACE):
            line = self._previous().line
            return Block(self._block_statements(), line)
        if self._match(TokenType.IF):
            return self._if_statement()
        if self._match(TokenType.WHILE):
            return self._while_statement()
        if self._match(TokenType.RETURN):
            return self._return_statement()
        return self._expression_statement()

    def _print_statement(self) -> Node:
        line = self._previous().line
        value = self._expression()
        self._consume(TokenType.SEMICOLON, "Expected ';' after value")
        return PrintStatement(value, line)

    def _block_statements(self) -> list[Node]:
        statements = []
        while not self._check(TokenType.RBRACE) and not self._at_end():
            statements.append(self._declaration())
        self._consume(TokenType.RBRACE, "Expected '}' after block")
        return statements

    def _if_statement(self) -> Node:
        line = self._previous().line
        self._consume(TokenType.LPAREN, "Expected '(' after 'if'")
        condition = self._expression()
        self._consume(TokenType.RPAREN, "Expected ')' after if condition")
        then_branch = self._statement()
        else_branch = None
        if self._match(TokenType.ELSE):
            else_branch = self._statement()
        return IfStatement(condition, then_branch, else_branch, line)

    def _while_statement(self) -> Node:
        line = self._previous().line
        self._consume(TokenType.LPAREN, "Expected '(' after 'while'")
        condition = self._expression()
        self._consume(TokenType.RPAREN, "Expected ')' after while condition")
        body = self._statement()
        return WhileStatement(condition, body, line)

    def _return_statement(self) -> Node:
        line = self._previous().line
        value = None
        if not self._check(TokenType.SEMICOLON):
            value = self._expression()
        self._consume(TokenType.SEMICOLON, "Expected ';' after return value")
        return ReturnStatement(value, line)

    def _expression_statement(self) -> Node:
        line = self._peek().line
        expr = self._expression()
        self._consume(TokenType.SEMICOLON, "Expected ';' after expression")
        return ExpressionStatement(expr, line)

    # -- expressions ---------------------------------------------------------

    def _expression(self) -> Node:
        return self._assignment()

    def _assignment(self) -> Node:
        expr = self._logic_or()
        if self._match(TokenType.EQUAL):
            equals_line = self._previous().line
            value = self._assignment()
            if isinstance(expr, Variable):
                return Assign(expr.name, value, equals_line)
            raise ParseError("Invalid assignment target", equals_line)
        return expr

    def _logic_or(self) -> Node:
        expr = self._logic_and()
        while self._match(TokenType.OR):
            line = self._previous().line
            right = self._logic_and()
            expr = Logical(expr, "or", right, line)
        return expr

    def _logic_and(self) -> Node:
        expr = self._equality()
        while self._match(TokenType.AND):
            line = self._previous().line
            right = self._equality()
            expr = Logical(expr, "and", right, line)
        return expr

    def _equality(self) -> Node:
        expr = self._comparison()
        while self._check_any(_EQUALITY):
            op_token = self._advance()
            right = self._comparison()
            expr = Binary(expr, _OP_LEXEME[op_token.type], right, op_token.line)
        return expr

    def _comparison(self) -> Node:
        expr = self._term()
        while self._check_any(_COMPARISON):
            op_token = self._advance()
            right = self._term()
            expr = Binary(expr, _OP_LEXEME[op_token.type], right, op_token.line)
        return expr

    def _term(self) -> Node:
        expr = self._factor()
        while self._check_any(_TERM):
            op_token = self._advance()
            right = self._factor()
            expr = Binary(expr, _OP_LEXEME[op_token.type], right, op_token.line)
        return expr

    def _factor(self) -> Node:
        expr = self._unary()
        while self._check_any(_FACTOR):
            op_token = self._advance()
            right = self._unary()
            expr = Binary(expr, _OP_LEXEME[op_token.type], right, op_token.line)
        return expr

    def _unary(self) -> Node:
        if self._check_any((TokenType.BANG, TokenType.MINUS)):
            op_token = self._advance()
            right = self._unary()
            return Unary(_OP_LEXEME[op_token.type], right, op_token.line)
        return self._call()

    def _call(self) -> Node:
        expr = self._primary()
        while True:
            if self._match(TokenType.LPAREN):
                expr = self._finish_call(expr)
            else:
                break
        return expr

    def _finish_call(self, callee: Node) -> Node:
        line = self._previous().line
        args: list[Node] = []
        if not self._check(TokenType.RPAREN):
            args.append(self._expression())
            while self._match(TokenType.COMMA):
                args.append(self._expression())
        self._consume(TokenType.RPAREN, "Expected ')' after arguments")
        return Call(callee, args, line)

    def _primary(self) -> Node:
        token = self._peek()

        if self._match(TokenType.NUMBER, TokenType.STRING):
            return Literal(self._previous().literal, token.line)
        if self._match(TokenType.TRUE):
            return Literal(True, token.line)
        if self._match(TokenType.FALSE):
            return Literal(False, token.line)
        if self._match(TokenType.NIL):
            return Literal(None, token.line)
        if self._match(TokenType.IDENTIFIER):
            return Variable(self._previous().lexeme, token.line)
        if self._match(TokenType.LPAREN):
            expr = self._expression()
            self._consume(TokenType.RPAREN, "Expected ')' after expression")
            return expr

        raise ParseError(f"Unexpected token '{token.lexeme}'", token.line)

    # -- token stream helpers ------------------------------------------------

    def _match(self, *types: TokenType) -> bool:
        if self._check_any(types):
            self._advance()
            return True
        return False

    def _check_any(self, types) -> bool:
        return any(self._check(t) for t in types)

    def _check(self, token_type: TokenType) -> bool:
        if self._at_end():
            return False
        return self._peek().type == token_type

    def _advance(self) -> Token:
        if not self._at_end():
            self.pos += 1
        return self._previous()

    def _at_end(self) -> bool:
        return self._peek().type == TokenType.EOF

    def _peek(self) -> Token:
        return self.tokens[self.pos]

    def _previous(self) -> Token:
        return self.tokens[self.pos - 1]

    def _consume(self, token_type: TokenType, message: str) -> Token:
        if self._check(token_type):
            return self._advance()
        raise ParseError(message, self._peek().line)


def parse(tokens: list[Token]) -> Program:
    return Parser(tokens).parse()
