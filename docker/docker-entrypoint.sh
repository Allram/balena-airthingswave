#!/bin/bash
#
# Docker entrypoint script
#
# This file will be copied to /usr/local/bin/.
#

# Optimize shell for safety.
set -o errexit -o noclobber -o nounset -o pipefail

# Pass through the CMD directive
exec "$@"
