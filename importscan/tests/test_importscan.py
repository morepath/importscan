from __future__ import annotations

import contextlib
import os
import re
import sys
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest
from pytest import raises

from importscan import scan
from importscan.scan import import_module

from . import fixtures

if TYPE_CHECKING:
    from collections.abc import Generator

# note that due to the nature of imports, we need to have a unique fixture
# for each test


@contextlib.contextmanager
def with_entry_in_sys_path(entry: str) -> Generator[None]:
    """Context manager that temporarily puts an entry at head of sys.path"""
    sys.path.insert(0, entry)
    yield
    sys.path.remove(entry)


def zip_file_in_sys_path() -> contextlib.AbstractContextManager[None]:
    """Context manager that puts zipped.zip at head of sys.path"""
    zip_pkg_path = os.path.join(
        os.path.dirname(__file__), "fixtures", "zipped.zip"
    )
    return with_entry_in_sys_path(zip_pkg_path)


@pytest.fixture(autouse=True, scope="function")
def reset_fixtures() -> None:
    fixtures.reset()


def test_empty_package() -> None:
    from .fixtures import empty_package

    scan(empty_package)

    assert fixtures.calls == 1


def test_module() -> None:
    from .fixtures import module

    scan(module)

    assert fixtures.calls == 1


def test_package() -> None:
    from .fixtures import package

    scan(package)

    assert fixtures.calls == 1


def test_empty_subpackage() -> None:
    from .fixtures import empty_subpackage

    scan(empty_subpackage)

    assert fixtures.calls == 1


def test_subpackage() -> None:
    from .fixtures import subpackage

    scan(subpackage)

    assert fixtures.calls == 1


def test_ignore_module_relative() -> None:
    from .fixtures import ignore_module

    scan(ignore_module, ignore=[".module"])

    assert fixtures.calls == 0


def test_ignore_module_absolute() -> None:
    from .fixtures import ignore_module_absolute

    scan(
        ignore_module_absolute,
        ignore=["importscan.tests.fixtures.ignore_module_absolute.module"],
    )

    assert fixtures.calls == 0


def test_ignore_module_function() -> None:
    from .fixtures import ignore_module_function

    scan(ignore_module_function, ignore=re.compile("module$").search)

    assert fixtures.calls == 0


def test_ignore_subpackage_relative() -> None:
    from .fixtures import ignore_subpackage

    scan(ignore_subpackage, ignore=[".sub"])

    assert fixtures.calls == 0


def test_ignore_subpackage_function() -> None:
    from .fixtures import ignore_subpackage_function

    scan(ignore_subpackage_function, ignore=re.compile("sub$").search)

    assert fixtures.calls == 0


def test_ignore_subpackage_module_relative() -> None:
    from .fixtures import ignore_subpackage_module

    scan(ignore_subpackage_module, ignore=[".sub.module"])

    assert fixtures.calls == 0


def test_importerror() -> None:
    from .fixtures import importerror

    with raises(ImportError):
        scan(importerror)


def test_attributeerror() -> None:
    from .fixtures import attributeerror

    with raises(AttributeError):
        scan(attributeerror)


def test_importerror_handle_error() -> None:
    from .fixtures import importerror_handle_error

    # skip import errors
    def handle_error(name: str, e: Exception) -> None:
        if not isinstance(e, ImportError):
            raise e

    scan(importerror_handle_error, handle_error=handle_error)

    assert fixtures.calls == 1


def test_attributeerror_not_handle_error() -> None:
    from .fixtures import attributeerror_not_handle_error

    # skip import errors but not attribute errors
    def handle_error(name: str, e: Exception) -> None:
        if not isinstance(e, ImportError):
            raise e

    with raises(AttributeError):
        scan(attributeerror_not_handle_error, handle_error=handle_error)


def test_package_in_zipped() -> None:
    with zip_file_in_sys_path():
        import packageinzipped  # type: ignore

    scan(packageinzipped)

    assert fixtures.calls == 1


def test_module_in_zipped() -> None:
    with zip_file_in_sys_path():
        import moduleinzipped  # type: ignore

    scan(moduleinzipped)

    assert fixtures.calls == 1


def test_scan_loader_file_close() -> None:
    # __init__.py overwrites the 'scan' attribute with the function, so
    # `import importscan.scan as x` resolves via getattr and yields the
    # function; sys.modules gives the actual module object.
    scan_mod = sys.modules["importscan.scan"]

    from .fixtures import package

    mock_file = MagicMock()
    mock_loader = MagicMock()
    mock_loader.file = mock_file
    mock_spec = MagicMock()
    mock_spec.loader = mock_loader
    mock_importer = MagicMock()
    mock_importer.find_spec.return_value = mock_spec

    # patch.object avoids ambiguity from importscan.__init__ re-exporting scan
    with patch.object(scan_mod, "walk_packages") as mock_wp:
        mock_wp.return_value = iter(
            [(mock_importer, "importscan.tests.fixtures.package.module", False)]
        )
        with patch.object(scan_mod, "import_module"):
            scan(package)

    mock_file.close.assert_called_once()


class _LoaderUnderscoreGetFilename:
    def _get_filename(self, modname: str | None = None) -> str:
        return "some_module.py"


class _LoaderGetFilenameTypeError:
    def get_filename(self, modname: str | None = None) -> str:
        if modname is not None:
            raise TypeError
        return "some_module.py"


class _LoaderPycFilename:
    def get_filename(self, modname: str | None = None) -> str:
        return "some_module.pyc"


def test_import_module_underscore_get_filename() -> None:
    loader = _LoaderUnderscoreGetFilename()
    with patch("builtins.__import__"):
        import_module("somemodule", loader, None)  # type: ignore[arg-type]


def test_import_module_get_filename_typeerror() -> None:
    loader = _LoaderGetFilenameTypeError()
    with patch("builtins.__import__"):
        import_module("somemodule", loader, None)  # type: ignore[arg-type]


def test_import_module_pyc_skipped() -> None:
    loader = _LoaderPycFilename()
    with patch("builtins.__import__") as mock_import:
        import_module("somemodule", loader, None)  # type: ignore[arg-type]
    mock_import.assert_not_called()


def test_walk_packages_importerror_subpackage() -> None:
    from .fixtures import importerror_pkg

    with raises(ImportError):
        scan(importerror_pkg)


def test_walk_packages_importerror_subpackage_handle_error() -> None:
    from .fixtures import importerror_pkg_handle_error

    errors: list[str] = []

    def handle_error(name: str, e: Exception) -> None:
        errors.append(name)

    scan(importerror_pkg_handle_error, handle_error=handle_error)
    assert len(errors) == 1
