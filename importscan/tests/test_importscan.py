import sys
import re
import os
import contextlib
from importscan import scan
from . import fixtures
from pytest import raises


# note that due to the nature of imports, we need to have a unique fixture
# for each test


@contextlib.contextmanager
def with_entry_in_sys_path(entry):
    """Context manager that temporarily puts an entry at head of sys.path"""
    sys.path.insert(0, entry)
    yield
    sys.path.remove(entry)


def zip_file_in_sys_path():
    """Context manager that puts zipped.zip at head of sys.path"""
    zip_pkg_path = os.path.join(
        os.path.dirname(__file__), "fixtures", "zipped.zip"
    )
    return with_entry_in_sys_path(zip_pkg_path)


def setup_function(function):
    fixtures.reset()


def test_empty_package():
    from .fixtures import empty_package

    scan(empty_package)

    assert fixtures.calls == 1


def test_module():
    from .fixtures import module

    scan(module)

    assert fixtures.calls == 1


def test_package():
    from .fixtures import package

    scan(package)

    assert fixtures.calls == 1


def test_empty_subpackage():
    from .fixtures import empty_subpackage

    scan(empty_subpackage)

    assert fixtures.calls == 1


def test_subpackage():
    from .fixtures import subpackage

    scan(subpackage)

    assert fixtures.calls == 1


def test_ignore_module_relative():
    from .fixtures import ignore_module

    scan(ignore_module, ignore=[".module"])

    assert fixtures.calls == 0


def test_ignore_module_absolute():
    from .fixtures import ignore_module_absolute

    scan(
        ignore_module_absolute,
        ignore=["importscan.tests.fixtures.ignore_module_absolute.module"],
    )

    assert fixtures.calls == 0


def test_ignore_module_function():
    from .fixtures import ignore_module_function

    scan(ignore_module_function, ignore=re.compile("module$").search)

    assert fixtures.calls == 0


def test_ignore_subpackage_relative():
    from .fixtures import ignore_subpackage

    scan(ignore_subpackage, ignore=[".sub"])

    assert fixtures.calls == 0


def test_ignore_subpackage_function():
    from .fixtures import ignore_subpackage_function

    scan(ignore_subpackage_function, ignore=re.compile("sub$").search)

    assert fixtures.calls == 0


def test_ignore_subpackage_module_relative():
    from .fixtures import ignore_subpackage_module

    scan(ignore_subpackage_module, ignore=[".sub.module"])

    assert fixtures.calls == 0


def test_importerror():
    from .fixtures import importerror

    with raises(ImportError):
        scan(importerror)


def test_attributeerror():
    from .fixtures import attributeerror

    with raises(AttributeError):
        scan(attributeerror)


def test_importerror_handle_error():
    from .fixtures import importerror_handle_error

    # skip import errors
    def handle_error(name, e):
        if not isinstance(e, ImportError):
            raise e

    scan(importerror_handle_error, handle_error=handle_error)

    assert fixtures.calls == 1


def test_attributeerror_not_handle_error():
    from .fixtures import attributeerror_not_handle_error

    # skip import errors but not attribute errors
    def handle_error(name, e):
        if not isinstance(e, ImportError):
            raise e

    with raises(AttributeError):
        scan(attributeerror_not_handle_error, handle_error=handle_error)


def test_package_in_zipped():
    with zip_file_in_sys_path():
        import packageinzipped

    scan(packageinzipped)

    assert fixtures.calls == 1


def test_module_in_zipped():
    with zip_file_in_sys_path():
        import moduleinzipped

    scan(moduleinzipped)

    assert fixtures.calls == 1
