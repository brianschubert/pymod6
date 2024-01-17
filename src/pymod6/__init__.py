from __future__ import annotations

import importlib.metadata
import os
import pathlib
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Final

from typing_extensions import Self

DISTRIBUTION_NAME: Final[str] = "pymod6"

__version__ = importlib.metadata.version(DISTRIBUTION_NAME)


@dataclass
class ModEnv:
    exe: pathlib.Path
    data: pathlib.Path

    @classmethod
    def from_environ(cls, environ: Mapping[str, str] = os.environ) -> Self:
        try:
            exe = pathlib.Path(environ["MODTRAN_EXE"])
        except KeyError as ex:
            raise ValueError("MODTRAN_EXE not set in environment") from ex

        try:
            data = pathlib.Path(environ["MODTRAN_DATA"])
        except KeyError as ex:
            raise ValueError("MODTRAN_DATA not set in environment") from ex

        return cls(exe=exe, data=data)
