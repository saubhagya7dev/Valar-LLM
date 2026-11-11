# Modal investigation: no deployment until $0 net spend is verified

Checked 11 November 2026. The owner selected: investigate Modal, proceeding only if an enforceable $0 cap is verified. No Modal account state, payment method, token, app, storage volume or GPU allocation has been changed by this project.

## What official documentation establishes

- [Starter pricing](https://modal.com/pricing) currently advertises a $0 subscription plus compute and $30 monthly free credit. Availability and remaining credit must still be checked in the owner's account.
- [Billing documentation](https://modal.com/docs/guide/billing) requires a payment method to use Modal and describes automatic billing for usage beyond applicable credits.
- [Budgets documentation](https://modal.com/docs/guide/budgets) distinguishes a workspace usage budget, calculated before credits, from a net-spend limit after credits. It says Modal stops workloads that would incur further out-of-pocket charges once the spend limit is reached, while work covered by applicable credits may continue.

| Control | Meaning | Project requirement |
| --- | --- | --- |
| Workspace usage budget | Total usage before credits | Keep bounded within actual available credit |
| Workspace spend limit | Net charges after credits | Must accept and retain an effective custom $0 value |
| Environment budget | Compute budget for a specific environment; separate plan restrictions apply | Does not replace the workspace net-spend control |

The docs do not explicitly show the minimum accepted custom spend-limit value, a $0 account screenshot, or the owner's effective settings. We therefore cannot yet claim this account can enforce zero cash spend. Setting a usage budget alone is insufficient evidence. The documented default spend limit derives from usage limit minus credits and must not be mistaken for zero by default.

## Account verification before any workload

1. Create/sign into a Starter workspace through [Modal](https://modal.com/). Do not start an example, deployment, volume, model endpoint or GPU function.
2. Open Settings → Usage & Billing. Inspect the current plan, available credit, usage limit and separate spend-limit control.
3. If available, set the custom workspace **spend limit to $0**. Save, reload and verify the displayed effective value remains $0. A blank field, unset value or default does not count.
4. Record the Starter plan, effective credit, saved net-spend limit and usage limit without exposing payment details or credentials. The account must not require a positive net-spend limit to run GPU work. If the page demands a payment method before these controls can be inspected, stop and resolve that ordering before activating resources.
5. Reconcile the control's scope with all planned compute, image builds, storage, networking and any recurring charges. Exclude optional paid services. If the provider cannot confirm the $0 boundary for the planned workload, retain the hosting blocker.

Only after the no-spend gate is evidenced should we prepare and activate the selected authenticated smoke endpoint. The first run should use one bounded T4 worker, scale to zero, no paid fallback, short timeout and the already-verified adapter. This is a proposed deployment profile, not a deployed Modal implementation. Any browser/account changes still depend on the owner's authenticated account; do not put passwords, card details or API tokens in chat or Git.

## Current outcome

**Modal is excluded under the current strict zero-cash-outlay requirement.** The owner's payment-verification screen requires an upfront $0.50 charge, described as refundable. No charge/refund has been performed by this project and the $0 net-spend control is still unverified. Do not proceed with adding a payment method or activating workloads. Hugging Face ZeroGPU remains a candidate when account eligibility or an approved grant is available.

## Owner's initial billing overview

The owner supplied a billing-overview screenshot on 11 November 2026. It shows Starter with **$1.00 included compute credit per month**, a **$1 usage limit set by Modal**, and **$0.00 total spend**. The page offers "Add a payment method to raise this limit." These observed account values supersede an assumption that this workspace already has the generally advertised $30 monthly credit. The screenshot does not establish GPU access or show the effective separate net-spend cap.

The next read-only check is the **Usage limit** tab. Inspect whether it exposes the separate Spend limit and an effective saved $0 value. Do not infer this from $0 spent so far. Do not add a payment method, raise a limit, or launch a workload merely to explore the setting. Modal's [GPU documentation](https://modal.com/docs/guide/gpu) still says GPU use requires a valid payment method, so the $1 allowance alone is not proof that the intended GPU host is available. Evidence is recorded in `results/phase0/modal-account-overview-20261111.json` without the account identifier or payment information.

## Verification-fee screen: investigation outcome

The owner then supplied a screenshot of an Add a default payment method dialog. It says the provider will charge $0.50 once to verify the account and refund it; successful verification unlocks $29 additional credit for $30 total. This is a required upfront cash charge in the observed flow. A possible later refund does not satisfy this project's current no-outlay requirement, and a future $0 usage/net-spend control would not establish that this verification charge is prevented.

The account-specific evidence is preserved in `results/phase0/modal-verification-fee-20261111.json`. Stop this route without entering payment details or launching an example. No fee waiver, alternate account route or grant is assumed. Investigation can resume only if a documented fee-free allocation becomes available or the owner explicitly changes the cost constraint; no such exception has been requested.
