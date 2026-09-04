"""Error types shared across the lexer, parser, and interpreter.

All of them carry a 1-based line number so error messages can point the
user at the offending source line, the way a real compiler would.
"""


class ToyError(Exception):
    """Base class for all errors produced while running Toy source."""

    def __init__(self, message: str, line: int | None = None):
        self.message = message
        self.line = line
        if line is not None:
            super().__init__(f"[line {line}] {message}")
        else:
            super().__init__(message)


class LexError(ToyError):
    """Raised when the lexer encounters characters it cannot tokenize."""


class ParseError(ToyError):
    """Raised when the parser encounters an unexpected token sequence."""


class ToyRuntimeError(ToyError):
    """Raised for errors that only surface while executing a program:
    undefined variables, type mismatches, wrong argument counts, etc.
    """


class ReturnSignal(Exception):
    """Internal control-flow signal used to unwind the Python call stack
    when a Toy ``return`` statement executes. Not a user-facing error.
    """

    def __init__(self, value):
        self.value = value
