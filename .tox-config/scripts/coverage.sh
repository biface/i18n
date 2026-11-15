#!/usr/bin/env bash
# ==============================================================================
# coverage.sh - Coverage report generation
# ==============================================================================
#
# Runs the coverage environment, whose interpreter is the single-version
# base Python set in pyproject.toml ([tool.tox.env_run_base] base_python).
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

# The tox of the environment this script runs in.
run_tox() {
    if [[ -z "${VIRTUAL_ENV:-}" ]]; then
        log_error "No active environment: run this script through 'tox -e pre-push'"
        return 1
    fi
    "${VIRTUAL_ENV}/bin/python" -m tox "$@"
}

generate_coverage() {
    cd "${PROJECT_ROOT}" || return 1

    log_section "Generating coverage report"
    run_tox -e coverage || { log_error "Coverage generation failed"; return 1; }

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
