# Release announcement — draft, not published

Prepared 2026-11-09 for review. **Nothing here has been posted anywhere.** Publishing is a
separate authorized action, and the claims below must be re-checked against
[open-source-readiness.md](open-source-readiness.md) before anyone sends them.

Do not publish this while the license, distribution rights and third-party naming decisions
are still open.

## Short version, for a README blurb or a social post

> **AI Agent Studio** — a local, single-user tool for testing chatbots. Run the same ten
> categories against one bot or compare up to four, using Black-box conversations, Gray-box
> declarations and White-box source scans. Evidence stays on your machine. Checks that
> cannot be evidenced are reported as **Not tested**, and unknown costs stay **Unknown**
> rather than quietly becoming zero. MIT licensed.
>
> There is a synthetic demo that needs no API key, so you can see the whole workflow before
> connecting anything of your own.

## Longer version, for a release page

> ### AI Agent Studio 0.1.0-rc.1
>
> A local tool for evaluating chatbots you own or are authorized to test. It binds loopback,
> keeps results and credentials on your machine, and is not a hosted service.
>
> **What it does.** Ten categories — hallucination, bias, prompt injection, jailbreak,
> guardrails, prompt leakage, personal data, toxicity, unnecessary refusals and consistency —
> run against one bot or up to four for comparison. Choose Black-box conversations, Gray-box
> declarations and traces, White-box read-only source scans, or any combination. Results come
> with transcripts, evidence quotes, an audit chain, retention controls, and JSON and PDF
> exports.
>
> **Try it with no account.** Start the bundled synthetic bot with
> `python scripts/demo_bot.py`, point Studio at it, and run a real evaluation scored on
> deterministic checks with the AI Judge switched off. No provider is called and nothing is
> billed. The demo deliberately includes a Case the bot fails.
>
> **What it does not claim.** This is a release _candidate_, and the honest limits are part
> of the release:
>
> - **Judges are uncalibrated.** No human-label validation has been completed, so there is no
>   measured Judge accuracy figure. The mechanics for two independent reviewers, inter-rater
>   agreement and a confidence interval are in place; the labels are not.
> - **Windows only, Python 3.12 only.** `start.sh` is checked in but has not been run on
>   native Linux or macOS, so those platforms are unqualified.
> - **No live provider test** was run for this candidate.
> - A passing check is evidence about one check. It is never a statement that an application
>   is secure, fair or accurate, and the tool is not a certification.
>
> **Install.** Python 3.12, then `run.ps1` on Windows or `./start.sh` elsewhere. Dependencies
> install from hash-pinned lockfiles. Docker is optional and only used by White-box scanning.
>
> MIT licensed. Issues and pull requests welcome — see CONTRIBUTING.md.

## Claims checklist before publishing

- [ ] License and distribution rights confirmed in writing by the owner.
- [ ] The third-party company naming decision is made and reflected in the text.
- [ ] A security reporting route exists, and SECURITY.md no longer says it is missing.
- [ ] Every figure quoted matches `verification.md` for the exact published artifact.
- [ ] The uncalibrated-Judge and unqualified-platform statements are still accurate.
- [ ] No private run identifier, workstation path or customer reference appears in the text.

## Screenshots

Take them from the synthetic demo only, never from a real evaluation. The browser check
already writes synthetic-fixture artifacts to `runtime/ui-artifacts`, which are the safe
source. Capture Evaluate, Results with evidence expanded, Tokens and cost, and Governance.

Confirm before publishing any image that it shows the synthetic demo bot, carries no bot URL
or key, and includes the synthetic-demonstration-data label.
