![Python - Language](https://img.shields.io/badge/Language-python-green.svg)
![Python - Status](https://img.shields.io/pypi/status/pyi18t-tools)
![Python - Licence](https://img.shields.io/pypi/l/pyi18t-tools)
![Python - Supported Versions](https://img.shields.io/pypi/pyversions/pyi18t-tools)
![Read the Docs](https://img.shields.io/readthedocs/pyi18t-tools)
![Github - CI](https://github.com/biface/i18n/actions/workflows/python-ci.yaml/badge.svg?branch=master)
![Codecov](https://img.shields.io/codecov/c/github/biface/i18n)
![Github - Release](https://img.shields.io/github/v/release/biface/i18n)
![PyPI - Version](https://img.shields.io/pypi/v/pyi18t-tools)

--------------
# i18n-tools

**[Version française](README.fr.md)** (lecteur français et francophones)

---

## English reader and ROW

### Description

The **i18n-tools** project aims to simplify and modernize translation management in Python applications. It introduces a **new flexible translation file format**, independent of any dominant language, designed to coexist with existing standards such as **gettext** (`.po`/`.mo` files) and **i18next**.

The goal is to provide a **modular**, **adaptable**, and **language-agnostic** solution, with native support for **translation variants**, **multiple plurals**, and transparent language fallback management.

---

### Roadmap

The project follows a progression by deliverable value. Each version is independently usable.

| Milestone  | Description                                                                                   | Status      |
|------------|-----------------------------------------------------------------------------------------------|-------------|
| **v0.1.x** | Foundational cleanup — fix blocking bugs                                                      | ✅ Delivered |
| **v0.2.x** | Loaders ↔ models bridge — `Book.load()`, `.i18t` extension, partial `Config → Repository`     | ✅ Delivered |
| **v0.3.x** | Complete model hierarchy — `Corpus`, `FallbackBook`, `Encyclopaedia`, exceptions              | ✅ Delivered |
| **v0.4.x** | Quality and coverage — error handling, circular imports, Sphinx/Furo init                     | ✅ Delivered |
| **v0.5.0** | Architecture & layering hardening — models/loaders boundary sealed, `Config → Repository` completed | ✅ Delivered |
| **v0.6.0** | CI/CD & repository hygiene — `uv`/`tox-uv`, `basedpyright`, `.codecov.yml`                     | ✅ Delivered |
| **v0.7.0** | Test coverage & repository hygiene — `.codecov.yml` components, `coverage-gate`, issue/PR templates, Node.js 24 CI migration. No separate tag — merged into v0.8.0 (calendar reagencement) | ✅ Delivered |
| **v0.8.0** | Orchestration — `core.py` high-level entry point, `fallback.py` language chain resolution      | ✅ Delivered |
| **v0.9.0** | Formatting & CLI — `formatter.py` complete with `PluralRule`, CLI/REPL                         | ✅ Delivered |
| **v0.10.0**| Reviewing architecture & models — architectural review ahead of the v1.0.0 freeze             | 🔵 Planned  |
| **v0.11.0**| Comprehensive documentation — reference material across languages                             | 🔵 Planned  |
| **v1.0.0** | Freeze & verification — `.i18t` format frozen, public API frozen, full Sphinx docs published  | 🔵 Planned  |
| **v1.x**   | gettext interoperability — `.po`/`.mo` import/export via Babel                                | 🔵 Horizon  |
| **v2.x**   | Third-party formats — i18next and others, central conversion hub                              | 🔵 Horizon  |
| **v3.x**   | Complete CLI, stable API, Rust/JavaScript ports                                               | 🔵 Horizon  |

---

### Features

| Feature                                     | v0.2.x    | v0.8.0 | v0.9.0 | v1.0.0 | v1.x | v2.x |
|---------------------------------------------|-----------|--------|--------|--------|------|------|
| Native `.i18t` format (JSON/YAML)           | ✅         | ✅      | ✅      | ✅      | ✅    | ✅    |
| Language-neutral identifiers                | ✅         | ✅      | ✅      | ✅      | ✅    | ✅    |
| Variants and multiple plurals               | ✅         | ✅      | ✅      | ✅      | ✅    | ✅    |
| Load a `Book` from `.i18t`                  | ✅         | ✅      | ✅      | ✅      | ✅    | ✅    |
| Save a `Book` to `.i18t`                    | ✅        | ✅      | ✅      | ✅      | ✅    | ✅    |
| Complete hierarchy (Corpus, Encyclopaedia)  | ✅        | ✅      | ✅      | ✅      | ✅    | ✅    |
| Language fallback management                | ✅        | ✅      | ✅      | ✅      | ✅    | ✅    |
| High-level orchestration (`core.py`: load/save a Book or Corpus, synchronize a repository) | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Interpolation and active plural rules       | ❌         | ❌      | ✅      | ✅      | ✅    | ✅    |
| CLI/REPL interface                          | ❌         | ❌      | ✅      | ✅      | ✅    | ✅    |
| `.po`/`.mo` import/export (Babel/gettext)   | ❌         | ❌      | ❌      | ❌      | ✅    | ✅    |
| i18next conversion                          | ❌         | ❌      | ❌      | ❌      | ❌    | ✅    |

---

### Why This Project?

- **Flexibility**: a format designed to adapt to all translation needs, without linguistic constraints — no language is dominant.
- **Expressiveness**: native support for contextual variants (gender, register, context) and business plurals beyond CLDR rules.
- **Extensibility**: layered architecture enabling conversion to existing standards (gettext, i18next) without modifying the models.
- **Interoperability**: bridge with the Babel ecosystem for progressive compatibility with existing tools.

---

### License

See the [license.md](LICENSE.md) file.

---

### Contact

For any questions or contributions, open a [GitHub issue](https://github.com/biface/i18n/issues).
