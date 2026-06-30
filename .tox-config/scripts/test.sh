#!/usr/bin/env bash
# ==============================================================================
# test.sh - Sequential multi-environment test execution
# ==============================================================================
#
# Reads .tox-config/versions.txt and runs unit tests for each Python version
# sequentially. Stops immediately on first failure.
#
# Usage:
#   ./.tox-config/scripts/test.sh [versions_file]
#
# Exit codes:
#   0: All tests passed
#   1: At least one test failed
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
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
readonly VERSIONS_FILE="${1:-${PROJECT_ROOT}/.tox-config/versions.txt}"

log_info()    { echo -e "${BLUE}[INFO]${NC} $*"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $*"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $*"; }
log_error()   { echo -e "${RED}[ERROR]${NC} $*" >&2; }
log_section() {
    echo ""
    echo -e "${BLUE}================================================================${NC}"
    echo -e "${BLUE}$*${NC}"
    echo -e "${BLUE}================================================================${NC}"
    echo ""
}

run_tests() {
    cd "${PROJECT_ROOT}"

    if [[ ! -f "${VERSIONS_FILE}" ]]; then
        log_warning "File not found: ${VERSIONS_FILE}"
        log_info "Using default versions: py310 py311 py312"
        for env in py310 py311 py312; do
            log_section "Running tests with ${env}"
            tox -e "${env}" || { log_error "Tests failed for ${env}"; return 1; }
            log_success "Tests passed for ${env}"
        done
        return 0
    fi

    log_info "Reading versions from: ${VERSIONS_FILE}"

    local versions=()
    while IFS= read -r line || [[ -n "${line}" ]]; do
        line="${line#"${line%%[![:space:]]*}"}"
        line="${line%"${line##*[![:space:]]}"}"
        [[ -z "${line}" ]] && continue
        [[ "${line}" =~ ^# ]] && continue
        versions+=("${line}")
    done < "${VERSIONS_FILE}"

    if [[ ${#versions[@]} -eq 0 ]]; then
        log_warning "No versions found — using defaults: py310 py311 py312"
        versions=(py310 py311 py312)
    fi

    log_info "Test versions: ${versions[*]}"

    local total=${#versions[@]}
    local current=0

    for env in "${versions[@]}"; do
        ((current++))
        log_section "Running tests with ${env} (${current}/${total})"
        tox -e "${env}" || { log_error "Tests failed for ${env} (${current}/${total})"; return 1; }
        log_success "Tests passed for ${env} (${current}/${total})"
    done

    echo ""
    log_success "All tests passed! (${total}/${total})"
}

main() {
    log_info "Starting sequential test execution"
    log_info "Working directory: ${PROJECT_ROOT}"
    run_tests && log_success "Completed successfully" && exit 0
    log_error "Test execution failed"
    exit 1
}

main "$@"
