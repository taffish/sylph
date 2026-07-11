FROM rust:1.89.0-slim-bookworm AS builder

ARG SYLPH_VERSION=0.9.0
ARG SYLPH_COMMIT=9e0e48c389fe0998b0c1c3fa0321eb93b8b36394
ARG SYLPH_SHA256=c11fbe5720500c43e7102a359dd9ec59b09b93a15a8ce6f6a3bb917430c3059e
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

FROM debian:12-slim

LABEL org.opencontainers.image.title="sylph" \
      org.opencontainers.image.description="TAFFISH wrapper for sylph metagenomic profiling and containment ANI queries" \
      org.opencontainers.image.source="https://github.com/bluenote-1577/sylph" \
      org.opencontainers.image.licenses="Apache-2.0"

ARG SYLPH_VERSION=0.9.0
ENV DEBIAN_FRONTEND=noninteractive \
    PATH=/opt/sylph/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

RUN set -eux; \
    apt-get -o Acquire::Retries=5 update; \
    apt-get -o Acquire::Retries=5 install -y --no-install-recommends \
        coreutils \
        gzip \
        grep \
        libc-bin \
        libgcc-s1 \
        mawk; \
    rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*

COPY --from=builder /opt/sylph /opt/sylph
COPY docker/sylph-smoke.sh /opt/sylph/share/testdata/sylph-smoke.sh

RUN set -eux; \
    chmod 0755 /opt/sylph/share/testdata/sylph-smoke.sh; \
    grep -F "source_sha256=c11fbe5720500c43e7102a359dd9ec59b09b93a15a8ce6f6a3bb917430c3059e" \
      /opt/sylph/share/doc/sylph/source.txt >/dev/null; \
    sylph --version 2>&1 | grep -Fx "sylph ${SYLPH_VERSION}" >/dev/null; \
    sylph --help 2>&1 | grep -F "Ultrafast genome ANI queries" >/dev/null; \
    sylph profile --help 2>&1 | grep -F -- "--estimate-read-counts" >/dev/null; \
    ldd "$(command -v sylph)" > /tmp/sylph-ldd.txt; \
    if grep -F "not found" /tmp/sylph-ldd.txt; then exit 1; fi; \
    /opt/sylph/share/testdata/sylph-smoke.sh \
      buildtime /tmp/taf-sylph-build-check; \
    rm -rf /tmp/sylph-ldd.txt

ENV TAFFISH_ENV=TAFFISH \
    TAFFISH_NAME=sylph \
    TAFFISH_VERSION=${SYLPH_VERSION} \
    TAFFISH_RELEASE=1

WORKDIR /work
