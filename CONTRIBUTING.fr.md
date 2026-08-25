# Contribuer à i18n-tools

**[English version](CONTRIBUTING.md)**

---

Merci de l'intérêt porté à i18n-tools. Ce document décrit la façon dont le
projet est développé aujourd'hui. Il reflète l'état *actuel* de l'outillage
et du processus — les templates d'issues/PR font partie du jalon v0.6.x (CI/
hygiène du dépôt) et ne sont pas encore totalement en place ; ce document
ne prétend pas le contraire.

## Politique linguistique

Le code, les commentaires, les docstrings, les commits, les issues et les
pull requests sont **exclusivement en anglais jusqu'à v1.0.0.** Ce n'est pas
une préférence stylistique — c'est une décision de projet, qui s'applique
indépendamment de la langue maternelle du contributeur. Les noms de
classes, méthodes, fonctions et modules restent en anglais de façon
permanente, même après la transition bilingue FR+EN prévue pour la
documentation narrative (post-v1.0.0) — voir
[l'issue #93](https://github.com/biface/i18n/issues/93) pour le
raisonnement complet.

`README.md`/`README.fr.md` (et ce fichier) sont l'exception : les documents
destinés aux utilisateurs sont maintenus en parallèle, un document complet
par langue, ni générés ni traduits automatiquement.

## Décisions de conception

Les changements d'architecture ou d'API ne sont pas implémentés avant
qu'une décision ait été actée. Les décisions sont suivies sous forme
d'issues GitHub étiquetées `type: decision` — si tu proposes un changement
touchant à l'architecture, à l'API publique, ou au format `.i18t`, ouvre
d'abord une telle issue pour que l'approche puisse être discutée avant
l'écriture du code. Le mainteneur a l'arbitrage final sur les décisions de
conception ; la discussion sur l'issue est bienvenue, mais une PR qui saute
cette étape pour un changement non trivial se verra probablement demander
de l'ajouter.

## Environnement de développement

Le projet utilise `uv` + `tox-uv` (pas `pip`/`virtualenv` classiques) :

```bash
uv sync --group dev               # tox, outils qualité, lanceurs de tests
uv sync --group dev --group docs  # + Sphinx/Furo pour la documentation
```

Toutes les vérifications passent par `tox` — voir la table `[tool.tox]`
de `pyproject.toml` pour la liste complète des environnements. En particulier :

```bash
uv run tox -e pre-push   # gate qualité + tests unitaires — à lancer avant de pousser
uv run tox -e local      # workflow complet : auto-fix, toutes les vérifications, couverture complète
uv run tox -e ci-quality # exactement ce que le job `quality` de la CI exécute
```

Chaque outil (`basedpyright`, `flake8`, `black`, `isort`, `bandit`) a son
propre environnement `tox` si tu veux n'en lancer qu'un seul.

## Tests

### Arborescence

```
tests/
├── 00_api/          — tests validate_api_url() / validate_url_format()
├── 00_locale/        — tests utilitaires de locale (normalisation IETF)
├── 01_loader/        — tests loaders/loader.py (initialise le Singleton Config)
├── 02_models/        — tests des modèles Message, Book, Corpus, Repository
├── 09_config/        — tests d'intégration Config / Repository (dépend du Singleton)
├── mock/              — fixtures de dépôt statiques (arbres package/ et application/)
├── locales/           — fixtures de fichiers de config autonomes (.json/.yaml/.toml)
├── conftest.py        — fixtures de niveau session, partagées entre toutes les suites
├── helpers.py         — copy_and_update_repository(), update_tmp_repository()
├── parametrize.yaml   — données de test centralisées, externalisées
└── test_04_sync.py    — tests de sync.py (échafaudage de répertoires/fichiers)
```

Chaque répertoire numéroté reflète une couche ou une préoccupation de
`src/i18n_tools/` et possède son propre `conftest.py` pour les fixtures
locales à la suite, héritant des fixtures de session du `tests/conftest.py`
racine.

### Ordre d'exécution — obligatoire

`Config` (dans `patterns.py`) est un **Singleton** : une seule instance
existe par processus pytest. Les préfixes numériques imposent un ordre
d'exécution sûr :

```
00_api, 00_locale   → aucune dépendance à Config, ordre libre
01_loader           → initialise le Singleton
02_models           → aucune dépendance à Config
09_config           → hérite de l'état du Singleton depuis 01_loader
```

**`09_config/` doit toujours s'exécuter après `01_loader/`.** Inverser cet
ordre provoque des échecs en cascade dans `09_config`, car le Singleton
n'aurait pas été initialisé comme ces tests l'attendent. Ne renomme pas les
répertoires d'une façon qui changerait leur ordre alphabétique/numérique
sans revérifier cette contrainte — également documenté en tête de
`tests/conftest.py`.

### `parametrize.yaml`

Les données de test sont externalisées plutôt que codées en dur. Sections
de premier niveau actuelles : `configuration` (chemins vers les arbres
mock source), `repository` (fragments de chemin injectés dans les fichiers
de config temporaires), `repository-content` (kwargs passés à
`Repository()`), `files` (noms de fichiers de config), `setup` (structure
langues/domaines/modules). Ajoute les nouveaux chemins/formes de fixture
ici plutôt que de coder en dur une chaîne de chemin dans un module de test.

### `helpers.py` et `mock/`

- `copy_and_update_repository(root_conf_test, tmp_path, conf_tests, key)` —
  copie un arbre de dépôt mock (`mock/package/...` ou `mock/application/...`)
  dans un `tmp_path` pytest, puis réécrit les entrées `paths.*` de son
  fichier de config pour pointer vers l'emplacement temporaire. C'est la
  façon standard d'obtenir une fixture de dépôt isolée sur disque sans
  toucher à l'arbre `mock/` réel.
- `mock/` contient deux arbres source, copiés (jamais mutés en place) : une
  fixture en contexte `package` et plusieurs fixtures en contexte
  `application`, suivant toutes deux la disposition réelle
  `locales/<langue>/LC_MESSAGES/<domaine>.i18t`.

### Markers

Déclarés dans `pyproject.toml` (`[tool.pytest.ini_options]`) :

- `@pytest.mark.network` — nécessite un accès réseau réel (`httpbingo.org`).
  Exécuté uniquement en CI sur tags/schedule (job `test-integration`).
- `@pytest.mark.timeout` — appels HTTP lents ; exclu partout en CI
  (`-m "not timeout"`), y compris dans le job `coverage` déclenché par tag.

### Couverture

Objectif : **80 %** sur tout le projet (jalon v0.7.x), suivi par module via
les composants Codecov (`models`, `loaders`, `exceptions`, `converter`,
`config`, `api` — voir `.codecov.yml`).

## Commits

Format [Conventional Commits](https://www.conventionalcommits.org/) :

```
<type>[scope optionnel]: <description>

[corps optionnel]

[footer(s) optionnel(s)]
```

Types utilisés dans ce dépôt : `feat`, `fix`, `chore`, `ci`, `docs`,
`refactor`, `test`, `perf`, `security`. Breaking changes : `!` après le type
ou footer `BREAKING CHANGE:`. Une unité logique par commit — ne grouper
plusieurs fichiers que s'ils forment un changement indivisible ; ne pas
mélanger des préoccupations distinctes dans un même commit.

## Pull requests

Les labels sont appliqués sur ce dépôt (8 catégories — `type:`, `status:`,
`priority:`, `scope:`, `effort:`, `ecosystem:`, `domain:`, `meta:`), mais
les templates d'issue/PR formels ne sont pas encore en place — ça fait
partie du jalon v0.6.x (CI/hygiène du dépôt). En attendant :

- Ouvre une issue d'abord pour tout ce qui dépasse une petite correction
  évidente, et applique le label `type:` pertinent.
- Référence l'issue liée dans la description de ta PR (`Closes #NN` /
  `Fixes #NN`) si elle existe.
- Vérifie que `uv run tox -e pre-push` passe en local avant d'ouvrir la PR —
  la CI exécute les mêmes vérifications (`quality` → matrice `test-unit`) et
  ne mergera pas une build rouge.
- Garde la PR centrée sur une seule préoccupation ; sépare les changements
  non liés dans des PR distinctes.

## Code de conduite

En participant à ce projet, tu acceptes de respecter le
[Code de conduite](CODE_OF_CONDUCT.fr.md).

## Questions

Ouvre une [issue GitHub](https://github.com/biface/i18n/issues).
