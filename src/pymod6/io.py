"""
I/O for input and output files.
"""

from __future__ import annotations

import contextlib
import json
import pathlib
import re
import struct
from typing import Any, BinaryIO, ContextManager, Final, Literal, TextIO, cast, overload

import numpy as np
import pydantic
import spectral.io.envi  # type: ignore[import-untyped]
import xarray as xr
from numpy import typing as npt

from . import _util
from ._env import ModtranEnv
from .input import _json

AtmoCorrectDataDType: Final = np.dtype(
    [
        ("freq", "<f4"),
        ("los", "<i4"),
        ("k_int", "<i4"),
        ("k_weight", "<f4"),
        ("sun_gnd_diffuse_transm", "<f4"),
        ("sun_gnd_obs_direct_transm", "<f4"),
        ("obs_gnd_embedded_dif_transm", "<f4"),
        ("obs_gnd_direct_transm", "<f4"),
        ("spherical_albedo", "<f4"),
    ]
)
"""Numpy dtype for Atmospheric Correction Data (ACD) outputs."""


Tape7TransmittanceDType: Final = np.dtype(
    [
        ("freq", "<f4"),
        ("combin trans", "<f4"),
        ("H2O trans", "<f4"),
        ("umix trans", "<f4"),
        ("O3 trans", "<f4"),
        ("trace trans", "<f4"),
        ("N2 trans", "<f4"),
        ("H2Ocnt trans", "<f4"),
        ("molec scat", "<f4"),
        ("aercld trans", "<f4"),
        ("HNO3 trans", "<f4"),
        ("aercld abtrns", "<f4"),
        # NOTE: '-log combin' is only present in tape7 output files (text and binary).
        # It is not included in the JSON, SLI, or CSV outputs.
        ("-log combin", "<f4"),
        ("CO2 trans", "<f4"),
        ("CO trans", "<f4"),
        ("CH4 trans", "<f4"),
        ("N2O trans", "<f4"),
        ("O2 trans", "<f4"),
        ("NH3 trans", "<f4"),
        ("NO trans", "<f4"),
        ("NO2 trans", "<f4"),
        ("SO2 trans", "<f4"),
        ("cloud trans", "<f4"),
        ("F11 trans", "<f4"),
        ("F12 trans", "<f4"),
        ("CCl3F trans", "<f4"),
        ("CF4 trans", "<f4"),
        ("F22 trans", "<f4"),
        ("F113 trans", "<f4"),
        ("F114 trans", "<f4"),
        ("F115 trans", "<f4"),
        ("ClONO2 trans", "<f4"),
        ("HNO4 trans", "<f4"),
        ("CHCl2F trans", "<f4"),
        ("CCl4 trans", "<f4"),
        ("N2O5 trans", "<f4"),
        ("H2-H2 trans", "<f4"),
        ("H2-He trans", "<f4"),
        ("H2-CH4 trans", "<f4"),
        ("CH4-CH4 trans", "<f4"),
    ]
)
"""Numpy dtype for spectral *transmittance* outputs (tape7)."""

Tape7RadianceDType: Final = np.dtype(
    [
        ("freq", "<f4"),
        ("total transmittance", "<f4"),
        ("path emission", "<f4"),
        ("path thermal scat", "<f4"),
        ("surface emission", "<f4"),
        ("path multiple scat", "<f4"),
        ("path single scat", "<f4"),
        ("ground reflect", "<f4"),
        ("direct reflect", "<f4"),
        ("total radiance", "<f4"),
        ("reference irradiance", "<f4"),
        ("irradiance at observer", "<f4"),
        ("- nat log path trans", "<f4"),
        ("directional emissivity", "<f4"),
        ("top-of-atmosphere irradiance", "<f4"),
        ("brightness temp", "<f4"),
    ]
)
"""Numpy dtype for spectral *radiance* outputs (tape7)."""

Tape7RadianceThermalOnlyDType: Final = np.dtype(
    [
        ("freq", "<f4"),
        ("total transmittance", "<f4"),
        ("path emission", "<f4"),
        ("path thermal scat", "<f4"),
        ("surface emission", "<f4"),
        # ("path multiple scat", "<f4"),
        # ("path single scat", "<f4"),
        ("ground reflect", "<f4"),
        # ("direct reflect", "<f4"),
        ("total radiance", "<f4"),
        # ("reference irradiance", "<f4"),
        # ("irradiance at observer", "<f4"),
        ("- nat log path trans", "<f4"),
        ("directional emissivity", "<f4"),
        # ("top-of-atmosphere irradiance", "<f4"),
        ("brightness temp", "<f4"),
    ]
)
"""Numpy dtype for *thermal-only* spectral *radiance* outputs (tape7)."""


# Raw file dtypes.

_AtmoCorrectDataFileDtype: Final = np.dtype(
    [
        ("_delim1", "<i4"),
        ("data", AtmoCorrectDataDType),
        ("_delim2", "<i4"),
    ]
)

_Tape7TransmittanceFileDType: Final = np.dtype(
    [
        ("_delim_A0_0", "<u4"),
        ("data", Tape7TransmittanceDType),
        ("_delim_A0_1", "<u4"),
    ]
)

_Tape7RadianceFileDType: Final = np.dtype(
    [
        ("_delim_74_0", "<u4"),
        ("data", Tape7RadianceDType),
        ("_fill_zero_0", "<u4", 11),
        ("_fill_99", "<f4"),
        ("_fill_zero_1", "<u4"),
        ("_delim_74_1", "<u4"),
    ]
)

_Tape7RadianceThermalOnlyFileDType: Final = np.dtype(
    [
        ("_delim_48_0", "<u4"),
        ("data", Tape7RadianceThermalOnlyDType),
        ("_fill_zero_0", "<u4", 6),
        ("_fill_99", "<f4"),
        ("_fill_zero_1", "<u4"),
        ("_delim_48_1", "<u4"),
    ]
)


_Tape7HeaderLength: Final = 0x6F


_COMMENT_PATTERN: Final = re.compile(
    r'#(?:[^\n"]*(!<\\)"[^\n"]*(!<\\)")*[^\n"]*$', flags=re.MULTILINE
)


def read_acd_text(
    file: pathlib.Path | TextIO, *, dtype: npt.DTypeLike = AtmoCorrectDataDType
) -> np.ndarray[Any, Any]:
    """
    Read ASCII atmospheric correction data file (`.acd`).

    Parameters
    ----------
    file : path or file-like
        File name or file-like object to read.
    dtype : optional
        Desired datatype. Defaults to `AtmoCorrectDataDType`, resulting in a structured array output.
        Set to `"f4"` for homogenous float outputs.

    Returns
    -------
    array : numpy.ndarray
        ACD data as numpy array.
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
) -> tuple[np.ndarray[Any, Any], _json.RTAlgorithm]:
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
) -> np.ndarray[Any, Any] | tuple[np.ndarray[Any, Any], _json.RTAlgorithm]:
    """
    Read binary atmospheric correction data file (`_b.acd`).

    Reading binary ACD files is ~140 times faster than reading the text version. The
    binary ACD files also contain full 32-bit float values instead values rounded to
    four decimal places.

    Parameters
    ----------
    file : path or file-like
        File name or file-like object to read.
    return_algorithm : bool, optional
        Whether to return the detected value of RTOPTIONS.MODTRN (pymod6.input.RTOptions.MODTRN) used to generate the ACD file.

    Returns
    -------
    array : numpy.ndarray
        ACD data as numpy array.
    algorithm : pymod6.input.RTAlgorithm, optional
        Inferred `RTAlgorithm` used to generate the ACD data. Only provided if `return_algorithm` is True.
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
            1: _json.RTAlgorithm.RT_MODTRAN,  # or RT_MODTRAN_POLAR
            17: _json.RTAlgorithm.RT_CORRK_FAST,
            33: _json.RTAlgorithm.RT_CORRK_SLOW,
            100: _json.RTAlgorithm.RT_LINE_BY_LINE,
        }
        return data, algo_lookup[k_int]

    return data


def read_sli(file: str | pathlib.Path) -> xr.Dataset:
    """
    Read spectra outputs from ENVI spectral library.

    Parameters
    ----------
    file : file path
        Path to ENVI spectral library header or data file.

    Returns
    -------
    dataset
        Spectra outputs as an [`xarray.Dataset`](https://docs.xarray.dev/en/stable/generated/xarray.Dataset.html).

    """
    spec_lib = spectral.io.envi.open(file)
    if not isinstance(spec_lib, spectral.io.envi.SpectralLibrary):
        raise ValueError(f"SLI file not a spectral library: {file}")

    return xr.DataArray(
        spec_lib.spectra,
        dims=["output", "wavelength"],
        coords={"output": spec_lib.names, "wavelength": spec_lib.bands.centers},
        attrs=spec_lib.metadata,
    ).to_dataset("output")


def read_tape7_binary(
    file: str | pathlib.Path | BinaryIO,
) -> np.ndarray[Any, Any]:
    """
    Read spectra outputs from binary tape7 file (`_b.tp7`).

    Parameters
    ----------
    file : path or file-like
        File name or file-like object to read.

    Returns
    -------
    array : numpy.ndarray
        Spectral outputs as numpy array. The data type will be one of
        `Tape7TransmittanceDType`, `Tape7RadianceDType`, or `Tape7RadianceThermalOnlyDType`,
        depending on which spectral outputs are present.

    """
    cm: ContextManager[BinaryIO]
    if _util.is_binary_io(file):
        cm = contextlib.nullcontext(file)
    else:
        cm = open(cast("str | pathlib.Path", file), "rb")

    with cm as fd:
        buffer = fd.read()

    # Infer spectra type by examining the "row delimiter" word.
    # Each "row" begins and ends with a particular word, which is different for each spectra output type.
    row_delimiter = buffer[_Tape7HeaderLength]
    try:
        # TODO: irradiance support
        inferred_dtype = {
            0x48: _Tape7RadianceThermalOnlyFileDType,
            0x74: _Tape7RadianceFileDType,
            0xA0: _Tape7TransmittanceFileDType,
        }[row_delimiter]
    except KeyError:
        raise ValueError(
            f"unable to determine spectra type - unknown delimiter byte 0x{row_delimiter:x}"
        )

    contents = np.frombuffer(
        buffer,
        offset=_Tape7HeaderLength,
        dtype=inferred_dtype,
    )
    data = contents["data"]

    # Sanity check - examine start and end word of first and law row.
    check_delims = (
        (contents[0][inferred_dtype.names[0]], contents[0][inferred_dtype.names[-1]]),  # type: ignore[index]
        (contents[-1][inferred_dtype.names[0]], contents[-1][inferred_dtype.names[-1]]),  # type: ignore[index]
    )
    if check_delims != ((row_delimiter, row_delimiter), (row_delimiter, row_delimiter)):
        raise ValueError(
            f"got unexpected word(s) in (first, last)-row delimiter columns: {check_delims}"
        )

    return data


def read_json_input(
    s: str, *, strip_comments: bool = False, validate: bool = True
) -> _json.JSONInput:
    """
    Read input JSON file.

    Parameters
    ----------
    s : str
        JSON string.
    strip_comments : bool, optional
        Whether to strip comments after a `#` symbol.
    validate : bool, optional
        Whether to validate the JSON input against the expected input schema.

    Returns
    -------
    pymod6.input.JSONInput
        Dictionary representation of the JSON input file.

    """
    if strip_comments:
        input_dict = json.loads(
            s, cls=_CommentedJSONDecoder, comment_pattern=_COMMENT_PATTERN
        )
    else:
        input_dict = json.loads(s)

    if validate:
        return pydantic.TypeAdapter(_json.JSONInput).validate_python(input_dict)

    return input_dict  # type: ignore


def load_input_defaults(
    mod_data: str | pathlib.Path | None = None,
) -> _json.ModtranInput:
    """
    Load the default JSON keywords from the `keywords.json` file in the MODTRAN
    DATA directory.

    Parameters
    ----------
    mod_data : path, optional
        Path to MODTRAN DATA directory. Defaults to the `MODTRAN_DATA` environment variable.

    Returns
    -------
    pymod6.input.ModtranInput
        Dictionary representation of the JSON input file defaults.
    """
    if mod_data is None:
        mod_data = ModtranEnv.from_environ().data
    else:
        mod_data = pathlib.Path(mod_data)

    with mod_data.joinpath("keywords.json").open("r") as fd:
        raw_dict: dict[str, Any] = json.load(fd)["VALID_MODTRAN"]["MODTRANINPUT"]

    def _marshal_inner(value: dict[str, Any]) -> Any:
        if not isinstance(value, dict):
            return value

        if "ENUM" in value:
            return value["ENUM"]

        if "DEFAULT" in value:
            return value["DEFAULT"]

        return {k: _marshal_inner(v) for k, v in value.items()}

    for key, val in raw_dict.items():
        raw_dict[key] = _marshal_inner(val)

    return pydantic.TypeAdapter(_json.ModtranInput).validate_python(raw_dict)


class _CommentedJSONDecoder(json.JSONDecoder):
    _comment_pattern: re.Pattern[str]

    def __init__(self, comment_pattern: str | re.Pattern[str], **kwargs: Any) -> None:
        self._comment_pattern = re.compile(comment_pattern)
        super().__init__(**kwargs)

    # noinspection PyMethodOverriding
    def decode(self, s: str) -> Any:  # type: ignore[override]
        return super().decode(self._comment_pattern.sub("", s))
