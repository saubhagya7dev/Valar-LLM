# Resource evidence register

Checked 11 November 2026 against official documentation. Documentation availability is not account eligibility or a successful runtime test.

| Resource | Documentation evidence | Account/runtime evidence | Decision |
| --- | --- | --- | --- |
| Colab Free | Free resources and accelerator access are limited, variable and not guaranteed; intended for notebook work | Owner supplied T4 training, externally verified checkpoint, and fresh-session restored image inference | Training/restore smoke demonstrated; not the public server |
| HF ZeroGPU | Free personal accounts in good standing with verified email and age over 30 days can host up to two Spaces; Gradio only, shared GPU and daily quotas | Owner reports account created; hosting eligibility not verified | Hosting blocked on account eligibility; prepare service without deploying |
| Kaggle | Candidate alternative, allocation/account requirements not verified here | Owner reports accounts created; accelerator access unverified | Do not assume GPU type or fixed weekly allowance |
| Modal | Current billing/GPU docs require a payment method; budgets docs define a separate net-spend limit; general Starter pricing is not account-specific allocation evidence | Owner's overview shows Starter, $1 monthly compute credit, $1 provider-set usage limit and $0 spent; custom $0 net-spend cap and GPU access unverified | Investigate Usage limit controls; do not assume $30 credit or activate workloads |
| Qwen3-VL-2B-Instruct | Public model card: Apache-2.0, image-text-to-text; commit resolved from official Hub API | T4 training/restore smoke verified on one image; researcher and reviewer failures retained | Provisional; cloud-serving mechanics and per-role quality gates remain |

Sources:

- [Colab FAQ](https://research.google.com/colaboratory/faq.html)
- [HF ZeroGPU](https://huggingface.co/docs/hub/spaces-zerogpu)
- [HF Space configuration](https://huggingface.co/docs/hub/spaces-config-reference)
- [Qwen model card](https://huggingface.co/Qwen/Qwen3-VL-2B-Instruct)
- [Qwen immutable revision metadata](https://huggingface.co/api/models/Qwen/Qwen3-VL-2B-Instruct/revision/89644892e4d85e24eaac8bacfd4f463576704203)
- [Transformers Qwen3-VL](https://huggingface.co/docs/transformers/model_doc/qwen3_vl)
- [PEFT quantization](https://huggingface.co/docs/peft/main/en/developer_guides/quantization)
- [Modal billing and required payment method](https://modal.com/docs/guide/billing)
- [Modal workspace budgets and separate net-spend limits](https://modal.com/docs/guide/budgets)
- [Modal Starter pricing](https://modal.com/pricing)

Do not infer a particular GPU, quota duration, payment requirement or backend-caller attribution from these notes. Before hosting, inspect the actual Space hardware, plan, quota and caller authentication behavior. Do not enable prepaid overage. Record actual account checks without emails, passwords or tokens.

Training GPU time, private artifact storage, inference quota, teacher tokens and the other application components are separate budgets. The owner ran Colab setup, base inference, three synthetic training steps and fresh-session adapter restoration; supplied measurements and failures are saved under `results/phase0/`. Teacher labeling and cloud serving deployment have not been demonstrated. No paid resource activation was reported. Modal's general spend-limit documentation is evidence for investigating the route, not proof that this owner's account has a saved, effective $0 cap.
