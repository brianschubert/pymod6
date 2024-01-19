from __future__ import annotations

import contextlib
import pathlib
from typing import Any, BinaryIO, ContextManager, TextIO, cast

import numpy as np

from . import _util

_AtmoCorrectDataDType = np.dtype(
    [
        ("freq", "<f4"),
        ("los", "<i4"),
        ("k_int", "<i4"),
        ("k_weight", "<f4"),
        ("sun_gnd_diffuse_transm", "<f4"),
        ("sun_gnd_obs_direct_transm", "<f4"),
        ("obs_gdn_embedded_dif_transm", "<f4"),
        ("obs_gnd_direct_transm", "<f4"),
        ("spherical_albedo", "<f4"),
    ]
)

_AtmoCorrectDataFileDtype = np.dtype(
    [
        ("_delim1", "B", 4),
        ("data", _AtmoCorrectDataDType),
        ("_delim2", "B", 4),
    ]
)


def read_acd_text(file: pathlib.Path | TextIO) -> np.ndarray[Any, Any]:
    return np.loadtxt(file, skiprows=5, dtype=_AtmoCorrectDataDType)


def read_acd_binary(file: pathlib.Path | BinaryIO) -> np.ndarray[Any, Any]:
    cm: ContextManager[BinaryIO]
    if _util.is_binary_io(file):
        cm = contextlib.nullcontext(file)
    else:
        cm = open(cast("str | pathlib.Path", file), "rb")

    with cm as fd:
        buffer = fd.read()

    contents = np.frombuffer(
        buffer,
        offset=_AtmoCorrectDataFileDtype.itemsize,
        dtype=_AtmoCorrectDataFileDtype,
    )

    return contents["data"]
