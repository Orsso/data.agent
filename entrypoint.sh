#!/bin/sh
set -e

# Auto-detect Docker socket GID and grant access to the app user.
# This removes the need for a manual DOCKER_GID env var — works on
# Linux, macOS Docker Desktop, and Windows Docker Desktop.
if [ -S /var/run/docker.sock ]; then
    SOCK_GID=$(stat -c '%g' /var/run/docker.sock)
    # Resolve GID to an existing group name, or create one
    GROUP_NAME=$(getent group "$SOCK_GID" | cut -d: -f1)
    if [ -z "$GROUP_NAME" ]; then
        GROUP_NAME=dockersock
        groupadd -g "$SOCK_GID" "$GROUP_NAME"
    fi
    usermod -aG "$GROUP_NAME" app
fi

gosu app alembic upgrade head

exec gosu app "$@"
