FROM python:3.12.12-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    ca-certificates \
    build-essential \
    procps \
    iproute2 \
    iputils-ping \
    tini \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspaces/app

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["sleep", "infinity"]