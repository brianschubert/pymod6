"""
* `pymod6.input` - Input file construction and handling.
* `pymod6.io` - I/O for input and output files.
* `pymod6.output` - Utilities for navigating output file placement in the filesystem.
* `pymod6.unit` - Unit conversion utilities.
"""
from __future__ import annotations

import importlib.metadata
from typing import Final

from . import input, io, output, unit
from ._env import ModtranEnv
from ._exec import ModtranExecutable, ModtranResult

DISTRIBUTION_NAME: Final[str] = "pymod6"

__version__ = importlib.metadata.version(DISTRIBUTION_NAME)

__all__ = [
    "input",
    "io",
    "output",
    "unit",
    "ModtranExecutable",
    "ModtranResult",
    "ModtranEnv",
]
