# Changelog

Notable changes to AI Agent Studio. Dates are release-candidate dates, not
published release dates. This project has not had a tagged public release yet.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
loosely; versions are not yet semantic because no public API is promised.

## Unreleased — release candidate 0.1.0-rc.1 (2026-11-09)

First candidate prepared for an open-source release. The application itself was
already developed over the preceding commits; this entry records the work done
to make it distributable and honestly described.

### Added

- **A no-key synthetic demo.** `scripts/demo_bot.py` serves a deterministic
  synthetic chatbot on loopback, and `GET /api/blackbox/case-set/demo` publishes
  8 matching Cases that score on literal checks with the AI Judge switched off.
  A new installation can now complete a real evaluation — real connector, real
  runner, real Governance and exports — with no provider account and no chatbot
  of its own. Results are labelled synthetic demonstration data, and the Case
  set deliberately includes a Case the bot fails.
- `LICENSE`: MIT, copyright 2026 Moinuddeen Hussain.
- `CHANGELOG.md`, issue templates and a pull request template.
- `docs/open-source-readiness.md`: the release gate ledger with evidence.
- `docs/release-checklist.md` with rollback steps, and `docs/troubleshooting.md`.
- `scripts/release_manifest.py`: describes a built artifact for review, and
  refuses to attribute a dirty-tree build to a commit alone.
- Packaging tests that export the **real** repository and assert the archive
  contains the launchers, hash-locked requirements and the license.

### Fixed

- The source packager omitted `requirements*.lock`, `start.sh`, `Dockerfile`,
  `Dockerfile.scanners`, `compose.yaml` and `.dockerignore`, so an extracted
  archive could not follow its own documented setup instructions.
- The README quality badge pointed at an unrelated repository and branch.
- `docs/api-keys.md` contained an absolute workstation path into a separate
  local project; it now uses a portable placeholder.
- The shipped README linked internal working history that the source archive
  deliberately excludes.
- **PDF export was unbounded.** `generate_pdf` appended one flowable per
  transcript turn inside the request handler, so a large saved Run could block
  the single server worker until the client timed out. Rendering is now bounded
  per paragraph and per document, a truncated report says so inside the
  document, and a report that cannot be rendered returns `413` naming the JSON
  export instead of hanging. No stored evidence or audit record is altered.
- `docs/Architecture.md` claimed no Python lockfile existed. Three hash-pinned
  locks are checked in and the launchers install with `--require-hashes`.
- `docs/legacy-guide.md` had five broken relative links, unresolved since the
  file moved into `docs/`. Document link checking now covers every maintained
  Markdown file rather than five, which is how they were found.
- `SECURITY.md` had no vulnerability reporting route and a stale absolute path.
  It now states the real situation: GitHub private reporting is **not** enabled,
  with the maintainer step needed to enable it.
- An empty `STUDIO_RUNTIME` resolved to the current directory, writing runtime
  caches into the source tree. It is now treated as unset.

### Known limitations

See [docs/open-source-readiness.md](docs/open-source-readiness.md) for the full
gate status. In short: Judges are **uncalibrated** against human labels, native
Linux and macOS startup is **not qualified**, and no live provider smoke test
was run for this candidate.
