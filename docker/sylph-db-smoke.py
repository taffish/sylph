#!/usr/bin/python3
"""Offline synthetic storage-contract test, not production-database validation."""
import hashlib
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

loader = importlib.machinery.SourceFileLoader("sylph_db", "/opt/sylph/bin/sylph-db")
spec = importlib.util.spec_from_loader(loader.name, loader)
db = importlib.util.module_from_spec(spec)
loader.exec_module(db)
root = Path(sys.argv[1]) / "db"
root.mkdir(mode=0o755)
source = Path(sys.argv[1]) / "fixture.syldb"
# Arbitrary bytes test storage/integrity only; functional smoke creates real sketches.
source.write_bytes(b"synthetic storage-contract member\n" * 17)
checksum = db.digest(source)
item = dict(id="synthetic-v1", size=source.stat().st_size, suffix=".syldb",
            source="synthetic fixture", source_identity=checksum,
            notice="Synthetic test content, CC0-1.0.\n", algorithm="sha256",
            checksum=checksum, url="https://example.invalid/synthetic")
checks = 0


def check(condition):
    global checks
    assert condition
    checks += 1


def rejects(function):
    global checks
    try:
        function()
    except (ValueError, OSError):
        checks += 1
        return
    raise AssertionError("invalid state was accepted")


record = db.install(root, item, source)
check(record["sha256"] == checksum)
check(db.verify(root / item["id"], item["id"]) == record)
before = (root / item["id"] / "manifest.json").read_bytes()
db.install(root, item, source)
check((root / item["id"] / "manifest.json").read_bytes() == before)
check((root / item["id"]).stat().st_mode & 0o777 == 0o755)
check((root / ".downloads").stat().st_mode & 0o777 == 0o700)
rejects(lambda: db.install(root, dict(item, source_identity="changed"), source))
rejects(lambda: db.identifier("../escape"))
broken = root / "partial-v1"
broken.mkdir()
rejects(lambda: db.verify(broken, "partial-v1"))
link = root / "link-v1"
link.symlink_to(root / item["id"], target_is_directory=True)
rejects(lambda: db.verify(link, "link-v1"))
badsha = dict(item, id="badsha-v1", checksum="0" * 64)
rejects(lambda: db.install(root, badsha, source))
check(not (root / "badsha-v1").exists())
check((root / ".downloads/badsha-v1.part").exists())
lock = root / ".lock-locked-v1"
lock.mkdir()
rejects(lambda: db.install(root, dict(item, id="locked-v1"), source))
check(lock.exists())
lock.rmdir()
member = root / item["id"]
data = member / "database.syldb"
data.chmod(0o666)
rejects(lambda: db.verify(member, item["id"]))
data.chmod(0o644)
data.write_bytes(b"corruption")
rejects(lambda: db.verify(member, item["id"]))
data.write_bytes(source.read_bytes())
check(db.verify(member, item["id"]) == record)
(member / "unexpected").touch()
rejects(lambda: db.verify(member, item["id"]))
(member / "unexpected").unlink()
root.chmod(0o777)
rejects(lambda: db.install(root, dict(item, id="unsafe-root"), source))
root.chmod(0o755)
ready = member / "READY"
old_ready = ready.read_bytes()
ready.write_text("0" * 64 + "\n")
rejects(lambda: db.verify(member, item["id"]))
ready.write_bytes(old_ready)
rejects(lambda: db.verify(member, "different-id"))
# Simulate a transport interruption, then check cached-byte recovery through
# the same install function. This tests orchestration, not a production URL.
calls = []
def transport(argv):
    calls.append(argv)
    output = Path(argv[argv.index("--output") + 1])
    if len(calls) == 1:
        output.write_bytes(source.read_bytes()[:10])
        raise SystemExit(56)
    check(output.read_bytes() == source.read_bytes()[:10])
    with output.open("ab") as handle:
        handle.write(source.read_bytes()[10:])
db.run_download = transport
resumable = dict(item, id="resume-v1")
try:
    db.install(root, resumable)
except SystemExit as error:
    check(error.code == 56)
else:
    raise AssertionError("expected transport failure")
check(not (root / "resume-v1").exists())
check(not (root / ".lock-resume-v1").exists())
db.install(root, resumable)
check(db.verify(root / "resume-v1", "resume-v1")["sha256"] == checksum)
check(len(calls) == 2 and calls[1][calls[1].index("--continue-at") + 1] == "-")
check(calls[1][calls[1].index("--proto") + 1] == "=https")
check(calls[1][calls[1].index("--retry") + 1] == "3")
check(not (root / ".downloads/resume-v1.part").exists())
catalog = json.loads(db.CATALOG.read_text())
check(len(catalog["members"]) == 4)
for name, entry in catalog["members"].items():
    check("generation=" in entry["url"] and entry["algorithm"] == "md5" and entry["size"] > 0)
notice = Path(sys.argv[1]) / "LICENSE"
notice.write_text("Synthetic engineering fixture, CC0-1.0.\n")
fetch = ["sylph-db", "fetch", "--id", "custom-https-v1", "--db-root", str(root),
         "--sha256", checksum, "--source", "urn:taffish:synthetic", "--license-file", str(notice),
         "--url", "https://example.invalid/fixed.syldb", "--size", str(source.stat().st_size),
         "--format", "syldb", "--rights-reviewed", "--dry-run"]
plan = subprocess.run(fetch, check=True, capture_output=True, text=True)
check(json.loads(plan.stdout)["checksum"] == checksum)
check(not (root / "custom-https-v1").exists())
for flag, value in [("--url", "http://example.invalid/fixed.syldb"),
                    ("--url", "https://user:password@example.invalid/fixed.syldb"),
                    ("--size", "0"), ("--sha256", "bad")]:
    invalid = fetch.copy(); invalid[invalid.index(flag) + 1] = value
    result = subprocess.run(invalid, capture_output=True, text=True)
    check(result.returncode != 0 and "stage=prepare-or-verify" in result.stderr)
invalid = fetch.copy(); invalid.remove("--rights-reviewed")
check(subprocess.run(invalid, capture_output=True).returncode != 0)
print(f"sylph-db storage contract: {checks} PASS")
