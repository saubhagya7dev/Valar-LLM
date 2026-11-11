"""Build allowlisted source or Space artifacts; never read .env, caches or private data."""
import argparse
import hashlib
import json
import re
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def source_files():
    fixed = [ROOT / name for name in ("pyproject.toml", "README.md", "uv.lock")]
    folders = [ROOT / name for name in ("src", "configs", "requirements", "scripts", "tests/fixtures")]
    return sorted(fixed + [p for folder in folders for p in folder.rglob("*")
                           if p.is_file() and "__pycache__" not in p.parts
                           and p.suffix in {".py", ".json", ".in", ".lock"}])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("kind", choices=["notebook", "space"])
    args = parser.parse_args()
    target = ROOT / "artifacts"
    target.mkdir(exist_ok=True)
    if args.kind == "notebook":
        output = target / "valar-phase0-source.zip"
        with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for path in source_files():
                archive.write(path, path.relative_to(ROOT).as_posix())
        print(output)
        return
    output = target / "space"
    output.mkdir(exist_ok=True)
    for folder in ("src", "configs"):
        shutil.copytree(ROOT / folder, output / folder, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    lock = (ROOT / "requirements/serving.lock").read_text(encoding="utf-8")
    gradio_version = re.search(r"^gradio==([^\s]+)", lock, re.MULTILINE).group(1)
    (output / "requirements.txt").write_text(lock, encoding="utf-8")
    (output / "app.py").write_text(
        'import sys\nsys.path.insert(0, "src")\n'
        'from valar_llm.serve.zerogpu import main\nmain()\n', encoding="utf-8"
    )
    (output / "README.md").write_text(
        f"---\ntitle: Valar Phase 0\nsdk: gradio\nsdk_version: {gradio_version}\n"
        "python_version: '3.12'\napp_file: app.py\n---\n\n"
        "Authenticated synthetic feasibility service. Select eligible FREE ZeroGPU hardware manually.\n"
        "Never upgrade to paid hardware. Set VALAR_API_KEY secret (32+ characters).\n"
        "Set VALAR_ENABLE_GPU=1 only after free hardware eligibility is verified.\n"
        "Upload the saved smoke adapter directory separately and set VALAR_ADAPTER_DIR.\n"
        "Without an adapter this tests the base only. No private document uploads.\n"
        "Local SQLite request counts depend on ephemeral storage; this is not a production gateway.\n",
        encoding="utf-8",
    )
    files = [p for p in output.rglob("*") if p.is_file() and p.name != "bundle-manifest.json"]
    manifest = {p.relative_to(output).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted(files)}
    (output / "bundle-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(output)


if __name__ == "__main__":
    main()
