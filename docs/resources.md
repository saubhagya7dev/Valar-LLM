# Resource evidence register

Checked 11 November 2026 against official documentation. Documentation availability is not account eligibility or a successful runtime test.

| Resource | Documentation evidence | Account/runtime evidence | Decision |
| --- | --- | --- | --- |
| Colab Free | Free resources and accelerator access are limited, variable and not guaranteed; intended for notebook work | Owner has not yet configured an account/runtime | First training candidate; no serving through Colab |
| HF ZeroGPU | Free personal accounts in good standing with verified email and age over 30 days can host up to two Spaces; Gradio only, shared GPU and daily quotas | Owner reported no HF account yet | Hosting blocked on account eligibility; prepare service without deploying |
| Kaggle | Candidate alternative, allocation/account requirements not verified here | No account configured | Do not assume GPU type or fixed weekly allowance |
| Modal | No enforceable no-spend account evidence gathered | No account configured | Excluded from initial route |
| Qwen3-VL-2B-Instruct | Public model card: Apache-2.0, image-text-to-text; commit resolved from official Hub API | No local/online model execution yet | Provisional candidate only |

Sources:

- [Colab FAQ](https://research.google.com/colaboratory/faq.html)
- [HF ZeroGPU](https://huggingface.co/docs/hub/spaces-zerogpu)
- [HF Space configuration](https://huggingface.co/docs/hub/spaces-config-reference)
- [Qwen model card](https://huggingface.co/Qwen/Qwen3-VL-2B-Instruct)
- [Qwen immutable revision metadata](https://huggingface.co/api/models/Qwen/Qwen3-VL-2B-Instruct/revision/89644892e4d85e24eaac8bacfd4f463576704203)
- [Transformers Qwen3-VL](https://huggingface.co/docs/transformers/model_doc/qwen3_vl)
- [PEFT quantization](https://huggingface.co/docs/peft/main/en/developer_guides/quantization)

Do not infer a particular GPU, quota duration, payment requirement or backend-caller attribution from these notes. Before hosting, inspect the actual Space hardware, plan, quota and caller authentication behavior. Do not enable prepaid overage. Record actual account checks without emails, passwords or tokens.

Training GPU time, private artifact storage, inference quota, teacher tokens and the other application components are separate budgets. No teacher labeling calls, model download, GPU run, cloud deployment or paid resource activation has occurred in this implementation session.
