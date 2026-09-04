"""Tree-walking interpreter for Toy.

Executes a ``Program`` AST directly -- no bytecode compilation step.
Dispatch is a plain dict keyed on node type, which is a common and
readable alternative to the classic visitor pattern in a small
from-scratch interpreter.
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
from .environment import Environment
from .errors import ReturnSignal, ToyRuntimeError


class ToyFunction:
    """A user-defined Toy function value, capturing its defining scope
    (its ``closure``) so it can be called later with the right lexical
    environment even if that call happens from somewhere else entirely.
    """

    def __init__(self, decl: FunctionDecl, closure: Environment, interpreter: "Interpreter"):
        self.decl = decl
        self.closure = closure
        self.interpreter = interpreter

    @property
    def arity(self) -> int:
        return len(self.decl.params)

    def call(self, args: list[object], line: int) -> object:
        if len(args) != self.arity:
            raise ToyRuntimeError(
                f"Function '{self.decl.name}' expects {self.arity} argument(s) but got {len(args)}",
                line,
            )
        call_env = Environment(self.closure)
        for param, value in zip(self.decl.params, args):
            call_env.define(param, value)
        try:
            self.interpreter._execute_block(self.decl.body, call_env)
        except ReturnSignal as ret:
            return ret.value
        return None

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<fn {self.decl.name}>"


class Interpreter:
    def __init__(self, output=None):
        self.globals = Environment()
        self.environment = self.globals
        # `output` lets tests/CLI capture printed output instead of stdout.
        self._output = output if output is not None else []

    def interpret(self, program: Program) -> list[str]:
        for statement in program.statements:
            self._execute(statement)
        return self._output

    # -- statement execution ---------------------------------------------

    def _execute(self, node: Node) -> None:
        handler = self._STATEMENT_DISPATCH.get(type(node))
        if handler is None:
            raise ToyRuntimeError(f"Cannot execute node of type {type(node).__name__}", getattr(node, "line", 0))
        handler(self, node)

    def _exec_expression_statement(self, node: ExpressionStatement) -> None:
        self._evaluate(node.expr)

    def _exec_print(self, node: PrintStatement) -> None:
        value = self._evaluate(node.expr)
        self._output.append(stringify(value))

    def _exec_var_decl(self, node: VarDecl) -> None:
        value = self._evaluate(node.initializer) if node.initializer is not None else None
        self.environment.define(node.name, value)

    def _exec_block(self, node: Block) -> None:
        self._execute_block(node.statements, Environment(self.environment))

    def _execute_block(self, statements: list[Node], environment: Environment) -> None:
        previous = self.environment
        try:
            self.environment = environment
            for statement in statements:
                self._execute(statement)
        finally:
            self.environment = previous

    def _exec_if(self, node: IfStatement) -> None:
        if is_truthy(self._evaluate(node.condition)):
            self._execute(node.then_branch)
        elif node.else_branch is not None:
            self._execute(node.else_branch)

    def _exec_while(self, node: WhileStatement) -> None:
        while is_truthy(self._evaluate(node.condition)):
            self._execute(node.body)

    def _exec_function_decl(self, node: FunctionDecl) -> None:
        function = ToyFunction(node, self.environment, self)
        self.environment.define(node.name, function)

    def _exec_return(self, node: ReturnStatement) -> None:
        value = self._evaluate(node.value) if node.value is not None else None
        raise ReturnSignal(value)

    _STATEMENT_DISPATCH = {
        ExpressionStatement: _exec_expression_statement,
        PrintStatement: _exec_print,
        VarDecl: _exec_var_decl,
        Block: _exec_block,
        IfStatement: _exec_if,
        WhileStatement: _exec_while,
        FunctionDecl: _exec_function_decl,
        ReturnStatement: _exec_return,
    }

    # -- expression evaluation -----------------------------------------------

    def _evaluate(self, node: Node) -> object:
        handler = self._EXPRESSION_DISPATCH.get(type(node))
        if handler is None:
            raise ToyRuntimeError(f"Cannot evaluate node of type {type(node).__name__}", getattr(node, "line", 0))
        return handler(self, node)

    def _eval_literal(self, node: Literal) -> object:
        return node.value

    def _eval_variable(self, node: Variable) -> object:
        return self.environment.get(node.name, node.line)

    def _eval_assign(self, node: Assign) -> object:
        value = self._evaluate(node.value)
        self.environment.assign(node.name, value, node.line)
        return value

    def _eval_unary(self, node: Unary) -> object:
        right = self._evaluate(node.right)
        if node.op == "-":
            _check_number_operand(right, node.line)
            return -right
        if node.op == "!":
            return not is_truthy(right)
        raise ToyRuntimeError(f"Unknown unary operator '{node.op}'", node.line)

    def _eval_logical(self, node: Logical) -> object:
        left = self._evaluate(node.left)
        if node.op == "or":
            if is_truthy(left):
                return left
        else:  # "and"
            if not is_truthy(left):
                return left
        return self._evaluate(node.right)

    def _eval_binary(self, node: Binary) -> object:
        left = self._evaluate(node.left)
        right = self._evaluate(node.right)
        op = node.op
        line = node.line

        if op == "+":
            if isinstance(left, str) or isinstance(right, str):
                return stringify(left) + stringify(right)
            _check_number_operands(left, right, line)
            return left + right
        if op == "-":
            _check_number_operands(left, right, line)
            return left - right
        if op == "*":
            _check_number_operands(left, right, line)
            return left * right
        if op == "/":
            _check_number_operands(left, right, line)
            if right == 0:
                raise ToyRuntimeError("Division by zero", line)
            result = left / right
            if isinstance(left, int) and isinstance(right, int) and left % right == 0:
                return int(result)
            return result
        if op == "%":
            _check_number_operands(left, right, line)
            if right == 0:
                raise ToyRuntimeError("Modulo by zero", line)
            return left % right
        if op == "==":
            return _is_equal(left, right)
        if op == "!=":
            return not _is_equal(left, right)
        if op in ("<", "<=", ">", ">="):
            _check_number_operands(left, right, line)
            if op == "<":
                return left < right
            if op == "<=":
                return left <= right
            if op == ">":
                return left > right
            return left >= right

        raise ToyRuntimeError(f"Unknown binary operator '{op}'", line)

    def _eval_call(self, node: Call) -> object:
        callee = self._evaluate(node.callee)
        args = [self._evaluate(arg) for arg in node.args]
        if not isinstance(callee, ToyFunction):
            raise ToyRuntimeError("Can only call functions", node.line)
        return callee.call(args, node.line)

    _EXPRESSION_DISPATCH = {
        Literal: _eval_literal,
        Variable: _eval_variable,
        Assign: _eval_assign,
        Unary: _eval_unary,
        Logical: _eval_logical,
        Binary: _eval_binary,
        Call: _eval_call,
    }


# -- shared helpers -----------------------------------------------------------


def is_truthy(value: object) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    return True


def _is_equal(a: object, b: object) -> bool:
    if isinstance(a, bool) or isinstance(b, bool):
        return type(a) is type(b) and a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return a == b
    return type(a) is type(b) and a == b


def _check_number_operand(value: object, line: int) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ToyRuntimeError(f"Operand must be a number, got {type_name(value)}", line)


def _check_number_operands(left: object, right: object, line: int) -> None:
    _check_number_operand(left, line)
    _check_number_operand(right, line)


def type_name(value: object) -> str:
    if value is None:
        return "nil"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, ToyFunction):
        return "function"
    return type(value).__name__


def stringify(value: object) -> str:
    if value is None:
        return "nil"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)
