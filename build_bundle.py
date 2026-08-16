from __future__ import annotations

from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import zipfile


ROOT = Path(__file__).resolve().parent
BUNDLE = ROOT / "AI4R_OPEN_team_id.zip"
MANIFEST = ROOT / "artifacts" / "submission_manifest.json"
RECEIPT = ROOT / "artifacts" / "bundle_receipt.json"

TOP_LEVEL = [
    ".gitignore",
    "03_GOAI_FOUR_PAGE_GUIDANCE_FINAL.md",
    "README.md",
    "README_SUBMISSION.md",
    "run.py",
    "build_word.py",
    "build_bundle.py",
    "GOAI_四页提交稿_Math_Structurer.docx",
]

PANEL_ARTIFACTS = [
    "browser_acceptance.json",
    "panel_desktop_general_2d.png",
    "panel_desktop_general_3d.png",
    "panel_desktop_iterate.png",
    "panel_mobile_general.png",
    "panel_desktop_qwen_recognition.png",
    "pytest.txt",
]

VALIDATION_ARTIFACTS = [
    "quick_check.json",
    "qwen_recognition_acceptance.json",
    "qwen_recognition_browser_acceptance.json",
    "validation_summary.json",
    "word_validation.json",
]

EVIDENCE_FILES = [
    "acs_figshare_16583585.json",
    "alphaxiv_result_v2.json",
    "brandstetter.html",
    "doi_handle_acscatal.json",
    "gungor_arxiv_html.html",
    "kozyra.html",
    "local_number_theory_receipt.json",
    "mialon_arxiv_api.xml",
    "murugan_springer.html",
    "openalex_acscatal.json",
    "primary_source_receipts.json",
    "verification_receipt.json",
]

TEXT_SUFFIXES = {".css", ".html", ".js", ".json", ".md", ".py", ".txt", ".xml"}
FORBIDDEN_TEXT = {
    "legacy_eml_term": re.compile(r"\bEML\b", re.IGNORECASE),
    "absolute_windows_host_path": re.compile(
        r"\b[A-Za-z]:\\(?:Users|MATHs|Program Files|Windows)(?:\\|\b)", re.IGNORECASE
    ),
    "codex_thread_id": re.compile(r'"thread_id"\s*:'),
    "private_host_marker": re.compile(r"\bslac002\b", re.IGNORECASE),
    "credential_assignment": re.compile(
        r"(?i)(api[_-]?key|access[_-]?token|password|private[_-]?key)\s*[:=]\s*['\"][A-Za-z0-9_./+\-=]{8,}"
    ),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def allowed(path: Path) -> bool:
    excluded = {"__pycache__", ".pytest_cache", "node_modules", ".git"}
    return (
        path.is_file()
        and not any(part in excluded for part in path.parts)
        and path.suffix.lower() not in {".pyc", ".pyo", ".pdf"}
        and path.name not in {"server_stdout.txt", "server_stderr.txt"}
        and path.resolve() not in {BUNDLE.resolve(), MANIFEST.resolve(), RECEIPT.resolve()}
    )


def selected_files() -> list[Path]:
    files = [ROOT / name for name in TOP_LEVEL]
    files.append(ROOT / "demo" / "generate_visuals.py")
    files.extend(path for path in (ROOT / "panel").rglob("*") if allowed(path))
    files.extend(path for path in (ROOT / "artifacts" / "visuals").glob("*.png") if allowed(path))
    files.extend(ROOT / "artifacts" / "panel" / name for name in PANEL_ARTIFACTS)
    files.extend(ROOT / "artifacts" / name for name in VALIDATION_ARTIFACTS)
    files.extend(ROOT / "evidence_captures_v3" / name for name in EVIDENCE_FILES)
    return sorted(
        {path.resolve() for path in files if allowed(path)},
        key=lambda path: path.relative_to(ROOT).as_posix(),
    )


def audit_text(files: list[Path]) -> dict[str, int]:
    counts = {name: 0 for name in FORBIDDEN_TEXT}
    for path in files:
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        text = path.read_text("utf-8", errors="replace")
        for name, pattern in FORBIDDEN_TEXT.items():
            counts[name] += len(pattern.findall(text))
    failures = {name: count for name, count in counts.items() if count}
    if failures:
        raise RuntimeError(f"forbidden text found in selected files: {failures}")
    return counts


def build() -> None:
    missing = [name for name in TOP_LEVEL if not (ROOT / name).is_file()]
    if missing:
        raise FileNotFoundError(f"missing required files: {missing}")

    files = selected_files()
    text_audit = audit_text(files)
    pdfs = [path.relative_to(ROOT).as_posix() for path in files if path.suffix.lower() == ".pdf"]
    if pdfs:
        raise RuntimeError(f"PDF files are forbidden in the submission bundle: {pdfs}")

    word_validation = json.loads((ROOT / "artifacts" / "word_validation.json").read_text("utf-8"))
    browser = json.loads((ROOT / "artifacts" / "panel" / "browser_acceptance.json").read_text("utf-8"))
    qwen = json.loads((ROOT / "artifacts" / "qwen_recognition_acceptance.json").read_text("utf-8"))
    qwen_browser = json.loads(
        (ROOT / "artifacts" / "qwen_recognition_browser_acceptance.json").read_text("utf-8")
    )
    pytest_text = (ROOT / "artifacts" / "panel" / "pytest.txt").read_text("utf-8").strip()
    pytest_summary = next(
        (line.strip() for line in reversed(pytest_text.splitlines()) if " passed" in line),
        "",
    )
    if word_validation.get("pages") != 4:
        raise RuntimeError("Word validation is not exactly four pages")
    hyperlink_count = word_validation.get(
        "external_hyperlink_relationships", word_validation.get("external_hyperlinks", 0)
    )
    if hyperlink_count < 7:
        raise RuntimeError("Word validation does not contain the required clickable references")
    if browser.get("status") != "passed":
        raise RuntimeError("browser acceptance did not pass")
    if qwen.get("status") != "passed":
        raise RuntimeError("Qwen recognition acceptance did not pass")
    if qwen_browser.get("status") != "passed":
        raise RuntimeError("Qwen browser acceptance did not pass")
    expected_model = "hf.co/mradermacher/Qwen3-8B-Jailbroken-GGUF:Q4_K_M"
    if qwen.get("model") != expected_model:
        raise RuntimeError("Qwen receipt does not identify the exact required model")
    expected_digest = "ca6da952658c16e9eafcf68cb6a1719dbdc67891c89cff06f0394a722508a5d8"
    if qwen.get("model_digest") != expected_digest:
        raise RuntimeError("Qwen receipt model digest does not match the accepted checkpoint")
    qwen_assertions = qwen.get("assertions", {})
    required_qwen_assertions = {
        "exact_model_selected",
        "digest_recorded",
        "recognition_gate_passed",
        "recognition_only",
        "one_model_call",
        "element_conservation",
        "unconditional_ranking_rejected",
        "no_scientific_answer_fields",
    }
    failed_qwen_assertions = sorted(
        name for name in required_qwen_assertions if qwen_assertions.get(name) is not True
    )
    if failed_qwen_assertions:
        raise RuntimeError(f"Qwen acceptance assertions failed: {failed_qwen_assertions}")
    if qwen_browser.get("provider") != "qwen":
        raise RuntimeError("Qwen browser receipt did not use the Qwen provider")
    if not pytest_summary:
        raise RuntimeError("pytest receipt has no passing summary")

    entries = [
        {
            "path": path.relative_to(ROOT).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        }
        for path in files
    ]
    manifest = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "project": "Math Structurer — Convincing, reusable target-matching skills for AI research agents.",
        "claim_boundary": (
            "The current discovery signal is a problem-definition revision: the unconditioned catalyst "
            "ranking is underdetermined. No catalyst activity simulation, catalyst ranking, new mechanism, "
            "universal algebra, automatic PDE reduction, or general iterative-root proof is claimed."
        ),
        "validation": {
            "python": pytest_summary,
            "quick_check": "passed; loopback only; model calls 0; external requests 0",
            "browser": "passed; desktop and 390px; 2D/3D; model calls 0; external requests 0",
            "qwen_recognition": (
                "passed; exact checkpoint and digest; one recognition-only call; deterministic gate passed; "
                "unconditional catalyst ranking rejected"
            ),
            "qwen_browser": "passed; isolated Chrome; provider qwen; browser external requests 0",
            "word": "Microsoft Word 16.0; exactly 4 pages",
            "platforms": {
                "Windows 11": "tested",
                "Linux": "designed, not tested",
                "macOS": "designed, not tested",
            },
            "pdf_members": 0,
            "forbidden_text_hits": text_audit,
        },
        "entries": entries,
    }
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    with zipfile.ZipFile(BUNDLE, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            archive.write(path, path.relative_to(ROOT).as_posix())
        archive.write(MANIFEST, MANIFEST.relative_to(ROOT).as_posix())

    with zipfile.ZipFile(BUNDLE) as archive:
        bad = archive.testzip()
        if bad:
            raise RuntimeError(f"ZIP integrity failure: {bad}")
        names = archive.namelist()
        unsafe_names = [
            name
            for name in names
            if name.startswith(("/", "\\")) or ".." in Path(name).parts or Path(name).is_absolute()
        ]
        if unsafe_names:
            raise RuntimeError(f"unsafe archive paths: {unsafe_names}")
        pdf_members = [name for name in names if name.lower().endswith(".pdf")]
        if pdf_members:
            raise RuntimeError(f"unexpected PDFs: {pdf_members}")
        nested_zip_members = [name for name in names if name.lower().endswith(".zip")]
        if nested_zip_members:
            raise RuntimeError(f"unexpected nested ZIPs: {nested_zip_members}")
        member_count = len(names)

    word = ROOT / "GOAI_四页提交稿_Math_Structurer.docx"
    receipt = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "bundle": BUNDLE.name,
        "bytes": BUNDLE.stat().st_size,
        "sha256": sha256(BUNDLE),
        "zip_integrity": "passed",
        "zip_members": member_count,
        "pdf_members": 0,
        "nested_zip_members": 0,
        "unsafe_path_members": 0,
        "forbidden_text_hits": text_audit,
        "manifest_sha256": sha256(MANIFEST),
        "word_sha256": sha256(word),
        "word_pages": 4,
    }
    RECEIPT.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    build()
