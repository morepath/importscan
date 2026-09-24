from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, TypeAlias

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from importlib.machinery import ModuleSpec
    from os import PathLike
    from types import ModuleType


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


IgnoreModuleCallback: TypeAlias = "Callable[[str], object]"
IgnoreModule: TypeAlias = str | IgnoreModuleCallback
ModuleFinder: TypeAlias = MetaPathFinderProtocol | PathEntryFinderProtocol
ModuleInfo: TypeAlias = tuple[ModuleFinder, str, bool]
StrOrBytesPath: TypeAlias = "PathLike[str] | PathLike[bytes] | str | bytes"
