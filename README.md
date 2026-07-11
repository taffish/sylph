# sylph

`sylph` packages the Sylph command-line program for TAFFISH. Sylph performs
species-level metagenomic profiling and coverage-adjusted containment ANI
queries with compact k-mer sketches.

## Package Identity

- Name: `sylph`
- Command: `taf-sylph`
- Kind: `tool`
- TAFFISH version: `0.9.0-r1`
- Container image: `ghcr.io/taffish/sylph:0.9.0-r1`
- Upstream: [`bluenote-1577/sylph`](https://github.com/bluenote-1577/sylph)
- Upstream release: `v0.9.0`
- Upstream commit: `9e0e48c389fe0998b0c1c3fa0321eb93b8b36394`
- TAFFISH app license: `Apache-2.0`
- Upstream license: `MIT OR Apache-2.0`

The image is built from the tagged source archive with locked Cargo
dependencies. Its SHA256 is:

```text
c11fbe5720500c43e7102a359dd9ec59b09b93a15a8ce6f6a3bb917430c3059e
```

## Scope

This app supports the complete Sylph `v0.9.0` command surface:

- `sketch` for genome databases, single-end reads and paired-end reads
- `profile` for species-level abundance and ANI profiling
- `query` for coverage-adjusted containment ANI searches
- `inspect` for `.syldb` and `.sylsp` metadata
- raw FASTA/FASTQ, gzip-compressed inputs and precomputed sketches
- custom databases and upstream pre-built databases
- the `v0.9.0` `--estimate-read-counts` profile option

This app does not bundle a production database, choose a reference catalogue,
or include the separate `sylph-tax` Python project. Sylph's native TSV output
identifies reference genomes. Use `sylph-tax` separately when a hierarchical
taxonomic profile is required.

## Container Contents

- `sylph`: the complete upstream Rust executable
- upstream README, changelog, lock file, license and source provenance
- an offline smoke script that creates deterministic synthetic test data

No compiler, Cargo cache, source tree or production `.syldb` file remains in
the final image.

## Command Mode

Because `profile`, `query`, `sketch` and `inspect` are Sylph subcommands rather
than separate executables, use the explicit packaged command form:

```sh
taf-sylph sylph profile ...
taf-sylph sylph sketch ...
```

Without the second `sylph`, TAFFISH automatic command mode may interpret a
subcommand name as another executable. Option-leading arguments for the
default command can also be passed after `--`:

```sh
taf-sylph -- --help
taf-sylph -- --version
```

## Database Boundary

Production Sylph databases are external scientific inputs. Current upstream
catalogues range from hundreds of megabytes to tens of gigabytes and change
independently of the executable, so embedding one would make the image large,
stale and scientifically ambiguous.

### Use A Pre-Built Database

1. Review the official [pre-built database page](https://sylph-docs.github.io/pre%E2%80%90built-databases/).
2. Choose the organism scope, catalogue release and subsampling parameter
   appropriate for the study.
3. Download the `.syldb` file into a persistent project or shared directory.
4. Record its release, URL, size and checksum with the analysis.
5. Keep the database visible to the selected container backend.

For a database stored under the current project directory:

```sh
mkdir -p sylph-db
curl -fL \
  http://faust.compbio.cs.cmu.edu/sylph-stuff/gtdb-r232-c1000-dbv1.syldb \
  -o sylph-db/gtdb-r232-c1000-dbv1.syldb

taf-sylph sylph profile \
  sylph-db/gtdb-r232-c1000-dbv1.syldb \
  -1 sample_R1.fastq.gz -2 sample_R2.fastq.gz \
  -t 8 -o sample.profile.tsv
```

The URL above is an upstream-hosted example current at packaging time. Always
consult the official database page before a production download. Databases
built with different `-c` values may require matching profile parameters; see
the upstream parameter guide.

For a shared database outside the working directory, mount it read-only with
the selected backend and use its container path. For example with Docker:

```sh
TAFFISH_CONTAINER_BACKEND=docker \
TAFFISH_DOCKER_RUN_ARGS="-v /absolute/path/sylph-db:/db:ro" \
taf-sylph sylph profile /db/database.syldb reads.fastq.gz -t 8 -o result.tsv
```

Sylph accepts database paths directly, so this app does not impose a fixed
database location or automatic download policy.

### Build A Custom Database

Sketch one or more genome FASTA files into a database:

```sh
taf-sylph sylph sketch \
  genomes/*.fna.gz \
  -o custom-reference \
  -t 8
```

This creates `custom-reference.syldb`. For one multi-record FASTA where each
record should be treated as a separate genome, add `--individual-records`.
For very large collections, use `--list-genomes genome-files.txt`.

## Usage

Show wrapper and upstream help:

```sh
taf-sylph --help
taf-sylph --version
taf-sylph -- --help
taf-sylph sylph profile --help
```

Sketch single-end reads and genomes explicitly:

```sh
mkdir -p sample-sketches
taf-sylph sylph sketch \
  -g genomes/*.fna.gz \
  -r sample.fastq.gz \
  -o reference \
  -d sample-sketches \
  -t 8
```

Sketch paired-end samples:

```sh
taf-sylph sylph sketch \
  -1 sample_R1.fastq.gz \
  -2 sample_R2.fastq.gz \
  -d sample-sketches \
  -t 8
```

Profile precomputed sketches:

```sh
taf-sylph sylph profile \
  reference.syldb sample-sketches/sample.fastq.gz.sylsp \
  -t 8 -o sample.profile.tsv
```

Query containment ANI without abundance reassignment:

```sh
taf-sylph sylph query \
  reference.syldb sample-sketches/sample.fastq.gz.sylsp \
  --minimum-ani 90 -t 8 -o sample.query.tsv
```

Inspect sketches:

```sh
taf-sylph sylph inspect \
  reference.syldb sample-sketches/sample.fastq.gz.sylsp \
  -o sketches.yaml
```

Sylph can lazily sketch raw input during `profile` or `query`, but explicit
sketching is preferable for reusable databases, repeated analyses and clearer
provenance.

## Inputs And Outputs

| Item | Meaning |
| --- | --- |
| Genome FASTA | One or more reference genomes; gzip is supported |
| Read FASTA/FASTQ | Single-end or long-read sample input; gzip is supported |
| Paired FASTQ | Matching `-1` and `-2` sample lists |
| `.syldb` | A database sketch containing one or more reference genomes |
| `.sylsp` | A metagenomic sample sketch |
| Profile TSV | Genome hits, taxonomic/sequence abundance, adjusted ANI and coverage statistics |
| Query TSV | Genome-to-sample containment ANI and coverage statistics without profile abundance columns |
| Inspect YAML | Sketch metadata emitted by `inspect` |

Output redirects and `-o/--output-file` are both supported. Profile and query
TSV headers should be retained with the result because fields can evolve
between upstream versions.

## Resources And Platform

Native images are built from source for `linux/amd64` and `linux/arm64`.
Sylph is CPU-only; `-t` controls threads. No GPU, service, MPI runtime or
network is required for normal sketching and profiling.

RAM and disk use are dominated by the selected database, sample count and
subsampling parameter. Upstream offers `-c 200` databases for greater
sensitivity and larger files and `-c 1000` variants for smaller, more
efficient profiling. Consult the official database and method documentation
before fixing production resource requests.

## Boundaries And Troubleshooting

- The reference catalogue and its version are part of the scientific method;
  record them alongside the Sylph version and command line.
- `profile` is generally preferred for community abundance analysis; `query`
  answers a different containment ANI question and omits abundance fields.
- Sylph's TSV does not itself provide full taxonomic lineages. Use the separate
  `sylph-tax` project with metadata matching the exact database release.
- The `--estimate-read-counts` option is explicitly described upstream as a
  rough estimate and forces unknown-read estimation; do not treat it as direct
  read classification.
- Raw single-end FASTA reads require explicit `sketch -r`; lazy profiling of
  raw reads is intended for FASTQ.
- If a host path is outside the backend-visible working directory, mount it
  explicitly before passing the corresponding container path.

## Testing

The independent offline smoke suite checks:

- exact source provenance, executable version and all four command interfaces
- the `v0.9.0` `--estimate-read-counts` option
- genome, single-end and paired-end sketch generation
- gzip-compressed genome and metagenomic read inputs
- lazy raw-input profiling and direct paired-end raw-read profiling
- `.syldb` and `.sylsp` serialization plus YAML inspection
- real profile and query TSV rows from deterministic matching DNA fixtures
- dynamic-library completeness

The generated deterministic fixtures validate packaging behavior only. Smoke
does not test a production database or establish scientific accuracy for user
data.

Upstream's Rust integration suite passes on `linux/amd64` (11 tests). Its
`unit_test.rs` imports x86_64/AVX2 APIs without an architecture guard, so the
upstream test target itself does not compile on arm64. Native `linux/arm64` is
instead validated by the same locked source build, dynamic-link inspection and
the complete architecture-neutral runtime smoke suite listed above. No
upstream source is patched to conceal that test-only limitation.

## License And Citation

TAFFISH packaging files are licensed under Apache-2.0. Upstream Cargo metadata
declares `MIT OR Apache-2.0`; the tagged source archive's MIT license text is
retained in the image.

Cite:

> Shaw J, Yu YW. Rapid species-level metagenome profiling and containment
> estimation with sylph. Nature Biotechnology. 2025;43:1348-1359.
> https://doi.org/10.1038/s41587-024-02412-y

Also record the source and release of every reference database used.

## Upstream Resources

- [Official documentation](https://sylph-docs.github.io/)
- [Install and quick start](https://sylph-docs.github.io/install%2Bquickstart/)
- [Pre-built databases](https://sylph-docs.github.io/pre%E2%80%90built-databases/)
- [Cookbook](https://sylph-docs.github.io/sylph-cookbook/)
- [Output format](https://sylph-docs.github.io/Output-format/)
- [Official `v0.9.0` release](https://github.com/bluenote-1577/sylph/releases/tag/v0.9.0)
