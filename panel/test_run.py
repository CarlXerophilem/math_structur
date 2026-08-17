from __future__ import annotations

from http.client import HTTPConnection
import importlib.util
import json
from pathlib import Path
import socket
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parent.parent
RUN = ROOT / "run.py"


def isolated_command(*arguments: str) -> list[str]:
    return [sys.executable, "-I", "-S", "-B", str(RUN), *arguments]


def test_check_is_path_independent_and_offline(tmp_path: Path) -> None:
    completed = subprocess.run(
        isolated_command("--check"),
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    receipt = json.loads(completed.stdout.strip().splitlines()[-1])
    assert receipt["status"] == "passed"
    assert receipt["panel_http"] == 200
    assert receipt["local_kernel"] == "passed"
    assert receipt["core_reaction_fields"] == "passed"
    assert receipt["reaction_energy"] is None
    assert receipt["sort_semantics"] == "sort_only"
    assert receipt["possibilities_blocking"] is False
    assert receipt["geometry_scope"] == "support_only"
    assert receipt["database_external_requests"] == 0
    assert receipt["model_calls"] == 0
    assert receipt["external_network_requests"] == 0


def test_help_documents_the_one_line_modes(tmp_path: Path) -> None:
    completed = subprocess.run(
        isolated_command("--help"),
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert completed.returncode == 0
    assert "--check" in completed.stdout
    assert "--host" in completed.stdout
    assert "--port" in completed.stdout


def test_default_server_starts_from_another_directory_without_site_packages(tmp_path: Path) -> None:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]

    process = subprocess.Popen(
        isolated_command("--port", str(port)),
        cwd=tmp_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        deadline = time.monotonic() + 8
        body = b""
        status = None
        while time.monotonic() < deadline:
            if process.poll() is not None:
                stdout, stderr = process.communicate()
                raise AssertionError(f"server exited early\nstdout={stdout}\nstderr={stderr}")
            connection = HTTPConnection("127.0.0.1", port, timeout=1)
            try:
                connection.request("GET", "/")
                response = connection.getresponse()
                status = response.status
                body = response.read()
                break
            except OSError:
                time.sleep(0.1)
            finally:
                connection.close()
        assert status == 200
        assert b"Math Structurer" in body
    finally:
        if process.poll() is None:
            process.terminate()
        stdout, stderr = process.communicate(timeout=5)

    assert f"http://127.0.0.1:{port}/" in stdout
    assert "literature and public-database evidence retrieval" in stdout
    assert "@best changes order only" in stdout
    assert stderr == ""


def test_failed_check_is_nonzero_and_never_reported_as_passed(monkeypatch, capsys) -> None:
    spec = importlib.util.spec_from_file_location("math_structurer_run_test", RUN)
    assert spec is not None and spec.loader is not None
    entry = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(entry)

    def fail() -> dict:
        raise RuntimeError("deliberate validator failure")

    monkeypatch.setattr(entry, "quick_check", fail)
    assert entry.main(["--check"]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    failure = json.loads(captured.err)
    assert failure["status"] == "failed"
    assert failure["error_type"] == "RuntimeError"
    assert "passed" not in captured.err
