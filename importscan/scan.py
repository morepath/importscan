from .compat import is_nonstr_iter
from pkgutil import iter_modules
import imp
import sys


def scan(package, ignore=None, onerror=None):
    """Scan a package by importing it.

    A framework can provide registration decorators: a decorator that
    when used on a class or a function causes it to be registered with
    the framework. Metaclasses can also be used for this effect. As a
    consequence of this, registration only takes place when the module
    is actually imported. You can do this import explicitly in your
    code.  It can however also be convenient to import everything in a
    package all at once automatically. This is what ``scan`` does.

    This function was extracted and refactored from the ``Venusian``
    library which also provides infrastructure for finding such
    decorators.

    :param package: A reference to a Python package or module object.

    :param ignore: Ignore certain modules or packages during a scan. It
      should be a sequence containing strings and/or callables that
      are used to match against the dotted name of a module
      encountered during a scan. The sequence can contain any of these
      three types of objects:

      - A string representing a dotted name. For example, if you want
        to ignore the ``my.package`` package *and any of its
        submodules* during the scan, pass
        ``ignore=['my.package']``.

      - A string representing a relative dotted name, a string
        starting with a dot. The relative module or package is
        relative to the ``package`` being scanned, so this does *not*
        match deeper relative packages.

        For example, if the ``package`` you've passed is imported as
        ``my.package``, and you pass ``ignore=['.mymodule']``, the
        ``my.package.mymodule`` mymodule *and any of its submodules*
        are omitted during scan processing. But ``my.package.sub.mymodule``
        is *not* ignored as ``mymodule`` is nested in ``sub``.

      - A callable that accepts a dotted name indicating a module or a
        package as its single positional argument and returns ``True``
        or ``False``. For example, if you want to skip all packages and
        modules with a full dotted path that ends
        with the word "tests", you can use
        ``ignore=[re.compile('tests$').search]``. If the callable
        returns ``True`` (or anything else truthy), the object is
        ignored, if it returns ``False`` (or anything else falsy) the
        object is not ignored.

      You can mix and match the three types of strings in the list.
      For example, if the package being scanned is ``my``,
      ``ignore=['my.package', '.someothermodule',
      re.compile('tests$').search]`` would cause ``my.package`` (and
      all its submodules and subobjects) to be ignored,
      ``my.someothermodule`` to be ignored, and any modules, packages,
      or global objects found during the scan that have a full dotted
      name that ends with the word ``tests`` to be ignored.

      Packages and modules matched by any ignore in the list are not
      imported, and their top-level (registration) code is not run as
      a result.

      You can also pass in a string or callable by itself as a single
      non-list argument.

    :param onerror: A callback function which behaves the same way as the
      ``onerror`` callback function described in
      http://docs.python.org/library/pkgutil.html#pkgutil.walk_packages
      .  By default scan propagates all errors that happen during its
      code importing process, including :exc:`ImportError`. If you
      use a custom ``onerror`` callback, you can change this behavior.

      Here's an example ``onerror`` callback that ignores
      :exc:`ImportError`::

        import sys
        def onerror(name):
            if not issubclass(sys.exc_info()[0], ImportError):
                raise # reraise the last exception

      The ``name`` passed to ``onerror`` is the module or package
      dotted name that could not be imported due to an exception.

    """
    is_ignored = get_is_ignored(package, ignore)

    # not a package but a module
    if not hasattr(package, '__path__'):
        return

    for importer, modname, ispkg in walk_packages(
            package.__path__,
            package.__name__ + '.',
            is_ignored=is_ignored,
            onerror=onerror):
        loader = importer.find_module(modname)
        if loader is None:
            # happens on pypy with orphaned pyc
            continue
        try:
            import_module(modname, loader, onerror)
        finally:
            if hasattr(loader, 'file') and hasattr(loader.file, 'close'):
                loader.file.close()


def import_module(modname, loader, onerror):
    if hasattr(loader, 'etc'):
        # python < py3.3
        module_type = loader.etc[2]
    else:  # pragma: no cover
        # py3.3b2+ (importlib-using)
        module_type = imp.PY_SOURCE
        get_filename = getattr(loader, 'get_filename', None)
        if get_filename is None:
            get_filename = loader._get_filename
        try:
            fn = get_filename(modname)
        except TypeError:
            fn = get_filename()
        if fn.endswith(('.pyc', '.pyo', '$py.class')):
            module_type = imp.PY_COMPILED
    # only scan non-orphaned source files and package directories
    if module_type not in (imp.PY_SOURCE, imp.PKG_DIRECTORY):
        return

    # NB: use __import__(modname) rather than
    # loader.load_module(modname) to prevent
    # inappropriate double-execution of module code
    try:
        __import__(modname)
    except Exception:
        if onerror is not None:
            onerror(modname)
        else:
            raise


def get_is_ignored(package, ignore):
    pkg_name = package.__name__

    if ignore is None:
        ignore = []
    elif not is_nonstr_iter(ignore):
        ignore = [ignore]

    # non-leading-dotted name absolute object name
    str_ignores = [ign for ign in ignore if isinstance(ign, str)]
    # leading dotted name relative to scanned package
    rel_ignores = [ign for ign in str_ignores if ign.startswith('.')]
    # non-leading dotted names
    abs_ignores = [ign for ign in str_ignores if not ign.startswith('.')]
    # functions, e.g. re.compile('pattern').search
    callable_ignores = [ign for ign in ignore if callable(ign)]

    def is_ignored(fullname):
        for ign in rel_ignores:
            if fullname.startswith(pkg_name + ign):
                return True
        for ign in abs_ignores:
            # non-leading-dotted name absolute object name
            if fullname.startswith(ign):
                return True
        for ign in callable_ignores:
            if ign(fullname):
                return True
        return False

    return is_ignored


def walk_packages(path=None, prefix='', is_ignored=None, onerror=None):
    """Yields (module_loader, name, ispkg) for all modules recursively
    on path, or, if path is ``None``, all accessible modules.

    Note that this function must import all *packages* (NOT all
    modules!) on the given path, in order to access the __path__
    attribute to find submodules.

    :param path: A list of paths to look for modules in, or `None`.
    :param prefix: A string to output on the front of every module name
      on output.
    :param is_ignored: A function fed a dotted name; if it returns True,
      the package is skipped and not returned in results nor
      imported.
    :onerror: A function which gets called with one argument (the name of
      the package which was being imported) if any exception occurs while
      trying to import a package.  If no onerror function is supplied, any
      exception is exceptions propagated, terminating the search.

    Examples:
    # list all modules python can access
    walk_packages()
    # list all submodules of ctypes
    walk_packages(ctypes.__path__, ctypes.__name__+'.')
    # NB: we can't just use pkgutils.walk_packages because we need to ignore
    # things
    """

    def seen(p, m={}):
        if p in m:  # pragma: no cover
            return True
        m[p] = True

    # iter_modules is nonrecursive
    for importer, name, ispkg in iter_modules(path, prefix):

        if is_ignored is not None and is_ignored(name):
            # if name is a package, ignoring here causes
            # all subpackages and submodules to be ignored too
            continue

        if not ispkg:
            yield importer, name, ispkg
            continue

        try:
            __import__(name)
        except Exception:
            # do any onerror handling before yielding
            if onerror is not None:
                onerror(name)
            else:
                raise
        else:
            yield importer, name, ispkg
            path = getattr(sys.modules[name], '__path__', None) or []

            # don't traverse path items we've seen before
            path = [p for p in path if not seen(p)]

            for item in walk_packages(path, name+'.', is_ignored, onerror):
                yield item
