"""
Import rules of the loaders layers, checked on the source tree.

- ``loaders._utils``: imports no other loaders module.
- ``loaders._settings``: may import ``loaders._utils``.
- ``loaders._handler``: may import ``loaders._utils`` and ``loaders._settings``.
- ``loaders.loader``: may import ``loaders._handler`` only.
- Every module outside ``loaders/`` may import ``loaders.loader`` only.

Every import counts, including function-local imports and imports under
``TYPE_CHECKING``. Tests are not checked: they test the internal modules
directly.
"""

import ast
from pathlib import Path

import pytest

import i18n_tools

PACKAGE = "i18n_tools"
LOADERS = PACKAGE + ".loaders"
SRC_ROOT = Path(i18n_tools.__file__).resolve().parent

ALLOWED_INSIDE_LOADERS: dict[str, set[str]] = {
    LOADERS: set(),
    LOADERS + "._utils": set(),
    LOADERS + "._settings": {LOADERS + "._utils"},
    LOADERS + "._handler": {LOADERS + "._utils", LOADERS + "._settings"},
    LOADERS + ".loader": {LOADERS + "._handler"},
}
ALLOWED_OUTSIDE_LOADERS = {LOADERS + ".loader"}


def _module_name(path: Path, root: Path = SRC_ROOT) -> str:
    parts = list(path.relative_to(root).with_suffix("").parts)
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join([PACKAGE, *parts])


def _is_module(name: str, root: Path = SRC_ROOT) -> bool:
    relative = Path(*name.split(".")[1:])
    return (root / relative).with_suffix(".py").is_file() or (
        root / relative / "__init__.py"
    ).is_file()


def _imported_modules(path: Path, root: Path = SRC_ROOT) -> set[str]:
    """Absolute names of the i18n_tools modules imported by ``path``."""
    module = _module_name(path, root)
    package = module if path.name == "__init__.py" else module.rpartition(".")[0]
    found: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                base_parts = package.split(".")
                base_parts = base_parts[: len(base_parts) - (node.level - 1)]
                base = ".".join(base_parts)
                target = base + "." + node.module if node.module else base
            else:
                target = node.module or ""
            for alias in node.names:
                candidate = target + "." + alias.name
                found.add(candidate if _is_module(candidate, root) else target)
    return {name for name in found if name.split(".")[0] == PACKAGE}


SOURCE_FILES = sorted(SRC_ROOT.rglob("*.py"))


@pytest.mark.parametrize(
    "path", SOURCE_FILES, ids=lambda p: str(p.relative_to(SRC_ROOT))
)
def test_loaders_import_rules(path):
    module = _module_name(path)
    imported_loaders = {
        name
        for name in _imported_modules(path)
        if name == LOADERS or name.startswith(LOADERS + ".")
    }
    if module == LOADERS or module.startswith(LOADERS + "."):
        allowed = ALLOWED_INSIDE_LOADERS[module]
    else:
        allowed = ALLOWED_OUTSIDE_LOADERS
    assert imported_loaders <= allowed, (
        f"{module} imports {sorted(imported_loaders - allowed)}; "
        f"allowed: {sorted(allowed) or 'no loaders module'}"
    )


def test_every_loaders_module_has_a_rule():
    loaders_modules = {
        _module_name(path) for path in (SRC_ROOT / "loaders").glob("*.py")
    }
    assert loaders_modules == set(ALLOWED_INSIDE_LOADERS)


@pytest.mark.parametrize(
    "source, module, expected",
    [
        (
            "from . import _settings, _utils\n",
            "loaders._handler",
            {"_settings", "_utils"},
        ),
        ("from ._utils import check_path\n", "loaders._settings", {"_utils"}),
        ("from .loaders.loader import build_path\n", "core", {"loader"}),
        (
            "def f():\n    from i18n_tools.loaders._handler import x\n",
            "converter",
            {"_handler"},
        ),
    ],
)
def test_import_resolution(tmp_path, source, module, expected):
    """The resolver sees relative, package-level and function-local imports."""
    fake_root = tmp_path / PACKAGE
    (fake_root / "loaders").mkdir(parents=True)
    for name in ("__init__", "core", "converter"):
        (fake_root / f"{name}.py").write_text("")
    for name in ("__init__", "_utils", "_settings", "_handler", "loader"):
        (fake_root / "loaders" / f"{name}.py").write_text("")
    target = fake_root / Path(*module.split(".")).with_suffix(".py")
    target.write_text(source)

    imported = {
        name.rpartition(".")[2]
        for name in _imported_modules(target, fake_root)
        if name.startswith(LOADERS + ".")
    }
    assert imported == expected
