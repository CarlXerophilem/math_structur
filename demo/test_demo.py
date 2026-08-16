import inspect

import pytest

from function_contract import (
    ContractError,
    adaptive_probe,
    check_compiled_ln,
    compiled_ln_ast,
    parse_node,
    sympy_real_domain_baseline,
    validate_finite_square_root,
)


@pytest.fixture
def ln_node():
    return parse_node(compiled_ln_ast(), {"x"})


def test_unknown_operator_fails_closed():
    with pytest.raises(ContractError):
        parse_node({"op": "python", "value": "__import__('os')"}, {"x"})


def test_extra_fields_rejected():
    with pytest.raises(ContractError):
        parse_node({"op": "var", "name": "x", "payload": "ignored?"}, {"x"})


def test_undeclared_variable_rejected():
    with pytest.raises(ContractError):
        parse_node({"op": "var", "name": "y"}, {"x"})


def test_positive_real_matches(ln_node):
    assert check_compiled_ln(ln_node, 2.0).status == "equivalent"


def test_negative_real_branch_counterexample(ln_node):
    result = check_compiled_ln(ln_node, -1.0)
    assert result.status == "mismatch"
    assert result.absolute_error == pytest.approx(2 * 3.141592653589793)


def test_zero_is_undefined(ln_node):
    assert check_compiled_ln(ln_node, 0.0).status == "undefined"


def test_feedback_changes_next_probe(ln_node):
    events, revisions = adaptive_probe(ln_node, budget=3)
    assert [e["action"]["probe"] for e in events[:2]] == [1.0, -1.0]
    assert events[0]["feedback"]["status"] == "equivalent"
    assert events[1]["feedback"]["status"] == "mismatch"
    assert len(revisions) >= 2


def test_sympy_baseline_has_explicit_status(ln_node):
    result = sympy_real_domain_baseline(ln_node)
    assert result["status"] in {"computed", "unknown"}
    if result["status"] == "computed":
        assert "Interval.open(0, oo)" in result["reference_domain"]


def test_finite_square_root_positive():
    assert validate_finite_square_root([0, 1, 2], [0, 1, 2])["status"] == "proved_finite"


def test_finite_square_root_counterexample():
    result = validate_finite_square_root([0, 1, 2], [1, 2, 0])
    assert result["status"] == "refuted"
    assert result["counterexample"]["x"] == 0


def test_finite_map_closure_failure_precedes_composition():
    result = validate_finite_square_root([0, 1, 2], [1, 3, 0])
    assert result["status"] == "invalid"
    assert "not closed" in result["reason"]


def test_runtime_contains_no_eval_or_exec_calls():
    import function_contract

    source = inspect.getsource(function_contract)
    assert "eval(" not in source
    assert "exec(" not in source

