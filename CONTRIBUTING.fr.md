# Contribuer à i18n-tools

**[English version](CONTRIBUTING.md)**

---

Merci de l'intérêt porté à i18n-tools. Ce document décrit la façon dont le
projet est développé aujourd'hui.

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

Chaque catégorie de décision a son propre formulaire d'issue :
architecture (`DA-NNN`), conception (`DD-NNN`), technique (`DT-NNN`) et
qualité (`DQ-NNN`). Les quatre préfixes partagent un seul compteur à
trois chiffres : vérifie dans les issues de décision existantes le
prochain numéro libre avant de choisir un titre comme
`[DD-041] Titre`. Le formulaire applique `type: decision` et
`status: triage` ; ajoute les labels `scope:`, `priority:`, `effort:` et
`ecosystem:` qui correspondent à tes réponses.

## Environnement de développement

Le projet utilise `uv` + `tox-uv` (pas `pip`/`virtualenv` classiques).
L'environnement du projet ne contient que le paquet et ses dépendances
d'exécution :

```bash
uv sync --extra api      # le paquet, avec l'extra [api]
```

Les outils de développement (tox, outils qualité, lanceurs de tests,
Sphinx) n'y sont pas installés : tox les installe dans ses propres
environnements, à partir de `.tox-config/requirements/*.txt`, où leurs
versions sont épinglées. Les `[dependency-groups]` de `pyproject.toml` ne
font que les nommer. tox lui-même se lance avec `uvx` :

```bash
uvx --with tox-uv tox -e local      # applique black et isort, puis toutes les vérifications et la couverture complète
uvx --with tox-uv tox -e pre-push   # dernière étape avant de pousser : vérifie seulement, s'arrête au premier écart
uvx --with tox-uv tox -e ci-quality # exactement ce que le job `quality` de la CI exécute
uvx --with tox-uv tox               # tous les environnements de vérification (env_list)
```

`pre-push` ne modifie aucun fichier : s'il signale un problème de
formatage, lance `local` (ou `format`) puis relance `pre-push`. Voir la
table `[tool.tox]` de `pyproject.toml` pour la liste complète des
environnements.

Chaque outil (`basedpyright`, `flake8`, `black`, `isort`, `bandit`) a son
propre environnement `tox` si tu veux n'en lancer qu'un seul.

Installe une fois par clone les hooks Git versionnés :

```bash
uvx --with tox-uv tox -e hooks   # git config core.hooksPath .githooks
```

- `commit-msg` refuse un message qui ne suit pas Conventional Commits
  (`type(scope)!: description`, deuxième ligne vide, pied de page
  `BREAKING CHANGE:` quand le sujet porte `!`, sujet de 100 caractères
  au plus, 72 recommandés) ;
- `pre-push` lance `tox -e pre-push` avant `git push` et interrompt
  l'envoi en cas d'échec ; il refuse un envoi avec des modifications non
  committées de fichiers suivis, ou d'une autre référence que `HEAD`,
  puisque la vérification porte sur l'arbre de travail.

`--no-verify` contourne l'un ou l'autre hook pour un commit ou un envoi.

Les versions de Python se règlent dans deux fichiers, et seulement là :

- `.tox-config/versions.txt` : un environnement tox par ligne avec ses
  marqueurs, `local` (lancé par `pre-push`), `ci` (matrice de tests de la
  CI), `experimental` (échec toléré, exige `ci` ; avec `local`, `pre-push` la
  lance et n'avertit qu'en cas d'échec), par exemple
  `py315 local ci experimental` ;
- `.tox-config/coverage-version.txt` : la version qui mesure la
  couverture (marquée `local` et `ci`). En local, elle n'est testée
  qu'une fois, par la couverture.

Quand une version est ajoutée ou retirée, mets aussi à jour les
classifiers `Programming Language` de `pyproject.toml` : `tox -e versions`
(lancé en premier par `ci-quality`, `pre-push` et `local`) s'arrête à la
moindre incohérence entre les deux fichiers et les classifiers.

La documentation se construit avec `tox -e docs` (`sphinx-build -E -W`,
avertissements traités comme des erreurs, sortie dans `docs/build/html`).
C'est la construction que lance le workflow GitHub Pages, et `pre-push`
l'exécute aussi.

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
`config`, `api`, `orchestrator`, `translation`, `package`, `cli` — voir
`.codecov.yml`).

## Commits

Format [Conventional Commits](https://www.conventionalcommits.org/) :

```
<type>[scope optionnel]: <description>

[corps optionnel]

[footer(s) optionnel(s)]
```

Types utilisés dans ce dépôt : `feat`, `fix`, `chore`, `ci`, `docs`,
`refactor`, `test`, `perf`, `security`, `build`, `revert`, `style`.
Breaking changes : `!` après le type
ou footer `BREAKING CHANGE:`. Une unité logique par commit — ne grouper
plusieurs fichiers que s'ils forment un changement indivisible ; ne pas
mélanger des préoccupations distinctes dans un même commit.

## Pull requests

Le dépôt utilise le jeu de labels standard, en sept catégories :
`type:`, `status:`, `priority:`, `scope:`, `effort:`, `ecosystem:` et
`meta:`. Les issues s'ouvrent depuis les formulaires d'issue (bug,
feature, documentation, tâche technique et les quatre formulaires de
décision) ; les issues vierges sont désactivées. Le template de pull
request liste ce qu'une PR indique.

- Ouvre une issue d'abord pour tout ce qui dépasse une petite correction
  évidente.
- Avant le merge, une PR porte un jalon et au moins un label `type:` :
  Release Drafter construit les notes de version à partir de celui-ci.
- Référence l'issue liée dans la description de ta PR (`Closes #NN` /
  `Fixes #NN`) si elle existe.
- Vérifie que `uvx --with tox-uv tox -e pre-push` passe en local avant d'ouvrir la PR —
  la CI exécute les mêmes vérifications (`quality` → matrice `test-unit`) et
  ne mergera pas une build rouge.
- Garde la PR centrée sur une seule préoccupation ; sépare les changements
  non liés dans des PR distinctes.

## Code de conduite

En participant à ce projet, tu acceptes de respecter le
[Code de conduite](CODE_OF_CONDUCT.fr.md).

## Questions

Ouvre une [issue GitHub](https://github.com/biface/i18n/issues).
