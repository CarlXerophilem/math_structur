"""A deliberately small, whitelist-only FunctionContract runtime.

The code supports only constants, declared variables, and the EML operator.
It does not parse Python expressions or natural language.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Iterable
import cmath
import math

import sympy as sp
from sympy.calculus.util import continuous_domain


ALLOWED_OPS = {"const", "var", "eml"}


class ContractError(ValueError):
    """Raised when a contract is structurally invalid or leaves the whitelist."""


@dataclass(frozen=True)
class Node:
    op: str
    value: float | int | None = None
    name: str | None = None
    left: "Node | None" = None
    right: "Node | None" = None


@dataclass
class CheckResult:
    status: str
    input: float
    compiled_value: dict[str, float] | None
    reference_value: dict[str, float] | None
    absolute_error: float | None
    reason: str
    oracle_trace: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def parse_node(data: Any, allowed_variables: set[str]) -> Node:
    """Parse a JSON-like AST without executing input text."""
    if not isinstance(data, dict):
        raise ContractError("each AST node must be an object")
    extra = set(data) - {"op", "value", "name", "left", "right"}
    if extra:
        raise ContractError(f"unexpected AST fields: {sorted(extra)}")
    op = data.get("op")
    if op not in ALLOWED_OPS:
        raise ContractError(f"operator is not whitelisted: {op!r}")
    if op == "const":
        value = data.get("value")
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ContractError("const.value must be a finite number")
        if not math.isfinite(float(value)):
            raise ContractError("const.value must be finite")
        return Node(op="const", value=value)
    if op == "var":
        name = data.get("name")
        if name not in allowed_variables:
            raise ContractError(f"undeclared variable: {name!r}")
        return Node(op="var", name=name)
    if "left" not in data or "right" not in data:
        raise ContractError("eml requires left and right children")
    return Node(
        op="eml",
        left=parse_node(data["left"], allowed_variables),
        right=parse_node(data["right"], allowed_variables),
    )


def compiled_ln_ast() -> dict[str, Any]:
    """EML tree for ln(x) reported in E1."""
    one = {"op": "const", "value": 1}
    x = {"op": "var", "name": "x"}
    return {
        "op": "eml",
        "left": one,
        "right": {
            "op": "eml",
            "left": {"op": "eml", "left": one, "right": x},
            "right": one,
        },
    }


def eval_complex(node: Node, env: dict[str, complex], trace: list[str]) -> complex:
    if node.op == "const":
        return complex(node.value)
    if node.op == "var":
        if node.name not in env:
            raise ContractError(f"missing variable value: {node.name}")
        return complex(env[node.name])
    assert node.left is not None and node.right is not None
    left = eval_complex(node.left, env, trace)
    right = eval_complex(node.right, env, trace)
    if right == 0:
        trace.append("eml denominator/log argument reached zero")
        raise ZeroDivisionError("principal complex log is undefined at zero")
    value = cmath.exp(left) - cmath.log(right)
    trace.append(f"eml({left!r}, {right!r}) -> {value!r}")
    return value


def encode_complex(value: complex) -> dict[str, float]:
    return {"real": float(value.real), "imag": float(value.imag)}


def check_compiled_ln(node: Node, x: float, tolerance: float = 1e-10) -> CheckResult:
    trace = ["branch_policy=principal_complex_log", "compiled_backend=sympy_symbolic_then_numeric"]
    symbol = sp.Symbol("x")
    expression = to_sympy(node, {"x": symbol})
    exact_input = sp.Rational(str(x))
    try:
        compiled_symbolic = expression.subs(symbol, exact_input)
        reference_symbolic = sp.log(exact_input)
        invalid_atoms = (sp.zoo, sp.nan, sp.oo, -sp.oo)
        if any(compiled_symbolic.has(atom) for atom in invalid_atoms) or any(
            reference_symbolic.has(atom) for atom in invalid_atoms
        ):
            raise ValueError("symbolic result contains an undefined or infinite value")
        compiled = complex(sp.N(compiled_symbolic, 30))
        reference = complex(sp.N(reference_symbolic, 30))
        trace.append(f"compiled_symbolic={compiled_symbolic}")
        trace.append(f"reference_symbolic={reference_symbolic}")
        # Record a second backend because signed-zero/approach-direction behavior
        # is itself part of the branch-policy problem. It is not used as proof.
        try:
            recursive = eval_complex(node, {"x": complex(x)}, trace=[])
            trace.append(f"recursive_cmath_auxiliary={recursive!r}")
        except (ZeroDivisionError, ValueError, OverflowError) as exc:
            trace.append(f"recursive_cmath_auxiliary_error={type(exc).__name__}: {exc}")
    except (ZeroDivisionError, ValueError, OverflowError, TypeError) as exc:
        return CheckResult(
            status="undefined",
            input=x,
            compiled_value=None,
            reference_value=None,
            absolute_error=None,
            reason=f"compiled expression undefined: {type(exc).__name__}: {exc}",
            oracle_trace=trace,
        )
    error = abs(compiled - reference)
    status = "equivalent" if error <= tolerance else "mismatch"
    reason = (
        "values agree within tolerance"
        if status == "equivalent"
        else "principal-branch values differ; inspect negative-real-axis branch"
    )
    return CheckResult(
        status=status,
        input=x,
        compiled_value=encode_complex(compiled),
        reference_value=encode_complex(reference),
        absolute_error=float(error),
        reason=reason,
        oracle_trace=trace,
    )


def sympy_real_domain_baseline(node: Node) -> dict[str, str]:
    x = sp.Symbol("x", real=True)
    expression = to_sympy(node, {"x": x})
    try:
        compiled_domain = continuous_domain(expression, x, sp.S.Reals)
        reference_domain = continuous_domain(sp.log(x), x, sp.S.Reals)
        return {
            "status": "computed",
            "compiled_domain": str(compiled_domain),
            "reference_domain": str(reference_domain),
            "note": "real continuity baseline; it does not compare complex principal-branch values",
        }
    except NotImplementedError as exc:
        return {"status": "unknown", "reason": f"NotImplementedError: {exc}"}


def to_sympy(node: Node, symbols: dict[str, sp.Symbol]) -> sp.Expr:
    if node.op == "const":
        return sp.Integer(node.value) if isinstance(node.value, int) else sp.Float(node.value)
    if node.op == "var":
        return symbols[node.name]
    assert node.left is not None and node.right is not None
    left = to_sympy(node.left, symbols)
    right = to_sympy(node.right, symbols)
    return sp.Add(
        sp.exp(left, evaluate=False),
        -sp.log(right, evaluate=False),
        evaluate=False,
    )


def adaptive_probe(node: Node, budget: int = 5) -> tuple[list[dict[str, Any]], list[str]]:
    """A small feedback-changing policy, not an LLM and not claimed optimal."""
    if budget < 1:
        return [], ["budget exhausted before first action"]
    queue = [1.0]
    visited: set[float] = set()
    events: list[dict[str, Any]] = []
    revisions = ["H0: uncorrected compiled ln matches principal log for every nonzero real x"]

    while queue and len(events) < budget:
        point = queue.pop(0)
        if point in visited:
            continue
        visited.add(point)
        result = check_compiled_ln(node, point)
        event = {
            "step": len(events) + 1,
            "action": {"probe": point},
            "feedback": result.to_dict(),
        }
        events.append(event)

        if result.status == "equivalent" and point > 0 and -point not in visited:
            queue.insert(0, -point)
            event["next_action_reason"] = "positive point agreed; probe sign-reflected point for branch asymmetry"
        elif result.status == "mismatch":
            for candidate in (-2.0, -0.5, 0.0):
                if candidate not in visited and candidate not in queue:
                    queue.append(candidate)
            if not any("negative real axis" in r for r in revisions):
                revisions.append(
                    "H1: mismatch is supported on the negative real axis; restrict the uncorrected contract to x>0 or supply a branch correction"
                )
            event["next_action_reason"] = "mismatch found; probe neighboring negative points and the zero boundary"
        elif result.status == "undefined":
            revisions.append("H2: x=0 is excluded because principal log is undefined")
            event["next_action_reason"] = "record excluded boundary; do not coerce undefined to false"
    return events, revisions


def validate_finite_square_root(f: Iterable[int], g: Iterable[int]) -> dict[str, Any]:
    f_list = list(f)
    g_list = list(g)
    if len(f_list) != len(g_list) or not f_list:
        return {"status": "invalid", "reason": "f and g must have the same positive finite domain"}
    n = len(f_list)
    for name, mapping in (("f", f_list), ("g", g_list)):
        for i, value in enumerate(mapping):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value < n:
                return {
                    "status": "invalid",
                    "reason": f"{name} is not closed on D=0..{n-1}",
                    "counterexample": {"input": i, "output": value},
                }
    for i in range(n):
        lhs = g_list[g_list[i]]
        rhs = f_list[i]
        if lhs != rhs:
            return {
                "status": "refuted",
                "reason": "g(g(x)) != f(x)",
                "counterexample": {"x": i, "g_g_x": lhs, "f_x": rhs},
            }
    return {"status": "proved_finite", "reason": "checked every x in the declared finite domain", "domain_size": n}
