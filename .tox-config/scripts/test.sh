#!/usr/bin/env bash
# ==============================================================================
# test.sh - Sequential multi-environment test execution
# ==============================================================================
#
# Runs test-core, then the unit tests for each Python version listed in
# .tox-config/versions.txt, one after the other. Stops on the first failure.
#
# Run through tox (`tox -e pre-push`): the nested runs use the tox installed
# in that environment (.tox-config/requirements/tox.txt), not whichever tox
# comes first on PATH.
#
# Usage:
#   ./.tox-config/scripts/test.sh [versions_file]
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
readonly VERSIONS_FILE="${1:-${PROJECT_ROOT}/.tox-config/versions.txt}"

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

# Prints the versions listed in the versions file, one per line.
read_versions() {
    if [[ ! -f "${VERSIONS_FILE}" ]]; then
        log_error "File not found: ${VERSIONS_FILE}"
        return 1
    fi

    local line
    local count=0
    while IFS= read -r line || [[ -n "${line}" ]]; do
        line="${line#"${line%%[![:space:]]*}"}"
        line="${line%"${line##*[![:space:]]}"}"
        [[ -z "${line}" ]] && continue
        [[ "${line}" =~ ^# ]] && continue
        echo "${line}"
        count=$((count + 1))
    done < "${VERSIONS_FILE}"

    if [[ ${count} -eq 0 ]]; then
        log_error "No version listed in ${VERSIONS_FILE}"
        return 1
    fi
}

run_tests() {
    cd "${PROJECT_ROOT}" || return 1

    local versions=()
    local listing
    listing="$(read_versions)" || return 1
    mapfile -t versions <<< "${listing}"
    log_info "Test versions: ${versions[*]}"

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
