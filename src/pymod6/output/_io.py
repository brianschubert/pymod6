"""
Output file I/O.
"""

from __future__ import annotations

import contextlib
import pathlib
import struct
from typing import Any, BinaryIO, ContextManager, Final, TextIO, cast

import numpy as np
import spectral.io.envi  # type: ignore[import-untyped]
import xarray as xr
from numpy import typing as npt

from pymod6 import _util

_AtmoCorrectDataDType: Final = np.dtype(
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
_AtmoCorrectDataFileDtype: Final = np.dtype(
    [
        ("_delim1", "<i4"),
        ("data", _AtmoCorrectDataDType),
        ("_delim2", "<i4"),
    ]
)


def read_acd_text(
    file: pathlib.Path | TextIO, *, dtype: npt.DTypeLike = _AtmoCorrectDataDType
) -> np.ndarray[Any, Any]:
    return np.loadtxt(file, skiprows=5, dtype=dtype)


def read_acd_binary(
    file: str | pathlib.Path | BinaryIO, *, check: bool = False
) -> np.ndarray[Any, Any]:
    # TODO handle multiple cases in one file?
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

    # Run optional sanity checks.
    if check:
        # Check header row contents.
        expected_header = struct.pack(
            "ifiiiiiiiii", ord("$"), -9999.0, 0, 1, 0, 0, 0, 0, 0, 0, ord("$")
        )
        if buffer[: _AtmoCorrectDataFileDtype.itemsize] != expected_header:
            raise ValueError(
                f"invalid header: expected '{expected_header.hex()}',"
                f" got '{buffer[: _AtmoCorrectDataFileDtype.itemsize].hex()}'"
            )

        # Check start and end word of every row.
        delim_words = set(contents["_delim1"]) | set(contents["_delim2"])
        if unexpected_delims := delim_words - {ord("$")}:
            raise ValueError(
                f"got unexpected word(s) in delimiter columns: {unexpected_delims}"
            )

    return contents["data"]


def read_sli(file: str | pathlib.Path) -> xr.Dataset:
    spec_lib = spectral.io.envi.open(file)
    if not isinstance(spec_lib, spectral.io.envi.SpectralLibrary):
        raise ValueError(f"SLI file not a spectral library: {file}")

    return xr.DataArray(
        spec_lib.spectra,
        dims=["output", "wavelength"],
        coords={"output": spec_lib.names, "wavelength": spec_lib.bands.centers},
        attrs=spec_lib.metadata,
    ).to_dataset("output")
