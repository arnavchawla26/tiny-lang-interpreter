# tiny-lang-interpreter

A hand-written lexer, recursive-descent parser, and tree-walking interpreter for **Toy** — a small, dynamically-typed toy programming language. No parser-generator, no external interpreter library: every stage (scanning source into tokens, building an AST, walking that AST to execute it) is implemented from scratch in plain Python, in the classic style of Crafting Interpreters' `jlox`.

This is a compilers/PL-fundamentals project, deliberately different in flavor from the CLI linters/analyzers and ML/data-science projects elsewhere in this portfolio.

## What Toy looks like

```
fn fib(n) {
    if (n < 2) {
        return n;
    }
    return fib(n - 1) + fib(n - 2);
}

let i = 0;
while (i < 10) {
    print fib(i);
    i = i + 1;
}
```

More examples live in [`examples/`](examples/): [`fibonacci.toy`](examples/fibonacci.toy), [`fizzbuzz.toy`](examples/fizzbuzz.toy), and [`closures.toy`](examples/closures.toy) (a `make_counter` function that returns a closure with private state).

### Language features

- **Types:** numbers (int and float), strings, booleans, `nil`, and functions as first-class values.
- **Variables:** `let x = 5;` — lexically scoped, block-scoped (`{ ... }` opens a new scope).
- **Control flow:** `if`/`else` (including `else if` chains), `while` loops.
- **Functions:** `fn name(params) { ... }`, with `return`. Functions are closures — they capture the environment they were defined in, not the one they're called from, so a function returned from another function keeps access to that function's local variables (see `examples/closures.toy`).
- **Operators:** `+ - * / %`, comparisons (`< <= > >=`), equality (`== !=`), logical `&& ||` (short-circuiting), unary `- !`.
- **Truthiness:** only `nil` and `false` are falsy — everything else (including `0` and `""`) is truthy, matching Lua/Ruby rather than C/JS/Python.
- **`print`** is a statement, not a function call, to keep the grammar and interpreter simple.
- **Comments:** `# like this`, to end of line.
- Runtime errors (undefined variable, division by zero, wrong argument count, calling a non-function, non-number arithmetic operand, ...) and syntax errors both report a source line number.

### What it deliberately doesn't have (yet)

No arrays/lists, no maps/objects, no `for` loops (use `while`), no classes, no standard library beyond `print`. These are natural follow-ups if the project continues in a future run — see Current status below.

## Tech stack

Pure Python 3.10+, standard library only (`dataclasses`, `enum`) — no parser-generator, no regex-based lexer, no third-party runtime dependency. `pytest` is used for the test suite (dev-only dependency).

## Project layout

```
tiny_lang/
    lexer.py         # source text -> list[Token]
    ast_nodes.py     # AST node dataclasses
    parser.py        # tokens -> AST (recursive descent, precedence climbing)
    environment.py   # lexically-scoped variable bindings, closure chain
    interpreter.py   # tree-walking evaluator, dict-dispatch on node type
    run.py           # lexer -> parser -> interpreter pipeline, shared by CLI/REPL/tests
    cli.py           # `toy script.toy` and the interactive REPL
    errors.py        # LexError / ParseError / ToyRuntimeError, all line-numbered
examples/            # .toy sample programs
tests/               # 79 pytest tests across lexer, parser, interpreter, and CLI
```

## How to run it

```bash
git clone https://github.com/arnavchawla26/tiny-lang-interpreter.git
cd tiny-lang-interpreter
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# run a script
toy examples/fibonacci.toy

# or the interactive REPL
toy
```

Real output, copied verbatim from actually running the commands above:

```
$ toy examples/fibonacci.toy
0
1
1
2
3
5
8
13
21
34

$ toy examples/fizzbuzz.toy
1
2
Fizz
4
Buzz
Fizz
7
8
Fizz
Buzz
11
Fizz
13
14
FizzBuzz
16
17
Fizz
19
Buzz

$ toy examples/closures.toy
1
2
3
1
```

REPL session (bare expressions are echoed automatically, like a real REPL; `print` and statements with a trailing `;`/`{`/`}` are executed as-is):

```
$ toy
tiny-lang REPL. Type 'exit' or Ctrl-D to quit.
toy> let x = 10;
toy> x * 2;
20
toy> print "hi " + x;
hi 10
toy> exit
```

You can also run it without installing, straight from a checkout:

```bash
python -m tiny_lang.cli examples/fibonacci.toy
```

### Running the tests

```bash
pip install -e ".[dev]"
pytest
```

79 tests currently pass, covering: every token type and lexer error case (unterminated strings, unexpected characters, comment handling, line-number tracking); operator precedence, associativity, and every statement/expression grammar rule in the parser, including parse-error cases; interpreter semantics for arithmetic, string concatenation, comparisons, truthiness, short-circuit evaluation, block scoping (including shadowing and that inner blocks don't leak variables outward), recursive functions, and closures (including that two closures created from the same factory function have independent state); and CLI/REPL behavior including a real subprocess end-to-end run of the installed `toy` console script against the example scripts.

## Current status

**v1 — functional and tested.** The full pipeline (lexer → parser → tree-walking interpreter) works end-to-end for the language features listed above: variables, arithmetic, string concatenation, control flow, functions, recursion, and closures. All 79 tests pass, and the three example programs (`fibonacci.toy`, `fizzbuzz.toy`, `closures.toy`) run correctly via both the installed `toy` command and `python -m tiny_lang.cli`.

Natural next steps if this project continues in a future run: array/list literals and indexing, a minimal standard library (`len`, string helpers, `input`), better REPL ergonomics (multi-line input for unfinished blocks), and possibly a simple static pass (e.g. detecting `return` outside a function) before execution.

## License

MIT — see [LICENSE](LICENSE).
