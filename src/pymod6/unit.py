"""
Unit conversion utilities.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar, Final, Generic, Literal, TypeVar, Union

import numpy as np
from typing_extensions import TypeAlias

_SCALE_PREFIX: TypeAlias = Literal[
    "P", "T", "G", "M", "k", "-", "c", "m", "u", "n", "p"
]

_SCALE_PREFIX_FREQUENCY: TypeAlias = Union[
    _SCALE_PREFIX,
    Literal[
        "PHz", "THz", "GHz", "MHz", "kHz", "-Hz", "cHz", "mHz", "uHz", "nHz", "pHz"
    ],
]

_SCALE_PREFIX_WAVELENGTH: TypeAlias = Union[
    _SCALE_PREFIX,
    Literal["Pm", "Tm", "Gm", "Mm", "km", "-m", "cm", "mm", "um", "nm", "pm"],
]

_SCALE_PREFIX_WAVENUMBER: TypeAlias = Union[
    _SCALE_PREFIX,
    Literal[
        "Pm-1",
        "Tm-1",
        "Gm-1",
        "Mm-1",
        "km-1",
        "-m-1",
        "cm-1",
        "mm-1",
        "um-1",
        "nm-1",
        "pm-1",
    ],
]

_T = TypeVar("_T", float, np.ndarray[Any, np.dtype[np.floating[Any]]])

_S = TypeVar(
    "_S",
    _SCALE_PREFIX_FREQUENCY,
    _SCALE_PREFIX_WAVELENGTH,
    _SCALE_PREFIX_WAVENUMBER,
)

SPEED_OF_LIGHT: Final[float] = 299792458.0

_BASE_SCALES: Final[dict[_SCALE_PREFIX, float]] = {
    "P": 1e15,
    "T": 1e12,
    "G": 1e9,
    "M": 1e6,
    "k": 1e3,
    "-": 1e0,
    "c": 1e-2,
    "m": 1e-3,
    "u": 1e-6,
    "n": 1e-9,
    "p": 1e-12,
}


@dataclass
class _FrequencyMeasure(Generic[_T, _S]):
    value: _T

    __slots__ = ("value",)

    _SCALE_SUFFIX: ClassVar[str]
    _SCALES: ClassVar[dict[str, float]]

    def __init__(self, value: _T, scale: _S) -> None:
        self.value = value * self._SCALES[scale]

    def __init_subclass__(cls, suffix: str = "", **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        cls._SCALE_SUFFIX = suffix
        cls._SCALES = {
            **_BASE_SCALES,  # type: ignore[dict-item]
            **{f"{p}{suffix}": v for p, v in _BASE_SCALES.items()},
        }

    def as_frequency(self, scale: _SCALE_PREFIX_FREQUENCY) -> _T:
        raise NotImplementedError

    def as_wavelength(self, scale: _SCALE_PREFIX_WAVELENGTH) -> _T:
        raise NotImplementedError

    def as_wavenumber(self, scale: _SCALE_PREFIX_WAVENUMBER) -> _T:
        raise NotImplementedError


class Frequency(_FrequencyMeasure[_T, _SCALE_PREFIX_FREQUENCY], suffix="Hz"):
    """
    Frequency measurement.

    >>> round(Frequency(120, "THz").as_wavelength("um"), 2)
    2.5
    >>> round(Frequency(120, "THz").as_wavenumber("cm-1"), -1)
    4000.0
    >>> round(Frequency(2.4, "GHz").as_wavelength("cm"), 1)
    12.5
    >>> round(Frequency(2.4, "GHz").as_wavenumber("cm-1"), 3)
    0.08
    >>> Frequency(1.25, "MHz").as_frequency("kHz")
    1250.0
    """

    def as_frequency(self, scale: _SCALE_PREFIX_FREQUENCY) -> _T:
        return self.value / self._SCALES[scale]

    def as_wavelength(self, scale: _SCALE_PREFIX_WAVELENGTH) -> _T:
        return SPEED_OF_LIGHT / self.value / Wavelength._SCALES[scale]

    def as_wavenumber(self, scale: _SCALE_PREFIX_WAVENUMBER) -> _T:
        return self.value / SPEED_OF_LIGHT * Wavenumber._SCALES[scale]


class Wavelength(_FrequencyMeasure[_T, _SCALE_PREFIX_WAVELENGTH], suffix="m"):
    """
    Wavelength measurement.

    >>> round(Wavelength(2.5, "um").as_frequency("THz"), 0)
    120.0
    >>> round(Wavelength(2.5, "um").as_wavenumber("cm-1"), 12)
    4000.0
    >>> round(Wavelength(12.5, "cm").as_frequency("GHz"), 2)
    2.4
    >>> round(Wavelength(12.5, "cm").as_wavenumber("cm-1"), 12)
    0.08
    >>> round(Wavelength(4000, "nm").as_wavelength("um"), 12)
    4.0
    """

    def as_frequency(self, scale: _SCALE_PREFIX_FREQUENCY) -> _T:
        return SPEED_OF_LIGHT / self.value / Frequency._SCALES[scale]

    def as_wavelength(self, scale: _SCALE_PREFIX_WAVELENGTH) -> _T:
        return self.value / self._SCALES[scale]

    def as_wavenumber(self, scale: _SCALE_PREFIX_WAVENUMBER) -> _T:
        return 1 / self.value * Wavenumber._SCALES[scale]


class Wavenumber(_FrequencyMeasure[_T, _SCALE_PREFIX_WAVENUMBER], suffix="m-1"):
    """
    Wavenumber measurement.

    >>> round(Wavenumber(4000, "cm-1").as_wavelength("um"), 12)
    2.5
    >>> round(Wavenumber(4000, "cm-1").as_frequency("THz"), 0)
    120.0
    >>> round(Wavenumber(0.08, "cm-1").as_wavelength("cm"), 12)
    12.5
    >>> round(Wavenumber(0.08, "cm-1").as_frequency("GHz"), 2)
    2.4
    >>> Wavenumber(4000, "cm-1").as_wavenumber("mm-1")
    400.0
    """

    # noinspection PyMissingConstructor
    def __init__(self, value: _T, scale: _SCALE_PREFIX_WAVENUMBER) -> None:
        self.value = value / self._SCALES[scale]

    def as_frequency(self, scale: _SCALE_PREFIX_FREQUENCY) -> _T:
        return SPEED_OF_LIGHT * self.value / Frequency._SCALES[scale]

    def as_wavelength(self, scale: _SCALE_PREFIX_WAVELENGTH) -> _T:
        return 1 / self.value / Wavelength._SCALES[scale]

    def as_wavenumber(self, scale: _SCALE_PREFIX_WAVENUMBER) -> _T:
        return self.value * self._SCALES[scale]
