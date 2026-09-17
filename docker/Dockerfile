FROM rust:1.89.0-slim-bookworm@sha256:d7fc7de78bb8c1469933aeecbf801314d30d7d6e9f0578bba4cfa285bfa37fe6 AS builder

ARG SYLPH_VERSION=1.0.0
ARG SYLPH_COMMIT=f2eafcdc1c4d9ab984a4fbee160a772686f02bd9
ARG SYLPH_SHA256=dd4ba47906be7f3502b6bec88fa212ba5340b1eefced0192052ef0da82ca3a2d
ENV DEBIAN_FRONTEND=noninteractive

RUN set -eux; \
    apt-get -o Acquire::Retries=5 update; \
    apt-get -o Acquire::Retries=5 install -y --no-install-recommends \
        ca-certificates \
        cmake \
        curl \
        g++ \
        gcc \
        make \
        pkg-config; \
    rm -rf /var/lib/apt/lists/*

WORKDIR /tmp/sylph-build

RUN set -eux; \
    curl --retry 5 --retry-delay 2 --retry-all-errors -fsSL \
      "https://github.com/bluenote-1577/sylph/archive/refs/tags/v${SYLPH_VERSION}.tar.gz" \
      -o sylph.tar.gz; \
    echo "${SYLPH_SHA256}  sylph.tar.gz" | sha256sum -c -; \
    mkdir src; \
    tar -xzf sylph.tar.gz -C src --strip-components=1; \
    cd src; \
    cargo build --locked --release; \
    strip target/release/sylph; \
    install -Dm0755 target/release/sylph /opt/sylph/bin/sylph; \
    install -Dm0644 LICENSE /opt/sylph/share/licenses/sylph/LICENSE; \
    install -Dm0644 README.md /opt/sylph/share/doc/sylph/README.md; \
    install -Dm0644 CHANGELOG.md /opt/sylph/share/doc/sylph/CHANGELOG.md; \
    install -Dm0644 Cargo.lock /opt/sylph/share/doc/sylph/Cargo.lock; \
    { \
      echo "sylph ${SYLPH_VERSION}"; \
      echo "source=https://github.com/bluenote-1577/sylph/archive/refs/tags/v${SYLPH_VERSION}.tar.gz"; \
      echo "source_sha256=${SYLPH_SHA256}"; \
      echo "upstream_tag=v${SYLPH_VERSION}"; \
      echo "upstream_commit=${SYLPH_COMMIT}"; \
      echo "build=official Rust source with locked Cargo dependencies"; \
      echo "rustc=$(rustc --version)"; \
      echo "cargo=$(cargo --version)"; \
      echo "upstream_license=MIT OR Apache-2.0; source archive includes MIT text"; \
    } > /opt/sylph/share/doc/sylph/source.txt

# Preserve notices from downloaded locked crates, including nested C libraries.
# This is an inventory of fetched build dependencies, not a claim that every
# target-specific entry in Cargo.lock is linked into both Linux executables.
RUN set -eu; \
    for crate in /usr/local/cargo/registry/src/*/*; do \
      destination="/opt/sylph/share/licenses/cargo/$(basename "$crate")"; \
      mkdir -p "$destination"; \
      cp "$crate/Cargo.toml" "$destination/Cargo.toml"; \
      (cd "$crate" && find . -type f \( -iname '*license*' -o -iname 'copying*' -o -iname 'notice*' -o -iname 'copyright*' \) \
        -exec cp --parents '{}' "$destination" \;); \
    done; \
    cp /usr/local/cargo/registry/src/*/fxhash-0.2.1/lib.rs /opt/sylph/share/licenses/cargo/fxhash-0.2.1/source-with-notice.rs

FROM debian:12-slim@sha256:88200866dfff7ea7f5cbcb6ec7c8a701889efe6fe859fe64d6990e4b07ea4171

LABEL org.opencontainers.image.title="sylph" \
      org.opencontainers.image.description="TAFFISH wrapper for sylph metagenomic profiling and containment ANI queries" \
      org.opencontainers.image.source="https://github.com/bluenote-1577/sylph" \
      org.opencontainers.image.licenses="Apache-2.0"

ARG SYLPH_VERSION=1.0.0
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH=/opt/sylph/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

RUN set -eux; \
    apt-get -o Acquire::Retries=5 update; \
    apt-get -o Acquire::Retries=5 install -y --no-install-recommends \
        coreutils \
        ca-certificates \
        curl \
        python3 \
        gzip \
        grep \
        libc-bin \
        libgcc-s1 \
        mawk; \
    rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*

COPY --from=builder /opt/sylph /opt/sylph
COPY docker/sylph-smoke.sh /opt/sylph/share/testdata/sylph-smoke.sh
COPY docker/sylph-db.py /opt/sylph/bin/sylph-db
COPY docker/sylph-db-catalog.json /opt/sylph/share/db/catalog.json
COPY docker/sylph-db-smoke.py /opt/sylph/share/testdata/sylph-db-smoke.py
COPY LICENSE /opt/sylph/share/licenses/packaging/LICENSE-APACHE-2.0

RUN set -eux; \
    chmod 0755 /opt/sylph/share/testdata/sylph-smoke.sh /opt/sylph/bin/sylph-db; \
    grep -F "source_sha256=dd4ba47906be7f3502b6bec88fa212ba5340b1eefced0192052ef0da82ca3a2d" \
      /opt/sylph/share/doc/sylph/source.txt >/dev/null; \
    sylph --version 2>&1 | grep -Fx "sylph ${SYLPH_VERSION}" >/dev/null; \
    sylph --help 2>&1 | grep -F "Ultrafast genome ANI queries" >/dev/null; \
    sylph profile --help 2>&1 | grep -F -- "--estimate-read-counts" >/dev/null; \
    ldd "$(command -v sylph)" > /tmp/sylph-ldd.txt; \
    if grep -F "not found" /tmp/sylph-ldd.txt; then exit 1; fi; \
    /opt/sylph/share/testdata/sylph-smoke.sh \
      buildtime /tmp/taf-sylph-build-check; \
    rm -f /tmp/sylph-ldd.txt; \
    rmdir /tmp/taf-sylph-build-check

ENV TAFFISH_ENV=TAFFISH \
    TAFFISH_NAME=sylph \
    TAFFISH_VERSION=${SYLPH_VERSION} \
    TAFFISH_RELEASE=1

WORKDIR /work
