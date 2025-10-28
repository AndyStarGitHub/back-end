#!/usr/bin/env bash
set -e

: "${LOG_DIR:=/app/logs}"
mkdir -p "$LOG_DIR"

exec "$@"
