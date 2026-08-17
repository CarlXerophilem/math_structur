from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from urllib.error import HTTPError

import serve_panel


QUERY = "CO2gas+H2gas -- CH3CH2OHgas @best"
REQUIRED_CONNECTORS = {
    "alphaxiv",
    "pubchem",
    "optimade_mp",
    "catalysis_hub",
    "oc20",
    "crossref",
    "openalex",
}


def run() -> dict:
    original_request = serve_panel._json_request
    calls_before = serve_panel.MODEL_CALLS

    def forbidden_request(*_args, **_kwargs):
        raise AssertionError("verified snapshot attempted an external request")

    serve_panel._json_request = forbidden_request
    try:
        snapshot = serve_panel.public_database_bundle("verified_snapshot")
        result = serve_panel.analyze_general(
            {
                "provider": "local",
                "problem": QUERY,
                "domain": "reaction",
                "basis": "literature_energy_geometry_space",
                "dimension": 4,
                "database_mode": "verified_snapshot",
            }
        )
    finally:
        serve_panel._json_request = original_request

    connector_ids = {item["id"] for item in snapshot["connectors"]}
    assertions = {
        "snapshot_mode": snapshot["mode_used"] == "verified_snapshot",
        "zero_external_requests": snapshot["external_requests"] == 0,
        "connector_contracts_present": REQUIRED_CONNECTORS.issubset(connector_ids),
        "pubchem_entities_present": {item["cid"] for item in snapshot["molecules"]} == {280, 702, 783},
        "support_record_present": (
            len(snapshot["catalyst_structures"]) == 1
            and snapshot["catalyst_structures"][0]["id"] == "mp-19306"
            and snapshot["catalyst_structures"][0]["chemical_formula_reduced"] == "Fe3O4"
        ),
        "reaction_energy_records_empty": snapshot["reaction_energy_records"] == [],
        "core_entities_preserved": (
            [item["formula"] for item in result["reactants"]] == ["CO2", "H2"]
            and [item["formula"] for item in result["products"]] == ["C2H6O"]
        ),
        "reaction_energy_unknown": (
            result["reaction_energy"]["value"] is None
            and result["reaction_energy"]["unit"] is None
            and result["reaction_energy"]["kind"] is None
            and result["reaction_energy"]["method"] is None
            and result["reaction_energy"]["reference_state"] is None
            and result["reaction_energy"]["source_record"] is None
        ),
        "sort_only": (
            result["sort"]["semantics"] == "sort_only"
            and result["sort"]["scientific_optimum_claim"] is False
            and result["sort"]["changes_evidence_grade"] is False
        ),
        "possibilities_nonblocking": result["possibilities"]["blocking"] is False,
        "geometry_is_support_only": (
            result["geometry"]["record_id"] == "mp-19306"
            and result["geometry"]["source_database"] == "Materials Project OPTIMADE"
            and result["geometry"]["source_scope"] == "support_only"
            and result["geometry"]["coordinate_status"] == "public_database_record_support_only"
            and {node["element"] for node in result["geometry"]["nodes"]} == {"Fe", "O"}
        ),
        "five_candidates_with_unknown_energy": (
            len(result["search_targets"]) == 5
            and all(item["reaction_energy"]["value"] is None for item in result["search_targets"])
        ),
        "discovery_is_process_signal": (
            result["discovery_signal"]["type"] == "source_coverage_gap_and_problem_definition_revision"
            and result["discovery_signal"]["scientific_discovery"] is False
            and "Catalysis-Hub" in result["discovery_signal"]["next_action"]
            and "拒绝或缩小" in result["discovery_signal"]["falsification"]
        ),
        "zero_model_calls": serve_panel.MODEL_CALLS == calls_before,
    }
    if not all(assertions.values()):
        raise AssertionError(assertions)
    return {
        "status": "passed",
        "query": QUERY,
        "mode": snapshot["mode_used"],
        "external_requests": snapshot["external_requests"],
        "model_calls": serve_panel.MODEL_CALLS - calls_before,
        "connector_ids": sorted(connector_ids),
        "pubchem_cids": sorted(item["cid"] for item in snapshot["molecules"]),
        "reaction_energy": None,
        "geometry": {
            "record_id": result["geometry"]["record_id"],
            "source_database": result["geometry"]["source_database"],
            "source_scope": result["geometry"]["source_scope"],
            "elements": sorted({node["element"] for node in result["geometry"]["nodes"]}),
        },
        "candidate_ids": [item["id"] for item in result["search_targets"]],
        "discovery_signal": result["discovery_signal"],
        "assertions": assertions,
    }


def run_live() -> dict:
    bundle = serve_panel.public_database_bundle("live_public")
    connectors = {item["id"]: item for item in bundle["connectors"]}

    def unauthorized(url: str, payload: dict | None = None) -> int | None:
        try:
            serve_panel._json_request(url, payload=payload)
        except HTTPError as exc:
            return exc.code
        return None

    catalyst_record_status = unauthorized(
        "https://api.catalysis-hub.org/graphql",
        {"query": "{reactions(first:1){edges{node{reactants products reactionEnergy}}}}"},
    )
    alphaxiv_status = unauthorized("https://api.alphaxiv.org/mcp/v1")
    assertions = {
        "live_mode_used": bundle["mode_used"] == "live_public_with_explicit_snapshot_fallbacks",
        "pubchem_live": connectors["pubchem"]["status"] == "live_verified",
        "optimade_live": connectors["optimade_mp"]["status"] == "live_verified",
        "crossref_live": connectors["crossref"]["status"] == "live_verified",
        "openalex_live": connectors["openalex"]["status"] == "live_verified",
        "catalysis_schema_live": (
            connectors["catalysis_hub"]["status"] == "live_schema_verified_records_not_queried"
            and {"reactants", "products", "reactionEnergy", "surfaceComposition", "systems"}.issubset(
                set(connectors["catalysis_hub"].get("schema_fields_present", []))
            )
        ),
        "catalysis_record_requires_key": catalyst_record_status == 401,
        "alphaxiv_requires_authorization": alphaxiv_status == 401,
        "pubchem_entities_exact": {item["cid"] for item in bundle["molecules"]} == {280, 702, 783},
        "optimade_support_exact": (
            bundle["catalyst_structures"][0]["id"] == "mp-19306"
            and bundle["catalyst_structures"][0]["chemical_formula_reduced"] == "Fe3O4"
            and len(bundle["catalyst_structures"][0]["cartesian_site_positions"]) == 14
        ),
        "literature_metadata_live": bundle["literature_metadata"][0]["status"] == "live_metadata_verified",
        "no_reaction_energy_record_obtained": bundle["reaction_energy_records"] == [],
    }
    if not all(assertions.values()):
        raise AssertionError(assertions)
    return {
        "status": "passed",
        "mode": bundle["mode_used"],
        "external_requests_recorded_by_bundle": bundle["external_requests"],
        "connector_status": {key: value["status"] for key, value in connectors.items()},
        "catalysis_record_query_http": catalyst_record_status,
        "alphaxiv_unauthenticated_http": alphaxiv_status,
        "pubchem_cids": sorted(item["cid"] for item in bundle["molecules"]),
        "optimade_record": {
            "id": bundle["catalyst_structures"][0]["id"],
            "formula": bundle["catalyst_structures"][0]["chemical_formula_reduced"],
            "site_count": len(bundle["catalyst_structures"][0]["cartesian_site_positions"]),
            "scope": "support_only",
        },
        "literature_metadata": bundle["literature_metadata"],
        "reaction_energy_records": bundle["reaction_energy_records"],
        "errors": bundle["errors"],
        "assertions": assertions,
        "boundary": "Live metadata and geometry access do not establish catalytic performance; no comparable reaction-energy record was obtained.",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true", help="exercise public Internet interfaces and authentication boundaries")
    args = parser.parse_args()
    result = run_live() if args.live else run()
    artifact_dir = Path(__file__).resolve().parents[1] / "artifacts"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    receipt_name = (
        "public_database_live_acceptance.json"
        if args.live
        else "public_database_snapshot_acceptance.json"
    )
    receipt_path = artifact_dir / receipt_name
    receipt_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"receipt={receipt_path}", file=sys.stderr)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
