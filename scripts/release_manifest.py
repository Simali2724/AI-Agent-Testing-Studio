"""Describe a built release artifact so a reviewer can check it before publication.

Standard library only. Reads the artifact, optionally reads the build provenance
record written beside it during packaging, and writes a Markdown manifest. It
records what is true of **this build**: the artifact's own hash, a framed
content digest of its members, and an explicit source-provenance state.

Three things this tool deliberately refuses to do:

* Overwrite its own input. The output path is compared against the artifact by
  resolved path and by filesystem identity, so a symlink or hard-link alias
  cannot turn the ZIP into Markdown. An existing output is kept unless
  ``--replace`` is passed.
* Report unknown provenance as clean. Missing Git, a failed ``git status``, an
  unresolvable HEAD and a non-repository source all produce **Unknown**. The
  artifact is then identified by its SHA-256, with the reason stated.
* Attribute an artifact to a commit on the strength of inspecting the repository
  now. Build attribution requires ``--build-manifest``, whose recorded hash must
  match these bytes. Without it, the Git state shown is labelled inspection-time
  and the artifact is identified by its hash alone.

Usage:

    python scripts/release_manifest.py --artifact runtime/release/<name>.zip \\
        --version 0.1.0-rc.1 --evidence docs/verification.md \\
        --build-manifest runtime/release/<name>.build.json
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_provenance import (  # noqa: E402
    CLEAN,
    DIRTY,
    UNKNOWN,
    ProvenanceError,
    git_state,
    load,
    sha256_file,
)

ROOT = Path(__file__).resolve().parents[1]

#: The content digest's canonical framing. Published comparisons quote the
#: version with the value, because v1 framed nothing and was ambiguous: it
#: concatenated member names and raw bytes, so {"a": b"bc"} and {"ab": b"c"}
#: both hashed b"abc". v2 length-frames every field, so no two different member
#: sets can produce the same canonical bytes.
CONTENT_DIGEST_VERSION = "studio-release-content-v2"


class ManifestError(ValueError):
    """A safe error that names the problem without echoing archive contents."""


def digest(path: Path) -> str:
    """The artifact's own SHA-256, over its exact published bytes."""
    return sha256_file(path)


def content_digest(path: Path) -> tuple[str, int]:
    """Hash the archive's member names and contents, ignoring ZIP metadata.

    Two archives built from identical sources compare equal here even when their
    timestamps, member order or compression differ, so this identifies content
    rather than the build moment. Names are sorted, and every field is framed by
    its byte length, so a rename cannot be mistaken for a content change.

    Duplicate member names are refused: a ZIP may legally hold two entries with
    one name, and no single digest can honestly describe which one a reader
    would extract.
    """
    lines = [CONTENT_DIGEST_VERSION.encode("ascii"), b"\n"]
    count = 0
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        duplicates = sorted({name for name in names if names.count(name) > 1})
        if duplicates:
            raise ManifestError(
                f"The archive holds {len(duplicates)} duplicated member name(s); "
                "a content digest cannot describe it unambiguously."
            )
        for name in sorted(names):
            raw = name.encode("utf-8")
            data = archive.read(name)
            member = hashlib.sha256(data).hexdigest()
            # length:bytes for the name, then length:digest for the content.
            lines.append(f"{len(raw)}:".encode("ascii"))
            lines.append(raw)
            lines.append(f"\n{len(data)}:{member}\n".encode("ascii"))
            count += 1
    return hashlib.sha256(b"".join(lines)).hexdigest(), count


def _same_file(left: Path, right: Path) -> bool:
    """Whether two paths are the same file, including link and alias cases."""
    if left.resolve(strict=False) == right.resolve(strict=False):
        return True
    try:
        return left.exists() and right.exists() and os.path.samefile(left, right)
    except OSError:
        return False


def resolve_output(artifact: Path, requested: Path | None, *, replace: bool) -> Path:
    """Choose and validate the manifest destination before anything is opened.

    Refuses the artifact itself, any alias of it, and any existing file unless
    replacement was asked for explicitly. Nothing is opened for writing here, so
    a refusal cannot have touched the input.
    """
    output = (requested or artifact.with_suffix(".manifest.md")).absolute()
    if output.suffix.casefold() == ".zip":
        raise ManifestError(
            "The manifest is a Markdown document; refusing to write it to a .zip path."
        )
    if _same_file(artifact, output):
        raise ManifestError(
            "The output path is the artifact itself. The manifest would destroy the "
            "archive it describes; choose a different --output."
        )
    if output.is_dir():
        raise ManifestError("The output path is a directory; name the manifest file.")
    if (output.exists() or output.is_symlink()) and not replace:
        raise ManifestError(
            f"A file already exists at {output.name}. Existing manifests are kept; pass "
            "--replace to replace it deliberately."
        )
    if not output.parent.is_dir():
        raise ManifestError("The output directory must already exist.")
    return output


def publish(output: Path, text: str, *, replace: bool) -> None:
    """Write through a temporary file, then publish without clobbering a race.

    Mirrors the source packager: the destination either does not exist and gains
    the new file atomically, or it already exists and is preserved, even when a
    second process created it after the checks above.
    """
    handle, temporary = tempfile.mkstemp(
        prefix=".studio-manifest-", suffix=".tmp", dir=output.parent
    )
    temporary = Path(temporary)
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
        try:
            if replace:
                os.replace(temporary, output)
            elif os.name == "nt":
                # Windows rename is atomic and refuses an existing destination.
                os.rename(temporary, output)
            else:
                # POSIX rename overwrites, so use no-clobber hard-link publication.
                os.link(temporary, output)
                temporary.unlink()
        except FileExistsError:
            raise ManifestError(
                "A file appeared at the output path during generation; it was preserved "
                "and no manifest was written."
            ) from None
    except ManifestError:
        raise
    except OSError:
        raise ManifestError(
            "Could not write the manifest; no existing file was replaced."
        ) from None
    finally:
        temporary.unlink(missing_ok=True)


def provenance(artifact: Path, build_manifest: Path | None) -> dict:
    """Resolve what may honestly be claimed about this artifact's source.

    With a verified build record, the state describes the tree that produced the
    artifact. Without one, the repository is still inspected, but the result is
    labelled inspection-time and never used to attribute the artifact.
    """
    inspected = git_state(ROOT)
    if build_manifest is None:
        return {
            "attributed": False,
            "state": UNKNOWN,
            "reason": (
                "No build provenance record was supplied, so the source this artifact was "
                "built from is unknown. The Git state below was read when this manifest was "
                "generated and does not describe the build."
            ),
            "commit": None,
            "tree": None,
            "branch": None,
            "uncommitted": None,
            "inspected": inspected,
            "record": None,
        }
    record = load(build_manifest, artifact)
    source = dict(record["source"])
    return {
        "attributed": True,
        "state": source["state"],
        "reason": source["reason"],
        "commit": source.get("commit"),
        "tree": source.get("tree"),
        "branch": source.get("branch"),
        "uncommitted": source.get("uncommitted"),
        "inspected": inspected,
        "record": record,
    }


def _identified_by(state: dict) -> str:
    """One sentence naming what actually identifies this artifact."""
    if state["attributed"] and state["state"] == CLEAN:
        return f"commit `{state['commit']}` (clean working tree at build time)"
    return "the artifact's own SHA-256 below"


def _state_label(state: dict) -> str:
    return {
        CLEAN: "**Clean** — no uncommitted paths at build time",
        DIRTY: "**Dirty** — uncommitted changes present at build time",
        UNKNOWN: "**Unknown** — source attribution is unavailable",
    }[state["state"]]


def render(artifact: Path, version: str, evidence: str, state: dict) -> str:
    """Build the manifest text. No file is written by this function."""
    archive_digest, members = content_digest(artifact)
    value = lambda text: f"`{text}`" if text else "Unavailable"  # noqa: E731
    lines = [
        f"# Release manifest — {version}",
        "",
        f"Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%SZ')} by "
        "`scripts/release_manifest.py`. This describes one build. It is not an approval, "
        "a signature, or a statement that publication was authorized.",
        "",
        "## Artifact",
        "",
        "| Field | Value |",
        "| --- | --- |",
        f"| File | `{artifact.name}` |",
        f"| Size | {artifact.stat().st_size} bytes |",
        f"| SHA-256 | `{digest(artifact)}` |",
        f"| Content digest | `{archive_digest}` |",
        f"| Content digest algorithm | `{CONTENT_DIGEST_VERSION}` |",
        f"| Members | {members} |",
        "",
        "The content digest covers member names and contents under the framed canonical "
        f"format `{CONTENT_DIGEST_VERSION}`, so it is unchanged by ZIP timestamps, member "
        "order or compression. It is **not** comparable with a value produced by an earlier "
        "algorithm version; compare the SHA-256 above when in doubt.",
        "",
        "## Source provenance",
        "",
        "| Field | Value |",
        "| --- | --- |",
        f"| Source state | {_state_label(state)} |",
        f"| Build attribution | {'Verified build record' if state['attributed'] else '**Not available**'} |",
        f"| Branch | {value(state['branch'])} |",
        f"| Commit | {value(state['commit'])} |",
        f"| Tree | {value(state['tree'])} |",
        f"| This artifact is identified by | {_identified_by(state)} |",
        "",
        f"{state['reason']}",
        "",
    ]
    if state["attributed"] and state["state"] == DIRTY:
        lines += [
            "> The working tree was **dirty** when this artifact was built, so the commit "
            "above does **not** describe its contents. Identify this artifact by its "
            "SHA-256 and content digest. Do not attribute it to the commit alone, and do "
            "not assume a rebuild from that commit reproduces it.",
            "",
            "Uncommitted paths at build time:",
            "",
            "```text",
            state["uncommitted"] or "(none recorded)",
            "```",
            "",
        ]
    elif state["state"] == UNKNOWN:
        lines += [
            "> Source provenance is **Unknown**. This is not a clean working tree: it means "
            "the source cannot be attributed to a commit from the evidence available. "
            "Identify this artifact by its SHA-256 and content digest only. Do not assume it "
            "matches any commit, and do not describe it as built from a clean tree.",
            "",
        ]
    inspected = state["inspected"]
    lines += [
        "### Inspection-time repository state",
        "",
        "Read from the working checkout when this manifest was generated. A manifest runs "
        "**after** packaging, so this describes the repository now, not the build. It is "
        "recorded for context and is never used to attribute the artifact.",
        "",
        "| Field | Value |",
        "| --- | --- |",
        f"| State | `{inspected['state']}` |",
        f"| Reason | {inspected['reason']} |",
        f"| Commit | {value(inspected.get('commit'))} |",
        f"| Branch | {value(inspected.get('branch'))} |",
        "",
        "## Evidence",
        "",
        f"Recorded test and verification evidence: `{evidence}`.",
        "",
        "A manifest cannot establish that those checks passed. Read the evidence document "
        "and the release gate ledger (`docs/open-source-readiness.md`) before authorizing "
        "publication.",
        "",
        "## Verify this artifact",
        "",
        "```powershell",
        f"Get-FileHash {artifact.name} -Algorithm SHA256",
        "```",
        "",
        "```sh",
        f"sha256sum {artifact.name}",
        "```",
        "",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--artifact", required=True, type=Path)
    parser.add_argument("--version", required=True)
    parser.add_argument(
        "--evidence",
        default="docs/verification.md",
        help="Document holding the recorded test evidence for this candidate.",
    )
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument(
        "--build-manifest",
        type=Path,
        default=None,
        help="Build provenance record written beside the artifact during packaging. "
        "Its recorded SHA-256 must match the artifact, or generation fails.",
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Replace an existing manifest at the output path. Off by default: an existing "
        "file is kept and generation fails instead.",
    )
    args = parser.parse_args(argv)

    try:
        artifact = args.artifact.absolute()
        if not artifact.is_file():
            raise ManifestError(f"No such artifact: {artifact.name}")
        output = resolve_output(artifact, args.output, replace=args.replace)
        if args.build_manifest is not None and _same_file(artifact, args.build_manifest):
            raise ManifestError("The build provenance record cannot be the artifact itself.")
        state = provenance(artifact, args.build_manifest)
        text = render(artifact, args.version, args.evidence, state)
        publish(output, text, replace=args.replace)
    except (ManifestError, ProvenanceError) as exc:
        print(f"Manifest refused: {exc}", file=sys.stderr)
        return 1
    except zipfile.BadZipFile:
        print("Manifest refused: the artifact is not a readable ZIP archive.", file=sys.stderr)
        return 1
    except OSError:
        print(
            "Manifest refused: the artifact or output could not be read or written.",
            file=sys.stderr,
        )
        return 1
    print(f"Manifest written: {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
