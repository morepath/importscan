from __future__ import annotations

from collections.abc import Callable, Sequence
from importlib.machinery import ModuleSpec
from os import PathLike
from types import ModuleType
from typing import Protocol, TypeAlias


class MetaPathFinderProtocol(Protocol):
    def find_spec(
        self,
        fullname: str,
        path: Sequence[str] | None,
        target: ModuleType | None = ...,
        /,
    ) -> ModuleSpec | None: ...


class PathEntryFinderProtocol(Protocol):
    def find_spec(
        self, fullname: str, target: ModuleType | None = ..., /
    ) -> ModuleSpec | None: ...


IgnoreModuleCallback: TypeAlias = Callable[[str], object]
IgnoreModule: TypeAlias = str | IgnoreModuleCallback
ModuleFinder: TypeAlias = MetaPathFinderProtocol | PathEntryFinderProtocol
ModuleInfo: TypeAlias = tuple[ModuleFinder, str, bool]
StrOrBytesPath: TypeAlias = PathLike[str] | PathLike[bytes] | str | bytes
