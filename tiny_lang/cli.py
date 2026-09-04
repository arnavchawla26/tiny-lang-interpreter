"""Command-line entry point: run a .toy script, or drop into a REPL.

Usage:
    toy script.toy       # run a script file
    toy                  # start an interactive REPL
    python -m tiny_lang.cli script.toy
"""

from __future__ import annotations

import sys

from .interpreter import Interpreter
from .run import run_source


def run_script(path: str) -> int:
    try:
        with open(path, "r", encoding="utf-8") as f:
            source = f.read()
    except OSError as exc:
        print(f"Could not read '{path}': {exc}", file=sys.stderr)
        return 1

    result = run_source(source)
    for line in result.output:
        print(line)
    if not result.ok:
        print(f"Error: {result.error}", file=sys.stderr)
        return 1
    return 0


def repl() -> int:
    print("tiny-lang REPL. Type 'exit' or Ctrl-D to quit.")
    interpreter = Interpreter()
    while True:
        try:
            line = input("toy> ")
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if line.strip() in ("exit", "quit"):
            return 0
        if not line.strip():
            continue
        # The REPL accepts bare expressions too, by treating a line with
        # no trailing ';' and no block-opening '{' as an expression whose
        # value should be echoed back, like a real REPL would.
        source = line
        echo_expression = not line.rstrip().endswith((";", "{", "}")) and "print" not in line
        if echo_expression:
            source = f"print {line};"

        result = run_source(source, interpreter)
        for out_line in result.output:
            print(out_line)
        if not result.ok:
            print(f"Error: {result.error}")


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) == 0:
        return repl()
    if len(argv) == 1:
        return run_script(argv[0])
    print("Usage: toy [script.toy]", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
