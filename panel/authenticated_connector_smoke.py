from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import time
from typing import Any
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "artifacts" / "authenticated_connector_acceptance.json"
MP_URL = (
    "https://api.materialsproject.org/materials/summary/"
    "?material_ids=mp-19306&_fields=material_id,formula_pretty,structure&_limit=1"
)
ALPHAXIV_URL = "https://api.alphaxiv.org/mcp/v1"
PAPER_URL = "https://arxiv.org/abs/2408.07818"


def _required_environment(name: str, *fallbacks: str) -> str:
    for candidate in (name, *fallbacks):
        value = os.environ.get(candidate, "").strip()
        if value:
            return value
    raise RuntimeError(f"required environment variable is missing: {name}")


def verify_materials_project() -> dict[str, Any]:
    key = _required_environment("MP_API_KEY", "MATERIALS_PROJECT_API_KEY")
    request = Request(
        MP_URL,
        headers={
            "X-API-KEY": key,
            "User-Agent": "MathStructurer/0.6 authenticated verification",
        },
    )
    with urlopen(request, timeout=40) as response:
        payload = json.loads(response.read().decode("utf-8"))
    records = payload.get("data") or []
    if len(records) != 1:
        raise AssertionError(f"expected one Materials Project record, received {len(records)}")
    record = records[0]
    sites = (record.get("structure") or {}).get("sites") or []
    if record.get("formula_pretty") != "Fe3O4" or len(sites) != 14:
        raise AssertionError("authenticated Materials Project record did not preserve Fe3O4/14-site scope")
    return {
        "status": "passed",
        "http": response.status,
        "requested_material_id": "mp-19306",
        "returned_material_id": record.get("material_id"),
        "formula": record.get("formula_pretty"),
        "site_count": len(sites),
        "interpretation": (
            "The authenticated summary endpoint resolved the requested legacy identifier to the "
            "returned canonical identifier. The public OPTIMADE geometry remains scoped as a bulk/support "
            "record and is not an active-site structure."
        ),
    }


def _mcp_call(payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    key = _required_environment("ALPHAXIV_API_KEY")
    request = Request(
        ALPHAXIV_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "User-Agent": "MathStructurer/0.6 authenticated verification",
        },
        method="POST",
    )
    with urlopen(request, timeout=240) as response:
        raw = response.read().decode("utf-8", errors="replace")
        status = response.status
    messages: list[dict[str, Any]] = []
    for line in raw.splitlines():
        if not line.startswith("data:"):
            continue
        try:
            messages.append(json.loads(line[5:].strip()))
        except json.JSONDecodeError:
            continue
    if not messages and raw.lstrip().startswith("{"):
        messages.append(json.loads(raw))
    if not messages:
        raise RuntimeError("alphaXiv returned no JSON-RPC message")
    message = messages[-1]
    if message.get("error"):
        raise RuntimeError(f"alphaXiv JSON-RPC error: {message['error'].get('code')}")
    return status, message


def verify_alphaxiv(full_text: bool) -> dict[str, Any]:
    initialize_http, initialize = _mcp_call(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {"name": "MathStructurer", "version": "0.6"},
            },
        }
    )
    tools_http, tools_message = _mcp_call(
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
    )
    result = tools_message.get("result") or {}
    tool_names = sorted(
        tool.get("name") for tool in result.get("tools", []) if tool.get("name")
    )
    if "get_paper_content" not in tool_names:
        raise AssertionError("alphaXiv did not advertise get_paper_content")
    receipt: dict[str, Any] = {
        "status": "passed",
        "initialize_http": initialize_http,
        "tools_http": tools_http,
        "protocol": (initialize.get("result") or {}).get("protocolVersion"),
        "server": (initialize.get("result") or {}).get("serverInfo"),
        "tool_count": len(tool_names),
        "tools": tool_names,
        "raw_full_text_requested": full_text,
    }
    if full_text:
        started = time.perf_counter()
        full_text_http, content_message = _mcp_call(
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "get_paper_content",
                    "arguments": {"url": PAPER_URL, "fullText": True},
                },
            }
        )
        content = (content_message.get("result") or {}).get("content") or []
        texts = [block.get("text", "") for block in content if block.get("type") == "text"]
        extracted = "\n".join(texts)
        if not extracted or "Boltzmann" not in extracted or "hard sphere" not in extracted.lower():
            raise AssertionError("alphaXiv full-text extraction did not contain the expected paper markers")
        receipt["full_text"] = {
            "http": full_text_http,
            "paper": PAPER_URL,
            "content_blocks": len(texts),
            "characters": len(extracted),
            "sha256": hashlib.sha256(extracted.encode("utf-8")).hexdigest(),
            "elapsed_seconds": round(time.perf_counter() - started, 3),
            "stored_locally": False,
        }
    return receipt


def run(full_text: bool) -> dict[str, Any]:
    result = {
        "checked_at": datetime.now().astimezone().isoformat(),
        "status": "passed",
        "credentials": {
            "MP_API_KEY": "present_not_recorded",
            "ALPHAXIV_API_KEY": "present_not_recorded",
        },
        "materials_project": verify_materials_project(),
        "alphaxiv": verify_alphaxiv(full_text),
        "catalysis_hub": "not_tested_no_CATALYSIS_HUB_API_KEY",
        "deepseek": "not_tested_no_DEEPSEEK_API_KEY",
        "scientific_discovery": False,
        "boundary": (
            "Authenticated access verifies interface availability and source retrieval only. It does not "
            "supply a comparable reaction-energy record, an active-site geometry, or a catalyst ranking."
        ),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--full-text",
        action="store_true",
        help="request raw alphaXiv extraction and record only its length and hash",
    )
    arguments = parser.parse_args()
    print(json.dumps(run(arguments.full_text), ensure_ascii=False, sort_keys=True))
