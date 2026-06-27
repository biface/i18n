![Python](https://img.shields.io/badge/Language-python-green.svg)
![Codecov](https://img.shields.io/codecov/c/github/biface/i18n)

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
| **v0.1.x** | Stabilisation — fix blocking bugs (B-01 to B-05)                                              | ✅ Delivered |
| **v0.2.x** | Loaders ↔ models bridge — `Book.load()`, `.i18t` extension, partial `Config → Repository`     | ✅ Delivered |
| **v0.3.x** | Complete model hierarchy — `Corpus`, `FallbackBook`, `Encyclopaedia`, exceptions              | ✅ Delivered |
| **v0.4.x** | Quality and coverage — error handling, ≥ 80% coverage, Sphinx documentation                   | 🔵 In progress |
| **v0.5.x** | Architecture & layering hardening — DD-06 boundary, `Config → Repository` completion          | 🔵 Planned  |
| **v0.6.x** | CI/CD & repository hygiene — `uv`/`tox-uv`, `basedpyright`, `.codecov.yml`                     | 🔵 Planned  |
| **v0.7.x** | Test coverage — ≥ 80% enforced across the package                                             | 🔵 Planned  |
| **v1.0.0** | Full native i18n-tools — `core.py`, `fallback.py`, `formatter.py`, CLI, `.i18t` format frozen | 🔵 Planned  |
| **v1.x**   | gettext interoperability — `.po`/`.mo` import/export via Babel                                | 🔵 Horizon  |
| **v2.x**   | Third-party formats — i18next and others, central conversion hub                              | 🔵 Horizon  |
| **v3.x**   | Complete CLI, stable API, Rust/JavaScript ports                                               | 🔵 Horizon  |

---

### Features

| Feature                                     | v0.2.x    | v1.0.0 | v1.x | v2.x |
|---------------------------------------------|-----------|--------|------|------|
| Native `.i18t` format (JSON/YAML)           | ✅         | ✅      | ✅    | ✅    |
| Language-neutral identifiers                | ✅         | ✅      | ✅    | ✅    |
| Variants and multiple plurals               | ✅         | ✅      | ✅    | ✅    |
| Load a `Book` from `.i18t`                  | ✅         | ✅      | ✅    | ✅    |
| Save a `Book` to `.i18t`                    | ✅        | ✅      | ✅    | ✅    |
| Complete hierarchy (Corpus, Encyclopaedia)  | ✅        | ✅      | ✅    | ✅    |
| Language fallback management                | ✅        | ✅      | ✅    | ✅    |
| Interpolation and active plural rules       | ❌         | ✅      | ✅    | ✅    |
| CLI/REPL interface                          | ❌         | ✅      | ✅    | ✅    |
| `.po`/`.mo` import/export (Babel/gettext)   | ❌         | ❌      | ✅    | ✅    |
| i18next conversion                          | ❌         | ❌      | ❌    | ✅    |

---

### Why This Project?

- **Flexibility**: a format designed to adapt to all translation needs, without linguistic constraints — no language is dominant.
- **Expressiveness**: native support for contextual variants (gender, register, context) and business plurals beyond CLDR rules.
- **Extensibility**: layered architecture enabling conversion to existing standards (gettext, i18next) without modifying the models.
- **Interoperability**: bridge with the Babel ecosystem for progressive compatibility with existing tools.

---

### License

See the [license.md](license.md) file.

---

### Contact

For any questions or contributions, open a [GitHub issue](https://github.com/biface/i18n/issues).
