# Changelog

Notable changes to AI Agent Studio. Dates are release-candidate dates, not
published release dates. This project has not had a tagged public release yet.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
loosely; versions are not yet semantic because no public API is promised.

## Unreleased — release candidate 0.1.0-rc.2 (2026-11-10)

Repairs for the five defects an offline release-candidate audit reproduced in
this checkout. The sixth finding, a failing Prettier gate, was already green
here. Nothing in this entry was published.

### Added

- **The advertised no-key demo is reachable from the shipped interface.** The
  Evaluate screen has a **Try it first, with no account** card, and
  `POST /api/blackbox/demo/runs` accepts only a consent boolean and builds the
  evaluation on the server: AI Judge off, no Judge selected, local fallback
  discovery disabled, and exactly the eight bundled Cases rather than the
  ten-Category suite. Measured in a real browser: 8 of 8 scored with no Judge,
  7 passed and 1 failed, 9 calls to the loopback fixture, **0 judge calls**.
- `scripts/check-demo-journey.py`: a browser regression that drives that whole
  journey across two real loopback processes, exports both formats, restarts
  Studio and reopens the Run, and fails on any request leaving the two loopback
  ports. It runs in CI.
- `scripts/build_provenance.py` and `package_release.py --build-manifest`: a
  build record written beside the archive, holding the finished bytes' SHA-256
  and the Git state of the tree that produced them.
- `tests/test_release_manifest.py`: 33 tests for the manifest command, which
  previously had none of its own.

### Fixed

- **The manifest command could destroy the artifact it described.** Passing one
  path as both `--artifact` and `--output` exited 0 and rewrote the ZIP as
  Markdown. The destination is now rejected if it is the artifact by resolved
  path or by filesystem identity, including through a symlink or hard link, and
  an existing manifest is preserved unless `--replace` is passed.
- **Unknown Git provenance was reported as a clean working tree.** Missing Git,
  a failed `git status`, an unresolvable HEAD and a non-repository source now
  all produce **Unknown** with a stated reason. Attributing an artifact to a
  commit requires the build record above; inspection-time repository state is
  reported separately and labelled as not describing the build.
- **The archive content digest framed its input ambiguously.** Member names and
  contents were concatenated without lengths, so two different single-member
  archives shared a digest. The digest is now the versioned
  `studio-release-content-v2`, which length-frames every field; duplicate member
  names are refused. Full artifact SHA-256 behaviour is unchanged, and the
  version travels with the value because the two are not comparable.
- **The shipped artifact failed its own documentation checker.** `docs/Rules.md`
  linked the local working history that the manifest deliberately excludes, so
  four links broke on extraction while the checkout passed. Rules now names
  those files without linking them, and `scripts/check_docs.py` fails any
  shipped document that links an excluded file.
- A Black-box-only Run's results were invisible in the current shell, because
  the assurance controller hides them unless its own tab is active.

### Known limitations unchanged by this candidate

Native Linux, macOS and Docker remain **not qualified**; bounded parallel pacing
stress remains **not tested**; every Judge remains **uncalibrated**; and the
owner approvals that gate publication remain outstanding.

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
