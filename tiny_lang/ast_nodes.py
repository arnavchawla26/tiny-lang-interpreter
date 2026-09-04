"""AST node definitions for Toy.

Plain dataclasses -- no visitor-pattern boilerplate. The interpreter
dispatches on ``type(node)`` via a dict, which keeps both this file and
``interpreter.py`` short and easy to extend with a new node type.
"""

from __future__ import annotations

from dataclasses import dataclass, field


class Node:
    """Marker base class for every AST node."""


# -- Expressions --------------------------------------------------------


@dataclass
class Literal(Node):
    value: object
    line: int


@dataclass
class Variable(Node):
    name: str
    line: int


@dataclass
class Assign(Node):
    name: str
    value: Node
    line: int


@dataclass
class Unary(Node):
    op: str
    right: Node
    line: int


@dataclass
class Binary(Node):
    left: Node
    op: str
    right: Node
    line: int


@dataclass
class Logical(Node):
    left: Node
    op: str  # "and" | "or"
    right: Node
    line: int


@dataclass
class Call(Node):
    callee: Node
    args: list[Node]
    line: int


# -- Statements -----------------------------------------------------------


@dataclass
class ExpressionStatement(Node):
    expr: Node
    line: int


@dataclass
class PrintStatement(Node):
    expr: Node
    line: int


@dataclass
class VarDecl(Node):
    name: str
    initializer: Node | None
    line: int


@dataclass
class Block(Node):
    statements: list[Node]
    line: int


@dataclass
class IfStatement(Node):
    condition: Node
    then_branch: Node
    else_branch: Node | None
    line: int


@dataclass
class WhileStatement(Node):
    condition: Node
    body: Node
    line: int


@dataclass
class FunctionDecl(Node):
    name: str
    params: list[str]
    body: list[Node]
    line: int


@dataclass
class ReturnStatement(Node):
    value: Node | None
    line: int


@dataclass
class Program(Node):
    statements: list[Node] = field(default_factory=list)
