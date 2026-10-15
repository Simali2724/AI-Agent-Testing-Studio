"""Scanner-only Docker sandbox. Uploaded programs are never started or imported."""

import asyncio
import json
import shutil
import uuid
from pathlib import Path

from ..config import ROOT, RUNTIME


class ToolUnavailable(Exception):
    """Missing daemon/image/database, bounded output or timeout: Not tested."""


def specification() -> dict:
    return json.loads((ROOT / "app/studio/scanners.json").read_text())


async def bounded_process(args: list[str], timeout: float, limit: int) -> tuple[int, bytes]:
    process = await asyncio.create_subprocess_exec(
        *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL
    )
    output = bytearray()
    try:
        async with asyncio.timeout(timeout):
            while chunk := await process.stdout.read(65536):
                output.extend(chunk)
                if len(output) > limit:
                    raise ToolUnavailable("Scanner output exceeded the bounded limit.")
            await process.wait()
    except BaseException:
        if process.returncode is None:
            process.kill()
        await process.wait()
        raise
    return process.returncode, bytes(output)


def command(tool: str, source: Path, name: str, image: str) -> list[str]:
    spec = specification()["tools"][tool]
    args = [
        "docker",
        "run",
        "--rm",
        "--pull=never",
        "--name",
        name,
        "--network=none",
        "--read-only",
        "--cap-drop=ALL",
        "--security-opt=no-new-privileges",
        "--memory=512m",
        "--cpus=1",
        "--pids-limit=64",
        "--user=65534:65534",
        "--tmpfs=/tmp:rw,noexec,nosuid,size=64m,mode=1777",
        "--env=HOME=/tmp",
        "--env=SEMGREP_SEND_METRICS=off",
        "--env=SEMGREP_ENABLE_VERSION_CHECK=0",
        "--mount",
        f"type=bind,src={source.resolve()},dst=/source,readonly",
        "--mount",
        f"type=bind,src={(ROOT / 'app/assurance/rules').resolve()},dst=/rules,readonly",
    ]
    if spec.get("database"):
        database = RUNTIME / "scanner-databases" / spec["database"]
        if not database.is_dir() or not any(database.iterdir()):
            raise ToolUnavailable(
                f"Offline {tool} database missing; provision it before a networkless scan."
            )
        args += [
            "--mount",
            f"type=bind,src={database.resolve()},dst=/offline/{spec['database']},readonly",
        ]
        if tool == "osv":
            args += ["--env=OSV_SCANNER_LOCAL_DB_CACHE_DIRECTORY=/offline/osv"]
    return [*args, image, *spec["args"]]


async def scan(tool: str, source: Path) -> dict:
    if not shutil.which("docker"):
        raise ToolUnavailable(
            "Docker scanner sandbox is unavailable; source was not executed on the host."
        )
    config = specification()
    spec = config["tools"][tool]
    name = "studio-scan-" + uuid.uuid4().hex
    try:
        rc, metadata = await bounded_process(
            ["docker", "image", "inspect", spec["image"], "--format={{.Id}}"], 5, 4096
        )
        if rc != 0 or not metadata.strip().startswith(b"sha256:"):
            raise ToolUnavailable(
                f"Pinned {tool} {spec['version']} image is not installed; automatic pulls are disabled."
            )
        image_id = metadata.decode().strip()
        base = command(tool, source, name, image_id)
        if tool != "controls":
            version_args = {
                "gitleaks": ["version"],
                "semgrep": ["semgrep", "--version"],
                "bandit": ["bandit", "--version"],
                "osv": ["--version"],
                "trivy": ["--version"],
            }[tool]
            rc, actual_version = await bounded_process(
                base[: -len(spec["args"])] + version_args, 15, 8192
            )
            if rc != 0 or spec["version"] not in actual_version.decode(errors="replace"):
                raise ToolUnavailable(
                    f"{tool} runtime does not match pinned version {spec['version']}."
                )
        # Execute the inspected content ID, preventing a mutable tag race.
        rc, output = await bounded_process(base, config["timeout_seconds"], config["output_bytes"])
        if rc not in (0, 1):
            raise ToolUnavailable(f"{tool} could not finish (exit {rc}); no pass was inferred.")
        result = json.loads(output)
        return {
            "data": result,
            "tool": tool,
            "version": spec["version"],
            "image_id": image_id,
            "ruleset": config["version"],
        }
    except asyncio.CancelledError:
        raise
    except (TimeoutError, OSError, ValueError) as exc:
        raise ToolUnavailable(f"{tool} unavailable: {type(exc).__name__}; no scan result.") from exc
    finally:
        # Killing docker's client alone can leave a container running. Remove by random name.
        try:
            await bounded_process(["docker", "rm", "-f", name], 5, 4096)
        except (OSError, TimeoutError, ToolUnavailable):
            pass
