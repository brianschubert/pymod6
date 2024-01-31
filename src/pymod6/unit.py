"""
Unit conversion utilities.

These utilities are strictly typed-hinted so that most argument issues become static
type errors instead of potential runtime errors. For example, attempting to use a
frequency measurement with an invalid unit like ``Frequency(1, "um")`` can be detected
as a type error by static analysis tools (mypy, pyright, PyCharm, ...).
"""

from __future__ import annotations

import abc
from dataclasses import dataclass
from typing import Any, ClassVar, Final, Generic, Literal, TypeVar, Union

import numpy as np
from typing_extensions import TypeAlias

_SCALE_PREFIX: TypeAlias = Literal[
    "P", "T", "G", "M", "k", "-", "c", "m", "u", "n", "p"
]

_UNIT_FREQUENCY: TypeAlias = Union[
    _SCALE_PREFIX,
    Literal[
        "PHz", "THz", "GHz", "MHz", "kHz", "-Hz", "cHz", "mHz", "uHz", "nHz", "pHz"
    ],
]

_UNIT_WAVELENGTH: TypeAlias = Union[
    _SCALE_PREFIX,
    Literal["Pm", "Tm", "Gm", "Mm", "km", "-m", "cm", "mm", "um", "nm", "pm"],
]

_UNIT_WAVENUMBER: TypeAlias = Union[
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


SPEED_OF_LIGHT: Final[float] = 299792458.0
"""Speed of light in a vacuum in meters per second."""

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


@dataclass(init=False, order=True)
class _FrequencyMeasure(abc.ABC, Generic[_T]):
    _value: _T

    # Using slots for marginal construction speed-up.
    __slots__ = ("_value",)

    _SCALES: ClassVar[dict[str, float]]

    def __init_subclass__(cls, unit_suffix: str = "", **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        cls._SCALES = {
            **_BASE_SCALES,  # type: ignore[dict-item]
            **{f"{p}{unit_suffix}": v for p, v in _BASE_SCALES.items()},
        }

    # Note: to avoid performance penalties, we should avoid nested function calls
    # and unnecessary computations. This means that each conversion should be
    # implemented directly instead of implementing some in terms of others.

    @abc.abstractmethod
    def as_frequency(self, unit: _UNIT_FREQUENCY) -> _T:
        """Convert to a frequency with the given unit."""

    @abc.abstractmethod
    def as_wavelength(self, unit: _UNIT_WAVELENGTH) -> _T:
        """Convert to a wavelength with the given unit."""

    @abc.abstractmethod
    def as_wavenumber(self, unit: _UNIT_WAVENUMBER) -> _T:
        """Convert to a wavenumber with the given unit."""


class Frequency(_FrequencyMeasure[_T], unit_suffix="Hz"):
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

    def __init__(self, value: _T, scale: _UNIT_FREQUENCY) -> None:
        self._value = value * self._SCALES[scale]

    def as_frequency(self, unit: _UNIT_FREQUENCY) -> _T:
        return self._value / self._SCALES[unit]

    def as_wavelength(self, unit: _UNIT_WAVELENGTH) -> _T:
        return SPEED_OF_LIGHT / self._value / Wavelength._SCALES[unit]

    def as_wavenumber(self, unit: _UNIT_WAVENUMBER) -> _T:
        return self._value / SPEED_OF_LIGHT * Wavenumber._SCALES[unit]


class Wavelength(_FrequencyMeasure[_T], unit_suffix="m"):
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

    def __init__(self, value: _T, scale: _UNIT_WAVELENGTH) -> None:
        self._value = value * self._SCALES[scale]

    def as_frequency(self, unit: _UNIT_FREQUENCY) -> _T:
        return SPEED_OF_LIGHT / self._value / Frequency._SCALES[unit]

    def as_wavelength(self, unit: _UNIT_WAVELENGTH) -> _T:
        return self._value / self._SCALES[unit]

    def as_wavenumber(self, unit: _UNIT_WAVENUMBER) -> _T:
        return 1 / self._value * Wavenumber._SCALES[unit]


class Wavenumber(_FrequencyMeasure[_T], unit_suffix="m-1"):
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

    def __init__(self, value: _T, scale: _UNIT_WAVENUMBER) -> None:
        self._value = value / self._SCALES[scale]

    def as_frequency(self, unit: _UNIT_FREQUENCY) -> _T:
        return SPEED_OF_LIGHT * self._value / Frequency._SCALES[unit]

    def as_wavelength(self, unit: _UNIT_WAVELENGTH) -> _T:
        return 1 / self._value / Wavelength._SCALES[unit]

    def as_wavenumber(self, unit: _UNIT_WAVENUMBER) -> _T:
        return self._value * self._SCALES[unit]
