"""
Utilities for handling quantities expressed using a band model.
"""
from typing import Any

import numpy as np
import numpy.typing as npt

# TODO axis handling


def combine_at(x: npt.ArrayLike, indices: npt.ArrayLike) -> np.ndarray[Any, Any]:
    return np.add.reduceat(x, indices)


def combine_by_k_int(x: npt.ArrayLike, k_int: npt.ArrayLike) -> np.ndarray[Any, Any]:
    """
    >>> combine_by_k_int(
    ...     [0.5, 0.5, 0.34, 0.33, 0.33, 0.5, 0.25, 0.125, 0.125],
    ...     [1, 2, 1, 2, 3, 1, 2, 3, 4],
    ... )
    array([1., 1., 1.])

    """
    # TODO check k_int?
    indices = np.nonzero(np.asarray(k_int) == 1)[0]
    return combine_at(x, indices)
