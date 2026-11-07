# -*- coding: utf-8 -*-
"""Stand-ins for Revit, .NET and pyRevit so the extension imports under CPython.

Any module under the stubbed prefixes imports, and any name taken from it is an
:class:`Anything`.  Tests replace the few names whose behaviour they check.
"""

import contextlib
import importlib.abc
import importlib.machinery
import os
import sys
import types

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
LIB = os.path.join(ROOT, "lib")
STUBBED = ("Autodesk", "System", "clr", "pyrevit", "Microsoft")


class Anything(object):
    def __init__(self, *args, **kwargs):
        pass

    def __getattr__(self, name):
        if name.startswith("__"):
            raise AttributeError(name)
        return Anything()

    def __call__(self, *args, **kwargs):
        return Anything()

    def __getitem__(self, key):
        return Anything()

    def __iter__(self):
        return iter(())


class StubModule(types.ModuleType):
    def __getattr__(self, name):
        if name.startswith("__"):
            raise AttributeError(name)
        return Anything()


class _StubFinder(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    def find_spec(self, fullname, path, target=None):
        if fullname.split(".")[0] in STUBBED:
            return importlib.machinery.ModuleSpec(fullname, self,
                                                  is_package=True)
        return None

    def create_module(self, spec):
        module = StubModule(spec.name)
        module.__path__ = []
        return module

    def exec_module(self, module):
        pass


@contextlib.contextmanager
def _wrapped(*args, **kwargs):
    yield


def stub(name, **attrs):
    """Register `name` as a stub module that also carries `attrs`."""
    module = sys.modules.get(name)
    if not isinstance(module, StubModule):
        module = StubModule(name)
        sys.modules[name] = module
    module.__dict__.update(attrs)
    return module


def install():
    """Make the extension's lib importable with Revit stubbed out."""
    if LIB not in sys.path:
        sys.path.insert(0, LIB)
    if not any(isinstance(f, _StubFinder) for f in sys.meta_path):
        sys.meta_path.insert(0, _StubFinder())
    import pyrevit.coreutils.applocales as applocales
    applocales.get_locale_string = lambda variants: None
    import core.selectionhelpers as selectionhelpers
    selectionhelpers.id_value = lambda element_id: element_id
    stub("core.transaction", WrappedTransaction=_wrapped,
         WrappedTransactionGroup=_wrapped)


def load_script(*parts):
    """Run a bundle script as a module, not as a click, and return its names."""
    install()
    path = os.path.join(ROOT, *parts)
    namespace = {"__name__": "bundle_script", "__file__": path,
                 "__revit__": Anything()}
    with open(path, encoding="utf-8") as source:
        exec(compile(source.read(), path, "exec"), namespace)
    return namespace
