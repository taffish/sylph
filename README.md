# sylph

`sylph` packages the Sylph command-line program for TAFFISH: species-level
metagenomic profiling and coverage-adjusted containment ANI queries.

## Package Identity

- Name / command / kind: `sylph` / `taf-sylph` / `tool`
- TAFFISH version: `1.0.0-r1`
- Image: `ghcr.io/taffish/sylph:1.0.0-r1`
- Upstream: [Sylph](https://github.com/bluenote-1577/sylph), stable [v1.0.0](https://github.com/bluenote-1577/sylph/releases/tag/v1.0.0)
- Commit: `f2eafcdc1c4d9ab984a4fbee160a772686f02bd9`
- Packaging license: Apache-2.0; upstream: MIT OR Apache-2.0

The versioned source archive is fixed to SHA256
`dd4ba47906be7f3502b6bec88fa212ba5340b1eefced0192052ef0da82ca3a2d`.
Rust 1.89.0 builds it with `cargo build --locked --release`; the mutable
upstream `latest` binary is not used. This wrapper does not patch Sylph algorithms.

## Scope

The complete upstream executable provides `sketch`, `profile`, `query`,
`inspect` and the new `convert-db-two-screen` command. Version 1.0.0 adds
two-stage `.syl2db` databases, parallel read sketching and explicit
`-d/--databases` for profiling/querying. Existing `.syldb` and `.sylsp`
inputs remain usable.

No production database, trained model or taxonomy mapping is embedded.
The official companion [sylph-tax](https://sylph-docs.github.io/sylph-tax-quick-start/)
is a separate Python CLI/environment, not part of this package. Its Pavian-format
export targets an independent downstream visualization application; it is not
a local GUI launched by Sylph. Core source/CLI and companion entry-point review
found no GUI, GPU, browser service, device or port requirement in the packaged
interface. This is not a claim to package every downstream ecosystem tool.

## Container Contents

- `sylph`: unmodified upstream Rust executable.
- `sylph-db`: independent, explicit resource installation/import/verification
  helper; it never intercepts analysis commands.
- Python 3 standard library and curl/CA certificates for that helper; gzip,
  mawk, coreutils and the required Debian shared libraries.
- Source provenance, Cargo.lock, upstream documentation and licenses under
  `/opt/sylph/share/`; downloaded crate metadata and nested notices under
  `share/licenses/cargo/`, Debian notices under `/usr/share/doc/`.
- Tiny synthetic offline tests; no compiler, Cargo cache, reference collection
  or unpacked source build tree in the final image.

The notice inventory includes build dependencies fetched for the native build,
not every platform-specific entry in Cargo.lock. The fxhash crate's embedded
source notice is retained; fxhash and nalgebra-macros declare Apache-2.0
(the former offers MIT as an alternative), and the full Apache-2.0 text is also
retained under `share/licenses/packaging/`.

## Installation

After this release is published and indexed, run `taf update`, then
`taf install sylph 1.0.0-r1`. Use `taf-sylph-v1.0.0-r1` to pin a script to this
release; `taf-sylph` is the alias for the latest locally installed version.
An administrator may use `taf install --system sylph 1.0.0-r1` with appropriate
site authority. Installing a wrapper does not install a production database.

## Usage and Command Mode

Use the explicit executable name before a Sylph subcommand:

```sh
taf-sylph sylph sketch -g genomes/*.fna.gz -o reference -t 8
taf-sylph sylph profile -d reference.syldb -r reads.fastq.gz -t 8 -o profile.tsv
taf-sylph sylph profile -d reference.syldb -1 R1.fq.gz -2 R2.fq.gz -o paired.tsv
taf-sylph sylph sketch -1 R1.fq.gz -2 R2.fq.gz -d samples -t 8
taf-sylph sylph query reference.syldb samples/R1.fq.gz.paired.sylsp -o query.tsv
taf-sylph sylph inspect reference.syldb -o reference.yaml
taf-sylph sylph convert-db-two-screen reference.syldb -o reference-two -t 8
taf-sylph sylph profile -d reference-two.syl2db -r reads.fq.gz -o profile.tsv
taf-sylph sylph profile --help
taf-sylph sylph-db --help
```

TAFFISH automatic command mode can interpret a bare `profile` as an executable,
so `taf-sylph profile ...` is not the recommended form. `taf-sylph --help`
and `--version` describe the wrapper; `taf-sylph -- --help` and
`taf-sylph -- --version` reach the default upstream command.
`--compile` prints the generated command.

The current wrapper re-parses shell arguments. For paths containing spaces,
retain literal shell quotes inside the argument:

```sh
taf-sylph sylph inspect "'data/reference 1.syldb'" -o "'results/info 1.yaml'"
```

## Inputs and Outputs

| Input/output | Meaning | Boundary |
| --- | --- | --- |
| FASTA/FASTQ, optionally gzip | Reference genomes or reads | Caller prepares inputs; no implicit fetch |
| `.syldb` | Standard reference database | Reference identity and subsampling are scientific choices |
| `.syl2db` | Two-stage reference database | Requires Sylph >=1.0.0; not a universal replacement |
| `.sylsp` | Reusable sample sketch | Preserve generation options and input provenance |
| Profile TSV | ANI, coverage and abundance estimates | Genome identifiers, not full taxonomic lineages |
| Query TSV / inspect YAML | Containment statistics / sketch metadata | Not a clinical or per-read classification guarantee |

Upstream recommends two-stage databases primarily for larger genomes (roughly
over 200 kbp); preserve the standard database for collections where sparse
screening is unsuitable. Conversion writes another database and requires
additional space. `-o` may overwrite existing files: use fresh output names.
The `--estimate-read-counts` result is a rough estimate, not direct read assignment.

## Resources, Databases, and Platform

### Fixed member selection and resource rights

A database is a separately versioned, reusable member, not an implicit property
of the executable. The helper has a fixed 2026-09-14 catalogue with these
GTDB-derived standard sketches:

| Member ID | Bytes | Reference |
| --- | ---: | --- |
| `gtdb-r232-c1000-dbv1` | 5,219,051,219 | GTDB r232, c=1000 |
| `gtdb-r232-c200-dbv1` | 25,872,594,195 | GTDB r232, c=200 |
| `gtdb-r226-c1000-dbv1` | 3,713,953,632 | GTDB r226, c=1000 |
| `gtdb-r226-c200-dbv1` | 18,414,135,368 | GTDB r226, c=200 |

`sylph-db list` is offline and prints exact member inventory, source, pinned
GCS object generation, size, publisher MD5 and resource notice. A
generation-qualified HTTPS mirror of the official Sylph database is used
instead of the documentation's plain-HTTP route; redirects remain HTTPS.
A full-file SHA256 is computed and recorded after acquisition. Publisher MD5
detects transfer changes; it is not a signature or a claim of independent
cryptographic authenticity. No command defaults to downloading the entire family.

Review [official Sylph databases](https://sylph-docs.github.io/pre%E2%80%90built-databases/)
and [GTDB license terms](https://gtdb.ecogenomic.org/licenses) before selecting
a member. GTDB data is CC-BY-SA-4.0, separate from the program and packaging
licenses; retain attribution, source and applicable share-alike obligations.
The sketches are distributed by the Sylph database provider. This notice
does not confer rights to unrelated third-party collections.

Older mirror objects without a publisher MD5 are intentionally not automatic
catalogue entries. Other authorized databases remain usable directly, can use
the generic `fetch` interface with an independently established SHA256/size,
or may be imported locally with their own permission notice. This is not a
manual-only exemption for reusable resources: fetch and import use the same
shared-root, integrity, resume and atomic installation contract. Absence from
this helper's fixed download catalogue does not mean
Sylph cannot read a compatible database. The catalogue is explicit and fixed;
it does not dynamically claim to cover every database on the upstream website.

### Personal and administrator-once installation

Personal root: `~/.local/share/taffish/databases/sylph`.
Site root: `/usr/local/share/taffish/databases/sylph` or
`/opt/taffish/databases/sylph`. The administrator creates and owns a site
root once, with directories traversable by intended ordinary readers.
The helper requires an existing absolute, non-symlink root, owned by its
installer and not group/world-writable.

The short install/reuse commands for all three backends are in
[the installed help](docs/help.md). For personal installation, Docker's
rootful engine needs `--user $(id -u):$(id -g)`; rootless Podman needs
`--userns keep-id`. Rootful Podman instead needs the matching host UID/GID.
Apptainer normally preserves the invoking user's identity. For a root-owned
site, the site administrator runs the helper with the matching root identity;
ordinary users do not need sudo or another download.

For example, after an administrator has created the site directory, their
Docker invocation is:

```sh
DBROOT=/usr/local/share/taffish/databases/sylph
ID=gtdb-r232-c1000-dbv1
TAFFISH_CONTAINER_BACKEND=docker \
TAFFISH_DOCKER_RUN_ARGS="--user 0:0 -v $DBROOT:/db-install" \
taf-sylph sylph-db install --id "$ID" --db-root /db-install
```

This only prepares one explicit member. Begin with `--dry-run` to inspect
the plan; it performs no installation or download and does not prove space,
permissions or scientific suitability. Site configuration/privilege changes
remain the administrator's responsibility.

Each complete member contains exactly `database.syldb` (or `database.syl2db`),
`manifest.json`, `READY`, and `RESOURCE_LICENSE.txt`. Member directories
are 0755 and files 0644; the installer-controlled root and 0700 download cache
protect writes. Sites requiring restricted reader groups should restrict
traversal on the parent site root, not change the member's verified modes.

### Other fixed HTTPS resources, local import and recovery

For another publicly downloadable, shareable `.syldb` or `.syl2db`, use
`sylph-db fetch --id <new-id> --db-root /db-install --url <public-https-url>
--size <exact-bytes> --sha256 <verified-sha256> --format syldb
--source <fixed-provenance> --license-file /input/LICENSE --rights-reviewed`.
Supply the actual install/input binds as below and add `--dry-run` first.
The explicit rights acknowledgement covers automatic acquisition and intended
sharing; there is no credential/login bypass or assumption that software MIT
licenses authorize third-party data. The SHA256 fixes the content even when a
site lacks object generations. No resource is fetched merely because analysis
uses a path or the remote catalogue has changed.

A compatible locally prepared or authorized database may be imported without
network, using a writable `/db-install` bind and read-only `/input` bind:

```sh
taf-sylph sylph-db import --id custom-reference-v1 --db-root /db-install \
  --file /input/reference.syldb --sha256 <independently-verified-sha256> \
  --source <fixed-source-or-local-provenance> --license-file /input/LICENSE
taf-sylph sylph-db verify --id custom-reference-v1 --db-root /db
```

These commands require the actual binds described in help; setting a marker
does not mount storage. Import validates storage identity, not Sylph format
or scientific quality. Test a custom resource with `sylph inspect` and
appropriate domain checks separately. Use a new ID for a converted `.syl2db`;
never mutate the original published member.

Downloads retain a private partial file and source identity. Repeating the
same network installation resumes from that offset. Curl has bounded retry
and stall handling; failure reports the original transport status and a log
tail. The helper checks space (remaining data plus 64 MiB reserve), size and
checksum before staging, records full SHA256 and notice hashes, and atomically
promotes a verified directory without replacing a destination. No second
large promotion copy is required. Repeating a completed installation performs
full verification and is idempotent.

A damaged/partial member, changed identity, active/stale lock, symlink,
unexpected file or permission drift fails closed. There is no `--force`.
After confirming no installer is running, the administrator may quarantine
the exact damaged member/partial cache pair and retry, or use a new ID.
A process killed abruptly can leave a lock or staging directory; do not remove
another process's lock automatically. Full verification reads the entire
database and may take time for a 26 GB member.

### Backend usage and write map

| Capability | Docker | Podman | Apptainer |
| --- | --- | --- | --- |
| CPU analysis | Ordinary wrapper command | Ordinary wrapper command | Ordinary wrapper command on native Linux |
| Explicit install | Actual host bind to `/db-install`, matching UID | Same; keep-id for rootless | Actual writable `--bind` |
| Read-only reuse | `-v $DBROOT:/db:ro` | `-v $DBROOT:/db:ro` | `--bind $DBROOT:/db:ro` |
| GUI/GPU/service | N/A: none in packaged CLI | N/A: none in packaged CLI | N/A: none in packaged CLI |

Choose `TAFFISH_CONTAINER_BACKEND=docker|podman|apptainer` and the matching
site-policy runtime argument variable shown in help. Paths containing spaces
in runtime argument strings also need shell quoting around the bind argument.
Python bytecode writing is disabled in the image. Outputs go to explicit
user/workdir paths; helper transient files go to
unique `/tmp` space and its explicit installation root. Image `/opt`, `/usr`
and custom mount targets remain read-only without a real bind.
`/db-install` must never be assumed writable merely because it is named.

Automatic discovery/injection was evaluated and deliberately not enabled:
multiple database members may coexist, choice affects analysis, and no resource
should be silently selected or fully rehashed on every wrapper startup.
The explicit `--db-root` controls preparation; `sylph -d /db/<id>/database.syldb`
selects analysis input. Omit the optional bind to disable resource exposure.
Manual fallback is always the upstream command with a compatible explicit path.
Normal analysis and verification do not download.

Native platforms are Linux amd64 and arm64. Docker Desktop runs a Linux VM
on macOS; Apptainer requires Linux (including Linux arm64), not macOS itself.
Platform/backend validation status is recorded below rather than inferred
from a build or an emulation run.

## Troubleshooting

- Unknown `profile` executable: include `sylph` after `taf-sylph`.
- Root ownership error: use the installer UID appropriate to the engine and
  an actual writable host bind; do not chmod shared storage to 0777.
- Read-only filesystem: choose an output under the mounted workdir; install
  resources through their explicit write bind, not into the SIF image root.
- No profile rows: check compatible reference choice and input quality before
  changing scientific thresholds. Tiny packaging tests do not choose these.
- Large conversion/download: inspect the member size and reserve disk/RAM;
  preserve the old database and provenance. No production resource is bundled.

## Testing

The current smoke manifest has 17 executable probes and 8 exact commands.
Each command is independent and offline: source identity, stable interfaces,
single/paired/gzip sketches, lazy raw input, profile/query/inspect, two-stage
conversion equivalence on a tiny synthetic reference, parallel consistency,
truncated-input rejection and resource lifecycle/failure tests.
It uses locally generated synthetic random sequences, not upstream biological
fixtures. Build-time testing is limited to stable version/help/ldd and a tiny
CPU data path; no pager, terminal-width or rendering assertions are required.

The current candidate was built from the canonical Action's repository-root
context on native Linux arm64 (Docker Desktop VM) and native Linux amd64 (xjp).
Docker normal/read-only smoke passed on both architectures. Native amd64
Podman normal/read-only and an actual read-only Apptainer SIF made from the
same candidate OCI also passed: **175 exact commands and 168 real-wrapper
checks** across the two independent platform/backend evidence axes.

Resource tests include actual writable installation and read-only reuse binds,
19 administrator-once/ordinary-user permission checks plus 8 exact cleanup
checks, and real HTTPS connection interruption/Range resumption on all four
tested native/backend paths. Injected upstream failure preserves exit 37 and
its visible diagnostic tail; a fake mount marker does not enable installation.
No production site directory was altered. Python imports were also checked in
a writable container to confirm they do not create bytecode beneath /opt.

Docker, Podman and Apptainer are PASS for this release; no backend exception
is used. Arm64 Podman/Apptainer combinations were not separately validated.
No architecture-specific backend/device/GUI/mount coupling was identified, so
this does not imply or require the full platform-by-backend Cartesian matrix.

Final image sizes: amd64 128,496,891 bytes; arm64 152,665,218 bytes (uncompressed
engine inspection). The app occupies about 5 MiB; the remainder is mainly
Debian/Python/curl runtime. Build sources, compilers and Cargo cache remain in
the builder only; apt caches/lists and build scratch are removed. The native
builds retain notices for 120 amd64 / 119 arm64 downloaded crate directories,
including transitive C library notices. Final tests were rerun after the
notice, failure-log and bytecode changes.

Full production GTDB downloads and metagenomic scientific accuracy are not
validated by these small engineering fixtures. A synthetic transport/storage
test is not a successful production catalogue download.

## License and Citation

TAFFISH packaging: [Apache-2.0](LICENSE). Sylph retains MIT OR Apache-2.0;
source and dependency notices remain in the image as described above.
Resources retain their separate licenses and attribution requirements.

Cite Shaw and Yu, “Rapid species-level metagenome profiling and containment
estimation with sylph,” Nature Biotechnology 43, 1348–1359 (2025),
[doi:10.1038/s41587-024-02412-y](https://doi.org/10.1038/s41587-024-02412-y).
See the [official manual](https://sylph-docs.github.io/) for scientific use.
