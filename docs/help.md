sylph 0.9.0-r1

Purpose:
  Fast species-level metagenomic profiling and coverage-adjusted containment
  ANI querying with genome-database and metagenome-sample sketches.

Usage:
  taf-sylph sylph sketch -g genomes/*.fna.gz -o reference -t 8
  taf-sylph sylph profile reference.syldb reads.fastq.gz -t 8 -o profile.tsv
  taf-sylph sylph query reference.syldb sample.sylsp -o query.tsv
  taf-sylph sylph inspect reference.syldb sample.sylsp -o sketches.yaml

Why the explicit sylph command:
  sketch, profile, query and inspect are subcommands, not executables. Use
  "taf-sylph sylph <subcommand> ..." so automatic command mode does not try
  to execute a program named profile or sketch.

Packaged command and subcommands:
  sylph sketch     Create .syldb genome and .sylsp sample sketches.
  sylph profile    Report species abundance, ANI and coverage statistics.
  sylph query      Query genome-to-sample containment ANI without abundances.
  sylph inspect    Emit YAML metadata for .syldb and .sylsp files.

Database requirements:
  No production database is embedded. Keep a pre-built or custom .syldb file
  in a persistent project/shared directory. Sylph accepts its path directly,
  so the app does not force a fixed database location.

  Pre-built database route:
    1. Open https://sylph-docs.github.io/pre%E2%80%90built-databases/
    2. Choose organism scope, catalogue release and -c parameter.
    3. Download the .syldb file into a persistent directory.
    4. Record its release, URL, size and checksum with the analysis.
    5. Keep it under the visible working directory or mount it read-only.

  Current upstream example at packaging time:
    mkdir -p sylph-db
    curl -fL http://faust.compbio.cs.cmu.edu/sylph-stuff/gtdb-r232-c1000-dbv1.syldb \
      -o sylph-db/gtdb-r232-c1000-dbv1.syldb

  Custom database:
    taf-sylph sylph sketch genomes/*.fna.gz -o custom-reference -t 8

Common workflows:
  Paired-end raw-read profiling:
    taf-sylph sylph profile database.syldb \
      -1 sample_R1.fastq.gz -2 sample_R2.fastq.gz -t 8 -o profile.tsv

  Reusable paired-end sample sketch:
    taf-sylph sylph sketch -1 sample_R1.fastq.gz -2 sample_R2.fastq.gz \
      -d sample-sketches -t 8

  Pre-sketched profiling:
    taf-sylph sylph profile database.syldb sample.sylsp -t 8 -o profile.tsv

Inputs and outputs:
  FASTA/FASTQ    Genome or read input; gzip is supported.
  .syldb         Reference genome database sketch.
  .sylsp         Metagenomic sample sketch.
  profile TSV    Abundance, adjusted ANI and coverage statistics.
  query TSV      Containment ANI and coverage without abundance columns.
  inspect YAML   Sketch metadata.

Platform and resources:
  Native linux/amd64 and linux/arm64 images are built from tagged source.
  CPU-only; -t controls threads. RAM/disk are dominated by database choice.
  Production databases range from hundreds of MB to tens of GB.

Boundaries:
  sylph-tax is a separate project and is not included. Use it when full
  taxonomic lineages are needed, with metadata matching the database release.
  --estimate-read-counts is a rough estimate, not direct read classification.
  Ordinary profiling is offline; database download is an explicit host step.
  Mount host paths outside the backend-visible working directory manually.

Detailed documentation:
  https://sylph-docs.github.io/
  https://sylph-docs.github.io/pre%E2%80%90built-databases/
  https://sylph-docs.github.io/sylph-cookbook/

Wrapper and upstream help:
  taf-sylph --help                 Show this TAFFISH help.
  taf-sylph --version              Show TAFFISH wrapper version.
  taf-sylph --compile              Compile the TAFFISH wrapper.
  taf-sylph -- --help              Show upstream top-level help.
  taf-sylph sylph profile --help   Show upstream profile help.
