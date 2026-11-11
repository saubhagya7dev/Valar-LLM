# Free account setup and first run

No credentials should be pasted into chat, committed to files, or saved in notebook outputs.

## Hugging Face

1. Create a free personal account at [huggingface.co/join](https://huggingface.co/join).
2. Verify email; remain on the free plan without billing or prepaid credits.
3. Record the creation date privately. The documented free ZeroGPU hosting route requires good standing and an account older than 30 days. If created 11 November, recheck eligibility after 11 December; that is a calendar estimate, not guaranteed approval.
4. A token is not needed to download the selected public base. For private artifact uploads later, create a narrowly scoped token and store it only in Colab Secrets or Space settings.
5. Do not create a paid GPU Space. Free hosting remains pending until the account offers eligible ZeroGPU hardware.

## Google Colab

1. Sign in at [colab.research.google.com](https://colab.research.google.com/) with your Google account.
2. Upload `notebooks/phase0_colab.ipynb` using File → Upload notebook.
3. Select Runtime → Change runtime type → a free GPU, if offered. Do not buy compute units. Availability varies.
4. Locally run `python scripts/prepare_bundle.py notebook` and upload the generated `artifacts/valar-phase0-source.zip` to the notebook when prompted.
5. Run the setup cells, confirm CUDA in the displayed output, then run base inference. Stop on dependency, memory or masking failures and save the error.
6. Run the three-step training smoke. Inspect the masking audit; download the adapter zip before disconnecting. This is external persistence on your computer, not local training or serving.
7. Restart the Colab session. Repeat setup, upload the saved adapter zip in the restore cell, then run the reload smoke. Save result JSON and actual runtime details.

Notebook installation is isolated from Colab's preinstalled packages. The checked-in locks target Linux/Python 3.12. If Colab changes interpreter, use a compatible free runtime or regenerate/review the locks; do not silently upgrade pinned GPU packages.

## Kaggle alternative

Create a free account at [kaggle.com](https://www.kaggle.com/) and check a new notebook's accelerator settings. If verification is requested, complete it in Kaggle itself. Record actual GPU access, internet setting, quota and persistence options. No fixed GPU allowance is assumed. Colab is the documented first notebook path in this repository.

## Eventual cloud smoke service

Run `python scripts/prepare_bundle.py space` and review `artifacts/space/README.md`. Upload that prepared directory to an eligible free ZeroGPU Space. Set a random private `VALAR_API_KEY` of at least 32 characters in Space secrets and `VALAR_ENABLE_GPU=1` in settings. The generated bundle defaults to disabled. Keep the trained smoke adapter in the Space's private storage/repository as appropriate and set `VALAR_ADAPTER_DIR`; verify platform access/retention before any real private evidence.

After a base endpoint works, repeat with the restored adapter. A base-only deployment does not pass the adapter-serving gate. Run `scripts/remote_probe.py` from Colab against all three task types, including image uploads. Record HF quota before/after, queue and cold/warm observations. The script reports end-to-end time including queue; it cannot independently separate provider queue time.

The full product gateway, multi-user budgets and both application deployments are later work. This endpoint is for authenticated synthetic smoke checks.
