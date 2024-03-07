"""
Utilities for handling quantities expressed using a band model.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import numpy.typing as npt


def combine_at(
    x: npt.ArrayLike,
    indices: npt.ArrayLike,
    axis: int = 0,
    dtype: npt.DTypeLike | None = None,
    out: np.ndarray[Any, Any] | None = None,
) -> np.ndarray[Any, Any]:
    """
    Combine weighted bandmodel components over the slices in `indices`.

    Parameters
    ----------
    x : array-like
        The array to act on.
    indices : array-like
        Paired indices specifying slices to sum over.
    Returns
    -------
    array
        Combined spectrum.

    Examples
    --------
    >>> var1 = np.array([0.50, 0.50,   0.25, 0.25, 0.25,  0.25,    0.33, 0.33, 0.34])
    >>> var2 = np.array([0.75, 0.25,   0.50, 0.25, 0.125, 0.125,   0.50, 0.25, 0.25])
    >>> combine_at(var1, [0, 2, 6])
    array([1., 1., 1.])
    >>> combine_at(var2, [0, 2, 6])
    array([1., 1., 1.])
    >>> combine_at(np.stack((var1, var2), axis=-1), [0, 2, 6])
    array([[1., 1.],
           [1., 1.],
           [1., 1.]])
    >>> combine_at(np.stack((var1, var2), axis=0), [0, 2, 6], axis=1)
    array([[1., 1., 1.],
           [1., 1., 1.]])
    """
    return np.add.reduceat(x, indices, axis, dtype, out)  # type: ignore


def combine_by_k_int(
    x: npt.ArrayLike,
    k_int: npt.ArrayLike,
    axis: int = 0,
    dtype: npt.DTypeLike | None = None,
    out: np.ndarray[Any, Any] | None = None,
) -> np.ndarray[Any, Any]:
    """
    Combine weighted bandmodel components using intra-band indices `k_int`.

    Parameters
    ----------
    x : array-like
        The array to act on.
    k_int : array-like
        Intra-band indices, progressing from 1 to N within each modelled band.
    Returns
    -------
    array
        Combined spectrum.

    Examples
    --------
    >>> var1 = np.array([0.50, 0.50,   0.25, 0.25, 0.25,  0.25,    0.33, 0.33, 0.34])
    >>> var2 = np.array([0.75, 0.25,   0.50, 0.25, 0.125, 0.125,   0.50, 0.25, 0.25])
    >>> k_int = np.array([  1,    2,      1,    2,     3,     4,      1,    2,    3])
    >>> combine_by_k_int(var1, k_int)
    array([1., 1., 1.])
    >>> combine_by_k_int(var2, k_int)
    array([1., 1., 1.])
    >>> combine_by_k_int(np.stack((var1, var2), axis=-1), k_int)
    array([[1., 1.],
           [1., 1.],
           [1., 1.]])
    >>> combine_by_k_int(np.stack((var1, var2), axis=0), k_int, axis=1)
    array([[1., 1., 1.],
           [1., 1., 1.]])

    """
    (indices,) = np.nonzero(np.ravel(k_int) == 1)
    return combine_at(x, indices, axis, dtype, out)


def check_k_int(k_int: npt.ArrayLike) -> bool:
    """
    Check whether the given array consists of piecewise integer
    progressions that start from 1.

    This structure for ``k_int`` is assumed by ``combine_by_k_int``.

    >>> check_k_int([1, 2, 3])
    True
    >>> check_k_int([1, 2, 3, 1, 2, 3, 4])
    True
    >>> check_k_int([1, 2, 3, 2, 3, 4])
    False
    """
    flat = np.ravel(k_int)
    starts = np.empty(flat.shape, dtype=bool)
    starts[0] = True
    starts[1:] = np.diff(flat) != 1
    return np.all(flat[starts] == 1)  # type: ignore
