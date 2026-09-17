#!/bin/sh
set -eu

mode="${1:-interfaces}"
base="${2:-/tmp}"
mkdir -p "$base"
tmp=$(mktemp -d "${base%/}/taf-sylph.XXXXXX")
trap 'rm -rf "$tmp"' EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

make_fixture() {
    out="$1"
    awk -v out="$out" '
      BEGIN {
        genome = out "/genome.fa"
        reads = out "/reads.fq"
        first = out "/reads_R1.fq"
        second = out "/reads_R2.fq"
        srand(1577)
        bases = "ACGT"
        genome_length = 100000
        read_length = 150
        for (i = 1; i <= genome_length; i++) {
          sequence = sequence substr(bases, 1 + int(rand() * 4), 1)
        }
        print ">synthetic_reference" > genome
        print sequence >> genome
        quality = ""
        for (i = 1; i <= read_length; i++) quality = quality "I"
        for (r = 1; r <= 2000; r++) {
          start = 1 + int(rand() * (genome_length - read_length - 500))
          read = substr(sequence, start, read_length)
          print "@single_" r > reads
          print read >> reads
          print "+" >> reads
          print quality >> reads
          if (r <= 500) {
            mate = substr(sequence, start + 300, read_length)
            print "@pair_" r "/1" > first
            print read >> first
            print "+" >> first
            print quality >> first
            print "@pair_" r "/2" > second
            print mate >> second
            print "+" >> second
            print quality >> second
          }
        }
      }
    '
    gzip -f "$out/genome.fa" "$out/reads.fq"
}

interfaces() {
    sylph --version > "$tmp/version.txt" 2>&1
    grep -Fx "sylph 1.0.0" "$tmp/version.txt" >/dev/null

    sylph --help > "$tmp/help.txt" 2>&1
    grep -F "Ultrafast genome ANI queries" "$tmp/help.txt" >/dev/null
    grep -F "sketch" "$tmp/help.txt" >/dev/null
    grep -F "profile" "$tmp/help.txt" >/dev/null
    grep -F "query" "$tmp/help.txt" >/dev/null
    grep -F "inspect" "$tmp/help.txt" >/dev/null

    sylph sketch --help > "$tmp/sketch-help.txt" 2>&1
    grep -F -- "--first-pairs" "$tmp/sketch-help.txt" >/dev/null
    grep -F -- "--individual-records" "$tmp/sketch-help.txt" >/dev/null

    sylph profile --help > "$tmp/profile-help.txt" 2>&1
    grep -F -- "--estimate-read-counts" "$tmp/profile-help.txt" >/dev/null
    grep -F -- "--estimate-unknown" "$tmp/profile-help.txt" >/dev/null

    sylph convert-db-two-screen --help > "$tmp/convert-help.txt" 2>&1
    grep -F -- "--screen-c" "$tmp/convert-help.txt" >/dev/null
    grep -F -- "--databases" "$tmp/profile-help.txt" >/dev/null

    sylph query --help > "$tmp/query-help.txt" 2>&1
    grep -F -- "--minimum-ani" "$tmp/query-help.txt" >/dev/null

    sylph inspect --help > "$tmp/inspect-help.txt" 2>&1
    grep -F ".syldb" "$tmp/inspect-help.txt" >/dev/null
}

buildtime() {
    mkdir -p "$tmp/samples"
    make_fixture "$tmp"

    sylph sketch \
      -g "$tmp/genome.fa.gz" \
      -r "$tmp/reads.fq.gz" \
      -o "$tmp/tiny-db" \
      -d "$tmp/samples" \
      -t 1
    test -s "$tmp/tiny-db.syldb"
    test -s "$tmp/samples/reads.fq.gz.sylsp"

    sylph inspect "$tmp/tiny-db.syldb" "$tmp/samples/reads.fq.gz.sylsp" \
      -o "$tmp/inspect.yaml"
    test -s "$tmp/inspect.yaml"

    sylph profile \
      "$tmp/tiny-db.syldb" "$tmp/samples/reads.fq.gz.sylsp" \
      -t 1 \
      -o "$tmp/profile.tsv"
    head -n 1 "$tmp/profile.tsv" | grep -F "Sample_file" >/dev/null
    head -n 1 "$tmp/profile.tsv" | grep -F "Genome_file" >/dev/null
    grep -F "synthetic_reference" "$tmp/profile.tsv" >/dev/null

}

profile() {
    mkdir -p "$tmp/sketches"
    make_fixture "$tmp"

    sylph sketch \
      -g "$tmp/genome.fa.gz" \
      -r "$tmp/reads.fq.gz" \
      -o "$tmp/reference" \
      -d "$tmp/sketches" \
      -t 1
    test -s "$tmp/reference.syldb"
    test -s "$tmp/sketches/reads.fq.gz.sylsp"

    sylph profile \
      "$tmp/reference.syldb" "$tmp/sketches/reads.fq.gz.sylsp" \
      -t 1 -o "$tmp/profile.tsv"
    head -n 1 "$tmp/profile.tsv" | grep -F "Taxonomic_abundance" >/dev/null
    grep -F "synthetic_reference" "$tmp/profile.tsv" >/dev/null
    grep -F "reads.fq.gz" "$tmp/profile.tsv" >/dev/null

    sylph profile \
      "$tmp/genome.fa.gz" "$tmp/reads.fq.gz" \
      -t 1 -o "$tmp/lazy-profile.tsv"
    head -n 1 "$tmp/lazy-profile.tsv" | grep -F "Taxonomic_abundance" >/dev/null
    grep -F "synthetic_reference" "$tmp/lazy-profile.tsv" >/dev/null

    sylph query \
      "$tmp/reference.syldb" "$tmp/sketches/reads.fq.gz.sylsp" \
      -t 1 -o "$tmp/query.tsv"
    head -n 1 "$tmp/query.tsv" | grep -F "Adjusted_ANI" >/dev/null
    grep -F "synthetic_reference" "$tmp/query.tsv" >/dev/null

    sylph inspect "$tmp/reference.syldb" "$tmp/sketches/reads.fq.gz.sylsp" \
      -o "$tmp/inspect.yaml"
    test -s "$tmp/inspect.yaml"
    grep -F "genome.fa.gz" "$tmp/inspect.yaml" >/dev/null
}

paired() {
    mkdir -p "$tmp/paired"
    make_fixture "$tmp"

    sylph sketch \
      -1 "$tmp/reads_R1.fq" \
      -2 "$tmp/reads_R2.fq" \
      -d "$tmp/paired" \
      -t 1
    test -s "$tmp/paired/reads_R1.fq.paired.sylsp"
    sylph inspect "$tmp/paired/reads_R1.fq.paired.sylsp" -o "$tmp/paired.yaml"
    test -s "$tmp/paired.yaml"

    sylph profile \
      "$tmp/genome.fa.gz" \
      -1 "$tmp/reads_R1.fq" \
      -2 "$tmp/reads_R2.fq" \
      -t 1 -o "$tmp/paired-profile.tsv"
    head -n 1 "$tmp/paired-profile.tsv" | grep -F "Taxonomic_abundance" >/dev/null
    grep -F "synthetic_reference" "$tmp/paired-profile.tsv" >/dev/null
}

two_stage() {
    make_fixture "$tmp"
    sylph sketch -g "$tmp/genome.fa.gz" -o "$tmp/reference" -t 1
    sylph convert-db-two-screen "$tmp/reference.syldb" -o "$tmp/two" -t 1
    test -s "$tmp/two.syl2db"
    sylph inspect "$tmp/two.syl2db" -o "$tmp/two.yaml"
    grep -F "genome.fa.gz" "$tmp/two.yaml" >/dev/null
    sylph profile -d "$tmp/two.syl2db" -r "$tmp/reads.fq.gz" -t 2 -o "$tmp/two.tsv"
    sylph profile -d "$tmp/reference.syldb" -r "$tmp/reads.fq.gz" -t 2 -o "$tmp/one.tsv"
    grep -F "synthetic_reference" "$tmp/two.tsv" >/dev/null
    # Same synthetic reference/sample: stable scientific fields must agree.
    cmp "$tmp/one.tsv" "$tmp/two.tsv"
    sylph query -d "$tmp/two.syl2db" -r "$tmp/reads.fq.gz" -t 2 -o "$tmp/query.tsv"
    grep -F "synthetic_reference" "$tmp/query.tsv" >/dev/null
    head -c 20 "$tmp/two.syl2db" > "$tmp/truncated.syl2db"
    if sylph inspect "$tmp/truncated.syl2db" -o "$tmp/invalid.yaml"; then
        echo "truncated database unexpectedly accepted" >&2
        exit 1
    fi
}

parallel() {
    make_fixture "$tmp"
    sylph sketch -g "$tmp/genome.fa.gz" -o "$tmp/db" -t 1
    for n in 1 4; do
        mkdir "$tmp/t$n"
        sylph sketch -r "$tmp/reads.fq.gz" -d "$tmp/t$n" -t "$n"
        sylph profile "$tmp/db.syldb" "$tmp/t$n/reads.fq.gz.sylsp" -t "$n" -o "$tmp/p$n.tsv"
        # Sample_file contains different sketch directories; compare all other fields.
        cut -f 2- "$tmp/p$n.tsv" > "$tmp/c$n.tsv"
    done
    cmp "$tmp/c1.tsv" "$tmp/c4.tsv"
    grep -F "synthetic_reference" "$tmp/c1.tsv" >/dev/null
}

resources() {
    python3 /opt/sylph/share/testdata/sylph-db-smoke.py "$tmp"
}

set +e
(
    set -e
    case "$mode" in
        interfaces) interfaces ;;
        buildtime) buildtime ;;
        profile) profile ;;
        paired) paired ;;
        two-stage) two_stage ;;
        parallel) parallel ;;
        resources) resources ;;
        *) echo "unknown smoke mode: $mode" >&2; exit 2 ;;
    esac
) > "$tmp/stage.log" 2>&1
status=$?
set -e
if [ "$status" -ne 0 ]; then
    printf 'sylph smoke: stage=%s exit=%s\n' "$mode" "$status" >&2
    {
        tail -n 160 "$tmp/stage.log"
        # Interface commands capture output for stable assertions; if one fails,
        # replay those captures too instead of hiding the upstream diagnostic.
        for capture in "$tmp"/*.txt; do
            [ -f "$capture" ] || continue
            printf '\n--- captured %s ---\n' "${capture##*/}"
            tail -n 40 "$capture"
        done
    } | tail -n 200 >&2
    exit "$status"
fi
printf 'sylph smoke: stage=%s PASS\n' "$mode"
