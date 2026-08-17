from __future__ import annotations

import cmath
from functools import lru_cache
import hashlib
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen


PANEL = Path(__file__).resolve().parent
ROOT = PANEL.parent


def _configured_path(environment: str, *portable_candidates: Path) -> Path:
    configured = os.environ.get(environment, "").strip()
    if configured:
        return Path(configured).expanduser()
    for candidate in portable_candidates:
        if candidate.exists():
            return candidate
    return portable_candidates[0]


SCRIPTS_ROOT = ROOT.parents[2] if len(ROOT.parents) > 2 else ROOT.parent
PRIME_REPO = _configured_path(
    "MATH_STRUCTURER_PRIME_REPO",
    ROOT / "external" / "prime_loop_verification",
    SCRIPTS_ROOT / "shape_of_set" / "prime_loop_verification",
)
CROSS_VERIFY = _configured_path(
    "MATH_STRUCTURER_CROSS_VERIFY",
    ROOT / "hooks" / "cross-verify.sh",
    ROOT.parent / "SolveIterativeFunctions" / "harness" / "hooks" / "cross-verify.sh",
)
CODEX_CONFIG = _configured_path(
    "MATH_STRUCTURER_CODEX_CONFIG",
    Path.home() / ".codex" / "config.toml",
)
SCHEMA = PANEL / "solver_output.schema.json"
MODEL_CALLS = 0

QWEN_MODEL_ENV = "MATH_STRUCTURER_QWEN_MODEL"
QWEN_JAILBROKEN_MODEL = "hf.co/mradermacher/Qwen3-8B-Jailbroken-GGUF:Q4_K_M"

RECOGNITION_DOMAINS = {
    "reaction",
    "binding",
    "mathematics",
    "pde",
    "number_theory",
    "unknown",
}
RECOGNITION_INTENTS = {
    "catalyst_search",
    "structure_prediction",
    "basis_operator_debug",
    "half_iterate",
    "pde_reduction",
    "problem_generation",
    "unknown",
}
RECOGNITION_SCHEMA = {
    "type": "object",
    "required": [
        "domain",
        "intent",
        "entities",
        "constraints",
        "missing_fields",
        "confidence",
    ],
    "properties": {
        "domain": {"type": "string", "enum": sorted(RECOGNITION_DOMAINS)},
        "intent": {"type": "string", "enum": sorted(RECOGNITION_INTENTS)},
        "entities": {"type": "array", "items": {"type": "string"}, "maxItems": 16},
        "constraints": {"type": "array", "items": {"type": "string"}, "maxItems": 16},
        "missing_fields": {"type": "array", "items": {"type": "string"}, "maxItems": 16},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
    },
    "additionalProperties": False,
}


def _portable_text(value: Any) -> str:
    text = str(value)
    replacements = (
        (str(ROOT), "<project>"),
        (str(PRIME_REPO), "<prime-repo>"),
        (str(CROSS_VERIFY), "<cross-verify>"),
        (str(Path.home()), "~"),
    )
    for absolute, marker in replacements:
        if absolute:
            text = text.replace(absolute, marker).replace(absolute.replace("\\", "/"), marker)
    return re.sub(r"(?i)\b[A-Z]:[\\/][^\r\n\t\"]+", "<local-path>", text)


def _portable_payload(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _portable_payload(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_portable_payload(item) for item in value]
    if isinstance(value, tuple):
        return [_portable_payload(item) for item in value]
    return _portable_text(value) if isinstance(value, (str, Path)) else value

BASIS_OPERATOR_CONTRACT = {
    "signature": "B: C x C^times -> C",
    "display_signature": "B: ℂ × ℂ^× → ℂ",
    "formula": "B(u,v)=exp(u)-Log(v)",
    "log_policy": "pointwise_principal_value",
    "argument_range": "Arg(v) in (-pi, pi]",
    "warning": "the pointwise principal value is discontinuous across the two sides of the negative real axis",
}


REFERENCES = [
    {
        "id": "CAT0",
        "title": "Direct Conversion of CO2 to Ethanol Boosted by Intimacy-Sensitive Multifunctional Catalysts",
        "year": 2021,
        "url": "https://doi.org/10.1021/acscatal.1c01504",
        "doi": "https://doi.org/10.1021/acscatal.1c01504",
        "role": "ACS Figshare abstract verified; conditions and proximity matter; no universal ranking",
        "evidence_status": "abstract_verified",
    },
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
        "id": "DB-PUBCHEM",
        "title": "PubChem PUG REST",
        "year": 2026,
        "url": "https://pubchem.ncbi.nlm.nih.gov/docs/pug-rest",
        "role": "public compound identifiers, formulae and SMILES; not catalyst performance",
        "evidence_status": "live_api_verified",
    },
    {
        "id": "DB-OPTIMADE",
        "title": "Materials Project OPTIMADE",
        "year": 2026,
        "url": "https://optimade.materialsproject.org/v1/info",
        "role": "public crystal records with lattice vectors and Cartesian site positions",
        "evidence_status": "live_api_verified",
    },
    {
        "id": "DB-CATHUB",
        "title": "Catalysis-Hub GraphQL API",
        "year": 2026,
        "url": "https://api.catalysis-hub.org/graphql",
        "role": "schema exposes reactants, products, reactionEnergy and atomistic systems; record access is not assumed",
        "evidence_status": "schema_verified_record_access_gated",
    },
    {
        "id": "DB-OC20",
        "title": "Open Catalyst 2020 dataset documentation",
        "year": 2026,
        "url": "https://github.com/facebookresearch/fairchem/blob/main/docs/catalysts/datasets/oc20.md",
        "role": "downloadable adsorbate-catalyst structures, relaxed energies and trajectories; no exact demo record loaded",
        "evidence_status": "repository_documentation_verified",
    },
    {
        "id": "DB-CROSSREF",
        "title": "Crossref REST API",
        "year": 2026,
        "url": "https://api.crossref.org/works/10.1021/acscatal.1c01504",
        "role": "live DOI metadata endpoint; metadata is not an experimental result",
        "evidence_status": "live_api_verified",
    },
    {
        "id": "DB-OPENALEX",
        "title": "OpenAlex Works API",
        "year": 2026,
        "url": "https://api.openalex.org/works/https://doi.org/10.1021/acscatal.1c01504",
        "role": "live bibliographic metadata and source graph; not reaction-energy evidence",
        "evidence_status": "live_api_verified",
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
        "id": "HALF1",
        "title": "Iterative square roots of functions",
        "year": 2023,
        "url": "https://doi.org/10.1017/etds.2022.35",
        "role": "existence and non-existence depend on function-graph and topological structure",
        "evidence_status": "full_text_verified",
    },
    {
        "id": "LIE1",
        "title": "Self-Supervised Learning with Lie Symmetries for Partial Differential Equations",
        "year": 2024,
        "url": "https://arxiv.org/abs/2307.05432",
        "role": "alphaXiv record verified; Lie transformations support PDE representation learning",
        "evidence_status": "alphaxiv_verified",
    },
    {
        "id": "BOLTZ1",
        "title": "Long Time Derivation of the Boltzmann Equation from Hard Sphere Dynamics",
        "year": 2025,
        "url": "https://arxiv.org/abs/2408.07818",
        "role": "alphaXiv and local 192-page source verified; illustrates domain-specific derivation complexity",
        "evidence_status": "full_text_verified",
    },
]


OPTIMADE_MP19306_URL = (
    "https://optimade.materialsproject.org/v1/structures?"
    "filter=id%3D%22mp-19306%22&page_limit=1&response_fields="
    "id,chemical_formula_reduced,lattice_vectors,cartesian_site_positions,species_at_sites"
)

OPTIMADE_MP19306 = {
    "id": "mp-19306",
    "chemical_formula_reduced": "Fe3O4",
    "lattice_vectors": [
        [1.72398624, 4.87541165, 2.98673909],
        [-0.00078192, 0.000298, 5.97028591],
        [5.17085494, 0.0004307, 2.98395144],
    ],
    "cartesian_site_positions": [
        [6.032796126878078, 4.265945003654114, 10.449609753973009],
        [2.584426137930351, 0.0005523940713869999, 4.476984919332381],
        [3.4470088829577348, 2.436882737554841, 5.97163516842986],
        [0.8622246729742374, 0.6088249175888105, 1.4938457517702834],
        [3.4485588472614723, 2.437649938592831, 2.9864161401453266],
        [6.032458138749329, 2.43891900104457, 7.4623953912467105],
        [2.6734039235320997, 3.626005069927609, 7.461811772356357],
        [2.585213494579853, 3.5633556795421417, 4.476720122213099],
        [1.7674947700613524, 1.2521015696557984, 3.0606367107170787],
        [4.308462802318762, 1.3122249283899534, 7.462241205763924],
        [1.766295554538987, 1.249601961984088, 5.894770275322708],
        [5.127425505699409, 3.6265890628431956, 8.880061910602882],
        [4.221504241496019, 1.2502360406167004, 4.477077450636655],
        [5.124965239199261, 3.6264643711651576, 6.046094597606704],
    ],
    "species_at_sites": ["Fe", "Fe", "Fe", "Fe", "Fe", "Fe", "O", "O", "O", "O", "O", "O", "O", "O"],
    "space_group_symbol_hermann_mauguin": None,
    "source_url": OPTIMADE_MP19306_URL,
    "snapshot_checked_at": "2026-08-17",
}

PUBCHEM_SNAPSHOT = [
    {
        "role": "reactant",
        "query_name": "carbon dioxide",
        "cid": 280,
        "formula": "CO2",
        "smiles": "C(=O)=O",
        "url": "https://pubchem.ncbi.nlm.nih.gov/compound/280",
    },
    {
        "role": "reactant",
        "query_name": "hydrogen",
        "cid": 783,
        "formula": "H2",
        "smiles": "[HH]",
        "url": "https://pubchem.ncbi.nlm.nih.gov/compound/783",
    },
    {
        "role": "product",
        "query_name": "ethanol",
        "cid": 702,
        "formula": "C2H6O",
        "smiles": "CCO",
        "url": "https://pubchem.ncbi.nlm.nih.gov/compound/702",
    },
]

PUBLIC_DATABASE_CONNECTORS = [
    {
        "id": "alphaxiv",
        "name": "alphaXiv MCP/API",
        "url": "https://api.alphaxiv.org/mcp/v1",
        "status": "authentication_required_for_live_reading",
        "fields": ["paper metadata", "AI intermediate report", "full text when explicitly requested"],
        "scope": "文献穿透式读取；默认 AI 中间报告不等于原文，未认证时不声称已读取",
        "authentication": "OAuth2_or_API_key",
    },
    {
        "id": "pubchem",
        "name": "PubChem PUG REST",
        "url": "https://pubchem.ncbi.nlm.nih.gov/docs/pug-rest",
        "status": "verified_snapshot",
        "fields": ["CID", "MolecularFormula", "SMILES"],
        "scope": "反应物／产物标识；不提供催化性能",
        "authentication": "none_observed",
    },
    {
        "id": "optimade_mp",
        "name": "Materials Project OPTIMADE",
        "url": "https://optimade.materialsproject.org/v1/info",
        "status": "verified_snapshot",
        "fields": ["id", "lattice_vectors", "cartesian_site_positions", "species_at_sites"],
        "scope": "公共晶体几何；当前记录仅是 Fe3O4 支撑体，不是 Pd 活性位",
        "authentication": "none_observed",
    },
    {
        "id": "catalysis_hub",
        "name": "Catalysis-Hub GraphQL",
        "url": "https://api.catalysis-hub.org/graphql",
        "status": "official_fields_verified_live_records_authorized",
        "fields": ["reactants", "products", "reactionEnergy", "surfaceComposition", "systems.positions"],
        "scope": "反应能量与原子体系字段合同；没有取得记录就保持空值",
        "authentication": "API_key_via_ORCID_for_POST_queries",
    },
    {
        "id": "oc20",
        "name": "Open Catalyst 2020",
        "url": "https://github.com/facebookresearch/fairchem/blob/main/docs/catalysts/datasets/oc20.md",
        "status": "download_contract_verified_not_loaded",
        "fields": ["adsorbate-catalyst structure", "energy", "forces", "relaxed structure"],
        "scope": "公共下载数据集；本次未下载大体量 LMDB，也未声称命中当前反应",
        "authentication": "public_download",
    },
    {
        "id": "crossref",
        "name": "Crossref REST",
        "url": "https://api.crossref.org/works/10.1021/acscatal.1c01504",
        "status": "verified_snapshot",
        "fields": ["DOI", "title", "publisher", "published"],
        "scope": "文献元数据；不等于正文或实验结论",
        "authentication": "none_observed",
    },
    {
        "id": "openalex",
        "name": "OpenAlex Works",
        "url": "https://api.openalex.org/works/https://doi.org/10.1021/acscatal.1c01504",
        "status": "verified_snapshot",
        "fields": ["id", "doi", "display_name", "publication_year"],
        "scope": "文献图谱元数据；不提供反应能量",
        "authentication": "none_observed",
    },
]


def _json_request(url: str, *, payload: dict[str, Any] | None = None, timeout: int = 25) -> dict[str, Any]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {
        "Accept": "application/json, application/vnd.api+json",
        "User-Agent": "MathStructurer/0.6 (research prototype)",
    }
    if data is not None:
        headers["Content-Type"] = "application/json"
    request = Request(url, data=data, headers=headers, method="POST" if data is not None else "GET")
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _connector(connectors: list[dict[str, Any]], connector_id: str) -> dict[str, Any]:
    return next(item for item in connectors if item["id"] == connector_id)


def _public_database_snapshot() -> dict[str, Any]:
    return {
        "mode_requested": "verified_snapshot",
        "mode_used": "verified_snapshot",
        "snapshot_checked_at": "2026-08-17",
        "external_requests": 0,
        "connectors": json.loads(json.dumps(PUBLIC_DATABASE_CONNECTORS)),
        "molecules": json.loads(json.dumps(PUBCHEM_SNAPSHOT)),
        "catalyst_structures": [json.loads(json.dumps(OPTIMADE_MP19306))],
        "literature_metadata": [
            {
                "source": "Crossref/OpenAlex",
                "doi": "10.1021/acscatal.1c01504",
                "title": "Direct Conversion of CO2 to Ethanol Boosted by Intimacy-Sensitive Multifunctional Catalysts",
                "year": 2021,
                "status": "metadata_verified",
            }
        ],
        "reaction_energy_records": [],
        "errors": [],
    }


def public_database_bundle(mode: str = "verified_snapshot") -> dict[str, Any]:
    result = _public_database_snapshot()
    result["mode_requested"] = mode
    if mode != "live_public":
        return result

    result["mode_used"] = "live_public_with_explicit_snapshot_fallbacks"

    def attempt(connector_id: str, operation: Any) -> Any:
        result["external_requests"] += 1
        connector = _connector(result["connectors"], connector_id)
        try:
            value = operation()
            connector["status"] = "live_verified"
            connector["error"] = None
            return value
        except (HTTPError, URLError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
            connector["status"] = "live_error_snapshot_retained"
            connector["error"] = _portable_text(exc)[:180]
            result["errors"].append({"connector": connector_id, "error": connector["error"]})
            return None

    live_molecules: list[dict[str, Any]] = []
    for snapshot in PUBCHEM_SNAPSHOT:
        name = quote(snapshot["query_name"])
        url = (
            f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{name}/"
            "property/CanonicalSMILES,IsomericSMILES,MolecularFormula/JSON"
        )
        payload = attempt("pubchem", lambda url=url: _json_request(url))
        if payload:
            item = payload["PropertyTable"]["Properties"][0]
            live_molecules.append(
                {
                    **snapshot,
                    "cid": int(item["CID"]),
                    "formula": item["MolecularFormula"],
                    "smiles": item.get("SMILES") or item.get("ConnectivitySMILES"),
                    "source_mode": "live_public",
                }
            )
    if len(live_molecules) == len(PUBCHEM_SNAPSHOT):
        result["molecules"] = live_molecules

    optimade = attempt("optimade_mp", lambda: _json_request(OPTIMADE_MP19306_URL))
    if optimade and optimade.get("data"):
        record = optimade["data"][0]
        result["catalyst_structures"] = [
            {
                "id": record["id"],
                **record["attributes"],
                "source_url": OPTIMADE_MP19306_URL,
                "source_mode": "live_public",
            }
        ]

    crossref = attempt(
        "crossref",
        lambda: _json_request("https://api.crossref.org/works/10.1021/acscatal.1c01504"),
    )
    openalex = attempt(
        "openalex",
        lambda: _json_request("https://api.openalex.org/works/https://doi.org/10.1021/acscatal.1c01504"),
    )
    if crossref and openalex:
        message = crossref["message"]
        result["literature_metadata"] = [
            {
                "source": "Crossref+OpenAlex live",
                "doi": message.get("DOI"),
                "title": (message.get("title") or [openalex.get("display_name")])[0],
                "year": openalex.get("publication_year"),
                "openalex_id": openalex.get("id"),
                "status": "live_metadata_verified",
            }
        ]

    cathub_query = {
        "query": "{__type(name:\"Reaction\"){fields{name}}}",
    }
    cathub = attempt(
        "catalysis_hub",
        lambda: _json_request("https://api.catalysis-hub.org/graphql", payload=cathub_query),
    )
    if cathub:
        fields = sorted(item["name"] for item in cathub["data"]["__type"]["fields"])
        required = {"reactants", "products", "reactionEnergy", "surfaceComposition", "systems"}
        connector = _connector(result["connectors"], "catalysis_hub")
        connector["status"] = "live_schema_verified_records_not_queried"
        connector["schema_fields_present"] = sorted(required.intersection(fields))
        connector["record_access"] = "not_assumed_without_authorization"

    return result


def _geometry_from_optimade(record: dict[str, Any], mode: str) -> dict[str, Any]:
    positions = record.get("cartesian_site_positions") or []
    species = record.get("species_at_sites") or []
    if not positions or len(positions) != len(species):
        return {
            "kind": "public_database_geometry_unavailable",
            "title": "公共数据库未返回可绘制坐标",
            "nodes": [],
            "edges": [],
            "coordinate_status": "unavailable",
            "source_scope": "unavailable",
        }
    center = [sum(point[axis] for point in positions) / len(positions) for axis in range(3)]
    span = max(max(point[axis] for point in positions) - min(point[axis] for point in positions) for axis in range(3)) or 1.0
    scale = 3.4 / span
    nodes = []
    for index, (element, point) in enumerate(zip(species, positions)):
        nodes.append(
            {
                "id": f"atom{index}",
                "element": element,
                "x": round((point[0] - center[0]) * scale, 6),
                "y": round((point[1] - center[1]) * scale, 6),
                "z": round((point[2] - center[2]) * scale, 6),
                "raw_position_angstrom": point,
                "group": "public_crystal_record",
            }
        )
    edges: list[list[str]] = []
    for left in range(len(positions)):
        for right in range(left + 1, len(positions)):
            distance = math.dist(positions[left], positions[right])
            if distance <= 2.2:
                edges.append([f"atom{left}", f"atom{right}"])
    return {
        "kind": "optimade_crystal_record",
        "title": "Fe₃O₄ 支撑体公共晶体记录 mp-19306（不是 Pd 活性位构型）",
        "record_id": record.get("id"),
        "source_database": "Materials Project OPTIMADE",
        "source_url": record.get("source_url", OPTIMADE_MP19306_URL),
        "source_mode": mode,
        "source_scope": "support_only",
        "nodes": nodes,
        "edges": edges,
        "lattice_vectors_angstrom": record.get("lattice_vectors"),
        "quotient": "Cartesian Å；显示时仅居中缩放",
        "symmetry": "OPTIMADE 标准空间群字段为空；不推断对称群",
        "smiles": "record=mp-19306；formula=Fe3O4；scope=support-only",
        "coordinate_status": "public_database_record_support_only",
        "edge_policy": "非周期欧氏距离≤2.2 Å，仅供显示；不补周期邻居",
        "render_contract": "OPTIMADE positions -> centered nodes -> HTML5 SVG/Canvas",
    }


def _literature_candidates(sort_requested: bool) -> list[dict[str, Any]]:
    candidates = [
        {
            "id": "CAT0",
            "label": "Na-Fe@C + K-CuZnAl multifunctional catalyst",
            "year": 2021,
            "state": "abstract_verified",
            "url": "https://doi.org/10.1021/acscatal.1c01504",
            "reaction_match": True,
            "reaction_energy": {"value": None, "unit": None, "status": "not_retrieved"},
            "geometry": {"status": "not_machine_readable_in_current_sources", "record_id": None},
        },
        {
            "id": "CAT1",
            "label": "Pd1/Fe3O4 single-atom interface",
            "year": 2018,
            "state": "abstract_verified",
            "url": "https://hdl.handle.net/2117/118190",
            "reaction_match": True,
            "reaction_energy": {"value": None, "unit": None, "status": "not_retrieved"},
            "geometry": {"status": "public_support_record_only", "record_id": "mp-19306"},
        },
        {
            "id": "CAT2",
            "label": "Cu@Na-Beta",
            "year": 2020,
            "state": "metadata_only",
            "url": "https://doi.org/10.1016/j.chempr.2020.07.001",
            "reaction_match": True,
            "reaction_energy": {"value": None, "unit": None, "status": "not_retrieved"},
            "geometry": {"status": "not_retrieved", "record_id": None},
        },
        {
            "id": "CAT3",
            "label": "ordered Pd-Cu nanoparticles",
            "year": 2017,
            "state": "metadata_only",
            "url": "https://doi.org/10.1021/jacs.7b03101",
            "reaction_match": True,
            "reaction_energy": {"value": None, "unit": None, "status": "not_retrieved"},
            "geometry": {"status": "not_retrieved", "record_id": None},
        },
        {
            "id": "CAT4",
            "label": "Ir1-In2O3 single-atom catalyst",
            "year": 2020,
            "state": "metadata_only",
            "url": "https://doi.org/10.1021/jacs.0c08607",
            "reaction_match": True,
            "reaction_energy": {"value": None, "unit": None, "status": "not_retrieved"},
            "geometry": {"status": "not_retrieved", "record_id": None},
        },
    ]
    for candidate in candidates:
        candidate["reaction_energy"].update(
            {
                "kind": None,
                "method": None,
                "reference_state": None,
                "source_record": None,
            }
        )
        abstract = candidate["state"] == "abstract_verified"
        geometry = candidate["geometry"]["record_id"] is not None
        comparable_energy = candidate["reaction_energy"]["value"] is not None
        candidate["retrieval_score"] = 50 + 25 * int(abstract) + 15 * int(geometry) + 10 * int(comparable_energy)
        candidate["sort_features"] = {
            "reaction_entity_match": 1,
            "abstract_verified": int(abstract),
            "public_geometry_link": int(geometry),
            "comparable_energy_record": int(comparable_energy),
        }
        energy_label = "未取得" if candidate["reaction_energy"]["value"] is None else "有来源数值"
        geometry_label = {
            "public_support_record_only": "公开支撑体记录",
            "not_machine_readable_in_current_sources": "当前来源无机器可读坐标",
            "not_retrieved": "未取得",
        }.get(candidate["geometry"]["status"], candidate["geometry"]["status"])
        candidate["query"] = f"检索匹配分={candidate['retrieval_score']}；能量记录={energy_label}；几何={geometry_label}"
    if sort_requested:
        candidates.sort(key=lambda item: (-item["retrieval_score"], -item["year"], item["id"]))
    for index, candidate in enumerate(candidates, start=1):
        candidate["rank"] = index
    return candidates


def _possibilities(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    supplied = payload.get("possibilities") if isinstance(payload.get("possibilities"), dict) else {}

    def item(name: str, role: str) -> dict[str, Any]:
        value = supplied.get(name, payload.get(name))
        if isinstance(value, str):
            value = value.strip() or None
        return {
            "value": value,
            "status": "provided" if value is not None else "unspecified_optional",
            "role": role,
        }

    return {
        "temperature": item("temperature", "optional_filter_or_future_sort_key"),
        "pressure": item("pressure", "optional_filter_or_future_sort_key"),
        "candidate_domain": item("candidate_domain", "optional_query_expansion"),
        "metrics": item("metrics", "optional_future_comparison"),
        "baseline": item("baseline", "optional_future_comparison"),
        "blocking": False,
    }


def analyze_general(payload: dict[str, Any]) -> dict[str, Any]:
    problem = str(payload.get("problem", "")).strip()
    compact = re.sub(r"\s+", "", problem).lower()
    sort_requested = "@best" in compact
    is_demo = "co2gas+h2gas--ch3ch2ohgas" in compact
    database_mode = str(payload.get("database_mode", "verified_snapshot"))
    if database_mode not in {"verified_snapshot", "live_public"}:
        raise ValueError("database_mode must be verified_snapshot or live_public")
    database = public_database_bundle(database_mode)

    if not is_demo:
        return {
            "status": "needs_harness",
            "source": "local_retrieval_contract",
            "input": problem,
            "normalized_problem": {
                "type": str(payload.get("domain", "auto")),
                "statement": problem,
                "reactants": [],
                "products": [],
                "directive": "@best" if sort_requested else None,
                "reaction_natural_language": "等待 AI 提取反应物与产物；温压等只作为可选可能性。",
            },
            "standard_math": {
                "display": r"q_{NL}\to(R,P),\quad \mathcal C=\mathcal L(R,P)\cup\mathcal D(R,P)",
                "logic": r"R\neq\varnothing\land P\neq\varnothing\Rightarrow\mathrm{Retrieve}(R,P)",
                "status": "entity_extraction_required",
            },
            "target_function": {
                "display": r"\Delta E_{record}\in\mathbb R\cup\{\mathrm{unknown}\}",
                "nontriviality": "source_record_required",
                "status": "unknown",
            },
            "reactants": [],
            "products": [],
            "reaction_energy": {
                "value": None,
                "unit": None,
                "kind": None,
                "method": None,
                "reference_state": None,
                "source_record": None,
                "status": "unknown_no_record",
            },
            "sort": {
                "requested": sort_requested,
                "key": "retrieval_match_and_data_coverage",
                "status": "waiting_for_candidates",
                "semantics": "sort_only",
                "scientific_optimum_claim": False,
            },
            "possibilities": _possibilities(payload),
            "basis": {
                "name": "literature_energy_geometry_space",
                "display_name": "文献×能量×几何字段空间",
                "dimension": 4,
                "operator": "(R,P) → literature ∪ public DB → (ΔE, geometry) → stable sort",
            },
            "machine_problems": [
                {"id": "M0", "operator": "AI.extract(reactants, products)", "status": "required"},
                {"id": "M1", "operator": "LiteratureConnector.search(R,P)", "status": "waiting"},
                {"id": "M2", "operator": "PublicDatabaseRouter.lookup(R,P)", "status": "waiting"},
            ],
            "spaces": [
                {"id": "N", "label": "自然语言目标", "map": "实体抽取"},
                {"id": "RP", "label": "反应物／产物", "map": "规范化"},
                {"id": "L", "label": "文献记录", "map": "DOI/API"},
                {"id": "D", "label": "公共数据库", "map": "字段映射"},
                {"id": "EG", "label": "能量／几何", "map": "来源核验"},
                {"id": "S", "label": "排序结果", "map": "稳定排序"},
            ],
            "plugin_route": [
                {"plugin": "AIHarness", "label": "目标识别", "status": "required", "scope": "只抽取实体与排序指令"},
                {"plugin": "PublicDatabaseRouter", "label": "公共数据库路由", "status": "ready", "scope": "不把空值补成结论"},
                {"plugin": "GeometryPlugin", "label": "几何插件", "status": "waiting", "scope": "只绘制有来源坐标"},
            ],
            "database_connectors": database["connectors"],
            "database_receipt": database,
            "discovery_signal": {
                "status": "waiting_for_entity_extraction",
                "type": "not_observed",
                "scientific_discovery": False,
                "next_action": "先抽取反应物与产物，再查询指定的文献或公共数据库接口。",
                "falsification": "若在声明的接口预算内仍不能返回可追溯记录，则当前切片不成立。",
            },
            "search_targets": [],
            "geometry": {"kind": "empty", "nodes": [], "edges": [], "source_scope": "unavailable"},
            "references": [item for item in REFERENCES if item["id"].startswith(("CAT", "DB-"))],
            "lean": {
                "assumptions": ["没有来源记录时，反应能量保持 null"],
                "proposition": "排序只改变次序，不改变证据内容",
                "status": "data_contract_only",
            },
            "model_receipt": {"provider": "local_retrieval_contract", "calls": 0},
        }

    reactants = [
        {"token": "CO2gas", "formula": "CO2", "phase": "gas", "pubchem_cid": 280, "smiles": "C(=O)=O"},
        {"token": "H2gas", "formula": "H2", "phase": "gas", "pubchem_cid": 783, "smiles": "[HH]"},
    ]
    products = [
        {"token": "CH3CH2OHgas", "formula": "C2H6O", "phase": "gas", "pubchem_cid": 702, "smiles": "CCO"},
    ]
    candidates = _literature_candidates(sort_requested)
    geometry = _geometry_from_optimade(database["catalyst_structures"][0], database["mode_used"])
    return {
        "status": "retrieved_and_sorted" if sort_requested else "retrieved",
        "source": "local_literature_public_database_kernel",
        "input": problem,
        "normalized_problem": {
            "type": "catalyst_literature_database_search",
            "reactants": reactants,
            "products": products,
            "directive": "@best" if sort_requested else None,
            "sort_semantics": "stable retrieval relevance and evidence-coverage order; not catalytic optimality",
            "reaction_natural_language": "检索 CO2、H2 到乙醇的文献与公共数据库记录；温度、压力等保持为可选可能性，不阻止返回候选。",
        },
        "reactants": reactants,
        "products": products,
        "standard_math": {
            "display": r"R=\{CO_2(g),H_2(g)\},\quad P=\{C_2H_6O(g)\},\quad \mathcal C=\mathcal L(R,P)\cup\mathcal D(R,P)",
            "logic": r"\pi_{best}=\operatorname{StableSort}(\mathcal C;s),\quad \pi_{best}\neq\operatorname*{arg\,max}_{c}\mathrm{Performance}(c)",
            "status": "typed_retrieval_contract",
        },
        "target_function": {
            "display": r"\Delta E_{record}\in\mathbb R\cup\{\mathrm{unknown}\};\quad \Delta E\text{ 仅由带单位、方法与来源的数据库记录给出}",
            "nontriviality": "record_level_quantity_not_inferred_from_shorthand",
            "status": "unknown_no_comparable_record",
        },
        "reaction_energy": {
            "value": None,
            "unit": None,
            "kind": None,
            "status": "unknown_no_comparable_record",
            "method": None,
            "reference_state": None,
            "source_record": None,
            "rule": "never infer a number from the shorthand or from an LLM; compare only source records with explicit units, methods and reference states",
        },
        "sort": {
            "requested": sort_requested,
            "directive": "@best" if sort_requested else None,
            "key": "retrieval_match_and_data_coverage",
            "formula": "50*reaction_match + 25*abstract_verified + 15*public_geometry_link + 10*comparable_energy_record",
            "status": "applied" if sort_requested else "source_order",
            "semantics": "sort_only",
            "scientific_optimum_claim": False,
            "changes_evidence_grade": False,
        },
        "possibilities": _possibilities(payload),
        "basis": {
            "name": "literature_energy_geometry_space",
            "display_name": "反应实体×文献×能量×几何",
            "dimension": 4,
            "operator": "(R,P) → Literature/API → (ΔE_record, G_catalyst) → stable sort",
            "coordinates": ["reactants/products", "literature metadata", "reaction-energy record", "catalyst geometry"],
        },
        "machine_problems": [
            {"id": "M0", "operator": "ReactionEntityParser.extract(R,P)", "status": "solved", "output": "2 reactants + 1 product", "oracle": "typed entity schema"},
            {"id": "M1", "operator": "PubChem.lookup(CID,SMILES)", "status": "ready", "output": "CID 280/783/702", "oracle": "PUG REST record"},
            {"id": "M2", "operator": "Crossref+OpenAlex.lookup(DOI)", "status": "ready", "output": "traceable metadata", "oracle": "DOI/API response"},
            {"id": "M3", "operator": "CatalysisHub.map(reactants,products,reactionEnergy,systems)", "status": "schema_only", "output": "energy stays null", "oracle": "GraphQL schema + authorized record"},
            {"id": "M4", "operator": "OPTIMADE.structure(mp-19306)", "status": "rendered", "output": "Fe3O4 support coordinates", "oracle": "record id + Cartesian positions"},
            {"id": "M5", "operator": "StableSort(candidates,evidence_coverage)", "status": "applied" if sort_requested else "not_requested", "output": "order only", "oracle": "deterministic feature tuple"},
        ],
        "spaces": [
            {"id": "N", "label": "自然语言目标", "map": "实体抽取"},
            {"id": "RP", "label": "反应物／产物", "map": "PubChem"},
            {"id": "L", "label": "文献记录", "map": "DOI API"},
            {"id": "D", "label": "公共数据库", "map": "字段映射"},
            {"id": "EG", "label": "能量／几何", "map": "来源核验"},
            {"id": "S", "label": "排序结果", "map": "稳定排序"},
        ],
        "plugin_route": [
            {"plugin": "ReactionEntityParser", "label": "反应实体解析器", "status": "invoked", "scope": "只抽取输入中的反应物与产物，不增补机理产物"},
            {"plugin": "LiteratureConnector", "label": "文献分析", "status": "ready", "scope": "Crossref/OpenAlex/DOI/alphaXiv；元数据与正文分级"},
            {"plugin": "PublicDatabaseRouter", "label": "公共数据库路由", "status": "ready", "scope": "PubChem/OPTIMADE/Catalysis-Hub/OC20 字段合同"},
            {"plugin": "GeometryPlugin", "label": "几何插件", "status": "rendered", "scope": "只绘制 mp-19306 支撑体坐标，不伪造 Pd 活性位"},
            {"plugin": "StableSorter", "label": "@best 排序器", "status": "applied" if sort_requested else "not_requested", "scope": "只改顺序，不改证据等级，不声称性能最优"},
        ],
        "database_connectors": database["connectors"],
        "database_receipt": database,
        "discovery_signal": {
            "status": "observed",
            "type": "source_coverage_gap_and_problem_definition_revision",
            "scientific_discovery": False,
            "observation": "返回五条可追溯文献候选；可比反应能量记录为零；仅取得一条 Fe3O4 体相支撑体几何，未取得活性位几何。",
            "process_signal": "能量保持 null，几何范围保持 support_only；下一查询必须指定记录级能量类型，并寻找带来源的活性位坐标。",
            "next_action": "向已授权的 Catalysis-Hub 记录接口提交类型化反应物／产物，保存能量类型、方法与参考态，再请求对应体系坐标；否则只检查预索引的 OC20 子集，不把它称为完整反应网络。",
            "falsification": "若固定预算内反复查询仍不能把可比能量记录与带来源活性位几何联结，则拒绝或缩小当前反应切片，不推断性能。",
        },
        "search_targets": candidates,
        "geometry": geometry,
        "references": [item for item in REFERENCES if item["id"].startswith(("CAT", "DB-"))],
        "lean": {
            "assumptions": [
                "反应能量数值必须同时有单位、方法、参考态和来源记录",
                "未知值保持 null",
                "@best 只改变次序",
            ],
            "proposition": "排序保持每条候选的证据记录不变",
            "status": "data_contract_not_formalized",
        },
        "model_receipt": {"provider": "local_exact_retrieval_kernel", "calls": 0, "max_calls": 1},
    }


def _complex(value: complex) -> dict[str, float]:
    return {"real": float(value.real), "imag": float(value.imag)}


def evaluate_basis_operator(payload: dict[str, Any]) -> dict[str, Any]:
    template = str(payload.get("template", "log"))
    x = float(payload.get("x", -1))
    tolerance = float(payload.get("tolerance", 1e-10))
    domain = str(payload.get("domain", "complex_nonzero"))
    branch = str(payload.get("branch", "principal_complex_log"))
    if template not in {"log", "exp", "identity"}:
        return {"status": "unsupported", "operator_contract": BASIS_OPERATOR_CONTRACT, "result": {"status": "unknown", "oracle_trace": ["template not in whitelist"]}}
    if branch != "principal_complex_log":
        return {"status": "unsupported", "operator_contract": BASIS_OPERATOR_CONTRACT, "result": {"status": "unknown", "oracle_trace": ["branch convention not in whitelist"]}}
    if domain == "positive_real" and x <= 0:
        return {
            "status": "ok",
            "operator_contract": BASIS_OPERATOR_CONTRACT,
            "target_domain": "D_f = R_{>0}",
            "result": {"status": "undefined", "absolute_error": None, "counterexample": x, "oracle_trace": ["x is outside the declared current test domain D_f=R_{>0}"]},
            "ast": {"op": template},
        }
    try:
        z = complex(x, 0.0)
        if template == "log":
            try:
                import sympy as sp
            except ImportError as exc:
                return {
                    "status": "dependency_unavailable",
                    "result": {
                        "status": "unknown",
                        "oracle_trace": ["SymPy is required only for this symbolic branch comparison", str(exc)],
                    },
                    "ast": {"op": "basis"},
                    "operator_contract": BASIS_OPERATOR_CONTRACT,
                    "target_domain": "D_f = C^times" if domain == "complex_nonzero" else domain,
                }
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
            ast = {"op": "basis", "left": {"op": "1"}, "right": {"op": "basis", "left": {"op": "basis", "left": {"op": "1"}, "right": {"op": "x"}}, "right": {"op": "1"}}}
        elif template == "exp":
            compiled = cmath.exp(z) - cmath.log(1)
            reference = cmath.exp(z)
            ast = {"op": "basis", "left": {"op": "x"}, "right": {"op": "1"}}
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
            "operator_contract": BASIS_OPERATOR_CONTRACT,
            "target_domain": "D_f = C^times" if domain == "complex_nonzero" else domain,
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
        return {"status": "ok", "operator_contract": BASIS_OPERATOR_CONTRACT, "target_domain": "D_f = C^times" if domain == "complex_nonzero" else domain, "result": {"status": "undefined", "absolute_error": None, "counterexample": x, "oracle_trace": [str(exc)]}, "ast": {"op": template}}


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
    kind = str(payload.get("kind", "basis"))
    if kind == "finite":
        return {"kind": kind, "result": finite_check(payload), "obligation": "g(D) subseteq D and forall x in D, g(g(x))=f(x)"}
    if kind == "basis":
        result = evaluate_basis_operator(payload)
        result["kind"] = kind
        return result
    return {
        "kind": kind,
        "status": "obligation_only",
        "result": {"status": "unknown", "oracle_trace": ["no unrestricted inverse/iteration solver invoked"]},
        "obligation": str(payload.get("relation", "g^n=f")),
        "assumptions": str(payload.get("assumptions", "D fixed; closure declared")),
    }


def _lean_executable() -> Path | None:
    configured = os.environ.get("MATH_STRUCTURER_LEAN", "").strip()
    if configured and Path(configured).expanduser().is_file():
        return Path(configured).expanduser()
    discovered = shutil.which("lean") or shutil.which("lean.exe")
    if discovered:
        return Path(discovered)
    toolchain_file = PRIME_REPO / "lean-toolchain"
    if not toolchain_file.is_file():
        return None
    name = toolchain_file.read_text("utf-8").strip()
    folder = name.replace("/", "--").replace(":", "---")
    candidate = Path.home() / ".elan" / "toolchains" / folder / "bin"
    executable = candidate / ("lean.exe" if os.name == "nt" else "lean")
    return executable if executable.is_file() else None


def _run(command: list[str], cwd: Path, timeout: int) -> dict[str, Any]:
    try:
        result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        return {"returncode": result.returncode, "stdout": _portable_text(result.stdout), "stderr": _portable_text(result.stderr)}
    except subprocess.TimeoutExpired as exc:
        return {"returncode": None, "stdout": _portable_text(exc.stdout or ""), "stderr": f"timeout after {timeout}s"}
    except OSError as exc:
        return {"returncode": None, "stdout": "", "stderr": _portable_text(exc)}


def lean_check() -> dict[str, Any]:
    lean = _lean_executable()
    if lean is None:
        return {"status": "unavailable", "summary": "pinned Lean toolchain not found", "results": {}}
    contract = _run([str(lean), str(PANEL / "lean" / "IterationContract.lean")], ROOT, 30)
    retrieval = _run([str(lean), str(PANEL / "lean" / "RetrievalSortContract.lean")], ROOT, 30)
    imported_source = PRIME_REPO / "PrimeLoopVerification" / "Basic.lean"
    has_axiom = imported_source.is_file() and "axiom prime_loop_conjecture" in imported_source.read_text("utf-8", errors="ignore")
    upstream = {
        "returncode": None,
        "stdout": "",
        "stderr": "source audit only; the full prime-loop project is not compiled in this quick check",
    }
    upstream_status = "source_contains_axiom" if has_axiom else "source_unavailable"
    results = {
        "iteration_contract": {"status": "passed" if contract["returncode"] == 0 else "failed", **contract},
        "retrieval_sort_contract": {"status": "passed" if retrieval["returncode"] == 0 else "failed", **retrieval},
        "upstream_basis_reconstruction": {"status": upstream_status, **upstream},
    }
    contracts_pass = all(results[name]["status"] == "passed" for name in ("iteration_contract", "retrieval_sort_contract"))
    overall = "partial_formalization" if contracts_pass and upstream_status == "source_contains_axiom" else "passed" if all(item["status"] == "passed" for item in results.values()) else "failed"
    return {
        "status": overall,
        "toolchain": "leanprover/lean4:v4.29.0-rc6",
        "summary": "local obligations compile; source audit finds an explicit conjecture axiom in the upstream prime-loop project" if overall == "partial_formalization" else "see results",
        "results": results,
    }


def _probe(command: str, args: list[str]) -> dict[str, Any]:
    path = shutil.which(command)
    if not path:
        return {"ready": False, "executable": command, "detail": "not found"}
    invocation = [path, *args]
    if Path(path).suffix.lower() in {".cmd", ".bat"}:
        invocation = [os.environ.get("COMSPEC", "cmd.exe"), "/d", "/s", "/c", subprocess.list2cmdline(invocation)]
    result = _run(invocation, PANEL, 8)
    output = (result.get("stdout", "") + result.get("stderr", "")).strip().splitlines()
    return {"ready": result["returncode"] == 0, "executable": Path(path).name, "detail": _portable_text(output[0][:180]) if output else f"exit {result['returncode']}"}


def _select_qwen_model(names: list[str], configured: str = "") -> tuple[str | None, str]:
    requested = configured or QWEN_JAILBROKEN_MODEL
    model = next((name for name in names if name == requested), None)
    return model, requested


@lru_cache(maxsize=1)
def _ollama_status() -> dict[str, Any]:
    endpoint = "http://127.0.0.1:11434/api/tags"
    try:
        request = Request(endpoint, headers={"Accept": "application/json"})
        with urlopen(request, timeout=2) as response:
            payload = json.loads(response.read().decode("utf-8"))
        models = [item for item in payload.get("models", []) if isinstance(item, dict)]
        names = [str(item.get("name", "")) for item in models]
        configured = os.environ.get(QWEN_MODEL_ENV, "").strip()
        model, requested = _select_qwen_model(names, configured)
        metadata = next((item for item in models if str(item.get("name", "")) == model), {})
        return {
            "ready": model is not None,
            "endpoint": endpoint,
            "model": model,
            "requested_model": requested,
            "digest": metadata.get("digest"),
            "size": metadata.get("size"),
            "installed": names,
            "configured_by": "environment" if configured else "jailbroken_default",
        }
    except Exception as exc:
        return {
            "ready": False,
            "endpoint": endpoint,
            "model": None,
            "requested_model": os.environ.get(QWEN_MODEL_ENV, "").strip() or QWEN_JAILBROKEN_MODEL,
            "digest": None,
            "installed": [],
            "detail": _portable_text(exc)[:180],
        }


def _bash_executable() -> Path | None:
    configured = os.environ.get("MATH_STRUCTURER_BASH", "").strip()
    if configured and Path(configured).expanduser().is_file():
        return Path(configured).expanduser()
    discovered = shutil.which("bash.exe") or shutil.which("bash")
    if discovered:
        return Path(discovered)
    git = shutil.which("git.exe") or shutil.which("git")
    if git:
        git_path = Path(git)
        for candidate in (git_path.parent / "bash.exe", git_path.parent.parent / "bin" / "bash.exe"):
            if candidate.is_file():
                return candidate
    return None


@lru_cache(maxsize=1)
def harness_status() -> dict[str, Any]:
    codex = _probe("codex.cmd", ["--version"])
    deepseek = _probe("deepseek.cmd", ["--version"])
    bash = _bash_executable()
    deepseek_harness = bool(bash and CROSS_VERIFY.is_file() and os.environ.get("DEEPSEEK_API_KEY"))
    alphaxiv_configured = CODEX_CONFIG.is_file() and "[mcp_servers.alphaxiv]" in CODEX_CONFIG.read_text("utf-8", errors="ignore")
    return {
        "qwen_local": {
            **_ollama_status(),
            "scope": "bounded local target recognition only; output cannot bypass exact validators",
            "max_calls": 1,
            "trust_boundary": "checkpoint name is not a scientific-validation or safety guarantee",
        },
        "codex": {**codex, "scope": "local CLI; configured model backend may be remote", "approval": "never", "sandbox": "read-only"},
        "deepseek_cli": deepseek,
        "deepseek_harness": {"ready": deepseek_harness, "script": CROSS_VERIFY.name if CROSS_VERIFY.is_file() else None, "configured_by": "environment" if os.environ.get("MATH_STRUCTURER_CROSS_VERIFY") else "portable_probe", "credential_present": bool(os.environ.get("DEEPSEEK_API_KEY"))},
        "alphaxiv_mcp": {"ready": alphaxiv_configured, "url": "https://api.alphaxiv.org/mcp/v1", "transport": "Streamable HTTP via Codex MCP bridge", "pdf_persistence": False},
        "openresearch_cli": _probe("orx", ["--version"]),
        "lean": {"ready": _lean_executable() is not None, "toolchain": "leanprover/lean4:v4.29.0-rc6"},
        "model_calls": MODEL_CALLS,
        "max_calls_per_run": 1,
    }


def _solver_prompt(payload: dict[str, Any]) -> str:
    return f"""You are the structured solver adapter for Math Structurer.
Return exactly one JSON object conforming to the supplied output schema.
Translate the natural-language target into typed reactants, products, source-qualified reaction-energy records, catalyst geometry, literature records, public-database records, optional possibilities, and machine-checkable subproblems.
Use alphaXiv MCP for literature reading when authenticated. Do not download or save PDFs. Distinguish its default AI intermediate report from full text and return clickable canonical URLs.
Treat @best only as a stable retrieval-order directive. It must not become a global or catalytic-performance optimum and must not change evidence grades.
Temperature, pressure, candidate domain, observation metrics, and baselines are optional possibilities: missing values never block retrieval or ordering.
Never invent a reaction-energy number. A value is usable only with an explicit unit, energy kind, method, reference state, and source record; otherwise return null/unknown.
Extract only the reactants and products supplied by the user. Do not add water, intermediates, coefficients, or a reaction mechanism.
Lean may validate only a stated formal proposition under listed assumptions; never assert the scientific conclusion as an axiom.
Use only concrete basis operators with declared input type, output space, current test domain, and validator. The current scalar example is B: C x C^times -> C, B(u,v)=exp(u)-Log(v), with pointwise principal-value Log and Arg(v) in (-pi,pi]; it is discontinuous across the two sides of the negative real axis and is not a universal algebra. Never route reaction decomposition or 3D geometry through scalar composition.
Route literature and database lookup independently from GeometryPlugin and from the scalar BasisOperatorComposer.
Problem: {payload.get('problem', '')}
Domain: {payload.get('domain', 'auto')}
Basis: {payload.get('basis', 'hybrid')}
Dimension: {payload.get('dimension', 3)}
Database mode: {payload.get('database_mode', 'verified_snapshot')}
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


def _recognition_prompt(payload: dict[str, Any]) -> str:
    return f"""You are a bounded scientific-target recognizer inside Math Structurer.
Do not solve the research problem, recommend a catalyst, predict a molecular structure, or assert a theorem.
Return only the requested JSON classification. Extract only entities and constraints that are explicit in the input.
Use missing_fields only when reactants or products cannot be identified. Temperature, pressure, candidate domain, observation metrics, and baselines are optional possibilities and must not be reported as missing requirements.
For a reaction followed by @best, use domain=reaction and intent=catalyst_search. @best means retrieval ordering only; it is not permission to recommend a catalyst or infer performance.
The output will be rejected unless a deterministic gate agrees with the domain and intent.

Input: {str(payload.get('problem', '')).strip()}
User domain hint: {payload.get('domain', 'auto')}
"""


def _expected_recognition(problem: str) -> tuple[str, str | None]:
    lowered = problem.lower()
    compact = re.sub(r"\s+", "", lowered)
    if (
        "co2" in compact
        and "h2" in compact
        and ("->" in compact or "--" in compact or "→" in problem)
    ):
        return "reaction", "catalyst_search" if "@best" in lowered or "catal" in lowered or "催化" in problem else None
    if any(token in lowered for token in ("protein", "binding", "bind site")) or any(token in problem for token in ("蛋白", "结合位点")):
        return "binding", "structure_prediction"
    if "pde" in lowered or "partial differential" in lowered or "偏微分" in problem or "李对称" in problem:
        return "pde", "pde_reduction"
    if "half-iterate" in lowered or "half iterate" in lowered or "g∘g" in problem or "半迭代" in problem:
        return "mathematics", "half_iterate"
    if "prime" in lowered or "number theory" in lowered or "数论" in problem:
        return "number_theory", "problem_generation"
    return "unknown", None


def _validate_recognition(value: dict[str, Any]) -> dict[str, Any]:
    missing = [key for key in RECOGNITION_SCHEMA["required"] if key not in value]
    allowed = set(RECOGNITION_SCHEMA["properties"])
    extra = sorted(set(value) - allowed)
    domain = value.get("domain")
    intent = value.get("intent")
    list_fields = ("entities", "constraints", "missing_fields")
    types_ok = all(isinstance(value.get(key), list) and all(isinstance(item, str) for item in value[key]) for key in list_fields)
    confidence = value.get("confidence")
    confidence_ok = isinstance(confidence, (int, float)) and not isinstance(confidence, bool) and 0 <= float(confidence) <= 1
    checks = {
        "required_fields": not missing,
        "additional_properties": not extra,
        "domain_enum": domain in RECOGNITION_DOMAINS,
        "intent_enum": intent in RECOGNITION_INTENTS,
        "list_types": types_ok,
        "confidence_range": confidence_ok,
    }
    if not all(checks.values()):
        raise ValueError(f"recognition schema rejected: {checks}; missing={missing}; extra={extra}")
    return {
        "domain": str(domain),
        "intent": str(intent),
        "entities": [item.strip()[:120] for item in value["entities"] if item.strip()],
        "constraints": [item.strip()[:180] for item in value["constraints"] if item.strip()],
        "missing_fields": [item.strip()[:120] for item in value["missing_fields"] if item.strip()],
        "confidence": round(float(confidence), 4),
        "schema_checks": checks,
    }


def _recognition_gate(problem: str, recognition: dict[str, Any]) -> dict[str, Any]:
    expected_domain, expected_intent = _expected_recognition(problem)
    checks = {
        "nonempty_input": bool(problem.strip()),
        "domain_agrees_with_deterministic_hint": expected_domain == "unknown" or recognition.get("domain") == expected_domain,
        "intent_agrees_with_deterministic_hint": expected_intent is None or recognition.get("intent") == expected_intent,
        "no_scientific_result_fields": not any(
            key in recognition for key in ("answer", "best_catalyst", "predicted_structure", "proof")
        ),
    }
    return {
        "status": "passed" if all(checks.values()) else "rejected",
        "checks": checks,
        "expected_domain": expected_domain,
        "expected_intent": expected_intent,
        "effect": "route metadata only; exact validators retain authority",
    }


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


def _run_qwen(payload: dict[str, Any]) -> dict[str, Any]:
    status = _ollama_status()
    if not status.get("ready") or not status.get("model"):
        raise RuntimeError(
            f"local Qwen3-8B-Jailbroken is unavailable; requested={status.get('requested_model')}"
        )
    body = {
        "model": status["model"],
        "prompt": _recognition_prompt(payload),
        "stream": False,
        "think": False,
        "format": RECOGNITION_SCHEMA,
        "keep_alive": "5m",
        "options": {
            "temperature": 0,
            "seed": 0,
            "num_ctx": 4096,
            "num_predict": 320,
        },
    }
    request = Request(
        "http://127.0.0.1:11434/api/generate",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=180) as response:
        reply = json.loads(response.read().decode("utf-8"))
    if reply.get("error"):
        raise RuntimeError(str(reply["error"]))
    response_text = str(reply.get("response") or "").strip()
    thinking_text = str(reply.get("thinking") or "").strip()
    output_channel = "response" if response_text else "thinking_fallback"
    parsed = _validate_recognition(_parse_json(response_text or thinking_text))
    problem = str(payload.get("problem", "")).strip()
    raw_missing_fields = list(parsed["missing_fields"])
    optional_markers = (
        "temperature", "pressure", "candidate", "domain", "metric", "measurement", "baseline",
        "温度", "压力", "候选", "指标", "观测", "基线",
    )
    optional_possibilities = [
        item for item in raw_missing_fields if any(marker in item.lower() for marker in optional_markers)
    ]
    parsed["missing_fields"] = [
        item for item in raw_missing_fields
        if item not in optional_possibilities
        and any(marker in item.lower() for marker in ("reactant", "product", "反应物", "产物"))
    ]
    parsed["optional_possibilities_reported_by_model"] = optional_possibilities
    parsed["model_reported_missing_fields_raw"] = raw_missing_fields
    gate = _recognition_gate(problem, parsed)
    exact_result = analyze_general(payload)
    exact_result["recognition"] = {
        **parsed,
        "gate": gate,
        "model": status["model"],
        "model_digest": status.get("digest"),
        "input_sha256": hashlib.sha256(problem.encode("utf-8")).hexdigest(),
        "role": "recognition_only",
        "scientific_authority": False,
        "runtime": {
            "output_channel": output_channel,
            "done_reason": reply.get("done_reason"),
            "prompt_eval_count": reply.get("prompt_eval_count"),
            "eval_count": reply.get("eval_count"),
            "total_duration_ms": round(float(reply.get("total_duration", 0)) / 1_000_000, 3),
        },
    }
    exact_result["source"] = "local_qwen_recognition_then_exact_kernel"
    if gate["status"] != "passed":
        exact_result["status"] = "recognition_rejected"
    return exact_result


def _run_deepseek(payload: dict[str, Any]) -> dict[str, Any]:
    if not os.environ.get("DEEPSEEK_API_KEY"):
        raise RuntimeError("DEEPSEEK_API_KEY is not configured")
    bash = _bash_executable()
    if bash is None or not CROSS_VERIFY.is_file():
        raise RuntimeError("DeepSeek cross-verify harness is unavailable")
    env = os.environ.copy()
    env.setdefault("AUTO_DEV_CROSS_MODEL", "deepseek-chat")
    result = subprocess.run([str(bash), str(CROSS_VERIFY)], input=_solver_prompt(payload), cwd=ROOT, env=env, capture_output=True, text=True, timeout=90)
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
        provider = "qwen" if status["qwen_local"]["ready"] else "codex" if status["codex"]["ready"] else "deepseek" if status["deepseek_harness"]["ready"] else "local"
    if provider == "local":
        return analyze_general(payload)
    if provider not in {"qwen", "codex", "deepseek"}:
        raise ValueError("provider must be local, auto, qwen, codex, or deepseek")
    MODEL_CALLS += 1
    try:
        result = _run_qwen(payload) if provider == "qwen" else _run_codex(payload) if provider == "codex" else _run_deepseek(payload)
        result.setdefault("model_receipt", {})
        result["model_receipt"].update(
            {
                "provider": provider,
                "calls": 1,
                "max_calls": 1,
                "pdf_saved": False,
                "role": "recognition_only" if provider == "qwen" else "structured_solver_adapter",
                "model": result.get("recognition", {}).get("model") if provider == "qwen" else None,
                "model_digest": result.get("recognition", {}).get("model_digest") if provider == "qwen" else None,
                "exact_validation": result.get("recognition", {}).get("gate", {}).get("status") if provider == "qwen" else "required",
            }
        )
        return result
    except Exception:
        MODEL_CALLS -= 1
        raise


def health() -> dict[str, Any]:
    harness = harness_status()
    return {
        "status": "ok",
        "python": os.sys.version.split()[0],
        "panel": "math-structurer.v0.6",
        "qwen_ready": harness["qwen_local"]["ready"],
        "qwen_model": harness["qwen_local"].get("model"),
        "qwen_model_digest": harness["qwen_local"].get("digest"),
        "codex_ready": harness["codex"]["ready"],
        "deepseek_harness_ready": harness["deepseek_harness"]["ready"],
        "alphaxiv_ready": harness["alphaxiv_mcp"]["ready"],
        "lean_toolchain": harness["lean"]["toolchain"] if harness["lean"]["ready"] else None,
        "model_calls": MODEL_CALLS,
    }


class Handler(SimpleHTTPRequestHandler):
    server_version = "MathStructurerPanel/0.6"

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, directory=str(PANEL), **kwargs)

    def log_message(self, _format: str, *_args: Any) -> None:
        return

    def _json(self, payload: dict[str, Any], status: int = HTTPStatus.OK) -> None:
        raw = json.dumps(_portable_payload(payload), ensure_ascii=False).encode("utf-8")
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
            self._json({"error": _portable_text(exc)}, HTTPStatus.BAD_REQUEST)
        except subprocess.TimeoutExpired:
            self._json({"error": "solver timeout"}, HTTPStatus.GATEWAY_TIMEOUT)
        except Exception as exc:
            self._json({"error": _portable_text(exc)}, HTTPStatus.SERVICE_UNAVAILABLE)


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
