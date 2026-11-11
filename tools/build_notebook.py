"""Generate a thin, output-free Colab notebook from reviewable commands."""
import json
from pathlib import Path

cells = []


def markdown(text):
    cells.append({"cell_type": "markdown", "metadata": {}, "source": text.splitlines(True)})


def code(text):
    cells.append({"cell_type": "code", "metadata": {}, "execution_count": None,
                  "outputs": [], "source": text.splitlines(True)})


markdown("""# Valar LLM — Phase 0 free online smoke

Synthetic examples only; this is not a quality benchmark. Choose a **free GPU runtime** manually.
No paid resources, teacher API calls, automatic Hub upload, or public serving from Colab.
Run `python scripts/prepare_bundle.py notebook` on the development machine and upload its source zip below.
The notebook installs a separate environment targeting Python 3.12; it fails visibly on a different interpreter.
""")
code("""import pathlib
import sys
import zipfile

from google.colab import files

assert sys.version_info[:2] == (3, 12), 'This lock targets Python 3.12; select a compatible runtime.'
uploaded = files.upload()
assert 'valar-phase0-source.zip' in uploaded, 'Upload the prepared source bundle.'
root = pathlib.Path('/content/valar-phase0')
root.mkdir(exist_ok=True)
with zipfile.ZipFile('valar-phase0-source.zip') as archive:
    for member in archive.infolist():
        path = (root / member.filename).resolve()
        assert path.is_relative_to(root.resolve()), 'Unsafe archive member'
    archive.extractall(root)
%cd /content/valar-phase0
""")
code("""import os
import subprocess

subprocess.run([sys.executable, '-m', 'venv', '/content/valar-env'], check=True)
python = '/content/valar-env/bin/python'
subprocess.run([python, '-m', 'pip', 'install', '-r', 'requirements/gpu.lock'], check=True)
subprocess.run([python, '-m', 'pip', 'install', '--no-deps', '-e', '.'], check=True)
subprocess.run([python, '-c', 'import torch; assert torch.cuda.is_available(); print(torch.cuda.get_device_name())'], check=True)
os.environ['VALAR_FREE_ONLINE_RUNTIME'] = 'confirmed'
subprocess.run([python, '-m', 'valar_llm.cli', 'check'], check=True)
""")
markdown("""## Untuned baseline smoke
This makes three bounded real inference attempts (research, review, image answer). Read the saved predictions; valid JSON alone is not correctness. Stop and preserve failures if the model does not fit.
""")
code("""subprocess.run([python, '-m', 'valar_llm.eval.smoke', '--output', 'results/runs/base-smoke.json'], check=True)
print(pathlib.Path('results/runs/base-smoke.json').read_text())
""")
markdown("""## Tiny image training smoke
Three steps on one synthetic image. The command verifies exact prompt-prefix masking, image tensors and nonempty answer loss. Training and re-evaluating this example measures mechanics only.
""")
code("""subprocess.run([python, '-m', 'valar_llm.train.smoke'], check=True)
print(pathlib.Path('artifacts/smoke-adapter/mask-audit.json').read_text())
""")
code("""import shutil

shutil.make_archive('/content/valar-smoke-adapter', 'zip', 'artifacts', 'smoke-adapter')
files.download('/content/valar-smoke-adapter.zip')
shutil.make_archive('/content/valar-smoke-results', 'zip', 'results/runs')
files.download('/content/valar-smoke-results.zip')
""")
markdown("""## Fresh-session restore
After downloading both archives, restart the runtime/session. Re-run only the source upload and environment setup cells. Skip base/training cells. Upload the saved adapter archive below, then run reload inference. This checks restore into a new process; record that the VM/session was actually restarted.
""")
code("""uploaded = files.upload()
assert 'valar-smoke-adapter.zip' in uploaded
destination = pathlib.Path('artifacts').resolve()
destination.mkdir(exist_ok=True)
with zipfile.ZipFile('valar-smoke-adapter.zip') as archive:
    for member in archive.infolist():
        assert (destination / member.filename).resolve().is_relative_to(destination)
    archive.extractall(destination)
subprocess.run([python, '-m', 'valar_llm.eval.smoke', '--adapter', 'artifacts/smoke-adapter',
                '--output', 'results/runs/reloaded-smoke.json'], check=True)
print(pathlib.Path('results/runs/reloaded-smoke.json').read_text())
""")
markdown("""## Cloud serving gate
Colab is not the inference server. Follow `docs/account-setup.md` to prepare an eligible free ZeroGPU Space and restore the adapter there. A new Hugging Face account may have to wait for eligibility. Keep this gate unpassed until remote text/image requests actually work, including a probe from a cloud client while the laptop is off.

To run the remote probe here later, install `requirements/probe.lock` into the separate environment, load secrets from Colab Secrets into environment variables without printing them, and run `python scripts/remote_probe.py owner/space-name`. Save quota before/after and cold/warm observations separately.
""")
notebook = {"nbformat": 4, "nbformat_minor": 5,
            "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                         "language_info": {"name": "python"}, "colab": {"provenance": []}},
            "cells": cells}
for index, cell in enumerate(cells):
    cell["id"] = f"valar-phase0-{index:02d}"
Path("notebooks").mkdir(exist_ok=True)
Path("notebooks/phase0_colab.ipynb").write_text(json.dumps(notebook, indent=2) + "\n", encoding="utf-8")
