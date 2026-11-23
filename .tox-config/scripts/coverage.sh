#!/usr/bin/env bash
# ==============================================================================
# coverage.sh - Coverage report generation
# ==============================================================================
#
# Runs the coverage environment on the version named in
# .tox-config/coverage-version.txt (checked by versions.py): that run is
# also the only test run of this version, test.sh skips it.
#
# Run through tox (`tox -e pre-push`): the nested run uses the tox installed
# in that environment (.tox-config/requirements/tox.txt), not whichever tox
# comes first on PATH.
#
# Usage:
#   ./.tox-config/scripts/coverage.sh
#
# Exit codes:
#   0: Report generated successfully
#   1: Configuration error, or report generation failed
#
# ==============================================================================

set -euo pipefail

# Colours
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly SCRIPT_DIR
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
readonly PROJECT_ROOT
readonly VERSIONS_PY="${SCRIPT_DIR}/versions.py"

# Logging goes to stderr: stdout stays free for values returned by functions.
log_info()    { echo -e "${BLUE}[INFO]${NC} $*" >&2; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $*" >&2; }
log_error()   { echo -e "${RED}[ERROR]${NC} $*" >&2; }
log_section() {
    {
        echo ""
        echo -e "${BLUE}================================================================${NC}"
        echo -e "${BLUE}$*${NC}"
        echo -e "${BLUE}================================================================${NC}"
        echo ""
    } >&2
}

# The tox and the Python of the environment this script runs in.
require_env() {
    if [[ -z "${VIRTUAL_ENV:-}" ]]; then
        log_error "No active environment: run this script through 'tox -e pre-push'"
        return 1
    fi
}

run_tox() {
    "${VIRTUAL_ENV}/bin/python" -m tox "$@"
}

generate_coverage() {
    cd "${PROJECT_ROOT}" || return 1
    require_env || return 1

    local coverage_python
    coverage_python="$("${VIRTUAL_ENV}/bin/python" "${VERSIONS_PY}" coverage-python)" \
        || { log_error "Invalid version files"; return 1; }

    log_section "Generating coverage report with ${coverage_python}"
    COVERAGE_PYTHON="${coverage_python}" run_tox -e coverage \
        || { log_error "Coverage generation failed"; return 1; }

    log_success "Coverage report generated successfully"
    log_info "Coverage reports:"
    if [[ -f "coverage/coverage.xml" ]]; then
        log_info "  - XML:  coverage/coverage.xml"
    fi
    if [[ -d "coverage/coverage_html" ]]; then
        log_info "  - HTML: coverage/coverage_html/index.html"
    fi
}

main() {
    log_info "Starting coverage report generation"
    log_info "Working directory: ${PROJECT_ROOT}"
    if generate_coverage; then
        log_success "Completed successfully"
        exit 0
    fi
    log_error "Coverage generation failed"
    exit 1
}

main "$@"
