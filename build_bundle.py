from __future__ import annotations

from datetime import datetime
import hashlib
import json
from pathlib import Path
import zipfile


ROOT = Path(__file__).resolve().parent
BUNDLE = ROOT / "AI4R_OPEN_team_id.zip"
MANIFEST = ROOT / "artifacts" / "submission_manifest.json"
RECEIPT = ROOT / "artifacts" / "bundle_receipt.json"

TOP_LEVEL = [
    "00_CURRENT_SCOPE_4H.md",
    "01_FUNCTION_CONTRACT_EVIDENCE_WAIT_CONFIRMATION.md",
    "02_QUALIFICATION_GATE.md",
    "03_GOAI_FOUR_PAGE_GUIDANCE_FINAL.md",
    "04_VALIDATION_AND_RED_TEAM.md",
    "README_SUBMISSION.md",
    "build_word.py",
    "build_bundle.py",
    "GOAI_四页提交稿_Math_Structurer.docx",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def selected_files() -> list[Path]:
    files = [ROOT / name for name in TOP_LEVEL]
    for directory in ("demo", "panel", "artifacts/demo", "artifacts/panel", "artifacts/visuals"):
        files.extend(path for path in (ROOT / directory).rglob("*") if path.is_file())
    files.append(ROOT / "artifacts" / "word_validation.json")
    files.append(ROOT / "evidence_captures_v2" / "core_manifest.json")
    files.extend(path for path in (ROOT / "evidence_captures_v2" / "core").rglob("*") if path.is_file())
    excluded_parts = {"__pycache__", ".pytest_cache"}
    return sorted(
        {
            path.resolve()
            for path in files
            if path.is_file()
            and not any(part in excluded_parts for part in path.parts)
            and path.name not in {"server_stdout.txt", "server_stderr.txt"}
            and path.suffix.lower() not in {".pyc", ".pyo"}
            and path not in {BUNDLE, MANIFEST, RECEIPT}
        },
        key=lambda path: path.relative_to(ROOT).as_posix(),
    )


def build() -> None:
    files = selected_files()
    missing = [name for name in TOP_LEVEL if not (ROOT / name).is_file()]
    if missing:
        raise FileNotFoundError(f"missing required files: {missing}")
    pdfs = [path.relative_to(ROOT).as_posix() for path in files if path.suffix.lower() == ".pdf"]
    if pdfs:
        raise RuntimeError(f"PDF files are forbidden in the active submission bundle: {pdfs}")

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
        "scope": "all ZIP members except this manifest",
        "claim_boundary": (
            "Math Structurer is a typed mathematical filter plus multi-space plugin router. "
            "EML/domain-branch exploration is the only executed scientific slice; the catalyst analyzer "
            "is an interface stress test; no new theorem, catalyst ranking, mechanism, or model call is claimed"
        ),
        "validation": {
            "demo_pytest": "12 passed",
            "panel_pytest": "11 passed",
            "browser_acceptance": "passed; two panels; 2D/3D; desktop + 390px mobile; external requests 0; model calls 0",
            "lean": "partial_formalization; local contract passed; prime EML accepted_with_sorry",
            "word": "Microsoft Word 16; exactly 4 pages",
            "pdf_members": 0,
        },
        "entries": entries,
    }
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    with zipfile.ZipFile(BUNDLE, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            archive.write(path, path.relative_to(ROOT).as_posix())
        archive.write(MANIFEST, MANIFEST.relative_to(ROOT).as_posix())

    with zipfile.ZipFile(BUNDLE) as archive:
        bad_member = archive.testzip()
        if bad_member is not None:
            raise RuntimeError(f"ZIP integrity failure: {bad_member}")
        member_count = len(archive.infolist())

    word = ROOT / "GOAI_四页提交稿_Math_Structurer.docx"
    receipt = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "bundle": BUNDLE.name,
        "bytes": BUNDLE.stat().st_size,
        "sha256": sha256(BUNDLE),
        "zip_integrity": "passed",
        "zip_members": member_count,
        "manifest_sha256": sha256(MANIFEST),
        "word_sha256": sha256(word),
    }
    RECEIPT.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    build()
