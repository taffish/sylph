sylph 1.0.0-r1

Purpose:
  Profile metagenomic reads or query containment ANI using explicit databases.

Usage:
  taf-sylph sylph sketch -g genomes/*.fna.gz -o reference -t 8
  taf-sylph sylph profile -d reference.syldb -r reads.fastq.gz -t 8 -o profile.tsv
  taf-sylph sylph query reference.syldb sample.sylsp -o query.tsv
  taf-sylph sylph inspect reference.syldb sample.sylsp -o sketches.yaml

Common tasks:
  taf-sylph sylph profile -d reference.syldb -1 R1.fq.gz -2 R2.fq.gz -o paired.tsv
  taf-sylph sylph sketch -1 R1.fq.gz -2 R2.fq.gz -d samples -t 8
  taf-sylph sylph convert-db-two-screen reference.syldb -o reference-two -t 8
  taf-sylph sylph profile -d reference-two.syl2db -r reads.fq.gz -o profile.tsv
  Two-stage databases require Sylph >=1.0.0. Keep .syldb for small genomes;
  do not assume .syl2db conversion is suitable for every reference collection.

Required inputs and key outputs:
  Genome FASTA / read FASTA or FASTQ; gzip supported.
  .syldb: standard reference sketch; .syl2db: two-stage reference sketch.
  .sylsp: reusable sample sketch; profile/query TSV: hits and ANI statistics.
  Profile TSV additionally contains abundance estimates; inspect emits YAML.
  No production database, taxonomy metadata or trained model is bundled.

Prepare a reusable database:
  Choose a fixed member explicitly; do not download every catalogue.
  taf-sylph sylph-db list
  DBROOT="$HOME/.local/share/taffish/databases/sylph"
  mkdir -p "$DBROOT"
  Member example (choose -c according to your study):
  ID=gtdb-r232-c1000-dbv1
  Each following command installs only $ID beneath the actual host bind.
  Add --dry-run first to inspect source, size, checksum and license.

  Docker:
    TAFFISH_CONTAINER_BACKEND=docker \
    TAFFISH_DOCKER_RUN_ARGS="--user $(id -u):$(id -g) -v $DBROOT:/db-install" \
    taf-sylph sylph-db install --id "$ID" --db-root /db-install
  Podman:
    TAFFISH_CONTAINER_BACKEND=podman \
    TAFFISH_PODMAN_RUN_ARGS="--userns keep-id -v $DBROOT:/db-install" \
    taf-sylph sylph-db install --id "$ID" --db-root /db-install
  Apptainer:
    TAFFISH_CONTAINER_BACKEND=apptainer \
    TAFFISH_APPTAINER_RUN_ARGS="--bind $DBROOT:/db-install" \
    taf-sylph sylph-db install --id "$ID" --db-root /db-install

Read-only reuse (set DBROOT and ID to the prepared member):
  Docker:
    TAFFISH_CONTAINER_BACKEND=docker \
    TAFFISH_DOCKER_RUN_ARGS="-v $DBROOT:/db:ro" \
    taf-sylph sylph profile -d "/db/$ID/database.syldb" -r reads.fq.gz -o result.tsv
  Podman:
    TAFFISH_CONTAINER_BACKEND=podman \
    TAFFISH_PODMAN_RUN_ARGS="-v $DBROOT:/db:ro" \
    taf-sylph sylph profile -d "/db/$ID/database.syldb" -r reads.fq.gz -o result.tsv
  Apptainer:
    TAFFISH_CONTAINER_BACKEND=apptainer \
    TAFFISH_APPTAINER_RUN_ARGS="--bind $DBROOT:/db:ro" \
    taf-sylph sylph profile -d "/db/$ID/database.syldb" -r reads.fq.gz -o result.tsv

Immediate notes:
  Admins may prepare /usr/local/share/taffish/databases/sylph once; ordinary
  users reuse it read-only. The installer must own its root. Keep parent paths
  traversable for intended readers; detailed UID/backend setup is in README.
  No automatic discovery or download during analysis: explicit bind + database
  path selects the resource; omit the bind to disable exposure.
  Only explicit install/fetch uses network. Re-run to resume; never remove an
  active install lock. Corrupt/partial members fail verification, not overwrite.
  CPU-only native linux/amd64 and linux/arm64; -t sets threads. Reserve space
  for the chosen database and new outputs; conversion creates another database.
  Use fresh output names: upstream -o can overwrite existing files.
  Custom DB: sylph-db import/fetch --help; sylph-tax is separate for taxonomy.
  Paths containing spaces need literal quotes inside the argument, e.g.
    taf-sylph sylph inspect "'data/reference 1.syldb'" -o "'results/info 1.yaml'"

More help:
  taf-sylph sylph profile --help
  taf-sylph sylph-db --help
  https://github.com/taffish/sylph
  https://sylph-docs.github.io/

Wrapper options:
  taf-sylph --help       Show this usage help.
  taf-sylph --version    Show the wrapper version.
  taf-sylph --compile    Print the generated shell.
  taf-sylph -- --help    Show upstream help; subcommands need explicit sylph.
