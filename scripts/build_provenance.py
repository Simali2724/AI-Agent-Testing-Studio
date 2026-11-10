"""Record, at packaging time, what source an artifact was actually built from.

Standard library only.

Why this module exists: a manifest generated *after* packaging can inspect the
repository as it is **now**, which says nothing about the tree that produced an
artifact minutes or days earlier. Attributing an artifact to whichever commit
happens to be checked out at inspection time is a guess. So the packager writes
a small JSON sidecar while it builds, holding the finished archive's SHA-256 and
the Git state captured at that moment, and the manifest generator verifies that
hash before repeating any of it.

Provenance is one of three explicit states, never a default:

``clean``
    Git answered, the working tree had no modified or untracked paths, and HEAD
    resolved. The commit describes the source.
``dirty``
    Git answered and reported uncommitted paths. The commit does **not**
    describe the source, so the artifact is identified by its own hash.
``unknown``
    Git is missing, Git failed, the source is not a repository, or HEAD does not
    resolve. This is **not** a clean tree. Source attribution is unavailable and
    the artifact is identified by its own hash.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

#: Versioned so a consumer never silently reinterprets an older sidecar.
SCHEME = "studio-build-provenance-v1"
CLEAN, DIRTY, UNKNOWN = "clean", "dirty", "unknown"


class ProvenanceError(ValueError):
    """A safe error that names the problem without echoing file contents."""


def _git(root: Path, *args: str) -> tuple[bool, str]:
    """Run one Git command, returning ``(succeeded, trimmed output)``."""
    try:
        done = subprocess.run(
            ["git", *args],
            cwd=root,
            capture_output=True,
            check=False,
            timeout=60,
        )
    except (OSError, subprocess.SubprocessError):
        return False, ""
    if done.returncode != 0:
        return False, ""
    return True, done.stdout.decode("utf-8", "replace").strip()


def sha256_file(path: Path) -> str:
    """Stream a file's SHA-256, so a large archive is never held in memory."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _unknown(reason: str, **known: str | None) -> dict:
    state = {"state": UNKNOWN, "reason": reason, "commit": None, "tree": None, "branch": None}
    state["uncommitted"] = None
    state.update(known)
    return state


def git_state(root: Path) -> dict:
    """Describe one source tree's Git provenance as clean, dirty or unknown.

    A Git failure, a non-repository directory (an extracted source archive, for
    example) and an unresolvable HEAD all return ``unknown`` with a stated
    reason. None of them is ever reported as a clean working tree.
    """
    root = Path(root)
    inside_ok, inside = _git(root, "rev-parse", "--is-inside-work-tree")
    if not inside_ok:
        return _unknown("Git is unavailable, or this directory is not a Git repository.")
    if inside != "true":
        return _unknown("This directory belongs to a Git repository but is not a working tree.")

    status_ok, status = _git(root, "status", "--porcelain")
    commit_ok, commit = _git(root, "rev-parse", "HEAD")
    tree_ok, tree = _git(root, "rev-parse", "HEAD^{tree}")
    branch_ok, branch = _git(root, "rev-parse", "--abbrev-ref", "HEAD")
    branch = branch if branch_ok and branch else None

    if not status_ok:
        return _unknown(
            "git status failed, so the working tree could not be inspected.",
            commit=commit if commit_ok and commit else None,
            tree=tree if tree_ok and tree else None,
            branch=branch,
        )
    if not (commit_ok and commit and tree_ok and tree):
        return _unknown(
            "HEAD does not resolve, so there is no commit to attribute this source to.",
            branch=branch,
            uncommitted=status,
        )
    if status:
        return {
            "state": DIRTY,
            "reason": (
                "git status reported uncommitted paths, so the commit does not describe "
                "this source."
            ),
            "commit": commit,
            "tree": tree,
            "branch": branch,
            "uncommitted": status,
        }
    return {
        "state": CLEAN,
        "reason": "git status reported no modified or untracked paths.",
        "commit": commit,
        "tree": tree,
        "branch": branch,
        "uncommitted": "",
    }


def record(
    path: Path,
    *,
    source_root: Path,
    artifact: Path,
    files: int,
    source_bytes: int,
) -> dict:
    """Write the build sidecar beside a finished artifact, never replacing one.

    The packager calls this immediately after publishing the archive, so the
    recorded hash is the hash of the bytes that were actually shipped.
    """
    path, artifact = Path(path).absolute(), Path(artifact).absolute()
    if path.exists() or path.is_symlink():
        raise ProvenanceError(
            "A build provenance record already exists at that path; it was not replaced."
        )
    if not path.parent.is_dir():
        raise ProvenanceError("The build provenance directory must already exist.")
    payload = {
        "scheme": SCHEME,
        "recorded_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "artifact_name": artifact.name,
        "artifact_sha256": sha256_file(artifact),
        "artifact_bytes": artifact.stat().st_size,
        "files": files,
        "source_bytes": source_bytes,
        "source": git_state(source_root),
        "note": (
            "Captured while packaging. The Git state above describes the tree that produced "
            "this artifact, not whatever is checked out when a manifest is generated."
        ),
    }
    data = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    handle, temporary = tempfile.mkstemp(prefix=".studio-build-", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary)
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(data)
        try:
            # Windows rename is atomic and refuses an existing destination. POSIX
            # rename overwrites, so publish there through a no-clobber hard link.
            if os.name == "nt":
                os.rename(temporary, path)
            else:
                os.link(temporary, path)
                temporary.unlink()
        except FileExistsError:
            raise ProvenanceError(
                "A build provenance record appeared at that path; the existing file was kept."
            ) from None
    except ProvenanceError:
        raise
    except OSError:
        raise ProvenanceError("Could not write the build provenance record.") from None
    finally:
        temporary.unlink(missing_ok=True)
    return payload


def load(path: Path, artifact: Path) -> dict:
    """Read a build sidecar and prove it describes *this* artifact's bytes.

    A hash mismatch means the sidecar belongs to a different build. That is an
    error rather than a warning, because the record exists precisely to stop an
    older or unrelated ZIP being attributed to the current commit.
    """
    path, artifact = Path(path), Path(artifact)
    try:
        raw = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        raise ProvenanceError("The build provenance record could not be read.") from None
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        raise ProvenanceError("The build provenance record is not valid JSON.") from None
    if not isinstance(payload, dict) or payload.get("scheme") != SCHEME:
        raise ProvenanceError(
            f"Unsupported build provenance scheme; this tool reads {SCHEME} only."
        )
    source = payload.get("source")
    if not isinstance(source, dict) or source.get("state") not in (CLEAN, DIRTY, UNKNOWN):
        raise ProvenanceError("The build provenance record has no explicit source state.")
    recorded = payload.get("artifact_sha256")
    actual = sha256_file(artifact)
    if not isinstance(recorded, str) or recorded.casefold() != actual:
        raise ProvenanceError(
            "The build provenance record describes a different artifact: its recorded SHA-256 "
            "does not match this file. Rebuild, or omit the record and accept unknown provenance."
        )
    payload["verified_sha256"] = actual
    return payload


def main(argv: list[str] | None = None) -> int:
    """Print one tree's provenance state, so the states can be checked by hand."""
    import argparse

    parser = argparse.ArgumentParser(description="Report a source tree's Git provenance state.")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    print(json.dumps(git_state(args.root), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
