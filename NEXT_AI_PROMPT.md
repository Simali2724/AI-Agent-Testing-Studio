# Continuation pointer

**Current as of 2026-11-09.** Older prompts from previous turns are historical; this file
holds only the current pointer. The authoritative state is [HANDOFF.md](HANDOFF.md), whose
first section is self-contained.

## Start here

```text
D:\AI-Agent-Testing-Studio
```

Branch `codex/open-source-release`. Read [HANDOFF.md](HANDOFF.md) first, then
[docs/open-source-readiness.md](docs/open-source-readiness.md) for the release gate ledger
and [docs/tasks.md](docs/tasks.md) Phase 10 for T-046 to T-053.

Recheck Git state rather than trusting this file: `git status --short`,
`git log -5 --oneline`, `git remote -v`.

## What this turn left

An open-source release candidate is prepared, committed locally and **not pushed**. The
source archive, its manifest and its SHA-256 are in `runtime/release/` (git-ignored).

Do **not** mark anything Done by citing numbers from another working tree or another chat.

## Blocked on the owner

1. Written confirmation that all included material is theirs to distribute under MIT.
2. The decision on the named third-party company in UI labels, auto-detection logic, API
   route names and case-pack filenames. Content is synthetic; the naming is public.
3. A security reporting route. GitHub private vulnerability reporting is verified disabled.
4. Explicit authorization before any push, tag, release or announcement.

## Blocked on the environment

- **Pacing stress:** no harness in this lineage. It exists only in
  `C:\Users\Moinuddeen hussain\Documents\ChatGPT\Moinuddeen_airm\studio-publish`, which uses a
  **different task-ID lineage** — do not cross-reference its task numbers.
- **Native Linux and macOS:** `start.sh` was never executed. Support claims are narrowed.
- **Docker:** not installed on this machine, so no image build and no scanner run.
- **Live provider:** no credential used. Ask for one only when a real smoke test is reached,
  naming the provider, model, role, data, call count and budget first.
- **Human calibration labels:** the two-reviewer mechanics exist (T-053); the labels do not.

## Next steps

1. Get the owner's answers to the four blocked items and record them in `DECISIONS.md` and
   `docs/open-source-readiness.md`.
2. If pacing matters, port only the pacing files from `studio-publish` (the `scheduling.py`
   clock seam, `tests/fake_clock.py`, `tests/test_pacing.py`, `scripts/pacing-stress.py`),
   renumbering their task IDs to free ones, then run
   `scripts/pacing-stress.py --repetitions 50 --parallel 12` **separately** from the benchmark.
3. For human calibration, prepare a blind sample, set `min_reviewers` to 2, and ask the owner
   and a second named reviewer for real labels. Never fabricate one.
4. On Linux or macOS, run a fresh extracted install and `./start.sh`, and record it in
   `docs/verification.md`.
5. Rebuild the archive after any change and recompute its hash; the manifest must describe
   the final artifact.

## Standing rules

Read [docs/Rules.md](docs/Rules.md). In particular: insufficient evidence stays **Not
tested**, unknown cost stays **Unknown** rather than zero, repeats are never substituted for
one another, uploaded application code is never executed, and a local commit is not
permission to push.

The real-time benchmark in `tests/test_speed_cache.py` measures wall-clock time. Run the
suite serially on an otherwise idle machine, never alongside other work, and never raise its
threshold to obtain a pass.
