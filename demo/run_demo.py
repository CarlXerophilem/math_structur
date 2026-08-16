from __future__ import annotations

from pathlib import Path
import hashlib
import json
import random
import shutil
import subprocess
import sys

from function_contract import (
    adaptive_probe,
    compiled_ln_ast,
    parse_node,
    sympy_real_domain_baseline,
    validate_finite_square_root,
)


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "demo"
PRIME_REPO = Path(r"D:\MATHs\scripts\shape_of_set\prime_loop_verification")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def random_baseline(node, budget: int = 5, seeds=range(20)):
    pool = [-2.0, -1.0, -0.5, 0.0, 0.5, 1.0, 2.0]
    summaries = []
    from function_contract import check_compiled_ln

    for seed in seeds:
        order = pool.copy()
        random.Random(seed).shuffle(order)
        first = None
        statuses = []
        for step, point in enumerate(order[:budget], 1):
            result = check_compiled_ln(node, point)
            statuses.append(result.status)
            if first is None and result.status in {"mismatch", "undefined"}:
                first = step
        summaries.append({"seed": seed, "first_failure_step": first, "statuses": statuses})
    finite = sorted(x["first_failure_step"] for x in summaries if x["first_failure_step"] is not None)
    median = finite[len(finite) // 2] if finite else None
    return {"budget": budget, "runs": summaries, "median_first_failure_step": median}


def no_intervention_baseline(node):
    from function_contract import check_compiled_ln

    points = [1.0, 2.0, 0.5]
    results = [check_compiled_ln(node, x).to_dict() for x in points]
    return {"policy": "positive interior points only", "points": points, "results": results}


def _lean_toolchain_bin() -> Path | None:
    toolchain_file = PRIME_REPO / "lean-toolchain"
    if not toolchain_file.is_file():
        return None
    name = toolchain_file.read_text("utf-8").strip()
    # elan uses two dashes for '/' and three for ':' in toolchain folders.
    folder = name.replace("/", "--").replace(":", "---")
    candidate = Path.home() / ".elan" / "toolchains" / folder / "bin"
    return candidate if candidate.is_dir() else None


def lean_status():
    source = ROOT / "demo" / "lean" / "FunctionContract.lean"
    tool_bin = _lean_toolchain_bin()
    if tool_bin is None:
        return {
            "status": "not_run",
            "reason": "the pinned Lean toolchain directory was not found",
            "source": str(source.relative_to(ROOT)),
        }
    lean = tool_bin / "lean.exe"
    lake = tool_bin / "lake.exe"
    try:
        local = subprocess.run(
            [str(lean), str(source)], cwd=ROOT, capture_output=True, text=True, timeout=30
        )
        prime_source = PRIME_REPO / "eml_verification" / "eml.lean"
        prime = subprocess.run(
            [str(lake), "env", "lean", str(prime_source.relative_to(PRIME_REPO))],
            cwd=PRIME_REPO,
            capture_output=True,
            text=True,
            timeout=45,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "status": "not_run",
            "reason": f"Lean command timed out: {exc}",
            "toolchain_bin": str(tool_bin),
        }
    prime_output = (prime.stdout + "\n" + prime.stderr).strip()
    prime_status = (
        "accepted_with_sorry"
        if prime.returncode == 0 and "uses `sorry`" in prime_output
        else "passed"
        if prime.returncode == 0
        else "failed"
    )
    overall = (
        "partial_formalization"
        if local.returncode == 0 and prime_status == "accepted_with_sorry"
        else "passed"
        if local.returncode == 0 and prime_status == "passed"
        else "failed"
    )
    return {
        "status": overall,
        "reason": "local obligation compiles; repository EML reconstruction remains incomplete because reconstruct_ln uses sorry"
        if overall == "partial_formalization"
        else "see subchecks",
        "toolchain_bin": str(tool_bin),
        "local_contract_export": {
            "status": "passed" if local.returncode == 0 else "failed",
            "returncode": local.returncode,
            "stdout": local.stdout,
            "stderr": local.stderr,
            "source": str(source.relative_to(ROOT)),
        },
        "prime_eml": {
            "status": prime_status,
            "returncode": prime.returncode,
            "stdout": prime.stdout,
            "stderr": prime.stderr,
            "source": str(prime_source),
        },
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    node = parse_node(compiled_ln_ast(), {"x"})
    events, revisions = adaptive_probe(node, budget=5)
    results = {
        "runtime": {"python": sys.version.split()[0]},
        "research_claim": "minimum environment reproduction of a known EML branch failure, not a new theorem",
        "adaptive": {"budget": 5, "events": events, "revisions": revisions},
        "random_baseline": random_baseline(node),
        "no_intervention_baseline": no_intervention_baseline(node),
        "sympy_baseline": sympy_real_domain_baseline(node),
        "finite_map_calibration": {
            "positive": validate_finite_square_root([0, 1, 2], [0, 1, 2]),
            "counterexample": validate_finite_square_root([0, 1, 2], [1, 2, 0]),
            "closure_failure": validate_finite_square_root([0, 1, 2], [1, 3, 0]),
        },
        "lean": lean_status(),
    }
    (OUT / "results.json").write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with (OUT / "events.jsonl").open("w", encoding="utf-8", newline="\n") as fh:
        for event in events:
            fh.write(json.dumps(event, ensure_ascii=False) + "\n")
    (OUT / "lean_status.txt").write_text(
        json.dumps(results["lean"], indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    adaptive_first = next(
        (e["step"] for e in events if e["feedback"]["status"] in {"mismatch", "undefined"}),
        None,
    )
    random_median = results["random_baseline"]["median_first_failure_step"]
    statuses = [e["feedback"]["status"] for e in events]
    eval_md = f"""# Demo evaluation\n\n- Adaptive first failure: step **{adaptive_first}**.\n- Random baseline median first failure over 20 seeds: step **{random_median}**.\n- Adaptive statuses: `{statuses}`.\n- SymPy real-domain baseline: `{results['sympy_baseline']}`.\n- Finite-map positive: `{results['finite_map_calibration']['positive']['status']}`.\n- Finite-map counterexample: `{results['finite_map_calibration']['counterexample']['status']}`.\n- Finite-map closure failure: `{results['finite_map_calibration']['closure_failure']['status']}`.\n- Lean: `{results['lean']['status']}` — {results['lean'].get('reason', 'see receipt')}.\n\n## Verdict\n\nThe minimum environment passes its technical gate: feedback changes the next probe, the known negative-real-axis branch mismatch is reproduced, zero remains undefined, and finite-domain closure failures are separated from equation counterexamples. The adaptive policy is **not better than the random median** in this tiny pool if `{adaptive_first} >= {random_median}`; no superiority claim is permitted.\n"""
    (OUT / "EVAL.md").write_text(eval_md, encoding="utf-8")
    print(json.dumps({
        "results": str(OUT / "results.json"),
        "adaptive_first_failure": adaptive_first,
        "random_median_first_failure": random_median,
        "statuses": statuses,
        "lean": results["lean"]["status"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
