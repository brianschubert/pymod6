import copy
from typing import Final

from .. import unit as _unit
from . import _json

BASE: Final[_json.ModtranInput] = _json.ModtranInput(
    RTOPTIONS=_json.RTOptions(
        IEMSCT=_json.RTExecutionMode.RT_SOLAR_AND_THERMAL,
        MODTRN=_json.RTAlgorithm.RT_MODTRAN,
        IMULT=_json.RTMultipleScattering.RT_DISORT,
        DISALB=True,
        # NSTR=8,
    ),
    SURFACE=_json.Surface(
        SURFTYPE=_json.SurfaceType.REFL_CONSTANT,
        SURREF=1.0,
    ),
    SPECTRAL=_json.Spectral(
        DV=1.0,  # recommended FWHM/2 for Nyquist sampling
        FWHM=2.0,
        LBMNAM="T",
        BMNAME="01_2013",
    ),
)

# https://en.wikipedia.org/wiki/VNIR
VNIR: Final[_json.ModtranInput] = copy.deepcopy(BASE)
VNIR["SPECTRAL"]["V1"] = _unit.Wavelength(1400, "nm").as_wavenumber("cm-1")
VNIR["SPECTRAL"]["V2"] = _unit.Wavelength(400, "nm").as_wavenumber("cm-1")

SWIR: Final[_json.ModtranInput] = copy.deepcopy(BASE)
SWIR["SPECTRAL"]["V1"] = _unit.Wavelength(2500, "nm").as_wavenumber("cm-1")
SWIR["SPECTRAL"]["V2"] = _unit.Wavelength(1400, "nm").as_wavenumber("cm-1")

VNIR_SWIR: Final[_json.ModtranInput] = copy.deepcopy(BASE)
VNIR_SWIR["SPECTRAL"]["V1"] = SWIR["SPECTRAL"]["V1"]
VNIR_SWIR["SPECTRAL"]["V2"] = VNIR["SPECTRAL"]["V2"]

LWIR: Final[_json.ModtranInput] = copy.deepcopy(BASE)
LWIR["SPECTRAL"]["V1"] = _unit.Wavelength(14, "um").as_wavenumber("cm-1")
LWIR["SPECTRAL"]["V2"] = _unit.Wavelength(8, "um").as_wavenumber("cm-1")
