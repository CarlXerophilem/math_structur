from __future__ import annotations

import argparse
from http.client import HTTPConnection
import importlib.util
import json
from pathlib import Path
import sys
import threading
from typing import Any

ROOT = Path(__file__).resolve().parent
DEMO_QUERY = "CO2gas+H2gas -- CH3CH2OHgas @best"

_SERVER_PATH = ROOT / "panel" / "serve_panel.py"
_SERVER_SPEC = importlib.util.spec_from_file_location("math_structurer_serve_panel", _SERVER_PATH)
if _SERVER_SPEC is None or _SERVER_SPEC.loader is None:
    raise RuntimeError(f"cannot load panel server from {_SERVER_PATH}")
serve_panel = importlib.util.module_from_spec(_SERVER_SPEC)
_SERVER_SPEC.loader.exec_module(serve_panel)


def _request(
    connection: HTTPConnection,
    method: str,
    path: str,
    payload: dict[str, Any] | None = None,
) -> tuple[int, str, bytes]:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {} if body is None else {"Content-Type": "application/json"}
    connection.request(method, path, body=body, headers=headers)
    response = connection.getresponse()
    return response.status, response.getheader("Content-Type", ""), response.read()


def quick_check() -> dict[str, Any]:
    """Exercise the static panel and exact local kernel over loopback only."""
    calls_before = serve_panel.MODEL_CALLS
    server = serve_panel.make_server("127.0.0.1", 0)
    port = server.server_port
    thread = threading.Thread(target=server.serve_forever, name="math-structurer-check", daemon=True)
    thread.start()

    try:
        connection = HTTPConnection("127.0.0.1", port, timeout=5)
        try:
            status, content_type, html = _request(connection, "GET", "/")
        finally:
            connection.close()
        if status != 200 or "text/html" not in content_type:
            raise RuntimeError(f"panel route failed: HTTP {status}, {content_type!r}")
        if b"Math Structurer" not in html:
            raise RuntimeError("panel title was not found")

        connection = HTTPConnection("127.0.0.1", port, timeout=5)
        try:
            status, content_type, raw = _request(
                connection,
                "POST",
                "/api/solver/run",
                {
                    "provider": "local",
                    "problem": DEMO_QUERY,
                    "domain": "reaction",
                    "basis": "literature_energy_geometry_space",
                    "dimension": 4,
                    "database_mode": "verified_snapshot",
                },
            )
        finally:
            connection.close()
        if status != 200 or "application/json" not in content_type:
            raise RuntimeError(f"local solver route failed: HTTP {status}, {content_type!r}")
        result = json.loads(raw.decode("utf-8"))

        if result.get("source") != "local_literature_public_database_kernel":
            raise RuntimeError("check did not use the local literature/public-database kernel")
        if [item.get("formula") for item in result.get("reactants", [])] != ["CO2", "H2"]:
            raise RuntimeError("reactant entities were not preserved")
        if [item.get("formula") for item in result.get("products", [])] != ["C2H6O"]:
            raise RuntimeError("product entities were not preserved")
        energy = result.get("reaction_energy", {})
        if energy.get("value") is not None or any(energy.get(key) is not None for key in ("unit", "kind", "method", "reference_state", "source_record")):
            raise RuntimeError("unknown reaction energy was fabricated or incompletely qualified")
        if result.get("sort", {}).get("semantics") != "sort_only":
            raise RuntimeError("@best was not compiled as an ordering-only directive")
        if result.get("sort", {}).get("scientific_optimum_claim") is not False:
            raise RuntimeError("retrieval order was mislabeled as a scientific optimum")
        if result.get("possibilities", {}).get("blocking") is not False:
            raise RuntimeError("optional possibilities blocked the retrieval")
        if result.get("geometry", {}).get("source_scope") != "support_only":
            raise RuntimeError("public geometry scope was not marked support-only")
        if result.get("database_receipt", {}).get("external_requests") != 0:
            raise RuntimeError("verified-snapshot mode made an external request")
        signal = result.get("discovery_signal", {})
        if signal.get("scientific_discovery") is not False or not signal.get("next_action") or not signal.get("falsification"):
            raise RuntimeError("the process signal did not preserve its discovery boundary or revision action")
        if serve_panel.MODEL_CALLS != calls_before:
            raise RuntimeError("a model call occurred during --check")

        return {
            "status": "passed",
            "panel_http": 200,
            "local_kernel": "passed",
            "core_reaction_fields": "passed",
            "reaction_energy": None,
            "sort_semantics": "sort_only",
            "possibilities_blocking": False,
            "geometry_scope": "support_only",
            "database_external_requests": 0,
            "discovery_signal": "process_only_with_next_action_and_falsification",
            "model_calls": 0,
            "external_network_requests": 0,
        }
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Start the local Math Structurer HTML5 workbench or run its offline check."
    )
    parser.add_argument("--host", default="127.0.0.1", help="bind address (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8766, help="TCP port (default: 8766)")
    parser.add_argument(
        "--check",
        action="store_true",
        help="run a loopback-only, zero-model validation and exit",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.check:
        try:
            receipt = quick_check()
        except Exception as exc:
            failure = {
                "status": "failed",
                "error_type": type(exc).__name__,
                "error": str(exc),
            }
            print(json.dumps(failure, ensure_ascii=False, sort_keys=True), file=sys.stderr)
            return 1
        artifact = ROOT / "artifacts" / "quick_check.json"
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_text(
            json.dumps(receipt, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"receipt={artifact}", file=sys.stderr)
        print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))
        return 0

    try:
        server = serve_panel.make_server(args.host, args.port)
    except OSError as exc:
        print(f"Math Structurer failed to start: {exc}", file=sys.stderr, flush=True)
        return 1
    display_host = "127.0.0.1" if args.host in {"0.0.0.0", "::"} else args.host
    url = f"http://{display_host}:{server.server_port}/"
    print(f"Math Structurer: {url}", flush=True)
    print("Scope: literature and public-database evidence retrieval; @best changes order only.", flush=True)
    print("Press Ctrl+C to stop.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nMath Structurer stopped.", flush=True)
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
