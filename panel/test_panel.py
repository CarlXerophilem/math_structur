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
    for name in ("index.html", "styles.css", "app.js", "solver_output.schema.json", "lean/IterationContract.lean", "vendor/katex/katex.min.js", "vendor/katex/katex.min.css", "vendor/katex/LICENSE"):
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
    assert "用户目标 → 反应物／产物 → 文献／公共数据库 → 来源化能量与几何 → 稳定排序" in html
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


def test_catalyst_demo_exposes_core_records_and_best_changes_order_only():
    base_problem = "CO2gas+H2gas -- CH3CH2OHgas"
    source_order = serve_panel.analyze_general({"problem": base_problem})
    sorted_result = serve_panel.analyze_general({"problem": base_problem + " @best"})

    for result in (source_order, sorted_result):
        assert [item["formula"] for item in result["reactants"]] == ["CO2", "H2"]
        assert [item["formula"] for item in result["products"]] == ["C2H6O"]
        assert result["reaction_energy"]["value"] is None
        assert result["reaction_energy"]["unit"] is None
        assert result["reaction_energy"]["status"] == "unknown_no_comparable_record"
        assert result["possibilities"]["blocking"] is False
        for name in ("temperature", "pressure", "candidate_domain", "metrics", "baseline"):
            assert result["possibilities"][name]["value"] is None
        assert result["database_receipt"]["external_requests"] == 0
        assert {item["id"] for item in result["database_connectors"]} >= {
            "pubchem", "optimade_mp", "catalysis_hub", "oc20", "crossref", "openalex"
        }
        assert len(result["search_targets"]) == 5
        assert all(item["reaction_energy"]["value"] is None for item in result["search_targets"])
        assert all(item["state"] in {"abstract_verified", "metadata_only"} for item in result["search_targets"])
        signal = result["discovery_signal"]
        assert signal["type"] == "source_coverage_gap_and_problem_definition_revision"
        assert signal["scientific_discovery"] is False
        assert "Catalysis-Hub" in signal["next_action"]
    assert "拒绝或缩小" in signal["falsification"]

    assert source_order["status"] == "retrieved"
    assert source_order["sort"]["requested"] is False
    assert source_order["sort"]["status"] == "source_order"
    assert sorted_result["status"] == "retrieved_and_sorted"
    assert sorted_result["sort"]["requested"] is True
    assert sorted_result["sort"]["directive"] == "@best"
    assert sorted_result["sort"]["status"] == "applied"
    assert sorted_result["sort"]["scientific_optimum_claim"] is False
    assert sorted_result["sort"]["changes_evidence_grade"] is False

    source_by_id = {
        item["id"]: {key: value for key, value in item.items() if key != "rank"}
        for item in source_order["search_targets"]
    }
    sorted_by_id = {
        item["id"]: {key: value for key, value in item.items() if key != "rank"}
        for item in sorted_result["search_targets"]
    }
    assert source_by_id == sorted_by_id
    assert [item["id"] for item in source_order["search_targets"]] != [
        item["id"] for item in sorted_result["search_targets"]
    ]
    assert [space["id"] for space in sorted_result["spaces"]] == ["N", "RP", "L", "D", "EG", "S"]


def test_geometry_is_a_traceable_support_record_and_not_an_active_site_prediction():
    result = serve_panel.analyze_general({"problem": "CO2gas+H2gas -- CH3CH2OHgas @best"})
    geometry = result["geometry"]
    elements = {node["element"] for node in geometry["nodes"]}
    assert elements == {"Fe", "O"}
    assert geometry["record_id"] == "mp-19306"
    assert geometry["source_database"] == "Materials Project OPTIMADE"
    assert geometry["source_url"].startswith("https://optimade.materialsproject.org/")
    assert geometry["coordinate_status"] == "public_database_record_support_only"
    assert "不是 Pd 活性位构型" in geometry["title"]
    assert "scope=support-only" in geometry["smiles"]
    assert all(node["group"] == "public_crystal_record" for node in geometry["nodes"])


def test_references_are_clickable_primary_or_doi_entries_without_pdf_paths():
    urls = [entry["url"] for entry in serve_panel.REFERENCES]
    assert "https://hdl.handle.net/2117/118190" in urls
    assert "https://doi.org/10.1016/j.chempr.2020.07.001" in urls
    assert "https://www.alphaxiv.org/docs/mcp" in urls
    assert all(not url.lower().endswith(".pdf") for url in urls)
    assert serve_panel.REFERENCES[0]["evidence_status"] == "abstract_verified"


def test_verified_public_database_snapshot_is_offline_and_source_bounded(monkeypatch):
    def forbidden_request(*_args, **_kwargs):
        raise AssertionError("snapshot mode attempted an external request")

    monkeypatch.setattr(serve_panel, "_json_request", forbidden_request)
    before = serve_panel.MODEL_CALLS
    snapshot = serve_panel.public_database_bundle("verified_snapshot")
    assert snapshot["mode_used"] == "verified_snapshot"
    assert snapshot["external_requests"] == 0
    assert snapshot["errors"] == []
    assert snapshot["reaction_energy_records"] == []
    assert {item["cid"] for item in snapshot["molecules"]} == {280, 702, 783}
    assert len(snapshot["catalyst_structures"]) == 1
    structure = snapshot["catalyst_structures"][0]
    assert structure["id"] == "mp-19306"
    assert structure["source_url"].startswith("https://optimade.materialsproject.org/")
    assert serve_panel.MODEL_CALLS == before


def test_unregistered_general_request_requires_harness_without_inventing_geometry():
    result = serve_panel.analyze_general({
        "problem": "molecule A binds protein B; infer a post-binding structure",
        "domain": "binding",
        "basis": "hybrid",
        "dimension": 5,
    })
    assert result["status"] == "needs_harness"
    assert result["reactants"] == []
    assert result["products"] == []
    assert result["reaction_energy"]["value"] is None
    assert result["possibilities"]["blocking"] is False
    assert result["database_receipt"]["external_requests"] == 0
    assert result["geometry"]["nodes"] == []
    assert result["search_targets"] == []
    assert result["model_receipt"]["calls"] == 0
    assert result["standard_math"]["status"] == "entity_extraction_required"
    assert {item["plugin"] for item in result["plugin_route"]} == {
        "AIHarness", "PublicDatabaseRouter", "GeometryPlugin"
    }


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
        "missing_fields": [],
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
    assert result["results"]["iteration_contract"]["status"] == "passed"
    assert result["results"]["retrieval_sort_contract"]["status"] == "passed"
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
            "database_mode": "verified_snapshot",
        })
        assert [item["formula"] for item in result["reactants"]] == ["CO2", "H2"]
        assert [item["formula"] for item in result["products"]] == ["C2H6O"]
        assert result["reaction_energy"]["value"] is None
        assert result["sort"]["requested"] is True
        assert result["possibilities"]["blocking"] is False
        assert result["database_receipt"]["external_requests"] == 0
        assert result["model_receipt"]["calls"] == 0
    finally:
        server.shutdown()
        server.server_close()

