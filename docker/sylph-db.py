#!/usr/bin/python3
"""Explicit, immutable Sylph database-member installation; no analysis interception."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from urllib.parse import urlsplit

CATALOG = Path("/opt/sylph/share/db/catalog.json")
RESERVE = 64 * 1024 * 1024


def fail(message):
    raise ValueError(message)


def digest(path, algorithm="sha256"):
    result = hashlib.new(algorithm)
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def identifier(value):
    if not re.fullmatch(r"[a-z0-9][a-z0-9._-]{0,95}", value) or ".." in value:
        fail("invalid member ID")
    return value


def regular(path):
    if path.is_symlink() or not stat.S_ISREG(path.lstat().st_mode):
        fail(f"not a regular, non-symlink file: {path}")


def safe_directory(path, writable=False):
    if path.is_symlink() or not path.is_dir():
        fail(f"root must be an existing physical directory: {path}")
    mode = path.stat().st_mode
    if mode & 0o022:
        fail(f"root must not be group/world writable: {path}")
    if writable and (path.stat().st_uid != os.geteuid() or not os.access(path, os.W_OK)):
        fail(f"installer must own and be able to write root: {path}")


def verify(member, expected_id):
    safe_directory(member)
    manifest_file = member / "manifest.json"
    ready = member / "READY"
    regular(manifest_file)
    regular(ready)
    if ready.read_text().strip() != digest(manifest_file):
        fail("manifest/READY mismatch; refusing incomplete or changed member")
    data = json.loads(manifest_file.read_text())
    if data.get("schema") != 1 or data.get("id") != expected_id:
        fail("manifest schema/member identity mismatch")
    filename = data.get("file")
    if filename not in ("database.syldb", "database.syl2db"):
        fail("invalid database filename")
    if set(p.name for p in member.iterdir()) != {filename, "manifest.json", "READY", "RESOURCE_LICENSE.txt"}:
        fail("unexpected/missing member files")
    for name in (filename, "manifest.json", "READY", "RESOURCE_LICENSE.txt"):
        path = member / name
        regular(path)
        if stat.S_IMODE(path.stat().st_mode) != 0o644:
            fail(f"member file permission drift: {name}")
    if stat.S_IMODE(member.stat().st_mode) != 0o755:
        fail("member directory permission drift")
    database = member / filename
    if database.stat().st_size != data.get("size") or digest(database) != data.get("sha256"):
        fail("database size/SHA256 mismatch")
    if digest(member / "RESOURCE_LICENSE.txt") != data.get("license_sha256"):
        fail("resource notice checksum mismatch")
    return data


def run_download(argv):
    # Capture a bounded tail even when curl writes many retry/progress messages.
    with tempfile.TemporaryFile() as output:
        result = subprocess.run(argv, stdout=output, stderr=subprocess.STDOUT)
        if result.returncode:
            output.seek(max(0, output.tell() - 32768))
            tail = output.read().decode(errors="replace").splitlines()[-80:]
            print(f"sylph-db: stage=download exit={result.returncode}", file=sys.stderr)
            print("\n".join(tail), file=sys.stderr)
            raise SystemExit(result.returncode)


def install(root, item, local_source=None):
    safe_directory(root, writable=True)
    name = identifier(item["id"])
    destination = root / name
    if os.path.lexists(destination):
        current = verify(destination, name)
        if current["source_identity"] != item["source_identity"]:
            fail("existing ID has different source identity; use a new member ID")
        print(f"already complete: {destination}")
        return current
    cache = root / ".downloads"
    if not cache.exists():
        cache.mkdir(mode=0o700)
    safe_directory(cache, writable=True)
    if stat.S_IMODE(cache.stat().st_mode) != 0o700:
        fail("download cache must have mode 0700")
    lock = root / (".lock-" + name)
    try:
        lock.mkdir(mode=0o700)
    except FileExistsError:
        fail(f"install lock exists: {lock}; do not remove while another installer runs")
    stage = None
    try:
        # Check again after taking the lock; never replace an existing release.
        if os.path.lexists(destination):
            fail("member appeared while locking; rerun verify")
        blob = cache / (name + ".part")
        cache_identity = cache / (name + ".identity")
        if os.path.lexists(blob):
            regular(blob)
            regular(cache_identity)
            if cache_identity.read_text() != item["source_identity"]:
                fail("partial cache identity mismatch")
        else:
            if os.path.lexists(cache_identity):
                regular(cache_identity)
            cache_identity.write_text(item["source_identity"])
            cache_identity.chmod(0o600)
        required = item["size"] - (blob.stat().st_size if blob.exists() else 0) + RESERVE
        if shutil.disk_usage(root).free < max(RESERVE, required):
            fail(f"insufficient space; need remaining member bytes plus {RESERVE} bytes reserve")
        if local_source is not None:
            regular(local_source)
            if blob.exists():
                fail(f"partial download exists: {blob}; remove this exact private cache pair or resume install")
            # Exclusive creation and no source symlinks; root is installer-controlled.
            with local_source.open("rb") as source, blob.open("xb") as target:
                shutil.copyfileobj(source, target, 8 * 1024 * 1024)
            blob.chmod(0o600)
        elif not blob.exists() or blob.stat().st_size < item["size"]:
            run_download([
                "curl", "--fail", "--location", "--proto", "=https",
                "--proto-redir", "=https", "--connect-timeout", "30",
                "--speed-limit", "1024", "--speed-time", "120",
                "--retry", "3", "--retry-delay", "5", "--continue-at", "-",
                "--output", str(blob), item["url"],
            ])
            blob.chmod(0o600)
        regular(blob)
        if blob.stat().st_size != item["size"] or digest(blob, item["algorithm"]) != item["checksum"]:
            fail(f"download integrity failed; retained private cache {blob}; never promoted")
        sha256 = digest(blob)
        stage = Path(tempfile.mkdtemp(prefix=".stage-" + name + "-", dir=root))
        filename = "database" + item["suffix"]
        # Hardlink within one filesystem: no second large copy and partial data
        # remains recoverable if interrupted before atomic directory promotion.
        os.link(blob, stage / filename)
        (stage / filename).chmod(0o644)
        (stage / "RESOURCE_LICENSE.txt").write_text(item["notice"])
        record = {
            "schema": 1, "id": name, "file": filename,
            "size": blob.stat().st_size, "sha256": sha256,
            "source_identity": item["source_identity"],
            "source": item["source"], "source_integrity": {
                "algorithm": item["algorithm"], "checksum": item["checksum"],
            },
            "license_sha256": digest(stage / "RESOURCE_LICENSE.txt"),
            "prepared_with": "sylph-db 1.0.0-r1",
            "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        (stage / "manifest.json").write_text(json.dumps(record, indent=2) + "\n")
        (stage / "READY").write_text(digest(stage / "manifest.json") + "\n")
        for path in stage.iterdir():
            path.chmod(0o644)
        stage.chmod(0o755)
        verify(stage, name)
        # GNU mv -T -n prevents replacing a directory created outside the lock.
        subprocess.run(["mv", "-T", "-n", "--", str(stage), str(destination)], check=True)
        if stage.exists():
            fail("destination appeared; refusing overwrite")
        stage = None
        blob.unlink()
        cache_identity.unlink()
        print(f"installed: {destination / filename}")
        return record
    finally:
        if stage is not None:
            # Only our exact staging directory, never a user-provided root.
            shutil.rmtree(stage)
        lock.rmdir()


def main():
    parser = argparse.ArgumentParser(
        description="Install one explicit immutable Sylph DB member; analysis never downloads.",
        epilog="Use a private/admin-controlled root (0755 or 0700). Downloads use a 0700 cache, "
        "resume with the same command, and never overwrite a completed member. "
        "No --force: damaged members must be quarantined by the administrator. "
        "Use actual backend binds for persistent installation and read-only reuse.",
    )
    parser.add_argument("--version", action="version", version="sylph-db 1.0.0-r1")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list", help="List the bundled fixed GTDB catalog without network access")
    for mode in ("install", "import", "fetch", "verify"):
        child = sub.add_parser(mode)
        child.add_argument("--id", required=True)
        child.add_argument("--db-root", required=True, type=Path)
        if mode != "verify":
            child.add_argument("--dry-run", action="store_true")
            if mode != "fetch":
                child.add_argument("--file", type=Path, required=(mode == "import"),
                                   help="Already acquired local member; no download")
        if mode in ("import", "fetch"):
            child.add_argument("--sha256", required=True)
            child.add_argument("--source", required=True)
            child.add_argument("--license-file", required=True, type=Path)
        if mode == "fetch":
            child.add_argument("--url", required=True, help="Public HTTPS URL; content fixed by SHA256")
            child.add_argument("--size", required=True, type=int)
            child.add_argument("--format", required=True, choices=("syldb", "syl2db"))
            child.add_argument("--rights-reviewed", action="store_true", required=True,
                               help="Confirm automatic acquisition and intended sharing are permitted")
    args = parser.parse_args()
    catalog = json.loads(CATALOG.read_text())
    if args.command == "list":
        print(json.dumps(catalog, indent=2))
        return
    name = identifier(args.id)
    if not args.db_root.is_absolute():
        fail("--db-root must be an absolute container-visible path")
    if args.command == "verify":
        safe_directory(args.db_root)
        print(json.dumps(verify(args.db_root / name, name), indent=2))
        return
    if args.command == "install":
        if name not in catalog["members"]:
            fail("unknown fixed catalog member; use list, or import an authorized custom database")
        item = dict(catalog["members"][name], id=name)
    else:
        if name in catalog["members"]:
            fail("fixed catalog IDs must use install (optionally --file)")
        if not re.fullmatch("[0-9a-f]{64}", args.sha256):
            fail("--sha256 must be a lowercase SHA256")
        regular(args.license_file)
        if args.command == "import":
            regular(args.file)
            if args.file.suffix not in (".syldb", ".syl2db"):
                fail("custom import accepts .syldb or .syl2db")
            size, suffix = args.file.stat().st_size, args.file.suffix
        else:
            parsed = urlsplit(args.url)
            if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.fragment:
                fail("fetch requires public HTTPS without embedded credentials or fragments")
            if args.size <= 0:
                fail("--size must be a positive exact byte count")
            size, suffix = args.size, "." + args.format
        notice = args.license_file.read_text()
        if not notice.strip() or len(notice) > 1024 * 1024:
            fail("resource license/permission notice must be nonempty and at most 1 MiB")
        if not args.source.strip() or "\n" in args.source:
            fail("provide a one-line stable source/provenance")
        item = {
            "id": name, "size": size,
            "suffix": suffix, "algorithm": "sha256", "checksum": args.sha256,
            "source": args.source, "notice": notice,
            "source_identity": json.dumps([args.source, args.sha256, size, suffix, hashlib.sha256(notice.encode()).hexdigest()]),
        }
        if item["size"] == 0:
            fail("empty custom database")
        if args.command == "fetch":
            item["url"] = args.url
            item["source_identity"] = json.dumps([item["source_identity"], args.url, size, suffix])
    local_file = getattr(args, "file", None)
    if args.dry_run:
        print(json.dumps(dict(item, destination=str(args.db_root / name),
                              reserve_bytes=RESERVE, network=local_file is None), indent=2))
        return
    install(args.db_root, item, local_file)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, KeyError, json.JSONDecodeError, subprocess.CalledProcessError) as error:
        print(f"sylph-db: stage=prepare-or-verify exit=1: {error}", file=sys.stderr)
        sys.exit(1)
