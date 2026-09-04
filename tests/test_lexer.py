import pytest

from tiny_lang.errors import LexError
from tiny_lang.lexer import TokenType, tokenize


def token_types(source):
    return [t.type for t in tokenize(source)]


def test_empty_source_is_just_eof():
    assert token_types("") == [TokenType.EOF]


def test_numbers_int_and_float():
    tokens = tokenize("42 3.14")
    assert [t.type for t in tokens[:2]] == [TokenType.NUMBER, TokenType.NUMBER]
    assert tokens[0].literal == 42
    assert isinstance(tokens[0].literal, int)
    assert tokens[1].literal == 3.14
    assert isinstance(tokens[1].literal, float)


def test_string_literal_with_escapes():
    tokens = tokenize('"hello\\nworld"')
    assert tokens[0].type == TokenType.STRING
    assert tokens[0].literal == "hello\nworld"


def test_unterminated_string_raises():
    with pytest.raises(LexError):
        tokenize('"unterminated')


def test_keywords_recognized():
    tokens = tokenize("let if else while fn return true false nil and or print")
    expected = [
        TokenType.LET,
        TokenType.IF,
        TokenType.ELSE,
        TokenType.WHILE,
        TokenType.FN,
        TokenType.RETURN,
        TokenType.TRUE,
        TokenType.FALSE,
        TokenType.NIL,
        TokenType.AND,
        TokenType.OR,
        TokenType.PRINT,
        TokenType.EOF,
    ]
    assert [t.type for t in tokens] == expected


def test_identifiers_vs_keywords():
    tokens = tokenize("letter iffy")
    assert tokens[0].type == TokenType.IDENTIFIER
    assert tokens[0].lexeme == "letter"
    assert tokens[1].type == TokenType.IDENTIFIER
    assert tokens[1].lexeme == "iffy"


def test_operators():
    tokens = tokenize("+ - * / % = == ! != < <= > >= && ||")
    expected = [
        TokenType.PLUS,
        TokenType.MINUS,
        TokenType.STAR,
        TokenType.SLASH,
        TokenType.PERCENT,
        TokenType.EQUAL,
        TokenType.EQUAL_EQUAL,
        TokenType.BANG,
        TokenType.BANG_EQUAL,
        TokenType.LESS,
        TokenType.LESS_EQUAL,
        TokenType.GREATER,
        TokenType.GREATER_EQUAL,
        TokenType.AND,
        TokenType.OR,
        TokenType.EOF,
    ]
    assert [t.type for t in tokens] == expected


def test_punctuation():
    tokens = tokenize("( ) { } , ;")
    expected = [
        TokenType.LPAREN,
        TokenType.RPAREN,
        TokenType.LBRACE,
        TokenType.RBRACE,
        TokenType.COMMA,
        TokenType.SEMICOLON,
        TokenType.EOF,
    ]
    assert [t.type for t in tokens] == expected


def test_line_comment_is_skipped():
    tokens = tokenize("let x = 1; # this is a comment\nlet y = 2;")
    # Comment contributes no tokens; line number still advances correctly.
    assert tokens[-2].line == 2  # the ';' after 'let y = 2'


def test_line_numbers_track_newlines():
    tokens = tokenize("let a = 1;\nlet b = 2;\nlet c = 3;")
    let_tokens = [t for t in tokens if t.type == TokenType.LET]
    assert [t.line for t in let_tokens] == [1, 2, 3]


def test_unexpected_character_raises():
    with pytest.raises(LexError):
        tokenize("let x = @;")


def test_lone_ampersand_raises():
    with pytest.raises(LexError):
        tokenize("&")


def test_lone_pipe_raises():
    with pytest.raises(LexError):
        tokenize("|")


def test_negative_number_is_two_tokens():
    # Lexer never produces a signed NUMBER token; '-' is a separate
    # MINUS token and negation is handled by the parser/interpreter.
    tokens = tokenize("-5")
    assert [t.type for t in tokens] == [TokenType.MINUS, TokenType.NUMBER, TokenType.EOF]
