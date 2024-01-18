from __future__ import annotations

import contextlib
import io
import os
import pathlib
import re
from dataclasses import dataclass
from typing import ContextManager, Final, Mapping

from typing_extensions import Self

# "Best effort" regex for extracting simple environment variables exports from Bourne
# family shell files.
_ENV_EXPORT_PATTERN: Final = re.compile(
    r"^[\t ]*(?:export[\t ]+)?(?P<name>[a-zA-Z_]+[a-zA-Z0-9_]*)=(['\"])?(?P<value>.*?)\2?[\t ]*$",
    flags=re.MULTILINE,
)


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

    @classmethod
    def from_shell_file(cls, file: str | pathlib.Path | io.TextIOBase) -> Self:
        cm: ContextManager[io.TextIOBase]
        if isinstance(file, io.TextIOBase):
            cm = contextlib.nullcontext(file)
        else:
            cm = open(file, "r")

        with cm as fd:
            text = fd.read()

        env_exports = {
            match["name"]: match["value"]
            for match in _ENV_EXPORT_PATTERN.finditer(text)
        }

        return cls.from_environ(env_exports)
