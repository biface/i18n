#!/usr/bin/env bash
# ==============================================================================
# test.sh - Sequential multi-environment test execution
# ==============================================================================
#
# Runs test-core, then the unit tests of each version marked `local` in
# .tox-config/versions.txt, one after the other, and stops on the first
# failure. The coverage version (.tox-config/coverage-version.txt) is
# skipped: coverage.sh tests it while measuring coverage. A version also
# marked `experimental` is run, but its failure is reported as a warning
# and does not stop the run. versions.py reads and checks both files.
#
# Run through tox (`tox -e pre-push`): the nested runs use the tox installed
# in that environment (.tox-config/requirements/tox.txt), not whichever tox
# comes first on PATH.
#
# Usage:
#   ./.tox-config/scripts/test.sh
#
# Exit codes:
#   0: All tests passed
#   1: Configuration error, or at least one test environment failed
#
# ==============================================================================

set -euo pipefail

# Colours
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
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
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $*" >&2; }
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

# Prints the local versions to test, coverage version excluded, one per
# line; an experimental one is followed by " experimental".
read_versions() {
    "${VIRTUAL_ENV}/bin/python" "${VERSIONS_PY}" local
}

run_tests() {
    cd "${PROJECT_ROOT}" || return 1
    require_env || return 1

    local lines=()
    local listing
    listing="$(read_versions)" || { log_error "Invalid version files"; return 1; }
    if [[ -n "${listing}" ]]; then
        mapfile -t lines <<< "${listing}"
    fi
    log_info "Test versions: ${lines[*]:-none} (coverage version tested by coverage.sh)"

    log_section "Running test-core (no [api] extra installed)"
    run_tox -e test-core || { log_error "test-core failed"; return 1; }
    log_success "test-core passed"

    local total=${#lines[@]}
    local current=0
    local failed_experimental=()
    local line env marker
    for line in "${lines[@]}"; do
        current=$((current + 1))
        read -r env marker <<< "${line}"
        log_section "Running tests with ${env} ${marker:+(${marker}) }(${current}/${total})"
        if run_tox -e "${env}"; then
            log_success "Tests passed for ${env} (${current}/${total})"
        elif [[ "${marker}" == "experimental" ]]; then
            log_warning "Tests failed for experimental ${env} (${current}/${total}); not blocking"
            failed_experimental+=("${env}")
        else
            log_error "Tests failed for ${env} (${current}/${total})"
            return 1
        fi
    done

    if [[ ${#failed_experimental[@]} -gt 0 ]]; then
        log_warning "Experimental versions failed: ${failed_experimental[*]}"
    fi
    log_success "All required tests passed! (${total} run)"
}

main() {
    log_info "Starting sequential test execution"
    log_info "Working directory: ${PROJECT_ROOT}"
    if run_tests; then
        log_success "Completed successfully"
        exit 0
    fi
    log_error "Test execution failed"
    exit 1
}

main "$@"
