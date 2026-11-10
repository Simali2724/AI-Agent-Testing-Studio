"""Release manifest generation (T-054).

`test_package_release.py` tests the packager; this file tests the separate
manifest command, which previously destroyed its own input, reported unknown Git
provenance as a clean working tree, and framed its content digest ambiguously.

Everything here runs on synthetic scratch archives and temporary Git
repositories. No real release artifact, repository or saved run is touched.
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import warnings
import zipfile
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).parents[1] / "scripts"
# The manifest imports its sibling provenance module, so the directory has to be
# importable before the module itself is loaded by path.
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault(name, module)
    spec.loader.exec_module(module)
    return module


manifest = _load("release_manifest")
provenance = _load("build_provenance")
packager = _load("package_release")

GIT = {"GIT_AUTHOR_NAME": "Fixture", "GIT_AUTHOR_EMAIL": "fixture@example.invalid"}


def zip_with(path: Path, members: dict[str, bytes], *, date=(2020, 1, 1, 0, 0, 0)) -> Path:
    with zipfile.ZipFile(path, "w") as archive:
        for name, data in members.items():
            archive.writestr(zipfile.ZipInfo(name, date), data)
    return path


def artifact(tmp_path: Path, name: str = "candidate.zip") -> Path:
    return zip_with(tmp_path / name, {"app/main.py": b"print(1)\n", "README.md": b"Studio\n"})


def run_cli(*args: str) -> subprocess.CompletedProcess:
    """Drive the real command line, so exit codes and messages are the ones shipped."""
    return subprocess.run(
        [sys.executable, str(SCRIPTS / "release_manifest.py"), *args],
        capture_output=True,
        text=True,
        timeout=180,
    )


def repository(root: Path, *, dirty: bool = False, commit: bool = True) -> Path:
    """A throwaway Git repository, optionally left dirty or without any commit."""
    root.mkdir(parents=True, exist_ok=True)
    (root / "tracked.txt").write_text("tracked\n", encoding="utf-8")
    environment = {**os.environ, **GIT}
    subprocess.run(["git", "init", "-q"], cwd=root, check=True, env=environment)
    subprocess.run(["git", "add", "tracked.txt"], cwd=root, check=True, env=environment)
    if commit:
        subprocess.run(
            [
                "git",
                "-c",
                "user.name=Fixture",
                "-c",
                "user.email=f@example.invalid",
                "commit",
                "-q",
                "-m",
                "fixture",
            ],
            cwd=root,
            check=True,
            env=environment,
        )
    if dirty:
        (root / "untracked.txt").write_text("uncommitted\n", encoding="utf-8")
    return root


# --------------------------------------------------------------------------
# Fix 2 — the manifest must never overwrite or destroy its input artifact
# --------------------------------------------------------------------------


def test_the_same_path_for_input_and_output_is_refused_without_touching_the_zip(tmp_path):
    """The audited probe passed one path as both --artifact and --output."""
    target = artifact(tmp_path)
    before = target.read_bytes()
    result = run_cli("--artifact", str(target), "--version", "t", "--output", str(target))
    assert result.returncode != 0
    assert target.read_bytes() == before
    assert zipfile.is_zipfile(target)
    assert "Traceback" not in result.stderr
    assert "refused" in result.stderr.casefold()


def test_a_markdown_named_alias_of_the_artifact_is_refused(tmp_path):
    """A hard link gives the artifact a second name; identity, not spelling, decides."""
    target = artifact(tmp_path)
    before = target.read_bytes()
    alias = tmp_path / "alias.md"
    try:
        os.link(target, alias)
    except OSError:
        pytest.skip("This account cannot create hard links.")
    result = run_cli("--artifact", str(target), "--version", "t", "--output", str(alias))
    assert result.returncode != 0
    assert target.read_bytes() == before
    assert zipfile.is_zipfile(target)


def test_a_relative_and_absolute_spelling_of_one_path_is_still_one_file(tmp_path, monkeypatch):
    target = artifact(tmp_path)
    before = target.read_bytes()
    monkeypatch.chdir(tmp_path)
    with pytest.raises(manifest.ManifestError):
        manifest.resolve_output(target, Path("candidate.zip"), replace=False)
    assert target.read_bytes() == before


def test_an_existing_unrelated_destination_is_preserved_by_default(tmp_path):
    target = artifact(tmp_path)
    destination = tmp_path / "notes.md"
    destination.write_text("hand-written notes\n", encoding="utf-8")
    result = run_cli("--artifact", str(target), "--version", "t", "--output", str(destination))
    assert result.returncode != 0
    assert destination.read_text(encoding="utf-8") == "hand-written notes\n"


def test_replacement_happens_only_when_it_is_asked_for(tmp_path):
    target = artifact(tmp_path)
    destination = tmp_path / "notes.md"
    destination.write_text("stale\n", encoding="utf-8")
    result = run_cli(
        "--artifact", str(target), "--version", "t", "--output", str(destination), "--replace"
    )
    assert result.returncode == 0, result.stderr
    assert "Release manifest" in destination.read_text(encoding="utf-8")


def test_a_destination_that_appears_during_generation_is_preserved(tmp_path, monkeypatch):
    """The race case: the checks passed, then another process created the file."""
    destination = tmp_path / "late.md"
    real_rename, real_link = os.rename, os.link

    def rename(src, dst):
        Path(dst).write_text("written by someone else\n", encoding="utf-8")
        return real_rename(src, dst)

    def link(src, dst):
        Path(dst).write_text("written by someone else\n", encoding="utf-8")
        return real_link(src, dst)

    monkeypatch.setattr(os, "rename", rename)
    monkeypatch.setattr(os, "link", link)
    with pytest.raises(manifest.ManifestError):
        manifest.publish(destination, "new manifest", replace=False)
    assert destination.read_text(encoding="utf-8") == "written by someone else\n"


def test_a_fresh_manifest_records_the_unchanged_artifact_hash(tmp_path):
    target = artifact(tmp_path)
    expected = manifest.digest(target)
    before = target.read_bytes()
    output = tmp_path / "candidate.manifest.md"
    result = run_cli("--artifact", str(target), "--version", "0.1.0-rc.1", "--output", str(output))
    assert result.returncode == 0, result.stderr
    text = output.read_text(encoding="utf-8")
    assert expected in text
    assert target.read_bytes() == before
    assert manifest.digest(target) == expected


def test_a_missing_artifact_fails_cleanly(tmp_path):
    result = run_cli("--artifact", str(tmp_path / "absent.zip"), "--version", "t")
    assert result.returncode == 1
    assert "Traceback" not in result.stderr


def test_a_file_that_is_not_a_zip_fails_cleanly(tmp_path):
    broken = tmp_path / "broken.zip"
    broken.write_bytes(b"not a zip at all")
    result = run_cli(
        "--artifact", str(broken), "--version", "t", "--output", str(tmp_path / "m.md")
    )
    assert result.returncode == 1
    assert "Traceback" not in result.stderr
    assert not (tmp_path / "m.md").exists()


# --------------------------------------------------------------------------
# Fix 3 — unknown provenance is never reported as a clean working tree
# --------------------------------------------------------------------------


def test_a_clean_and_a_dirty_repository_stay_distinguishable(tmp_path):
    clean = provenance.git_state(repository(tmp_path / "clean"))
    dirty = provenance.git_state(repository(tmp_path / "dirty", dirty=True))
    assert clean["state"] == provenance.CLEAN
    assert dirty["state"] == provenance.DIRTY
    assert clean["commit"] and dirty["commit"]
    assert dirty["uncommitted"]


def test_a_directory_that_is_not_a_repository_is_unknown_not_clean(tmp_path):
    """An extracted source archive has no .git, and must not look clean."""
    plain = tmp_path / "extracted"
    plain.mkdir()
    state = provenance.git_state(plain)
    assert state["state"] == provenance.UNKNOWN
    assert state["commit"] is None
    assert "not a Git repository" in state["reason"]


def test_a_repository_without_a_commit_is_unknown(tmp_path):
    state = provenance.git_state(repository(tmp_path / "fresh", commit=False))
    assert state["state"] == provenance.UNKNOWN
    assert state["commit"] is None
    assert "HEAD does not resolve" in state["reason"]


def test_missing_git_is_unknown(tmp_path, monkeypatch):
    def unavailable(*args, **kwargs):
        raise FileNotFoundError("git")

    monkeypatch.setattr(provenance.subprocess, "run", unavailable)
    state = provenance.git_state(tmp_path)
    assert state["state"] == provenance.UNKNOWN
    assert state["commit"] is None


def test_a_failing_git_status_is_unknown_even_with_a_resolvable_head(tmp_path, monkeypatch):
    root = repository(tmp_path / "repo")
    real = provenance.subprocess.run

    def selective(args, **kwargs):
        if list(args)[1:2] == ["status"]:
            return subprocess.CompletedProcess(args, 128, b"", b"fatal: fixture failure")
        return real(args, **kwargs)

    monkeypatch.setattr(provenance.subprocess, "run", selective)
    state = provenance.git_state(root)
    assert state["state"] == provenance.UNKNOWN
    assert state["commit"], "a resolvable HEAD is still worth recording"
    assert "git status failed" in state["reason"]


def test_a_manifest_without_a_build_record_claims_no_commit(tmp_path):
    target = artifact(tmp_path)
    output = tmp_path / "m.md"
    result = run_cli("--artifact", str(target), "--version", "t", "--output", str(output))
    assert result.returncode == 0, result.stderr
    text = output.read_text(encoding="utf-8")
    assert "| Source state | **Unknown**" in text
    assert "| Build attribution | **Not available**" in text
    assert "| This artifact is identified by | the artifact's own SHA-256 below |" in text
    assert "(clean working tree)" not in text
    assert manifest.digest(target) in text, "the hash must work when Git attribution does not"


def test_an_unrelated_archive_is_not_attributed_to_a_recorded_commit(tmp_path):
    """The build record is proof only for the bytes whose hash it carries."""
    root = repository(tmp_path / "repo")
    real = zip_with(tmp_path / "real.zip", {"a.txt": b"real"})
    record = tmp_path / "real.build.json"
    provenance.record(record, source_root=root, artifact=real, files=1, source_bytes=4)

    older = zip_with(tmp_path / "older.zip", {"a.txt": b"older"})
    result = run_cli(
        "--artifact",
        str(older),
        "--version",
        "t",
        "--output",
        str(tmp_path / "older.md"),
        "--build-manifest",
        str(record),
    )
    assert result.returncode == 1
    assert "different artifact" in result.stderr
    assert not (tmp_path / "older.md").exists()


def test_a_verified_build_record_attributes_a_clean_build(tmp_path):
    root = repository(tmp_path / "repo")
    built = zip_with(tmp_path / "built.zip", {"a.txt": b"built"})
    record = tmp_path / "built.build.json"
    written = provenance.record(record, source_root=root, artifact=built, files=1, source_bytes=5)
    assert written["source"]["state"] == provenance.CLEAN

    output = tmp_path / "built.md"
    result = run_cli(
        "--artifact",
        str(built),
        "--version",
        "t",
        "--output",
        str(output),
        "--build-manifest",
        str(record),
    )
    assert result.returncode == 0, result.stderr
    text = output.read_text(encoding="utf-8")
    assert "| Source state | **Clean**" in text
    assert written["source"]["commit"] in text
    assert "clean working tree at build time" in text


def test_a_dirty_build_record_refuses_commit_attribution(tmp_path):
    root = repository(tmp_path / "repo", dirty=True)
    built = zip_with(tmp_path / "built.zip", {"a.txt": b"built"})
    record = tmp_path / "built.build.json"
    written = provenance.record(record, source_root=root, artifact=built, files=1, source_bytes=5)
    assert written["source"]["state"] == provenance.DIRTY

    output = tmp_path / "built.md"
    assert (
        run_cli(
            "--artifact",
            str(built),
            "--version",
            "t",
            "--output",
            str(output),
            "--build-manifest",
            str(record),
        ).returncode
        == 0
    )
    text = output.read_text(encoding="utf-8")
    assert "| Source state | **Dirty**" in text
    assert "| This artifact is identified by | the artifact's own SHA-256 below |" in text


def test_an_unknown_build_record_is_reported_as_unknown(tmp_path):
    plain = tmp_path / "extracted"
    plain.mkdir()
    built = zip_with(tmp_path / "built.zip", {"a.txt": b"built"})
    record = tmp_path / "built.build.json"
    written = provenance.record(record, source_root=plain, artifact=built, files=1, source_bytes=5)
    assert written["source"]["state"] == provenance.UNKNOWN

    output = tmp_path / "built.md"
    assert (
        run_cli(
            "--artifact",
            str(built),
            "--version",
            "t",
            "--output",
            str(output),
            "--build-manifest",
            str(record),
        ).returncode
        == 0
    )
    text = output.read_text(encoding="utf-8")
    assert "| Source state | **Unknown**" in text
    assert "not a clean working tree" in text


def test_a_build_record_is_never_overwritten(tmp_path):
    root = repository(tmp_path / "repo")
    built = zip_with(tmp_path / "built.zip", {"a.txt": b"built"})
    record = tmp_path / "built.build.json"
    provenance.record(record, source_root=root, artifact=built, files=1, source_bytes=5)
    first = record.read_text(encoding="utf-8")
    with pytest.raises(provenance.ProvenanceError):
        provenance.record(record, source_root=root, artifact=built, files=1, source_bytes=5)
    assert record.read_text(encoding="utf-8") == first


def test_an_unsupported_build_record_scheme_is_refused(tmp_path):
    built = zip_with(tmp_path / "built.zip", {"a.txt": b"built"})
    record = tmp_path / "bad.json"
    record.write_text(json.dumps({"scheme": "something-else"}), encoding="utf-8")
    with pytest.raises(provenance.ProvenanceError):
        provenance.load(record, built)


def test_the_packager_records_build_provenance_for_the_bytes_it_published(tmp_path):
    """The packager's record must describe the archive it actually wrote."""
    root = repository(tmp_path / "source")
    (root / "README.md").write_text("Studio source\n", encoding="utf-8")
    (root / "app").mkdir()
    (root / "app" / "main.py").write_text("print('hello')\n", encoding="utf-8")
    output = tmp_path / "out.zip"
    record = tmp_path / "out.build.json"
    result = packager.package_release(root, output, record)
    assert result["build_manifest"] == str(record)
    loaded = provenance.load(record, output)
    assert loaded["artifact_sha256"] == manifest.digest(output)
    assert loaded["files"] == result["files"]
    assert loaded["source"]["state"] in (provenance.CLEAN, provenance.DIRTY)


# --------------------------------------------------------------------------
# Fix 4 — the content digest must frame its input unambiguously
# --------------------------------------------------------------------------


def test_the_audited_collision_pair_now_has_different_content_digests(tmp_path):
    """`{"a": b"bc"}` and `{"ab": b"c"}` both concatenated to b"abc" under v1."""
    left = zip_with(tmp_path / "a.zip", {"a": b"bc"})
    right = zip_with(tmp_path / "b.zip", {"ab": b"c"})
    assert manifest.content_digest(left)[0] != manifest.content_digest(right)[0]
    assert manifest.digest(left) != manifest.digest(right)


@pytest.mark.parametrize(
    ("left", "right"),
    [
        ({"a.txt": b"same"}, {"b.txt": b"same"}),
        ({"a.txt": b"one"}, {"a.txt": b"two"}),
        ({"a.txt": b""}, {"a.txt": b"\x00"}),
        ({"empty.txt": b"", "x.txt": b"x"}, {"x.txt": b"x"}),
        ({"ünïcode.txt": b"x"}, {"unicode.txt": b"x"}),
        ({"a/b.txt": b"x"}, {"ab.txt": b"x"}),
    ],
)
def test_different_archives_have_different_content_digests(tmp_path, left, right):
    one = zip_with(tmp_path / "left.zip", left)
    two = zip_with(tmp_path / "right.zip", right)
    assert manifest.content_digest(one)[0] != manifest.content_digest(two)[0]


def test_timestamps_order_and_compression_do_not_change_the_content_digest(tmp_path):
    members = {"b.txt": b"beta", "a.txt": b"alpha", "nested/c.txt": b"gamma"}
    one = tmp_path / "one.zip"
    with zipfile.ZipFile(one, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, data in members.items():
            archive.writestr(zipfile.ZipInfo(name, (1990, 1, 1, 0, 0, 0)), data)
    two = tmp_path / "two.zip"
    with zipfile.ZipFile(two, "w", zipfile.ZIP_STORED) as archive:
        for name, data in reversed(list(members.items())):
            archive.writestr(zipfile.ZipInfo(name, (2035, 12, 31, 23, 59, 58)), data)
    assert manifest.content_digest(one)[0] == manifest.content_digest(two)[0]
    assert manifest.content_digest(one)[1] == 3
    assert manifest.digest(one) != manifest.digest(two), "the artifact hashes still differ"


def test_an_empty_file_is_distinguished_from_a_missing_one(tmp_path):
    with_empty = zip_with(tmp_path / "with.zip", {"a.txt": b"a", "gap.txt": b""})
    without = zip_with(tmp_path / "without.zip", {"a.txt": b"a"})
    assert manifest.content_digest(with_empty)[1] == 2
    assert manifest.content_digest(without)[1] == 1
    assert manifest.content_digest(with_empty)[0] != manifest.content_digest(without)[0]


def test_duplicate_member_names_are_refused_explicitly(tmp_path):
    duplicated = tmp_path / "dup.zip"
    with warnings.catch_warnings():
        # zipfile warns about the duplicate; here it is the fixture, not a defect.
        warnings.simplefilter("ignore", UserWarning)
        with zipfile.ZipFile(duplicated, "w") as archive:
            archive.writestr("same.txt", b"first")
            archive.writestr("same.txt", b"second")
    with pytest.raises(manifest.ManifestError, match="duplicated member name"):
        manifest.content_digest(duplicated)
    result = run_cli(
        "--artifact",
        str(duplicated),
        "--version",
        "t",
        "--output",
        str(tmp_path / "dup.md"),
    )
    assert result.returncode == 1
    assert not (tmp_path / "dup.md").exists()


def test_the_content_digest_algorithm_version_is_published_in_the_manifest(tmp_path):
    """A published comparison may quote the old value, so the version must travel."""
    target = artifact(tmp_path)
    output = tmp_path / "m.md"
    assert (
        run_cli("--artifact", str(target), "--version", "t", "--output", str(output)).returncode
        == 0
    )
    text = output.read_text(encoding="utf-8")
    assert manifest.CONTENT_DIGEST_VERSION == "studio-release-content-v2"
    assert f"| Content digest algorithm | `{manifest.CONTENT_DIGEST_VERSION}` |" in text
    assert "not** comparable with a value produced by an earlier" in text
