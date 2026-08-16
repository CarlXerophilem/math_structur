from __future__ import annotations

import json
from pathlib import Path
import subprocess
import threading
from urllib.request import Request, urlopen

import pytest

import serve_panel


PANEL = Path(__file__).resolve().parent


def _post(url: str, payload: dict) -> dict:
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=10) as response:
        assert response.status == 200
        return json.loads(response.read().decode("utf-8"))


def test_static_delivery_has_exactly_two_panels_and_no_export_surface():
    for name in ("index.html", "styles.css", "app.js", "solver_output.schema.json", "lean/ReactionBalance.lean", "lean/IterationContract.lean", "vendor/katex/katex.min.js", "vendor/katex/katex.min.css", "vendor/katex/LICENSE"):
        assert (PANEL / name).is_file()
    assert len(list((PANEL / "vendor" / "katex" / "fonts").glob("*"))) >= 50
    assert not (PANEL / "data.js").exists()
    html = (PANEL / "index.html").read_text("utf-8")
    assert html.count('<button class="tab') == 2
    assert "Math Structurer" in html
    assert "Convincing, reusable target-matching skills for AI research agents." in html
    assert 'data-panel="general"' in html
    assert 'data-panel="iterate"' in html
    assert 'data-panel="mapping"' not in html
    assert "CO2gas+H2gas -- CH3CH2OHgas @best" in html
    assert "用户目标 → 类型与逻辑 → 相连空间 → 专业插件 → 验证器" in html
    assert "ReactionDecomposer" not in html
    assert "vendor/katex/katex.min.js" in html
    assert "特定基算子复合器" in html
    assert "B: ℂ × ℂ<sup>×</sup> → ℂ" in html
    assert "Arg(v)∈(−π,π]" in html
    assert "当前测试域" in html
    assert "基算子复合表达树" in html
    assert "Qwen3-8B-Jailbroken" in html
    assert '<option value="qwen" selected>' in html
    assert 'id="recognition-domain-intent"' in html
    assert 'id="recognition-model"' in html
    assert 'id="recognition-validation"' in html
    assert "函数空间" not in html
    assert "不主张统一代数" in html
    assert "E" + "ML" not in html
    lowered = html.lower()
    assert "export" not in lowered
    assert "download" not in lowered
    assert "导出" not in html


def test_javascript_syntax_and_browser_code_is_local_only():
    result = subprocess.run(["node", "--check", str(PANEL / "app.js")], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    source = (PANEL / "app.js").read_text("utf-8")
    assert "https://" not in source
    assert 'fetch("http' not in source
    assert "fetch('http" not in source


def test_catalyst_demo_fails_closed_then_balances_exactly():
    result = serve_panel.analyze_general({
        "problem": "CO2gas+H2gas -- CH3CH2OHgas @best",
        "basis": "stoichiometric_kernel",
        "dimension": 4,
        "weights": {"activity": 25, "selectivity": 35, "stability": 25, "cost": 15},
    })
    normalized = result["normalized_problem"]
    matrix = result["basis"]["matrix"]
    assert result["status"] == "decomposed"
    assert normalized["input_balance"] == "invalid"
    assert normalized["balanced_equation"] == "2 CO2(g) + 6 H2(g) -> C2H5OH(g) + 3 H2O(g)"
    assert normalized["best_status"].startswith("abstain")
    assert matrix["nu"] == [-2, -6, 1, 3]
    assert matrix["check"] == [0, 0, 0]
    assert len(result["search_targets"]) == 4
    assert result["search_targets"][0]["state"] == "abstract-verified"
    assert all(item["state"] in {"abstract-verified", "metadata-only"} for item in result["search_targets"])
    assert result["standard_math"]["status"] == "typed_but_objective_underdetermined"
    assert "A\\nu=0" in result["standard_math"]["display"]
    assert "冻结前未定义" in result["standard_math"]["display"]
    assert result["target_function"]["nontriviality"] == "unverified_on_candidate_set_without_conditioned_measurements"
    assert result["intermediates"]["status"] == "unknown"
    routes = {item["plugin"]: item for item in result["plugin_route"]}
    assert routes["ReactionDecomposer"]["status"] == "invoked"
    assert routes["BasisOperatorComposer"]["status"] == "not_invoked"
    assert routes["BasisOperatorComposer"]["label"] == "特定基算子复合器"
    assert "不进入标量算子复合" in routes["GeometryPlugin"]["scope"]
    assert [space["id"] for space in result["spaces"]] == ["N", "S", "C", "Y", "G", "P"]


def test_geometry_is_schematic_pd_fe_interface_with_honest_smiles_boundary():
    result = serve_panel.analyze_general({"problem": "CO2gas+H2gas -- CH3CH2OHgas @best"})
    geometry = result["geometry"]
    elements = {node["element"] for node in geometry["nodes"]}
    assert {"Pd", "Fe", "O", "C", "H"}.issubset(elements)
    assert geometry["coordinate_status"] == "illustrative_not_relaxed"
    assert "不主张空间群" in geometry["symmetry"]
    assert "ethanol=CCO" in geometry["smiles"]
    assert "catalyst=N/A" in geometry["smiles"]
    assert "Manim" in geometry["render_contract"]


def test_references_are_clickable_primary_or_doi_entries_without_pdf_paths():
    urls = [entry["url"] for entry in serve_panel.REFERENCES]
    assert "https://hdl.handle.net/2117/118190" in urls
    assert "https://doi.org/10.1016/j.chempr.2020.07.001" in urls
    assert "https://www.alphaxiv.org/docs/mcp" in urls
    assert all(not url.lower().endswith(".pdf") for url in urls)
    assert serve_panel.REFERENCES[0]["evidence_status"] == "abstract_verified"


def test_unregistered_general_request_requires_harness_without_inventing_geometry():
    result = serve_panel.analyze_general({
        "problem": "molecule A binds protein B; infer a post-binding structure",
        "domain": "binding",
        "basis": "hybrid",
        "dimension": 5,
    })
    assert result["status"] == "needs_harness"
    assert result["normalized_problem"]["objective"] == "unresolved"
    assert result["geometry"]["nodes"] == []
    assert result["search_targets"] == []
    assert result["model_receipt"]["calls"] == 0
    assert result["standard_math"]["status"] == "harness_required"
    assert {item["plugin"] for item in result["plugin_route"]} == {"AIHarness", "BasisOperatorComposer", "GeometryPlugin", "Lean4"}


def test_local_codex_alphaxiv_and_lean_interfaces_are_detected_without_calling_models():
    serve_panel.harness_status.cache_clear()
    status = serve_panel.harness_status()
    missing = [name for name in ("codex", "alphaxiv_mcp", "lean") if not status[name]["ready"]]
    if missing:
        pytest.skip(f"optional local harnesses unavailable: {', '.join(missing)}")
    assert status["codex"]["ready"] is True
    assert "codex" in status["codex"]["detail"].lower()
    assert status["codex"]["sandbox"] == "read-only"
    assert status["alphaxiv_mcp"]["ready"] is True
    assert status["alphaxiv_mcp"]["pdf_persistence"] is False
    assert status["lean"]["ready"] is True
    assert status["max_calls_per_run"] == 1
    assert status["model_calls"] == 0


def test_jailbroken_qwen_is_the_only_default_recognition_model():
    installed = [
        "qwen3:8b",
        "hf.co/mradermacher/Qwen3-8B-Jailbroken-GGUF:Q4_K_M",
    ]
    selected, requested = serve_panel._select_qwen_model(installed)
    assert selected == serve_panel.QWEN_JAILBROKEN_MODEL
    assert requested == serve_panel.QWEN_JAILBROKEN_MODEL
    missing, requested = serve_panel._select_qwen_model(["qwen3:8b"])
    assert missing is None
    assert requested == serve_panel.QWEN_JAILBROKEN_MODEL
    alias, requested = serve_panel._select_qwen_model(
        ["hf.co/mradermacher/Qwen3-8B-Jailbroken-GGUF:latest"]
    )
    assert alias is None
    assert requested == serve_panel.QWEN_JAILBROKEN_MODEL
    configured, requested = serve_panel._select_qwen_model(installed, "qwen3:8b")
    assert configured == "qwen3:8b"
    assert requested == "qwen3:8b"


def test_qwen_recognition_is_schema_limited_and_deterministically_gated():
    recognition = serve_panel._validate_recognition({
        "domain": "reaction",
        "intent": "catalyst_search",
        "entities": ["CO2gas", "H2gas", "CH3CH2OHgas"],
        "constraints": [],
        "missing_fields": ["temperature", "pressure", "candidate_space", "objective_measurements", "baseline"],
        "confidence": 0.95,
    })
    gate = serve_panel._recognition_gate(
        "CO2gas+H2gas -- CH3CH2OHgas @best",
        recognition,
    )
    assert gate["status"] == "passed"
    assert gate["effect"] == "route metadata only; exact validators retain authority"
    wrong = dict(recognition, domain="mathematics", intent="half_iterate")
    assert serve_panel._recognition_gate(
        "CO2gas+H2gas -- CH3CH2OHgas @best",
        wrong,
    )["status"] == "rejected"
    with pytest.raises(ValueError, match="additional_properties"):
        serve_panel._validate_recognition({
            **recognition,
            "best_catalyst": "unsupported scientific answer",
        })


def test_runtime_paths_are_portable_and_api_status_redacts_local_absolute_paths():
    source = (PANEL / "serve_panel.py").read_text("utf-8")
    assert "MATH_STRUCTURER_PRIME_REPO" in source
    assert "MATH_STRUCTURER_CROSS_VERIFY" in source
    assert "MATH_STRUCTURER_BASH" in source
    assert "Program Files" not in source
    assert "D:" + "\\MATHs" not in source
    browser_source = (PANEL / "browser_smoke.cjs").read_text("utf-8")
    assert "C:" + "\\\\Program Files" not in browser_source
    assert "discoverChrome" in browser_source
    serve_panel.harness_status.cache_clear()
    serialized = json.dumps(serve_panel.harness_status(), ensure_ascii=False)
    assert str(serve_panel.ROOT) not in serialized
    assert str(Path.home()) not in serialized
    assert str(serve_panel.PRIME_REPO) not in serialized
    assert str(serve_panel.CROSS_VERIFY) not in serialized


def test_specific_basis_operator_negative_real_branch_counterexample_is_two_pi():
    result = serve_panel.evaluate_basis_operator({"template": "log", "x": -1, "tolerance": 1e-10, "domain": "complex_nonzero", "branch": "principal_complex_log"})
    assert result["result"]["status"] == "mismatch"
    assert abs(result["result"]["absolute_error"] - 6.283185307179586) < 1e-12
    assert result["ast"]["op"] == "basis"
    assert result["operator_contract"]["display_signature"] == "B: ℂ × ℂ^× → ℂ"
    assert result["operator_contract"]["log_policy"] == "pointwise_principal_value"
    assert result["operator_contract"]["argument_range"] == "Arg(v) in (-pi, pi]"
    assert result["target_domain"] == "D_f = C^times"
    outside = serve_panel.evaluate_basis_operator({"template": "log", "x": -1, "domain": "positive_real"})
    assert outside["result"]["status"] == "undefined"
    assert "outside the declared current test domain" in outside["result"]["oracle_trace"][0]
    unsupported = serve_panel.evaluate_basis_operator({"template": "sin(x)+x^2", "x": 1})
    assert unsupported["status"] == "unsupported"


def test_finite_iteration_root_checks_closure_before_composition():
    proved = serve_panel.finite_check({"f": [0, 1, 2], "g": [0, 1, 2]})
    refuted = serve_panel.finite_check({"f": [0, 1, 2], "g": [1, 2, 0]})
    invalid = serve_panel.finite_check({"f": [0, 1, 2], "g": [0, 1, 3]})
    assert proved["status"] == "proved_finite"
    assert refuted["status"] == "refuted"
    assert invalid["status"] == "invalid"
    assert invalid["reason"] == "g(D) not subset D"


def test_fixed_lean_files_compile_with_honest_axiom_boundary():
    upstream = serve_panel.PRIME_REPO / "PrimeLoopVerification" / "Basic.lean"
    if serve_panel._lean_executable() is None or not upstream.is_file():
        pytest.skip("optional pinned Lean toolchain or prime-loop source unavailable")
    result = serve_panel.lean_check()
    assert result["status"] == "partial_formalization"
    assert result["results"]["reaction_balance"]["status"] == "passed"
    assert result["results"]["function_contract"]["status"] == "passed"
    assert result["results"]["upstream_basis_reconstruction"]["status"] == "source_contains_axiom"


def test_http_server_serves_local_analysis_health_and_references():
    server = serve_panel.make_server("127.0.0.1", 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        base = f"http://127.0.0.1:{server.server_port}"
        with urlopen(base + "/api/health", timeout=5) as response:
            health = json.loads(response.read().decode("utf-8"))
            assert health["status"] == "ok"
            assert health["model_calls"] == 0
        with urlopen(base + "/api/references", timeout=5) as response:
            references = json.loads(response.read().decode("utf-8"))["references"]
            assert len(references) >= 6
        result = _post(base + "/api/solver/run", {
            "provider": "local",
            "problem": "CO2gas+H2gas -- CH3CH2OHgas @best",
        })
        assert result["normalized_problem"]["input_balance"] == "invalid"
        assert result["model_receipt"]["calls"] == 0
    finally:
        server.shutdown()
        server.server_close()

