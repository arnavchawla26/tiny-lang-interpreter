"""End-to-end tests that exercise the actual `toy` console entry point
as a subprocess, plus tests of the CLI/REPL Python functions directly.
"""

import subprocess
import sys
import textwrap

import pytest

from tiny_lang.cli import main, run_script


def write_script(tmp_path, name, source):
    path = tmp_path / name
    path.write_text(textwrap.dedent(source))
    return str(path)


def test_run_script_prints_output(tmp_path, capsys):
    path = write_script(tmp_path, "hello.toy", 'print "hello"; print 1 + 2;')
    exit_code = run_script(path)
    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == "hello\n3\n"


def test_run_script_reports_runtime_error_and_nonzero_exit(tmp_path, capsys):
    path = write_script(tmp_path, "bad.toy", "print y;")
    exit_code = run_script(path)
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Error:" in captured.err


def test_run_script_missing_file_returns_error_code(tmp_path, capsys):
    exit_code = run_script(str(tmp_path / "does_not_exist.toy"))
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Could not read" in captured.err


def test_main_dispatches_to_run_script(tmp_path, capsys):
    path = write_script(tmp_path, "ok.toy", "print 42;")
    exit_code = main([path])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == "42\n"


def test_main_rejects_too_many_arguments(capsys):
    exit_code = main(["a.toy", "b.toy"])
    captured = capsys.readouterr()
    assert exit_code == 2
    assert "Usage" in captured.err


def test_console_entry_point_end_to_end(tmp_path):
    """Runs `python -m tiny_lang.cli <script>` as a real subprocess, the
    same way a user invoking the installed `toy` command would.
    """
    path = write_script(tmp_path, "e2e.toy", "let n = 0; while (n < 3) { print n; n = n + 1; }")
    proc = subprocess.run(
        [sys.executable, "-m", "tiny_lang.cli", path],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert proc.returncode == 0
    assert proc.stdout == "0\n1\n2\n"


def test_example_fizzbuzz_script_runs_end_to_end():
    import pathlib

    example = pathlib.Path(__file__).resolve().parent.parent / "examples" / "fizzbuzz.toy"
    proc = subprocess.run(
        [sys.executable, "-m", "tiny_lang.cli", str(example)],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert proc.returncode == 0
    lines = proc.stdout.splitlines()
    assert lines[0] == "1"
    assert lines[2] == "Fizz"
    assert lines[4] == "Buzz"
    assert lines[14] == "FizzBuzz"


def test_example_closures_script_runs_end_to_end():
    import pathlib

    example = pathlib.Path(__file__).resolve().parent.parent / "examples" / "closures.toy"
    proc = subprocess.run(
        [sys.executable, "-m", "tiny_lang.cli", str(example)],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert proc.returncode == 0
    assert proc.stdout.splitlines() == ["1", "2", "3", "1"]
