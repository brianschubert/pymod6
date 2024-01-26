from __future__ import annotations

import contextlib
import dataclasses
import os
import pathlib
import re
from dataclasses import dataclass
from typing import ContextManager, Final, Mapping, TextIO, cast

from typing_extensions import Self

from . import _util

# "Best effort" regex for extracting simple environment variables exports from Bourne
# family shell files.
_ENV_EXPORT_PATTERN: Final = re.compile(
    r"^[\t ]*(?:export[\t ]+)?(?P<name>[a-zA-Z_]+[a-zA-Z0-9_]*)=(['\"])?(?P<value>.*?)\2?[\t ]*$",
    flags=re.MULTILINE,
)


@dataclass
class ModtranEnv:
    exe: pathlib.Path
    data: pathlib.Path
    extra: dict[str, str] = dataclasses.field(default_factory=dict)

    @classmethod
    def from_environ(cls, environ: Mapping[str, str] = os.environ) -> Self:
        """
        Infer MODTRAN environment from environment variables.

        >>> ModtranEnv.from_environ(
        ...     {"MODTRAN_EXE": "exe", "MODTRAN_DATA": "data", "MODTRAN_OTHER": "other", "EXTRANEOUS": "misc"}
        ... ) # doctest: +ELLIPSIS
        ModtranEnv(exe=...Path('exe'), data=...Path('data'), extra={'MODTRAN_OTHER': 'other'})
        """
        mod_vars = {k: v for k, v in environ.items() if k.startswith("MODTRAN")}

        try:
            exe = pathlib.Path(mod_vars.pop("MODTRAN_EXE"))
        except KeyError as ex:
            raise ValueError("MODTRAN_EXE not set in environment") from ex

        try:
            data = pathlib.Path(mod_vars.pop("MODTRAN_DATA"))
        except KeyError as ex:
            raise ValueError("MODTRAN_DATA not set in environment") from ex

        return cls(exe=exe, data=data, extra=mod_vars)

    @classmethod
    def from_shell_file(cls, file: str | pathlib.Path | TextIO) -> Self:
        cm: ContextManager[TextIO]
        if _util.is_text_io(file):
            cm = contextlib.nullcontext(file)
        else:
            cm = open(cast("str | pathlib.Path", file), "r")

        with cm as fd:
            text = fd.read()

        env_exports = {
            match["name"]: match["value"]
            for match in _ENV_EXPORT_PATTERN.finditer(text)
        }

        return cls.from_environ(env_exports)

    def to_environ(self) -> dict[str, str]:
        return {
            "MODTRAN_EXE": str(self.exe),
            "MODTRAN_DATA": str(self.data),
            **self.extra,
        }
