from __future__ import annotations

import importlib.metadata
from typing import Final

from . import input, output, unit
from ._env import ModtranEnv
from ._exec import ModtranExecutable, ModtranResult

DISTRIBUTION_NAME: Final[str] = "pymod6"

__version__ = importlib.metadata.version(DISTRIBUTION_NAME)

__all__ = [
    "ModtranExecutable",
    "ModtranResult",
    "ModtranEnv",
    "input",
    "output",
    "unit",
]
