from __future__ import annotations

import cmath
from functools import lru_cache
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sympy as sp
import tempfile
from typing import Any
from urllib.parse import urlparse


PANEL = Path(__file__).resolve().parent
ROOT = PANEL.parent
PRIME_REPO = Path(r"D:\MATHs\scripts\shape_of_set\prime_loop_verification")
CROSS_VERIFY = Path(r"D:\MATHs\scripts\公众号文章\分析\SolveIterativeFunctions\harness\hooks\cross-verify.sh")
CODEX_CONFIG = Path.home() / ".codex" / "config.toml"
SCHEMA = PANEL / "solver_output.schema.json"
MODEL_CALLS = 0


REFERENCES = [
    {
        "id": "CAT1",
        "title": "Remarkable Carbon Dioxide Hydrogenation to Ethanol on a Palladium/Iron Oxide Single-Atom Catalyst",
        "year": 2018,
        "url": "https://hdl.handle.net/2117/118190",
        "doi": "https://doi.org/10.1002/cctc.201800362",
        "role": "abstract verified; Pd1/Fe3O4 literature candidate",
        "evidence_status": "abstract_verified",
    },
    {
        "id": "CAT2",
        "title": "CO2 Hydrogenation to Ethanol over Cu@Na-Beta",
        "year": 2020,
        "url": "https://doi.org/10.1016/j.chempr.2020.07.001",
        "role": "metadata verified; article text not checked",
        "evidence_status": "metadata_only",
    },
    {
        "id": "CAT3",
        "title": "Highly Active and Selective Hydrogenation of CO2 to Ethanol by Ordered Pd-Cu Nanoparticles",
        "year": 2017,
        "url": "https://doi.org/10.1021/jacs.7b03101",
        "role": "metadata verified; no cross-paper ranking",
        "evidence_status": "metadata_only",
    },
    {
        "id": "CAT4",
        "title": "Highly Selective Hydrogenation of CO2 to Ethanol via Designed Bifunctional Ir1-In2O3 Single-Atom Catalyst",
        "year": 2020,
        "url": "https://doi.org/10.1021/jacs.0c08607",
        "role": "metadata verified; article text not checked",
        "evidence_status": "metadata_only",
    },
    {
        "id": "AXMCP",
        "title": "MCP Server Documentation | alphaXiv",
        "year": 2026,
        "url": "https://www.alphaxiv.org/docs/mcp",
        "role": "retrieval interface contract; no PDF persistence",
        "evidence_status": "page_verified",
    },
    {
        "id": "OR1",
        "title": "alphaXiv/openresearch-cli",
        "year": 2026,
        "url": "https://github.com/alphaXiv/openresearch-cli",
        "role": "design reference; CLI is not installed locally",
        "evidence_status": "repository_verified",
    },
    {
        "id": "EML1",
        "title": "All elementary functions from a single binary operator",
        "year": 2026,
        "arxiv_id": "2603.21852",
        "url": "https://www.alphaxiv.org/abs/2603.21852",
        "role": "iteration/debug kernel",
    },
]


def _geometry() -> dict[str, Any]:
    nodes = [
        {"id": "fe0", "element": "Fe", "x": -2.1, "y": -0.8, "z": 0.0, "group": "support"},
        {"id": "ox0", "element": "O", "x": -1.4, "y": 0.0, "z": 0.05, "group": "support"},
        {"id": "fe1", "element": "Fe", "x": -0.7, "y": -0.8, "z": 0.0, "group": "support"},
        {"id": "ox1", "element": "O", "x": 0.0, "y": 0.0, "z": 0.05, "group": "support"},
        {"id": "fe2", "element": "Fe", "x": 0.7, "y": -0.8, "z": 0.0, "group": "support"},
        {"id": "ox2", "element": "O", "x": 1.4, "y": 0.0, "z": 0.05, "group": "support"},
        {"id": "fe3", "element": "Fe", "x": 2.1, "y": -0.8, "z": 0.0, "group": "support"},
        {"id": "pd0", "element": "Pd", "x": 0.0, "y": 0.25, "z": 0.78, "group": "single_atom"},
        {"id": "c0", "element": "C", "x": 0.0, "y": 0.3, "z": 1.72, "group": "adsorbate"},
        {"id": "o0", "element": "O", "x": -0.78, "y": 0.3, "z": 2.02, "group": "adsorbate"},
        {"id": "o1", "element": "O", "x": 0.78, "y": 0.3, "z": 2.02, "group": "adsorbate"},
        {"id": "h0", "element": "H", "x": -1.7, "y": 0.45, "z": 1.28, "group": "reactant"},
        {"id": "h1", "element": "H", "x": -1.25, "y": 0.45, "z": 1.28, "group": "reactant"},
    ]
    edges = [
        ["fe0", "ox0"], ["ox0", "fe1"], ["fe1", "ox1"], ["ox1", "fe2"],
        ["fe2", "ox2"], ["ox2", "fe3"], ["fe1", "pd0"], ["ox1", "pd0"],
        ["fe2", "pd0"], ["pd0", "c0"], ["c0", "o0"], ["c0", "o1"], ["h0", "h1"],
    ]
    return {
        "kind": "surface_reaction_graph",
        "title": "schematic Pd1/Fe3O4 interface motif / CO2 + H2",
        "nodes": nodes,
        "edges": edges,
        "quotient": "R^(3n) / SE(3)",
        "symmetry": "schematic interface graph; no space-group claim",
        "smiles": "CO2=O=C=O; H2=[H][H]; ethanol=CCO; catalyst=N/A (extended solid)",
        "coordinate_status": "illustrative_not_relaxed",
        "render_contract": "nodes+edges -> Manim VGroup / HTML5 SVG+Canvas",
    }


def _weights(payload: dict[str, Any]) -> dict[str, float]:
    raw = payload.get("weights") or {}
    keys = ("activity", "selectivity", "stability", "cost")
    values = {key: max(0.0, float(raw.get(key, 0.25))) for key in keys}
    total = sum(values.values()) or 1.0
    return {key: round(value / total, 4) for key, value in values.items()}


def analyze_general(payload: dict[str, Any]) -> dict[str, Any]:
    problem = str(payload.get("problem", "")).strip()
    basis_name = str(payload.get("basis", "stoichiometric_kernel"))
    dimension = max(1, min(12, int(payload.get("dimension", 3))))
    weights = _weights(payload)
    compact = re.sub(r"\s+", "", problem).lower()
    is_demo = "co2gas+h2gas--ch3ch2ohgas@best" in compact

    if not is_demo:
        return {
            "status": "needs_harness",
            "source": "local_typed_kernel",
            "input": problem,
            "normalized_problem": {
                "type": str(payload.get("domain", "auto")),
                "statement": problem,
                "objective": "unresolved",
                "reaction_natural_language": "awaiting typed decomposition",
            },
            "standard_math": {
                "display": r"q_{NL}\xrightarrow{\mathrm{AI\;parse}}(T,C,B,M,O,G)",
                "logic": r"\exists T,C,B,M,O,G\;\;\mathrm{Typed}(q_{NL},T,C,B,M,O,G)",
                "status": "harness_required",
            },
            "target_function": {
                "display": r"J:\mathcal X\to\mathbb R\cup\{\mathrm{unknown}\}",
                "nontriviality": "unresolved",
                "status": "harness_required",
            },
            "basis": {
                "name": basis_name,
                "dimension": dimension,
                "operator": "Pi_B : X -> R^k",
                "state": "candidate",
            },
            "machine_problems": [
                {"id": "M0", "operator": "type(problem)", "status": "ready", "oracle": "schema"},
                {"id": "M1", "operator": "choose(B from registered_dictionary)", "status": "ready", "oracle": "baseline comparison"},
                {"id": "M2", "operator": "alphaXiv.agentic_paper_retrieval(q)", "status": "harness_required", "oracle": "source URL"},
                {"id": "M3", "operator": "geometry -> R^(3n)/SE(3)", "status": "input_required", "oracle": "coordinate contract"},
                {"id": "M4", "operator": "Lean.check(assumptions -> proposition)", "status": "obligation_only", "oracle": "Lean kernel"},
            ],
            "spaces": [
                {"id": "N", "label": "natural language", "map": "AIParse"},
                {"id": "T", "label": "typed target + logic", "map": "ConstraintCompiler"},
                {"id": "B", "label": "registered basis space", "map": "BasisSelector"},
                {"id": "M", "label": "machine tasks", "map": "PluginRouter"},
                {"id": "O", "label": "oracle/evidence", "map": "Revision"},
                {"id": "G", "label": "2D/3D projection", "map": "GeometryPlugin"},
            ],
            "plugin_route": [
                {"plugin": "AIHarness", "status": "required", "scope": "typed target and logic"},
                {"plugin": "EMLExpander", "status": "gated", "scope": "scalar analytic expressions only; algebraic structure unconfirmed"},
                {"plugin": "GeometryPlugin", "status": "awaiting_typed_geometry", "scope": "2D/3D; never routed through EML"},
                {"plugin": "Lean4", "status": "obligation_only", "scope": "stated proposition under explicit assumptions"},
            ],
            "search_targets": [],
            "geometry": {"kind": "empty", "nodes": [], "edges": []},
            "references": [REFERENCES[4], REFERENCES[5]],
            "lean": {
                "assumptions": ["D is declared", "B belongs to the registered basis dictionary"],
                "proposition": "reduction_preserves declared invariants",
                "status": "not_instantiated",
            },
            "model_receipt": {"provider": "local_typed_kernel", "calls": 0},
        }

    matrix = {
        "rows": ["C", "H", "O"],
        "columns": ["CO2", "H2", "C2H5OH", "H2O"],
        "A": [[1, 0, 2, 0], [0, 2, 6, 2], [2, 0, 1, 1]],
        "nu": [-2, -6, 1, 3],
        "check": [0, 0, 0],
    }
    return {
        "status": "decomposed",
        "source": "local_exact_kernel",
        "input": problem,
        "normalized_problem": {
            "type": "heterogeneous_catalysis_search",
            "input_equation": "CO2(g) + H2(g) -> C2H5OH(g)",
            "input_balance": "invalid",
            "balanced_equation": "2 CO2(g) + 6 H2(g) -> C2H5OH(g) + 3 H2O(g)",
            "directive": "@best",
            "objective": weights,
            "objective_state": "multiobjective_without_observation_table",
            "best_status": "abstain_until_conditions_candidate_space_and_measurements_are_fixed",
            "retrieval_query": "gas-phase CO2 hydrogenation with H2 to ethanol heterogeneous catalyst",
            "retrieval_exclusions": ["electrochemical CO2 reduction", "ethanol reforming", "methanol-only studies"],
            "reaction_natural_language": "在尚未补齐温度、压力、空速和观测表的条件下，检索将二氧化碳与氢气转化为乙醇并伴生水的文献催化剂；当前只列候选，不排名。",
        },
        "standard_math": {
            "display": r"\begin{aligned} &\exists\,c\in\mathcal C_{\mathrm{lit}},\;\nu=(-2,-6,1,3)\in\ker_{\mathbb Z}(A),\\ &A\nu=0,\qquad J(c;\theta)=w^{\mathsf T}y(c\mid\theta),\\ &\operatorname*{arg\,max}_{c\in\mathcal C_{\mathrm{lit}}}J(c;\theta)\;\text{ is undefined until }(\theta,y)\text{ are observed.}\end{aligned}",
            "logic": r"\exists c\in\mathcal C_{\mathrm{lit}}:\;\mathrm{Conserved}(\nu)\land\mathrm{Measured}(y,c,\theta)\land\mathrm{Feasible}(c,\theta)",
            "status": "typed_but_objective_underdetermined",
        },
        "target_function": {
            "display": r"J(c;\theta)=0.25y_{act}+0.35y_{sel}+0.25y_{stab}-0.15y_{cost}",
            "nontriviality": "unverified_on_candidate_set_without_conditioned_measurements",
            "status": "abstain",
        },
        "basis": {
            "name": basis_name,
            "dimension": dimension,
            "operator": "ker_Z(A) + graph/symmetry coordinates",
            "matrix": matrix,
            "coordinates": ["stoichiometry", "site_graph", "SE(3)-quotient", "condition vector"],
        },
        "machine_problems": [
            {"id": "M0", "operator": "ReactionDecomposer.parse(species, phases, directive)", "status": "solved", "output": "typed reaction + invalid input audit", "oracle": "species schema"},
            {"id": "M1", "operator": "primitive_integer_kernel(A)", "status": "solved", "output": "nu=(-2,-6,+1,+3)", "oracle": "A nu = 0"},
            {"id": "M2", "operator": "ReactionDecomposer.intermediate_slots()", "status": "unknown", "output": "I?; no mechanism asserted", "oracle": "mechanism source or microkinetic plugin"},
            {"id": "M3", "operator": "ObjectiveStructurer.audit(argmax_c J(c|theta))", "status": "underdetermined", "output": "abstain", "oracle": "fixed candidate table + condition + measurements"},
            {"id": "M4", "operator": "alphaXiv.agentic_paper_retrieval(q)", "status": "ready", "output": "clickable metadata", "oracle": "URL + paper span"},
            {"id": "M5", "operator": "GeometryPlugin.Phi(c) in R^(3n)/SE(3)", "status": "rendered", "output": "2D/3D graph", "oracle": "coordinate and bond schema"},
            {"id": "M6", "operator": "Lean.check(element_conservation)", "status": "fixed_obligation", "output": "panel/lean/ReactionBalance.lean", "oracle": "Lean kernel"},
        ],
        "spaces": [
            {"id": "N", "label": "reaction language", "map": "ReactionDecomposer"},
            {"id": "S", "label": "stoichiometric kernel ker_Z(A)", "map": "integer kernel"},
            {"id": "C", "label": "literature candidate set", "map": "retrieval"},
            {"id": "Y", "label": "conditioned measurement space", "map": "objective oracle"},
            {"id": "G", "label": "geometry R^(3n)/SE(3)", "map": "GeometryPlugin"},
            {"id": "P", "label": "proof obligations Prop", "map": "Lean4"},
        ],
        "plugin_route": [
            {"plugin": "ReactionDecomposer", "status": "invoked", "scope": "balance, conservation, intermediate slots, target metrics"},
            {"plugin": "EMLExpander", "status": "not_invoked", "scope": "only scalar analytic subexpressions; algebraic structure unconfirmed"},
            {"plugin": "GeometryPlugin", "status": "invoked", "scope": "schematic 2D/3D coordinates; independent of EML"},
            {"plugin": "alphaXiv/Codex", "status": "optional", "scope": "source retrieval; maximum one selected model backend"},
            {"plugin": "Lean4", "status": "fixed_obligation", "scope": "element conservation only"},
        ],
        "intermediates": {
            "status": "unknown",
            "slots": ["CO2 + H2", "I?", "C2H5OH + H2O"],
            "claim": "no intermediate mechanism is asserted by the local kernel",
        },
        "search_targets": [
            {"label": "Pd1/Fe3O4 single-atom interface", "state": "abstract-verified", "query": "gas-phase CO2 hydrogenation to ethanol", "url": "https://hdl.handle.net/2117/118190"},
            {"label": "Cu@Na-Beta", "state": "metadata-only", "query": "CO2 hydrogenation to ethanol", "url": "https://doi.org/10.1016/j.chempr.2020.07.001"},
            {"label": "ordered Pd-Cu nanoparticles", "state": "metadata-only", "query": "CO2 hydrogenation to ethanol", "url": "https://doi.org/10.1021/jacs.7b03101"},
            {"label": "Ir1-In2O3 single-atom catalyst", "state": "metadata-only", "query": "CO2 hydrogenation to ethanol", "url": "https://doi.org/10.1021/jacs.0c08607"},
        ],
        "geometry": _geometry(),
        "references": REFERENCES[:6],
        "lean": {
            "assumptions": ["species atom counts are Nat-valued", "reaction coefficients are nonnegative integers"],
            "proposition": "2 CO2 + 6 H2 and C2H5OH + 3 H2O have equal C/H/O counts",
            "status": "fixed_obligation",
        },
        "model_receipt": {"provider": "local_exact_kernel", "calls": 0},
    }


def _complex(value: complex) -> dict[str, float]:
    return {"real": float(value.real), "imag": float(value.imag)}


def evaluate_eml(payload: dict[str, Any]) -> dict[str, Any]:
    template = str(payload.get("template", "log"))
    x = float(payload.get("x", -1))
    tolerance = float(payload.get("tolerance", 1e-10))
    if template not in {"log", "exp", "identity"}:
        return {"status": "unsupported", "result": {"status": "unknown", "oracle_trace": ["template not in whitelist"]}}
    try:
        z = complex(x, 0.0)
        if template == "log":
            if x == 0:
                raise ValueError("Log(0) undefined")
            one = sp.Integer(1)
            symbol = sp.Symbol("x")
            inner = sp.Add(sp.exp(one, evaluate=False), -sp.log(symbol, evaluate=False), evaluate=False)
            middle = sp.Add(sp.exp(inner, evaluate=False), -sp.log(one, evaluate=False), evaluate=False)
            expression = sp.Add(sp.exp(one, evaluate=False), -sp.log(middle, evaluate=False), evaluate=False)
            exact_input = sp.Rational(str(x))
            compiled_symbolic = expression.subs(symbol, exact_input)
            reference_symbolic = sp.log(exact_input)
            compiled = complex(sp.N(compiled_symbolic, 30))
            reference = complex(sp.N(reference_symbolic, 30))
            recursive_inner = cmath.exp(1) - cmath.log(z)
            recursive_middle = cmath.exp(recursive_inner) - cmath.log(1)
            recursive_auxiliary = cmath.exp(1) - cmath.log(recursive_middle)
            ast = {"op": "eml", "left": {"op": "1"}, "right": {"op": "eml", "left": {"op": "eml", "left": {"op": "1"}, "right": {"op": "x"}}, "right": {"op": "1"}}}
        elif template == "exp":
            compiled = cmath.exp(z) - cmath.log(1)
            reference = cmath.exp(z)
            ast = {"op": "eml", "left": {"op": "x"}, "right": {"op": "1"}}
        else:
            compiled = z
            reference = z
            ast = {"op": "x"}
        error = abs(compiled - reference)
        status = "equivalent" if error <= tolerance else "mismatch"
        trace = [f"compiled={compiled!r}", f"reference={reference!r}", f"abs_error={error:.16g}"]
        if template == "log":
            trace = [
                "branch_policy=principal_complex_log",
                "compiled_backend=sympy_symbolic_then_numeric",
                f"compiled_symbolic={compiled_symbolic}",
                f"reference_symbolic={reference_symbolic}",
                f"recursive_cmath_auxiliary={recursive_auxiliary!r}",
                f"abs_error={error:.16g}",
            ]
        return {
            "status": "ok",
            "result": {
                "status": status,
                "compiled_value": _complex(compiled),
                "reference_value": _complex(reference),
                "absolute_error": float(error),
                "counterexample": x if status == "mismatch" else None,
                "oracle_trace": trace,
            },
            "ast": ast,
        }
    except Exception as exc:
        return {"status": "ok", "result": {"status": "undefined", "absolute_error": None, "counterexample": x, "oracle_trace": [str(exc)]}, "ast": {"op": template}}


def finite_check(payload: dict[str, Any]) -> dict[str, Any]:
    f = [int(value) for value in payload.get("f", [])]
    g = [int(value) for value in payload.get("g", [])]
    if not f or len(f) != len(g):
        return {"status": "invalid", "reason": "|f| != |g| or empty"}
    n = len(f)
    for name, mapping in (("f", f), ("g", g)):
        for index, value in enumerate(mapping):
            if value < 0 or value >= n:
                return {"status": "invalid", "reason": f"{name}(D) not subset D", "counterexample": {"x": index, "value": value}}
    for index in range(n):
        if g[g[index]] != f[index]:
            return {"status": "refuted", "reason": "g(g(x)) != f(x)", "counterexample": {"x": index, "ggx": g[g[index]], "fx": f[index]}}
    return {"status": "proved_finite", "reason": "exhaustive finite-domain check", "domain_size": n}


def iterate_check(payload: dict[str, Any]) -> dict[str, Any]:
    kind = str(payload.get("kind", "eml"))
    if kind == "finite":
        return {"kind": kind, "result": finite_check(payload), "obligation": "g(D) subseteq D and forall x in D, g(g(x))=f(x)"}
    if kind == "eml":
        result = evaluate_eml(payload)
        result["kind"] = kind
        return result
    return {
        "kind": kind,
        "status": "obligation_only",
        "result": {"status": "unknown", "oracle_trace": ["no unrestricted inverse/iteration solver invoked"]},
        "obligation": str(payload.get("relation", "g^n=f")),
        "assumptions": str(payload.get("assumptions", "D fixed; closure declared")),
    }


def _lean_bin() -> Path | None:
    toolchain_file = PRIME_REPO / "lean-toolchain"
    if not toolchain_file.is_file():
        return None
    name = toolchain_file.read_text("utf-8").strip()
    folder = name.replace("/", "--").replace(":", "---")
    candidate = Path.home() / ".elan" / "toolchains" / folder / "bin"
    return candidate if candidate.is_dir() else None


def _run(command: list[str], cwd: Path, timeout: int) -> dict[str, Any]:
    try:
        result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        return {"returncode": result.returncode, "stdout": result.stdout, "stderr": result.stderr}
    except subprocess.TimeoutExpired as exc:
        return {"returncode": None, "stdout": exc.stdout or "", "stderr": f"timeout after {timeout}s"}
    except OSError as exc:
        return {"returncode": None, "stdout": "", "stderr": str(exc)}


def lean_check() -> dict[str, Any]:
    tool_bin = _lean_bin()
    if tool_bin is None:
        return {"status": "unavailable", "summary": "pinned Lean toolchain not found", "results": {}}
    lean = tool_bin / "lean.exe"
    lake = tool_bin / "lake.exe"
    reaction = _run([str(lean), str(PANEL / "lean" / "ReactionBalance.lean")], ROOT, 30)
    contract = _run([str(lean), str(ROOT / "demo" / "lean" / "FunctionContract.lean")], ROOT, 30)
    prime = _run([str(lake), "env", "lean", "eml_verification/eml.lean"], PRIME_REPO, 50)
    prime_output = f"{prime['stdout']}\n{prime['stderr']}"
    prime_status = "accepted_with_sorry" if prime["returncode"] == 0 and "uses `sorry`" in prime_output else "passed" if prime["returncode"] == 0 else "failed"
    results = {
        "reaction_balance": {"status": "passed" if reaction["returncode"] == 0 else "failed", **reaction},
        "function_contract": {"status": "passed" if contract["returncode"] == 0 else "failed", **contract},
        "prime_eml": {"status": prime_status, **prime},
    }
    overall = "partial_formalization" if results["reaction_balance"]["status"] == "passed" and results["function_contract"]["status"] == "passed" and prime_status == "accepted_with_sorry" else "passed" if all(item["status"] == "passed" for item in results.values()) else "failed"
    return {
        "status": overall,
        "toolchain": "leanprover/lean4:v4.29.0-rc6",
        "summary": "reaction balance and local contract pass; upstream reconstruct_ln remains accepted_with_sorry" if overall == "partial_formalization" else "see results",
        "results": results,
    }


def _probe(command: str, args: list[str]) -> dict[str, Any]:
    path = shutil.which(command)
    if not path:
        return {"ready": False, "path": None, "detail": "not found"}
    invocation = [path, *args]
    if Path(path).suffix.lower() in {".cmd", ".bat"}:
        invocation = [os.environ.get("COMSPEC", "cmd.exe"), "/d", "/s", "/c", subprocess.list2cmdline(invocation)]
    result = _run(invocation, PANEL, 8)
    output = (result.get("stdout", "") + result.get("stderr", "")).strip().splitlines()
    return {"ready": result["returncode"] == 0, "path": path, "detail": output[0][:180] if output else f"exit {result['returncode']}"}


@lru_cache(maxsize=1)
def harness_status() -> dict[str, Any]:
    codex = _probe("codex.cmd", ["--version"])
    deepseek = _probe("deepseek.cmd", ["--version"])
    bash = shutil.which("bash.exe") or shutil.which("bash") or r"C:\Program Files\Git\bin\bash.exe"
    deepseek_harness = bool(Path(bash).is_file() and CROSS_VERIFY.is_file() and os.environ.get("DEEPSEEK_API_KEY"))
    alphaxiv_configured = CODEX_CONFIG.is_file() and "[mcp_servers.alphaxiv]" in CODEX_CONFIG.read_text("utf-8", errors="ignore")
    return {
        "codex": {**codex, "scope": "local CLI; configured model backend may be remote", "approval": "never", "sandbox": "read-only"},
        "deepseek_cli": deepseek,
        "deepseek_harness": {"ready": deepseek_harness, "script": str(CROSS_VERIFY), "credential_present": bool(os.environ.get("DEEPSEEK_API_KEY"))},
        "alphaxiv_mcp": {"ready": alphaxiv_configured, "url": "https://api.alphaxiv.org/mcp/v1", "transport": "Streamable HTTP via Codex MCP bridge", "pdf_persistence": False},
        "openresearch_cli": _probe("orx", ["--version"]),
        "lean": {"ready": _lean_bin() is not None, "toolchain": "leanprover/lean4:v4.29.0-rc6"},
        "model_calls": MODEL_CALLS,
        "max_calls_per_run": 1,
    }


def _solver_prompt(payload: dict[str, Any]) -> str:
    return f"""You are the structured solver adapter for Math Structurer.
Return exactly one JSON object conforming to the supplied output schema.
Translate the natural-language target into typed targets, explicit logic, constraints, connected spaces, a registered finite basis, and machine-checkable subproblems.
Use alphaXiv MCP for literature reading when available. Do not download or save PDFs. Return clickable source URLs.
Do not call a catalyst 'best' unless candidate space, conditions, objective, measurements, and baseline are all explicit.
Lean may validate only a stated formal proposition under listed assumptions; never assert the scientific conclusion as an axiom.
EML is only a heuristic Exp-Minus-Log tree expander for eligible scalar analytic subexpressions; its algebraic structure is unconfirmed. Never route reaction decomposition or 3D geometry through EML.
Use a domain plugin such as ReactionDecomposer before any mathematical expander, and route coordinates to GeometryPlugin.
Problem: {payload.get('problem', '')}
Domain: {payload.get('domain', 'auto')}
Basis: {payload.get('basis', 'hybrid')}
Dimension: {payload.get('dimension', 3)}
Weights: {json.dumps(_weights(payload), ensure_ascii=False)}
The exact demo string must first undergo atom-balance and objective-completeness checks.
"""


def _parse_json(text: str) -> dict[str, Any]:
    text = text.strip()
    try:
        value = json.loads(text)
        if isinstance(value, dict):
            return value
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("model output did not contain a JSON object")
    value = json.loads(match.group(0))
    if not isinstance(value, dict):
        raise ValueError("model output must be an object")
    return value


def _run_codex(payload: dict[str, Any]) -> dict[str, Any]:
    codex = shutil.which("codex.cmd") or shutil.which("codex")
    if not codex:
        raise RuntimeError("codex CLI not found")
    with tempfile.TemporaryDirectory(prefix="function-basis-codex-") as temp:
        out = Path(temp) / "last.json"
        args = [codex, "-a", "never", "exec", "--ephemeral", "--sandbox", "read-only", "--skip-git-repo-check", "-C", str(ROOT), "--output-schema", str(SCHEMA), "-o", str(out), "-"]
        if Path(codex).suffix.lower() in {".cmd", ".bat"}:
            command = [os.environ.get("COMSPEC", "cmd.exe"), "/d", "/s", "/c", subprocess.list2cmdline(args)]
        else:
            command = args
        result = subprocess.run(command, input=_solver_prompt(payload), cwd=ROOT, capture_output=True, text=True, timeout=180)
        if result.returncode != 0:
            raise RuntimeError((result.stderr or result.stdout or f"codex exit {result.returncode}")[-1200:])
        text = out.read_text("utf-8") if out.is_file() else result.stdout
        return _parse_json(text)


def _run_deepseek(payload: dict[str, Any]) -> dict[str, Any]:
    if not os.environ.get("DEEPSEEK_API_KEY"):
        raise RuntimeError("DEEPSEEK_API_KEY is not configured")
    bash = shutil.which("bash.exe") or shutil.which("bash") or r"C:\Program Files\Git\bin\bash.exe"
    if not Path(bash).is_file() or not CROSS_VERIFY.is_file():
        raise RuntimeError("DeepSeek cross-verify harness is unavailable")
    env = os.environ.copy()
    env.setdefault("AUTO_DEV_CROSS_MODEL", "deepseek-chat")
    result = subprocess.run([bash, str(CROSS_VERIFY)], input=_solver_prompt(payload), cwd=ROOT, env=env, capture_output=True, text=True, timeout=90)
    if result.returncode != 0:
        raise RuntimeError((result.stderr or result.stdout or f"deepseek harness exit {result.returncode}")[-1200:])
    return _parse_json(result.stdout)


def solver_run(payload: dict[str, Any]) -> dict[str, Any]:
    global MODEL_CALLS
    provider = str(payload.get("provider", "local"))
    if provider == "local":
        return analyze_general(payload)
    status = harness_status()
    if provider == "auto":
        provider = "codex" if status["codex"]["ready"] else "deepseek" if status["deepseek_harness"]["ready"] else "local"
    if provider == "local":
        return analyze_general(payload)
    if provider not in {"codex", "deepseek"}:
        raise ValueError("provider must be local, auto, codex, or deepseek")
    MODEL_CALLS += 1
    try:
        result = _run_codex(payload) if provider == "codex" else _run_deepseek(payload)
        result.setdefault("model_receipt", {})
        result["model_receipt"].update({"provider": provider, "calls": 1, "max_calls": 1, "pdf_saved": False})
        return result
    except Exception:
        MODEL_CALLS -= 1
        raise


def health() -> dict[str, Any]:
    harness = harness_status()
    return {
        "status": "ok",
        "python": os.sys.version.split()[0],
        "panel": "math-structurer.v0.4",
        "codex_ready": harness["codex"]["ready"],
        "deepseek_harness_ready": harness["deepseek_harness"]["ready"],
        "alphaxiv_ready": harness["alphaxiv_mcp"]["ready"],
        "lean_toolchain": harness["lean"]["toolchain"] if harness["lean"]["ready"] else None,
        "model_calls": MODEL_CALLS,
    }


class Handler(SimpleHTTPRequestHandler):
    server_version = "MathStructurerPanel/0.4"

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, directory=str(PANEL), **kwargs)

    def log_message(self, _format: str, *_args: Any) -> None:
        return

    def _json(self, payload: dict[str, Any], status: int = HTTPStatus.OK) -> None:
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(raw)

    def _body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length > 128_000:
            raise ValueError("request body too large")
        raw = self.rfile.read(length)
        return json.loads(raw.decode("utf-8")) if raw else {}

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/api/health":
            self._json(health())
            return
        if path == "/api/harness/status":
            self._json(harness_status())
            return
        if path == "/api/references":
            self._json({"references": REFERENCES})
            return
        super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        try:
            body = self._body()
            if path == "/api/solver/run":
                self._json(solver_run(body))
            elif path == "/api/general/analyze":
                self._json(analyze_general(body))
            elif path == "/api/iterate/check":
                self._json(iterate_check(body))
            elif path == "/api/lean/check":
                self._json(lean_check())
            else:
                self._json({"error": "not found"}, HTTPStatus.NOT_FOUND)
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            self._json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
        except subprocess.TimeoutExpired:
            self._json({"error": "solver timeout"}, HTTPStatus.GATEWAY_TIMEOUT)
        except Exception as exc:
            self._json({"error": str(exc)}, HTTPStatus.SERVICE_UNAVAILABLE)


def make_server(host: str = "127.0.0.1", port: int = 8766) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), Handler)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8766)
    args = parser.parse_args()
    server = make_server(args.host, args.port)
    print(f"Math Structurer: http://{args.host}:{server.server_port}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
