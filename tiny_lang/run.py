"""High-level "run this source string" helpers shared by the CLI, the
REPL, and the test suite -- one place that wires lexer -> parser ->
interpreter together and turns errors into printable messages.
"""

from __future__ import annotations

from .errors import LexError, ParseError, ToyRuntimeError
from .interpreter import Interpreter
from .lexer import tokenize
from .parser import parse


class ToyResult:
    """Outcome of running a chunk of Toy source: either the printed
    output lines, or an error message -- never both.
    """

    def __init__(self, output: list[str] | None = None, error: str | None = None):
        self.output = output or []
        self.error = error

    @property
    def ok(self) -> bool:
        return self.error is None


def run_source(source: str, interpreter: Interpreter | None = None) -> ToyResult:
    """Run one chunk of Toy source against (optionally) an existing
    interpreter instance, so a REPL can keep state across lines.
    """
    interpreter = interpreter if interpreter is not None else Interpreter()
    try:
        tokens = tokenize(source)
        program = parse(tokens)
        before = len(interpreter._output)
        interpreter.interpret(program)
        return ToyResult(output=interpreter._output[before:])
    except (LexError, ParseError, ToyRuntimeError) as exc:
        return ToyResult(error=str(exc))


def run_file(path: str) -> ToyResult:
    with open(path, "r", encoding="utf-8") as f:
        source = f.read()
    return run_source(source)
