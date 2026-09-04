import pytest

from tiny_lang.errors import ToyRuntimeError
from tiny_lang.run import run_source


def run(source):
    result = run_source(source)
    if not result.ok:
        raise AssertionError(f"expected success, got error: {result.error}")
    return result.output


def run_error(source):
    result = run_source(source)
    assert not result.ok, f"expected an error, got output: {result.output}"
    return result.error


# -- arithmetic & literals -------------------------------------------------


def test_arithmetic_precedence():
    assert run("print 1 + 2 * 3;") == ["7"]


def test_integer_division_stays_integer_when_exact():
    assert run("print 6 / 3;") == ["2"]


def test_integer_division_produces_float_when_inexact():
    assert run("print 7 / 2;") == ["3.5"]


def test_modulo():
    assert run("print 7 % 3;") == ["1"]


def test_division_by_zero_is_runtime_error():
    err = run_error("print 1 / 0;")
    assert "division by zero" in err.lower()


def test_string_concatenation_with_plus():
    assert run('print "hello, " + "world";') == ["hello, world"]


def test_number_plus_string_coerces_to_string():
    assert run('print "count: " + 5;') == ["count: 5"]


def test_unary_minus():
    assert run("print -5;") == ["-5"]


def test_unary_not():
    assert run("print !true;") == ["false"]
    assert run("print !false;") == ["true"]
    assert run("print !nil;") == ["true"]


def test_comparison_operators():
    assert run("print 1 < 2;") == ["true"]
    assert run("print 2 <= 2;") == ["true"]
    assert run("print 3 > 2;") == ["true"]
    assert run("print 2 >= 3;") == ["false"]


def test_equality():
    assert run("print 1 == 1;") == ["true"]
    assert run('print "a" == "a";') == ["true"]
    assert run('print "a" == "b";') == ["false"]
    assert run("print 1 == 2;") == ["false"]
    assert run("print nil == nil;") == ["true"]


def test_adding_non_numbers_is_runtime_error():
    err = run_error("print true + false;")
    assert "number" in err.lower()


# -- variables & assignment -----------------------------------------------


def test_var_declaration_and_read():
    assert run("let x = 10; print x;") == ["10"]


def test_var_without_initializer_is_nil():
    assert run("let x; print x;") == ["nil"]


def test_reassignment():
    assert run("let x = 1; x = 2; print x;") == ["2"]


def test_undefined_variable_raises():
    err = run_error("print y;")
    assert "undefined variable" in err.lower()


def test_assign_to_undefined_variable_raises():
    err = run_error("x = 5;")
    assert "undefined variable" in err.lower()


# -- control flow -----------------------------------------------------------


def test_if_true_branch():
    assert run('if (true) { print "yes"; } else { print "no"; }') == ["yes"]


def test_if_false_branch():
    assert run('if (false) { print "yes"; } else { print "no"; }') == ["no"]


def test_if_without_else_when_false_does_nothing():
    assert run('if (false) { print "yes"; }') == []


def test_while_loop_counts_up():
    assert run("let i = 0; while (i < 5) { print i; i = i + 1; }") == ["0", "1", "2", "3", "4"]


def test_logical_and_short_circuits():
    # If short-circuiting is broken, calling f() would raise (undefined y),
    # so this only passes if 'and' never evaluates the right side.
    src = """
    fn f() { return y; }
    print false and f();
    """
    assert run(src) == ["false"]


def test_logical_or_short_circuits():
    src = """
    fn f() { return y; }
    print true or f();
    """
    assert run(src) == ["true"]


def test_logical_and_returns_operand_value_not_bool():
    # Only 'nil' and 'false' are falsy in Toy -- 0 and "" are truthy, so
    # 'and' evaluates and returns the right operand in both cases here.
    assert run('print 0 and "second";') == ["second"]
    assert run('print nil and "second";') == ["nil"]


# -- functions & closures ---------------------------------------------------


def test_function_call_returns_value():
    assert run("fn square(x) { return x * x; } print square(6);") == ["36"]


def test_function_with_no_return_yields_nil():
    assert run("fn f() {} print f();") == ["nil"]


def test_recursive_function():
    src = """
    fn fact(n) {
        if (n <= 1) { return 1; }
        return n * fact(n - 1);
    }
    print fact(5);
    """
    assert run(src) == ["120"]


def test_wrong_arity_raises():
    err = run_error("fn f(a, b) { return a + b; } f(1);")
    assert "expects 2 argument" in err.lower()


def test_closures_capture_enclosing_scope():
    src = """
    fn make_counter() {
        let count = 0;
        fn increment() {
            count = count + 1;
            return count;
        }
        return increment;
    }
    let counter = make_counter();
    print counter();
    print counter();
    print counter();
    """
    assert run(src) == ["1", "2", "3"]


def test_two_closures_have_independent_state():
    src = """
    fn make_counter() {
        let count = 0;
        fn increment() { count = count + 1; return count; }
        return increment;
    }
    let a = make_counter();
    let b = make_counter();
    print a();
    print a();
    print b();
    """
    assert run(src) == ["1", "2", "1"]


def test_calling_a_non_function_raises():
    err = run_error("let x = 5; x();")
    assert "can only call functions" in err.lower()


# -- scoping ------------------------------------------------------------------


def test_block_scope_does_not_leak_inner_variable():
    err = run_error("{ let x = 1; } print x;")
    assert "undefined variable" in err.lower()


def test_inner_scope_can_shadow_outer_variable():
    src = """
    let x = "outer";
    {
        let x = "inner";
        print x;
    }
    print x;
    """
    assert run(src) == ["inner", "outer"]


def test_inner_scope_assignment_mutates_outer_variable():
    src = """
    let x = 1;
    {
        x = 2;
    }
    print x;
    """
    assert run(src) == ["2"]


# -- end-to-end example scripts ---------------------------------------------


def test_fizzbuzz_first_few_lines():
    src = """
    let n = 1;
    while (n <= 5) {
        if (n % 15 == 0) { print "FizzBuzz"; }
        else if (n % 3 == 0) { print "Fizz"; }
        else if (n % 5 == 0) { print "Buzz"; }
        else { print n; }
        n = n + 1;
    }
    """
    assert run(src) == ["1", "2", "Fizz", "4", "Buzz"]


def test_fibonacci_sequence():
    src = """
    fn fib(n) {
        if (n < 2) { return n; }
        return fib(n - 1) + fib(n - 2);
    }
    let i = 0;
    while (i < 8) {
        print fib(i);
        i = i + 1;
    }
    """
    assert run(src) == ["0", "1", "1", "2", "3", "5", "8", "13"]


def test_lexer_or_parse_error_surfaces_through_run_source():
    result = run_source("let x = @;")
    assert not result.ok
    assert "unexpected character" in result.error.lower()
