"""Lexical scoping for Toy, implemented as a chain of Environments.

Each Environment holds one scope's variable bindings and a reference to
its enclosing scope. Lookups and assignments walk outward through the
chain, which is what gives Toy functions real closures: a function
captures the Environment active at its definition site, not at its call
site.
"""

from __future__ import annotations

from .errors import ToyRuntimeError


class Environment:
    def __init__(self, enclosing: "Environment | None" = None):
        self.enclosing = enclosing
        self.values: dict[str, object] = {}

    def define(self, name: str, value: object) -> None:
        """Bind a new variable in *this* scope (used by 'let' and params)."""
        self.values[name] = value

    def get(self, name: str, line: int) -> object:
        if name in self.values:
            return self.values[name]
        if self.enclosing is not None:
            return self.enclosing.get(name, line)
        raise ToyRuntimeError(f"Undefined variable '{name}'", line)

    def assign(self, name: str, value: object, line: int) -> None:
        """Assign to an *existing* binding, walking outward if needed.
        Unlike ``define``, this never creates a new variable -- assigning
        to an unknown name is a runtime error, matching 'let'-scoped
        languages like JavaScript's strict mode.
        """
        if name in self.values:
            self.values[name] = value
            return
        if self.enclosing is not None:
            self.enclosing.assign(name, value, line)
            return
        raise ToyRuntimeError(f"Undefined variable '{name}'", line)
