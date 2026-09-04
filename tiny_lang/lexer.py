"""Lexer (tokenizer) for the Toy language.

Turns raw source text into a flat list of Token objects. Hand-written,
single-pass, no regex-based tokenization tables -- just a scanner that
walks the source character by character, which keeps line-number
tracking simple and exact.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto

from .errors import LexError


class TokenType(Enum):
    # Literals
    NUMBER = auto()
    STRING = auto()
    IDENTIFIER = auto()

    # Keywords
    LET = auto()
    IF = auto()
    ELSE = auto()
    WHILE = auto()
    FN = auto()
    RETURN = auto()
    TRUE = auto()
    FALSE = auto()
    NIL = auto()
    AND = auto()
    OR = auto()
    PRINT = auto()

    # Single/multi-character operators and punctuation
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    PERCENT = auto()
    EQUAL = auto()
    EQUAL_EQUAL = auto()
    BANG = auto()
    BANG_EQUAL = auto()
    LESS = auto()
    LESS_EQUAL = auto()
    GREATER = auto()
    GREATER_EQUAL = auto()
    LPAREN = auto()
    RPAREN = auto()
    LBRACE = auto()
    RBRACE = auto()
    COMMA = auto()
    SEMICOLON = auto()

    EOF = auto()


KEYWORDS = {
    "let": TokenType.LET,
    "if": TokenType.IF,
    "else": TokenType.ELSE,
    "while": TokenType.WHILE,
    "fn": TokenType.FN,
    "return": TokenType.RETURN,
    "true": TokenType.TRUE,
    "false": TokenType.FALSE,
    "nil": TokenType.NIL,
    "and": TokenType.AND,
    "or": TokenType.OR,
    "print": TokenType.PRINT,
}


@dataclass(frozen=True)
class Token:
    type: TokenType
    lexeme: str
    literal: object
    line: int

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"Token({self.type.name}, {self.lexeme!r}, {self.literal!r}, line={self.line})"


class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.tokens: list[Token] = []
        self.start = 0
        self.current = 0
        self.line = 1

    def tokenize(self) -> list[Token]:
        while not self._at_end():
            self.start = self.current
            self._scan_token()
        self.tokens.append(Token(TokenType.EOF, "", None, self.line))
        return self.tokens

    # -- scanning -----------------------------------------------------

    def _scan_token(self) -> None:
        c = self._advance()

        if c in " \r\t":
            return
        if c == "\n":
            self.line += 1
            return
        if c == "#":
            self._skip_line_comment()
            return

        if c == "(":
            self._add(TokenType.LPAREN)
        elif c == ")":
            self._add(TokenType.RPAREN)
        elif c == "{":
            self._add(TokenType.LBRACE)
        elif c == "}":
            self._add(TokenType.RBRACE)
        elif c == ",":
            self._add(TokenType.COMMA)
        elif c == ";":
            self._add(TokenType.SEMICOLON)
        elif c == "+":
            self._add(TokenType.PLUS)
        elif c == "-":
            self._add(TokenType.MINUS)
        elif c == "*":
            self._add(TokenType.STAR)
        elif c == "%":
            self._add(TokenType.PERCENT)
        elif c == "/":
            self._add(TokenType.SLASH)
        elif c == "=":
            self._add(TokenType.EQUAL_EQUAL if self._match("=") else TokenType.EQUAL)
        elif c == "!":
            self._add(TokenType.BANG_EQUAL if self._match("=") else TokenType.BANG)
        elif c == "<":
            self._add(TokenType.LESS_EQUAL if self._match("=") else TokenType.LESS)
        elif c == ">":
            self._add(TokenType.GREATER_EQUAL if self._match("=") else TokenType.GREATER)
        elif c == "&":
            if self._match("&"):
                self._add(TokenType.AND)
            else:
                raise LexError(f"Unexpected character '&' (did you mean '&&'?)", self.line)
        elif c == "|":
            if self._match("|"):
                self._add(TokenType.OR)
            else:
                raise LexError(f"Unexpected character '|' (did you mean '||'?)", self.line)
        elif c == '"':
            self._string()
        elif c.isdigit():
            self._number()
        elif c.isalpha() or c == "_":
            self._identifier()
        else:
            raise LexError(f"Unexpected character {c!r}", self.line)

    def _skip_line_comment(self) -> None:
        while not self._at_end() and self._peek() != "\n":
            self._advance()

    def _string(self) -> None:
        start_line = self.line
        chars: list[str] = []
        while not self._at_end() and self._peek() != '"':
            ch = self._advance()
            if ch == "\n":
                self.line += 1
            if ch == "\\" and not self._at_end():
                nxt = self._advance()
                escapes = {"n": "\n", "t": "\t", '"': '"', "\\": "\\"}
                chars.append(escapes.get(nxt, nxt))
            else:
                chars.append(ch)

        if self._at_end():
            raise LexError("Unterminated string literal", start_line)

        self._advance()  # closing quote
        value = "".join(chars)
        self.tokens.append(Token(TokenType.STRING, self.source[self.start:self.current], value, start_line))

    def _number(self) -> None:
        while self._peek().isdigit():
            self._advance()
        is_float = False
        if self._peek() == "." and self._peek_next().isdigit():
            is_float = True
            self._advance()
            while self._peek().isdigit():
                self._advance()

        text = self.source[self.start:self.current]
        value = float(text) if is_float else int(text)
        self.tokens.append(Token(TokenType.NUMBER, text, value, self.line))

    def _identifier(self) -> None:
        while self._peek().isalnum() or self._peek() == "_":
            self._advance()
        text = self.source[self.start:self.current]
        token_type = KEYWORDS.get(text, TokenType.IDENTIFIER)
        literal = None
        if token_type == TokenType.TRUE:
            literal = True
        elif token_type == TokenType.FALSE:
            literal = False
        self.tokens.append(Token(token_type, text, literal, self.line))

    # -- low-level helpers ---------------------------------------------

    def _at_end(self) -> bool:
        return self.current >= len(self.source)

    def _advance(self) -> str:
        ch = self.source[self.current]
        self.current += 1
        return ch

    def _match(self, expected: str) -> bool:
        if self._at_end() or self.source[self.current] != expected:
            return False
        self.current += 1
        return True

    def _peek(self) -> str:
        if self._at_end():
            return "\0"
        return self.source[self.current]

    def _peek_next(self) -> str:
        if self.current + 1 >= len(self.source):
            return "\0"
        return self.source[self.current + 1]

    def _add(self, token_type: TokenType) -> None:
        text = self.source[self.start:self.current]
        self.tokens.append(Token(token_type, text, None, self.line))


def tokenize(source: str) -> list[Token]:
    return Lexer(source).tokenize()
