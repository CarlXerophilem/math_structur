from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
import platform
import threading
import time
from urllib.request import Request, urlopen

import serve_panel


ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "artifacts" / "qwen_recognition_acceptance.json"
QUERY = "CO2gas+H2gas -- CH3CH2OHgas @best"


def get_json(url: str, timeout: float = 10) -> dict:
    with urlopen(url, timeout=timeout) as response:
        if response.status != 200:
            raise RuntimeError(f"GET {url} returned HTTP {response.status}")
        return json.loads(response.read().decode("utf-8"))


def post_json(url: str, payload: dict, timeout: float = 240) -> dict:
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=timeout) as response:
        body = json.loads(response.read().decode("utf-8"))
        if response.status != 200:
            raise RuntimeError(body.get("error") or f"HTTP {response.status}")
        return body


def run() -> dict:
    serve_panel._ollama_status.cache_clear()
    serve_panel.harness_status.cache_clear()
    server = serve_panel.make_server("127.0.0.1", 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    started = time.perf_counter()
    try:
        base = f"http://127.0.0.1:{server.server_port}"
        harness = get_json(base + "/api/harness/status")
        qwen = harness["qwen_local"]
        if not qwen.get("ready"):
            raise RuntimeError(f"required local model unavailable: {qwen.get('requested_model')}")
        if qwen.get("model") != serve_panel.QWEN_JAILBROKEN_MODEL:
            raise RuntimeError(f"wrong model selected: {qwen.get('model')}")

        result = post_json(
            base + "/api/solver/run",
            {
                "provider": "qwen",
                "problem": QUERY,
                "domain": "reaction",
                "basis": "literature_energy_geometry_space",
                "dimension": 4,
                "database_mode": "verified_snapshot",
            },
        )
        recognition = result["recognition"]
        receipt = result["model_receipt"]
        energy = result["reaction_energy"]
        optional_names = {"temperature", "pressure", "candidate_domain", "metrics", "baseline"}
        assertions = {
            "exact_model_selected": recognition["model"] == serve_panel.QWEN_JAILBROKEN_MODEL,
            "digest_recorded": recognition.get("model_digest") == qwen.get("digest") and bool(qwen.get("digest")),
            "domain_recognized": recognition["domain"] == "reaction",
            "intent_recognized": recognition["intent"] == "catalyst_search",
            "recognition_gate_passed": recognition["gate"]["status"] == "passed",
            "recognition_only": recognition["role"] == "recognition_only" and recognition["scientific_authority"] is False,
            "one_model_call": receipt["calls"] == 1 and receipt["max_calls"] == 1,
            "core_entities_preserved": (
                [item["formula"] for item in result["reactants"]] == ["CO2", "H2"]
                and [item["formula"] for item in result["products"]] == ["C2H6O"]
            ),
            "optional_fields_not_missing_requirements": (
                recognition["missing_fields"] == []
                and not optional_names.intersection(recognition["missing_fields"])
            ),
            "reaction_energy_unknown": (
                energy["value"] is None
                and energy["unit"] is None
                and energy["kind"] is None
                and energy["method"] is None
                and energy["reference_state"] is None
                and energy["source_record"] is None
            ),
            "best_is_sort_only": (
                result["sort"]["requested"] is True
                and result["sort"]["semantics"] == "sort_only"
                and result["sort"]["scientific_optimum_claim"] is False
                and result["sort"]["changes_evidence_grade"] is False
            ),
            "possibilities_nonblocking": (
                result["possibilities"]["blocking"] is False
                and all(result["possibilities"][name]["value"] is None for name in optional_names)
            ),
            "verified_snapshot_offline": (
                result["database_receipt"]["mode_used"] == "verified_snapshot"
                and result["database_receipt"]["external_requests"] == 0
                and result["database_receipt"]["reaction_energy_records"] == []
            ),
            "support_geometry_scoped": (
                result["geometry"]["record_id"] == "mp-19306"
                and result["geometry"]["source_database"] == "Materials Project OPTIMADE"
                and result["geometry"]["source_scope"] == "support_only"
                and {node["element"] for node in result["geometry"]["nodes"]} == {"Fe", "O"}
            ),
            "five_source_candidates": (
                len(result["search_targets"]) == 5
                and all(item["reaction_energy"]["value"] is None for item in result["search_targets"])
            ),
            "discovery_is_process_signal": (
                result["discovery_signal"]["type"]
                == "source_coverage_gap_and_problem_definition_revision"
                and result["discovery_signal"]["scientific_discovery"] is False
                and "Catalysis-Hub" in result["discovery_signal"]["next_action"]
            and "拒绝或缩小" in result["discovery_signal"]["falsification"]
            ),
            "no_scientific_answer_fields": not any(
                key in recognition for key in ("answer", "best_catalyst", "predicted_structure", "proof")
            ),
        }
        if not all(assertions.values()):
            raise AssertionError(assertions)

        acceptance = {
            "checked_at": datetime.now().astimezone().isoformat(),
            "status": "passed",
            "platform": platform.platform(),
            "python": platform.python_version(),
            "transport": "loopback panel plus loopback Ollama",
            "external_network_requests": 0,
            "elapsed_seconds": round(time.perf_counter() - started, 3),
            "model": recognition["model"],
            "model_digest": recognition["model_digest"],
            "model_size_bytes": qwen.get("size"),
            "input_sha256": recognition["input_sha256"],
            "recognition": {
                "domain": recognition["domain"],
                "intent": recognition["intent"],
                "entities": recognition["entities"],
                "constraints": recognition["constraints"],
                "missing_fields": recognition["missing_fields"],
                "confidence": recognition["confidence"],
                "runtime": recognition["runtime"],
            },
            "gate": recognition["gate"],
            "exact_validation": {
                "reactants": result["reactants"],
                "products": result["products"],
                "reaction_energy": energy,
                "sort": result["sort"],
                "possibilities": result["possibilities"],
                "geometry": {
                    "record_id": result["geometry"]["record_id"],
                    "source_database": result["geometry"]["source_database"],
                    "source_scope": result["geometry"]["source_scope"],
                    "coordinate_status": result["geometry"]["coordinate_status"],
                },
                "candidate_ids": [item["id"] for item in result["search_targets"]],
                "discovery_signal": result["discovery_signal"],
                "database_mode": result["database_receipt"]["mode_used"],
                "database_external_requests": result["database_receipt"]["external_requests"],
            },
            "assertions": assertions,
            "scientific_boundary": (
                "The local model only recognized target metadata. The deterministic kernel ordered "
                "source records without changing evidence grades; it did not infer reaction energy, "
                "claim catalytic optimality, predict an active-site geometry, or prove a theorem."
            ),
        }
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(acceptance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return acceptance
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
