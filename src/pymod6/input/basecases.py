"""
Prototypes for common input cases.

This module defines partially-specified case-input dictionaries for common sets of
input parameters. These parts can be combined into a complete input case using
`pymod6.input.merge_case_parts`. For example:
```python
base_case = merge_case_parts(
    RTOPTIONS_COMMON,
    SURFACE_REFL_CONST_1,
    SPECTRAL_VNIR,
)
````

.. warning::
    Be careful not accidentally mutate these base cases. Always make a *deep copy*
    of a base case before modifying it:

    >>> import copy
    >>> from pymod6.input.basecases import BASE_0
    >>> my_base_case = copy.deepcopy(BASE_0)
    >>> my_base_case[...] = ...

See Also
--------
pymod6.input.merge_case_parts
pymod6.input.ModtranInputBuilder
"""

from typing import Final

from pymod6 import unit as _unit
from pymod6.input import _util as _input_util
from pymod6.input import schema as _schema

RTOPTIONS_COMMON: Final[_schema.CaseInput] = _schema.CaseInput(
    RTOPTIONS=_schema.RTOptions(
        IEMSCT=_schema.RTExecutionMode.RT_SOLAR_AND_THERMAL,
        MODTRN=_schema.RTAlgorithm.RT_MODTRAN,
        IMULT=_schema.RTMultipleScattering.RT_DISORT,
        DISALB=True,
        # NSTR=8,
    ),
)
"""Common RTOPTIONS."""

SURFACE_REFL_CONST_0: Final[_schema.CaseInput] = _schema.CaseInput(
    SURFACE=_schema.Surface(
        SURFTYPE=_schema.SurfaceType.REFL_CONSTANT,
        SURREF=0.0,
    ),
)
"""Surface with constant reflectance of 0."""

SURFACE_REFL_CONST_1: Final[_schema.CaseInput] = _schema.CaseInput(
    SURFACE=_schema.Surface(
        SURFTYPE=_schema.SurfaceType.REFL_CONSTANT,
        SURREF=1.0,
    ),
)
"""Surface with constant reflectance of 1."""


# --- Spectral bands

# https://en.wikipedia.org/wiki/VNIR
SPECTRAL_VNIR: Final[_schema.CaseInput] = _schema.CaseInput(
    SPECTRAL=_schema.Spectral(
        V1=round(_unit.Wavelength(1400, "nm").as_wavenumber("cm-1"), 0),
        V2=round(_unit.Wavelength(400, "nm").as_wavenumber("cm-1"), 0),
    )
)
"""
Visible and near-infrared (VNIR), 400-1400nm.

SPECTRAL.{V1,V2} are given in wavenumbers. This assume that SPECTRAL.FLAGS[0] is blank
or "W".
"""


SPECTRAL_SWIR: Final[_schema.CaseInput] = _schema.CaseInput(
    SPECTRAL=_schema.Spectral(
        V1=round(_unit.Wavelength(2500, "nm").as_wavenumber("cm-1"), 0),
        V2=round(_unit.Wavelength(1400, "nm").as_wavenumber("cm-1"), 0),
    )
)
"""
Short-wavelength infrared (SWIR), 1400-2500nm.

SPECTRAL.{V1,V2} are given in wavenumbers. This assume that SPECTRAL.FLAGS[0] is blank
or "W".
"""


SPECTRAL_VNIR_SWIR: Final[_schema.CaseInput] = _schema.CaseInput(
    SPECTRAL=_schema.Spectral(
        V1=SPECTRAL_SWIR["SPECTRAL"]["V1"],
        V2=SPECTRAL_VNIR["SPECTRAL"]["V2"],
    )
)
"""
VNIR-SWIR, 400-2500nm.

SPECTRAL.{V1,V2} are given in wavenumbers. This assume that SPECTRAL.FLAGS[0] is blank
or "W".
"""


SPECTRAL_LWIR: Final[_schema.CaseInput] = _schema.CaseInput(
    SPECTRAL=_schema.Spectral(
        V1=round(_unit.Wavelength(14, "um").as_wavenumber("cm-1"), 0),
        V2=round(_unit.Wavelength(8, "um").as_wavenumber("cm-1"), 0),
    )
)
"""
Long-wavelength infrared (LWIR), 8-14um.

SPECTRAL.{V1,V2} are given in wavenumbers. This assume that SPECTRAL.FLAGS[0] is blank
or "W".
"""

# --- Complete base cases.

BASE_0: Final[_schema.CaseInput] = _input_util.merge_case_parts(
    RTOPTIONS_COMMON,
    SURFACE_REFL_CONST_1,
    _input_util.make_case(
        # recommended FWHM/2 for Nyquist sampling
        SPECTRAL__FWHM=2.0,
        SPECTRAL__DV=1.0,
    ),
)
"""Base case consisting is miscellaneous common options."""
