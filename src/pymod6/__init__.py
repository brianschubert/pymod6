from __future__ import annotations

import importlib.metadata
from typing import Final

DISTRIBUTION_NAME: Final[str] = "pymod6"

__version__ = importlib.metadata.version(DISTRIBUTION_NAME)
