FROM alpine:latest

RUN apk add --no-cache \
    bash \
    curl \
    git \
    ca-certificates \
    python3 \
    py3-pip

# Create a non-root user (VS Code prefers this)
ARG USERNAME=admin
RUN adduser -D -s /bin/bash ${USERNAME} \
    && echo "${USERNAME} ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers.d/${USERNAME} \
    && chmod 0440 /etc/sudoers.d/${USERNAME}

USER ${USERNAME}
WORKDIR /workspace

# Default shell when you open the terminal
CMD ["/bin/bash"]