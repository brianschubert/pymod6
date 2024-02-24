from __future__ import annotations

import contextlib
import dataclasses
import os
import pathlib
import re
import string
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
    """
    MODTRAN environment.

    Encapsulates environment variables relevant to MODTRAN. Typically, this class
    will be constructed automatically from the actual process environment variables
    via ``ModtranEnv.from_environ``.

    When the relevant environment variables are not already set, this class can be
    constructed manually to specify the environemnt MODTRAN should be run in.

    Examples
    --------
    >>> from pathlib import Path
    >>> mod_env = ModtranEnv(
    ...     exe=Path("~/path/to/executable").expanduser(),
    ...     data=Path("~/path/to/DATA").expanduser(),
    ... )
    >>> str(mod_env.exe)
    '.../path/to/executable'
    >>> str(mod_env.data)
    '.../path/to/DATA'
    """

    exe: pathlib.Path
    """Path to MODTRAN executable."""

    data: pathlib.Path
    """Path to MODTRAN data directory."""

    extra: dict[str, str] = dataclasses.field(default_factory=dict)
    """Extra environment variables to be made available to MODTRAN."""

    @classmethod
    def from_environ(cls, environ: Mapping[str, str] = os.environ) -> Self:
        """
        Infer MODTRAN environment from environment variables.

        Parameters
        ----------
        environ : Mapping[str, str], optional
            Mapping of environment variables. Defaults to ``os.environ``.

        Returns
        -------
        Self
            Inferred MODTRAN environment.

        Examples
        --------
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
    def from_shell_file(
        cls, file: str | pathlib.Path | TextIO, *, substitute: bool = False
    ) -> Self:
        """
        Infer MODTRAN environment by parsing a shell file.

        Parameters
        ----------
        file : file path or file-like object
            The shell file to extract environment variable definitions from.
        substitute : bool, optional
            Whether to substitute `$variable` expansions. Defaults to `False`.

        Returns
        -------
        Self
            Inferred MODTRAN environment.

        Examples
        --------
        >>> import io
        >>> shell_file = io.StringIO('''
        ...     export MODTRAN_EXE=/path/to/exe
        ...     MODTRAN_DATA=/path/to/DATA
        ... ''')
        >>> ModtranEnv.from_shell_file(shell_file)
        ModtranEnv(exe=...Path('/path/to/exe'), data=...Path('/path/to/DATA'), extra={})
        >>> shell_file = io.StringIO('''
        ...     export MODTRAN_BASE=/base/path
        ...     export MODTRAN_EXE=$MODTRAN_BASE/exe
        ...     export MODTRAN_DATA="${MODTRAN_BASE}/DATA"
        ... ''')
        >>> ModtranEnv.from_shell_file(shell_file, substitute=True)
        ModtranEnv(exe=...Path('/base/path/exe'), data=...Path('/base/path/DATA'), extra={'MODTRAN_BASE': '/base/path'})
        """
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

        if substitute:
            for name, value in env_exports.items():
                env_exports[name] = string.Template(value).safe_substitute(env_exports)

        return cls.from_environ(env_exports)

    def to_environ(self) -> dict[str, str]:
        """
        Export this environment to an environment variable mapping.

        Returns
        -------
        environ : dict[str, str]
            Environment variable mapping, like ``os.environ``.
        """
        return {
            "MODTRAN_EXE": str(self.exe),
            "MODTRAN_DATA": str(self.data),
            **self.extra,
        }
