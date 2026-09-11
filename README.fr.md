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

**[English version](README.md)** (for English readers and ROW)

---

## Lecteur français et francophones

### Description

Le projet **i18n-tools** vise à simplifier et moderniser la gestion des traductions dans les applications Python. Il introduit un **nouveau format de fichiers de traduction** flexible, indépendant de toute langue dominante, et conçu pour coexister avec les standards existants comme **gettext** (fichiers `.po`/`.mo`) et **i18next**.

L'objectif est d'offrir une solution **modulaire**, **adaptable** et **sans contrainte linguistique**, avec un support natif pour les **variantes de traduction**, les **pluriels multiples**, et une gestion transparente des langues et des replis.

---

### Roadmap

Le projet suit une progression par valeur livrée. Chaque version est indépendamment utilisable.

| Jalon      | Description                                                                                     | État        |
|------------|-------------------------------------------------------------------------------------------------|-------------|
| **v0.1.x** | Nettoyage de base — corrections des bugs bloquants                                              | ✅ Livré     |
| **v0.2.x** | Pont loaders ↔ modèles — `Book.load()`, extension `.i18t`, pont `Config → Repository` (partiel) | ✅ Livré     |
| **v0.3.x** | Hiérarchie modèles complète — `Corpus`, `FallbackBook`, `Encyclopaedia`, exceptions             | ✅ Livré     |
| **v0.4.x** | Qualité et couverture — harmonisation des erreurs, imports circulaires, init Sphinx/Furo        | ✅ Livré     |
| **v0.5.0** | Renforcement architecture — frontière modèles/loaders scellée, `Config → Repository` finalisé | ✅ Livré     |
| **v0.6.0** | CI/CD et hygiène du dépôt — `uv`/`tox-uv`, `basedpyright`, `.codecov.yml`                        | ✅ Livré     |
| **v0.7.0** | Couverture de tests & hygiène du dépôt — composants `.codecov.yml`, `coverage-gate`, templates issues/PR, migration CI Node.js 24. Pas de tag séparé — fusionné dans v0.8.0 (réagencement calendaire) | ✅ Livré     |
| **v0.8.0** | Orchestration — point d'entrée `core.py`, résolution de repli `fallback.py`                      | ✅ Livré     |
| **v0.9.0** | Formatage & CLI — `formatter.py` complet avec `PluralRule`, CLI/REPL                             | ✅ Livré |
| **v0.10.0**| Revue d'architecture & des modèles — révision architecturale avant le gel v1.0.0                | 🔵 Planifié |
| **v0.11.0**| Documentation complète — matériel de référence multilingue                                      | 🔵 Planifié |
| **v1.0.0** | Gel & vérification — format `.i18t` gelé, API publique gelée, documentation Sphinx complète      | 🔵 Planifié |
| **v1.x**   | Interopérabilité gettext — import/export `.po`/`.mo` via Babel                                  | 🔵 Horizon  |
| **v2.x**   | Formats tiers — i18next et autres, hub de conversion central                                    | 🔵 Horizon  |
| **v3.x**   | CLI complet, API stable, ports Rust/JavaScript                                                  | 🔵 Horizon  |

---

### Fonctionnalités

| Fonctionnalité                              | v0.2.x    | v0.8.0 | v0.9.0 | v1.0.0 | v1.x | v2.x |
|---------------------------------------------|-----------|--------|--------|--------|------|------|
| Format `.i18t` natif (JSON/YAML)            | ✅         | ✅      | ✅      | ✅      | ✅    | ✅    |
| Identifiants indépendants de la langue      | ✅         | ✅      | ✅      | ✅      | ✅    | ✅    |
| Variantes et pluriels multiples             | ✅         | ✅      | ✅      | ✅      | ✅    | ✅    |
| Chargement d'un `Book` depuis `.i18t`       | ✅         | ✅      | ✅      | ✅      | ✅    | ✅    |
| Sauvegarde d'un `Book` vers `.i18t`         | ✅        | ✅      | ✅      | ✅      | ✅    | ✅    |
| Hiérarchie complète (Corpus, Encyclopaedia) | ✅        | ✅      | ✅      | ✅      | ✅    | ✅    |
| Gestion des replis linguistiques            | ✅        | ✅      | ✅      | ✅      | ✅    | ✅    |
| Orchestration de haut niveau (`core.py` : charger/sauvegarder un Book ou Corpus, synchroniser un dépôt) | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Interpolation et règles de pluriel actives  | ❌         | ❌      | ✅      | ✅      | ✅    | ✅    |
| Interface CLI/REPL                          | ❌         | ❌      | ✅      | ✅      | ✅    | ✅    |
| Import/export `.po`/`.mo` (Babel/gettext)   | ❌         | ❌      | ❌      | ❌      | ✅    | ✅    |
| Conversion vers i18next                     | ❌         | ❌      | ❌      | ❌      | ❌    | ✅    |

---

### Installation

```bash
pip install pyi18t-tools
```

Ceci installe tout le nécessaire pour charger, formater et sauvegarder
un fichier `.i18t` existant : `Message`, `Book`, `Corpus`,
`Encyclopaedia`, `formatter.publish()`, ainsi que la CLI
(`validate`/`info`/`sync`/`repl`) avec un fichier de réglages
`.yaml`/`.json`.

La gestion des auteurs et traducteurs (méthodes `Config`/`Repository`
dédiées, validation d'URL d'API traducteur, ou un fichier de réglages
`.toml`) nécessite en plus l'extra `api` :

```bash
pip install pyi18t-tools[api]
```

Appeler une de ces méthodes sans l'extra installé lève une erreur
`ModuleNotFoundError` explicite, nommant le paquet manquant et cette
commande d'installation, plutôt qu'un échec d'import brut (DD-41).

---

### Pourquoi ce projet ?

- **Flexibilité** : un format conçu pour s'adapter à tous les besoins de traduction, sans contrainte linguistique — aucune langue n'est dominante.
- **Expressivité** : support natif des variantes contextuelles (genre, registre, contexte) et des pluriels métier au-delà des règles CLDR.
- **Extensibilité** : architecture en couches permettant une conversion vers les standards existants (gettext, i18next) sans modifier les modèles.
- **Interopérabilité** : pont avec l'écosystème Babel pour une compatibilité progressive avec les outils existants.

---

### Licence

Voir le fichier [licence.md](LICENCE.md).

---

### Contact

Pour toute question ou contribution, ouvrez une [issue GitHub](https://github.com/biface/i18n/issues).
