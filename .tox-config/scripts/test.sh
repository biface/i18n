#!/usr/bin/env bash
# ==============================================================================
# test.sh - Sequential multi-environment test execution
# ==============================================================================
#
# Runs test-core, then the unit tests of each version marked `local` in
# .tox-config/versions.txt, one after the other, and stops on the first
# failure. The coverage version (.tox-config/coverage-version.txt) is
# skipped: coverage.sh tests it while measuring coverage. versions.py reads
# and checks both files.
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

# Prints the local versions to test, coverage version excluded.
read_versions() {
    "${VIRTUAL_ENV}/bin/python" "${VERSIONS_PY}" local
}

run_tests() {
    cd "${PROJECT_ROOT}" || return 1
    require_env || return 1

    local versions=()
    local listing
    listing="$(read_versions)" || { log_error "Invalid version files"; return 1; }
    if [[ -n "${listing}" ]]; then
        mapfile -t versions <<< "${listing}"
    fi
    log_info "Test versions: ${versions[*]:-none} (coverage version tested by coverage.sh)"

    log_section "Running test-core (no [api] extra installed)"
    run_tox -e test-core || { log_error "test-core failed"; return 1; }
    log_success "test-core passed"

    local total=${#versions[@]}
    local current=0
    local env
    for env in "${versions[@]}"; do
        current=$((current + 1))
        log_section "Running tests with ${env} (${current}/${total})"
        run_tox -e "${env}" || { log_error "Tests failed for ${env} (${current}/${total})"; return 1; }
        log_success "Tests passed for ${env} (${current}/${total})"
    done

    log_success "All tests passed! (${total}/${total})"
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
