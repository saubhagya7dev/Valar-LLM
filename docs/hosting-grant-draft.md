# Fee-free hosting allocation request — unsent draft

Prepared 11 November 2026. No message, application or public post has been sent. Fill in permitted repository/demo links before submitting through an official program. Do not include credentials, private documents or unreviewed security claims.

## Application route and current limitation

Hugging Face documents [Community GPU Grants](https://huggingface.co/docs/hub/spaces-gpus#community-gpu-grants) through a Space's hardware settings. Approval is discretionary. This route may require an existing eligible Space; the owner's newly created account does not yet satisfy the documented free ZeroGPU age requirement. Do not buy a plan or select metered hardware to make the grant form accessible. Ask a university or program administrator about an explicitly fee-free allocation if available; no sponsorship is assumed.

## Draft request

I am a student building Valar LLM, an evidence-grounded model-adaptation project for security-source extraction, repository security review and cited document-image answers. I am requesting a limited, fee-free cloud GPU allocation for a reproducible educational demonstration.

The provisional base is Apache-2.0 Qwen/Qwen3-VL-2B-Instruct at an immutable revision. I have completed a three-step synthetic image-training smoke on free Colab, downloaded and independently audited its 1,605,632-parameter LoRA adapter, and restored it in a fresh Colab session. Peak training allocation was approximately 3.19 GiB on Tesla T4. Restored generation on the single synthetic page took approximately 14.84 seconds; this is a Colab observation, not a benchmark of your hosting platform.

The project is not a production security reviewer. Its current untuned security judgments have known errors, and the image smoke does not demonstrate generalization. The initial hosted demonstration would use synthetic examples, authenticated calls, one concurrent request, bounded inputs/outputs, a small quota and explicit unavailability when the allowance is exhausted. No private evidence or public multi-user release is proposed at this stage.

My hard constraint is no upfront charge, subscription, verification fee or paid overflow. Could an allocation cover a small Gradio/PyTorch image-and-text inference demo on these terms, with a defined expiry and automatic stop? My account is new; if Space-creation eligibility prevents using the usual grant form, is there an official fee-free review path?

Repository: [add permitted public URL]

Demo/source preview: [add permitted URL, or state that hosting is pending]

The hardware fit, host compatibility, quotas and billing boundaries would be verified before any activation. I can provide reproducible smoke logs, the model/processor revision, adapter checksums and a clear limitations report.
