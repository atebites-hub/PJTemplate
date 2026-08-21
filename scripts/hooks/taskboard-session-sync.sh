#!/usr/bin/env bash
exec bash "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/taskboard-sync.sh" session
