"""
Output file I/O.
"""

from __future__ import annotations

import contextlib
import pathlib
import struct
from typing import Any, BinaryIO, ContextManager, Final, Literal, TextIO, cast, overload

import numpy as np
import spectral.io.envi  # type: ignore[import-untyped]
import xarray as xr
from numpy import typing as npt

from pymod6 import _util, input

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
    """
    Read ASCII atmospheric correction data file.

    :param file: File name or file-like object to read.
    :param dtype: Desired datatype. Defaults to structure with mixed integers and
        floats. Set to "f4" for homogenous float outputs.
    :return: ACD date as numpy array.
    """
    return np.loadtxt(file, skiprows=5, dtype=dtype)


@overload
def read_acd_binary(
    file: str | pathlib.Path | BinaryIO,
    *,
    return_algorithm: Literal[False],
) -> np.ndarray[Any, Any]:
    ...


@overload
def read_acd_binary(
    file: str | pathlib.Path | BinaryIO,
    *,
    return_algorithm: Literal[True],
) -> tuple[np.ndarray[Any, Any], input.RTAlgorithm]:
    ...


@overload
def read_acd_binary(
    file: str | pathlib.Path | BinaryIO,
) -> np.ndarray[Any, Any]:
    ...


def read_acd_binary(
    file: str | pathlib.Path | BinaryIO,
    *,
    return_algorithm: bool = False,
) -> np.ndarray[Any, Any] | tuple[np.ndarray[Any, Any], input.RTAlgorithm]:
    """
    Read binary atmospheric correction data file.

    Reading binary ACD files is ~140 times faster than reading the text version. The
    binary ACD files also contain full 32-bit float values instead values rounded to
    four decimal places.

    :param file: File name or file-like object to read.
    :param return_algorithm: Whether to return the detected value of RTOPTIONS.MODTRN
        used to generate the ACD file.
    :return: ACD data as numpy array, or tuple containing the ACD data and the
        algorithm indicator.
    """
    # TODO handle multiple cases in one file?
    cm: ContextManager[BinaryIO]
    if _util.is_binary_io(file):
        cm = contextlib.nullcontext(file)
    else:
        cm = open(cast("str | pathlib.Path", file), "rb")

    with cm as fd:
        buffer = fd.read()

    # Check header row contents.
    header = struct.unpack("ifiiiiiiiii", buffer[: _AtmoCorrectDataFileDtype.itemsize])
    header_checks = (
        (header[0] == ord("$"), "expected first word to be $"),
        (header[1] == -9999.0, "expected -9999.0 sentinel in second word"),
        (header[2] == 0, "expected third word to be 0"),
        (
            header[3] in (0x01, 0x11, 0x21, 0x64),
            "expected fourth word to be in (0x01, 0x11, 0x21, 0x64)",
        ),
        (all(b == 0 for b in header[4:-2]), "expected words [4:-2] to be zero"),
        (header[-1] == ord("$"), "expected last word to be $"),
    )
    for check_flag, fail_message in header_checks:
        if not check_flag:
            raise ValueError(
                f"bad header - {fail_message}: {buffer[: _AtmoCorrectDataFileDtype.itemsize].hex(':', bytes_per_sep=4)}"
            )

    contents = np.frombuffer(
        buffer,
        offset=_AtmoCorrectDataFileDtype.itemsize,
        dtype=_AtmoCorrectDataFileDtype,
    )
    data = contents["data"]
    k_int = header[3]

    # Sanity check - examine start and end word of first and law row.
    check_delims = (
        (contents[0]["_delim1"], contents[0]["_delim2"]),
        (contents[-1]["_delim1"], contents[-1]["_delim2"]),
    )
    if check_delims != ((0x24, 0x24), (0x24, 0x24)):
        raise ValueError(
            f"got unexpected word(s) in (first, last)-row delimiter columns: {check_delims}"
        )

    # # Sanity check - examine k_int progression if correlated-k was used.
    if k_int > 1:
        expected_k_progression = np.arange(1, k_int + 1)
        leading_progression = data[:k_int]["k_int"]
        trailing_progression = data[-k_int:]["k_int"]
        if np.any(leading_progression != expected_k_progression) or np.any(
            trailing_progression != expected_k_progression
        ):
            raise ValueError(
                f"unexpected k_int progression: expected {expected_k_progression}..., got {leading_progression}...{trailing_progression}"
            )

    if return_algorithm:
        algo_lookup = {
            1: input.RTAlgorithm.RT_MODTRAN,  # or RT_MODTRAN_POLAR
            17: input.RTAlgorithm.RT_CORRK_FAST,
            33: input.RTAlgorithm.RT_CORRK_SLOW,
            100: input.RTAlgorithm.RT_LINE_BY_LINE,
        }
        return data, algo_lookup[k_int]

    return data


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
