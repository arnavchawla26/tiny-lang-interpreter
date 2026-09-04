import pytest

from tiny_lang import ast_nodes as ast
from tiny_lang.errors import ParseError
from tiny_lang.lexer import tokenize
from tiny_lang.parser import parse


def parse_source(source):
    return parse(tokenize(source))


def test_var_decl_with_initializer():
    program = parse_source("let x = 5;")
    assert len(program.statements) == 1
    decl = program.statements[0]
    assert isinstance(decl, ast.VarDecl)
    assert decl.name == "x"
    assert isinstance(decl.initializer, ast.Literal)
    assert decl.initializer.value == 5


def test_var_decl_without_initializer():
    program = parse_source("let x;")
    decl = program.statements[0]
    assert decl.initializer is None


def test_binary_precedence_multiplication_before_addition():
    program = parse_source("1 + 2 * 3;")
    expr = program.statements[0].expr
    assert isinstance(expr, ast.Binary)
    assert expr.op == "+"
    assert isinstance(expr.right, ast.Binary)
    assert expr.right.op == "*"


def test_parentheses_override_precedence():
    program = parse_source("(1 + 2) * 3;")
    expr = program.statements[0].expr
    assert isinstance(expr, ast.Binary)
    assert expr.op == "*"
    assert isinstance(expr.left, ast.Binary)
    assert expr.left.op == "+"


def test_unary_minus_and_not():
    program = parse_source("-5; !true;")
    assert isinstance(program.statements[0].expr, ast.Unary)
    assert program.statements[0].expr.op == "-"
    assert isinstance(program.statements[1].expr, ast.Unary)
    assert program.statements[1].expr.op == "!"


def test_logical_and_or_parse_as_logical_nodes():
    program = parse_source("true and false or true;")
    expr = program.statements[0].expr
    assert isinstance(expr, ast.Logical)
    assert expr.op == "or"
    assert isinstance(expr.left, ast.Logical)
    assert expr.left.op == "and"


def test_assignment_is_right_associative():
    program = parse_source("let a; let b; a = b = 5;")
    assign = program.statements[2].expr
    assert isinstance(assign, ast.Assign)
    assert assign.name == "a"
    assert isinstance(assign.value, ast.Assign)
    assert assign.value.name == "b"


def test_assignment_to_non_variable_raises():
    with pytest.raises(ParseError):
        parse_source("5 = 3;")


def test_function_decl_parses_params_and_body():
    program = parse_source("fn add(a, b) { return a + b; }")
    decl = program.statements[0]
    assert isinstance(decl, ast.FunctionDecl)
    assert decl.name == "add"
    assert decl.params == ["a", "b"]
    assert len(decl.body) == 1
    assert isinstance(decl.body[0], ast.ReturnStatement)


def test_function_decl_with_no_params():
    program = parse_source("fn hello() { print \"hi\"; }")
    decl = program.statements[0]
    assert decl.params == []


def test_call_expression_parses_arguments():
    program = parse_source("foo(1, 2, 3);")
    call = program.statements[0].expr
    assert isinstance(call, ast.Call)
    assert isinstance(call.callee, ast.Variable)
    assert call.callee.name == "foo"
    assert len(call.args) == 3


def test_call_with_zero_arguments():
    program = parse_source("foo();")
    call = program.statements[0].expr
    assert call.args == []


def test_if_else_statement():
    program = parse_source("if (true) { print 1; } else { print 2; }")
    stmt = program.statements[0]
    assert isinstance(stmt, ast.IfStatement)
    assert stmt.else_branch is not None


def test_if_without_else():
    program = parse_source("if (true) { print 1; }")
    stmt = program.statements[0]
    assert stmt.else_branch is None


def test_else_if_chain_nests_if_in_else_branch():
    program = parse_source("if (a) { print 1; } else if (b) { print 2; } else { print 3; }")
    stmt = program.statements[0]
    assert isinstance(stmt.else_branch, ast.IfStatement)
    assert isinstance(stmt.else_branch.else_branch, ast.Block)


def test_while_statement():
    program = parse_source("while (true) { print 1; }")
    stmt = program.statements[0]
    assert isinstance(stmt, ast.WhileStatement)


def test_block_statement_collects_declarations():
    program = parse_source("{ let x = 1; let y = 2; }")
    block = program.statements[0]
    assert isinstance(block, ast.Block)
    assert len(block.statements) == 2


def test_missing_semicolon_raises_parse_error():
    with pytest.raises(ParseError):
        parse_source("let x = 5")


def test_unclosed_paren_raises_parse_error():
    with pytest.raises(ParseError):
        parse_source("print (1 + 2;")


def test_error_includes_line_number():
    try:
        parse_source("let x = 5\nlet y = 6;")
    except ParseError as exc:
        assert exc.line == 2
    else:
        pytest.fail("expected ParseError")
