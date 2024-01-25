from __future__ import annotations

import importlib.metadata
from typing import Final

from . import input, unit
from ._env import ModtranEnv
from ._exec import ModtranExecutable

DISTRIBUTION_NAME: Final[str] = "pymod6"

__version__ = importlib.metadata.version(DISTRIBUTION_NAME)

__all__ = ["ModtranEnv", "ModtranExecutable"]
