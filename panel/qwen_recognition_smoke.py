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
                "basis": "stoichiometric_kernel",
                "dimension": 4,
                "weights": {
                    "activity": 25,
                    "selectivity": 35,
                    "stability": 25,
                    "cost": 15,
                },
            },
        )
        recognition = result["recognition"]
        receipt = result["model_receipt"]
        normalized = result["normalized_problem"]
        matrix = result["basis"]["matrix"]
        assertions = {
            "exact_model_selected": recognition["model"] == serve_panel.QWEN_JAILBROKEN_MODEL,
            "digest_recorded": recognition.get("model_digest") == qwen.get("digest") and bool(qwen.get("digest")),
            "domain_recognized": recognition["domain"] == "reaction",
            "intent_recognized": recognition["intent"] == "catalyst_search",
            "recognition_gate_passed": recognition["gate"]["status"] == "passed",
            "recognition_only": recognition["role"] == "recognition_only" and recognition["scientific_authority"] is False,
            "one_model_call": receipt["calls"] == 1 and receipt["max_calls"] == 1,
            "unbalanced_input_detected": normalized["input_balance"] == "invalid",
            "balanced_equation_exact": normalized["balanced_equation"] == "2 CO2(g) + 6 H2(g) -> C2H5OH(g) + 3 H2O(g)",
            "element_conservation": matrix["check"] == [0, 0, 0],
            "unconditional_ranking_rejected": str(normalized["best_status"]).startswith("abstain"),
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
                "input_balance": normalized["input_balance"],
                "balanced_equation": normalized["balanced_equation"],
                "stoichiometric_vector": matrix["nu"],
                "element_conservation": matrix["check"],
                "best_status": normalized["best_status"],
            },
            "assertions": assertions,
            "scientific_boundary": (
                "The local model only recognized target metadata. It did not rank catalysts, "
                "simulate activity, predict a relaxed structure, or prove a theorem."
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
