"""
JSON input file schema.

This module defines [`TypedDict`][TypedDict]s for modelling MODTRAN's JSON
input data format. These models allow for better static analysis and code
completion when creating input file structures. At runtime, all of these
classes are represented by plain dictionaries:

>>> JSONInput()
{}
>>> type(JSONInput()) is dict
True

Dictionaries can be validated against these models using [`pydantic`][pydantic].
Simply create a [`pydantic.TypeAdapter`][pydantic.TypeAdapter] for a chosen
model and pass the dictionary you want to validate to the `validate_python`
method:

>>> import pydantic
>>> from pymod6.input.schema import CaseInput
>>> pydantic.TypeAdapter(CaseInput).validate_python(
...     {
...         "SPECTRAL": {"V1": 4000.0, "V2": "wrong type", "V3": "extraneous"}
...     }
... )
Traceback (most recent call last):
...
pydantic_core._pydantic_core.ValidationError: 2 validation errors for typed-dict
SPECTRAL.V2
  Input should be a valid number, unable to parse string as a number [type=float_parsing, input_value='wrong type', input_type=str]
    ...
SPECTRAL.V3
  Extra inputs are not permitted [type=extra_forbidden, input_value='extraneous', input_type=str]
    ...

[TypedDict]: https://docs.python.org/3/library/typing.html#typing.TypedDict
[pydantic]: https://docs.pydantic.dev/latest/
[pydantic.TypeAdapter]: https://docs.pydantic.dev/latest/concepts/type_adapter/

See Also
--------
pymod6.io.read_json_input : Reading inputs from JSON strings
pymod6.io.load_input_defaults : Load input keyword defaults.
"""

from __future__ import annotations

import enum
from typing import Any, Literal, Union

import pydantic
from pydantic import ConfigDict
from typing_extensions import TypedDict

# TODO: update stale exports
__all__ = [
    # JSON input
    "JSONInput",
    "Case",
    "CaseInput",
    "CaseStatus",
    # MODTRANINPUT
    "RTOptions",
    "Atmosphere",
    "Aerosol",
    "Geometry",
    "Surface",
    "Spectral",
    "FileOptions",
    # RTOPTIONS
    "RTAlgorithm",
    "RTExecutionMode",
    "RTMultipleScattering",
    # ATMOSPHERE
    "AtmosphereModel",
    "AtmosphereProfile",
    "AtmosphereProfileType",
    "AtmosphereProfileUnits",
    # AEROSOL
    "AerosolCloud",
    "AerosolHaze",
    "AerosolSeason",
    "AerosolStratospheric",
    # SURFACE
    "SurfaceBRDFModel",
    "SurfaceLambertianModel",
    "SurfaceParam",
    "SurfaceType",
    # FILEOPTIONS
    "JSONPrintOpt",
]


# Inherit from str so that the 'json' module can  serialize it.
# Can be swapped with enum.StrEnum if only Python 3.11+ is targeted.
# See also https://stackoverflow.com/q/24481852
class _StrEnum(str, enum.Enum):
    def __str__(self) -> str:
        return self.value  # type: ignore


@enum.unique
class RTExecutionMode(_StrEnum):
    """Options for RTOptions.IEMSCT"""

    RT_TRANSMITTANCE = "RT_TRANSMITTANCE"
    RT_THERMAL_ONLY = "RT_THERMAL_ONLY"
    RT_SOLAR_AND_THERMAL = "RT_SOLAR_AND_THERMAL"
    RT_SOLAR_IRRADIANCE = "RT_SOLAR_IRRADIANCE"
    RT_LUNAR_AND_THERMAL = "RT_LUNAR_AND_THERMAL"
    RT_LUNAR_IRRADIANCE = "RT_LUNAR_IRRADIANCE"

    @property
    def spectral_output_keyword(
        self,
    ) -> Literal["TRANSMITTANCE", "RADIANCE", "IRRADIANCE"]:
        if self == self.RT_TRANSMITTANCE:
            return "TRANSMITTANCE"
        if self in (self.RT_SOLAR_IRRADIANCE, self.RT_LUNAR_IRRADIANCE):
            return "IRRADIANCE"
        return "RADIANCE"


@enum.unique
class RTAlgorithm(_StrEnum):
    """Options for `RTOptions.MODTRN`."""

    RT_MODTRAN = "RT_MODTRAN"
    RT_CORRK_SLOW = "RT_CORRK_SLOW"
    RT_CORRK_FAST = "RT_CORRK_FAST"
    RT_MODTRAN_POLAR = "RT_MODTRAN_POLAR"
    RT_LINE_BY_LINE = "RT_LINE_BY_LINE"


@enum.unique
class RTMultipleScattering(_StrEnum):
    """Options for `RTOPTIONS.IMULT`."""

    RT_NO_MULTIPLE_SCATTER = "RT_NO_MULTIPLE_SCATTER"
    RT_DISORT = "RT_DISORT"
    RT_DISORT_AT_OBS = "RT_DISORT_AT_OBS"
    RT_ISAACS_2STREAM = "RT_ISAACS_2STREAM"
    RT_ISAACS_2STREAM_AT_OBS = "RT_ISAACS_2STREAM_AT_OBS"
    RT_ISAACS_SCALED = "RT_ISAACS_SCALED"
    RT_ISAACS_SCALED_AT_OBS = "RT_ISAACS_SCALED_AT_OBS"


@enum.unique
class AtmosphereModel(_StrEnum):
    """Options for `Atmosphere.MODEL`."""

    ATM_CONSTANT = "ATM_CONSTANT"
    ATM_TROPICAL = "ATM_TROPICAL"
    ATM_MIDLAT_SUMMER = "ATM_MIDLAT_SUMMER"
    ATM_MIDLAT_WINTER = "ATM_MIDLAT_WINTER"
    ATM_SUBARC_SUMMER = "ATM_SUBARC_SUMMER"
    ATM_SUBARC_WINTER = "ATM_SUBARC_WINTER"
    ATM_US_STANDARD_1976 = "ATM_US_STANDARD_1976"
    ATM_USER_ALT_PROFILE = "ATM_USER_ALT_PROFILE"
    ATM_USER_PRESS_PROFILE = "ATM_USER_PRESS_PROFILE"


@enum.unique
class AtmosphereProfileType(_StrEnum):
    """Options for `AtmosphereProfile.TYPE`."""

    PROF_UNKNOWN = "PROF_UNKNOWN"

    PROF_USER_DEF = "PROF_USER_DEF"
    PROF_ALTITUDE = "PROF_ALTITUDE"
    PROF_PRESSURE = "PROF_PRESSURE"
    PROF_TEMPERATURE = "PROF_TEMPERATURE"

    PROF_H2O = "PROF_H2O"
    PROF_WATER_VAPOR = "PROF_WATER_VAPOR"

    PROF_CO2 = "PROF_CO2"
    PROF_CARBON_DIOXIDE = "PROF_CARBON_DIOXIDE"

    PROF_O3 = "PROF_O3"
    PROF_OZONE = "PROF_OZONE"

    PROF_N2O = "PROF_N2O"
    PROF_NITROUS_OXIDE = "PROF_NITROUS_OXIDE"

    PROF_CO = "PROF_CO"
    PROF_CARBON_MONOXIDE = "PROF_CARBON_MONOXIDE"

    PROF_CH4 = "PROF_CH4"
    PROF_METHANE = "PROF_METHANE"

    PROF_O2 = "PROF_O2"
    PROF_OXYGEN = "PROF_OXYGEN"

    PROF_NO = "PROF_NO"
    PROF_NITRIC_OXIDE = "PROF_NITRIC_OXIDE"

    PROF_SO2 = "PROF_SO2"
    PROF_SULFUR_DIOXIDE = "PROF_SULFUR_DIOXIDE"
    PROF_SULPHUR_DIOXIE = "PROF_SULPHUR_DIOXIE"

    PROF_NO2 = "PROF_NO2"
    PROF_NITROGEN_DIOXIDE = "PROF_NITROGEN_DIOXIDE"

    PROF_NH3 = "PROF_NH3"
    PROF_AMMONIA = "PROF_AMMONIA"

    PROF_HNO3 = "PROF_HNO3"
    PROF_NITRIC_ACID = "PROF_NITRIC_ACID"

    PROF_CCl3F = "PROF_CCl3F"
    PROF_F11 = "PROF_F11"
    PROF_CFC11 = "PROF_CFC11"

    PROF_CCl2F2 = "PROF_CCl2F2"
    PROF_F12 = "PROF_F12"
    PROF_CFC12 = "PROF_CFC12"

    PROF_CClF3 = "PROF_CClF3"
    PROF_CFC13 = "PROF_CFC13"
    PROF_F13 = "PROF_F13"

    PROF_CF4 = "PROF_CF4"
    PROF_F14 = "PROF_F14"
    PROF_CFC14 = "PROF_CFC14"

    PROF_CHClF2 = "PROF_CHClF2"
    PROF_F22 = "PROF_F22"
    PROF_CFC22 = "PROF_CFC22"

    PROF_C2Cl3F3 = "PROF_C2Cl3F3"
    PROF_F113 = "PROF_F113"
    PROF_CFC113 = "PROF_CFC113"

    PROF_C2Cl2F4 = "PROF_C2Cl2F4"
    PROF_F114 = "PROF_F114"
    PROF_CFC114 = "PROF_CFC114"

    PROF_C2ClF5 = "PROF_C2ClF5"
    PROF_F115 = "PROF_F115"
    PROF_CFC115 = "PROF_CFC115"

    PROF_ClONO2 = "PROF_ClONO2"
    PROF_HNO4 = "PROF_HNO4"
    PROF_CHCl2F = "PROF_CHCl2F"
    PROF_CCl4 = "PROF_CCl4"
    PROF_N2O5 = "PROF_N2O5"
    PROF_AHAZE = "PROF_AHAZE"
    PROF_AHAZE2 = "PROF_AHAZE2"
    PROF_AHAZE3 = "PROF_AHAZE3"
    PROF_AHAZE4 = "PROF_AHAZE4"
    PROF_EQLWCZ = "PROF_EQLWCZ"
    PROF_RRATZ = "PROF_RRATZ"
    PROF_IHA = "PROF_IHA"
    PROF_ICLD = "PROF_ICLD"
    PROF_IVUL = "PROF_IVUL"
    PROF_ISEA = "PROF_ISEA"
    PROF_ICHR = "PROF_ICHR"


@enum.unique
class AtmosphereProfileUnits(_StrEnum):
    """Options for `AtmosphereProfile.UNITS`."""

    UNT_UNKNOWN = "UNT_UNKNOWN"
    UNT_KILOMETERS = "UNT_KILOMETERS"
    UNT_TKELVIN = "UNT_TKELVIN"
    UNT_TCELSIUS = "UNT_TCELSIUS"
    UNT_TDELTA_KELVIN = "UNT_TDELTA_KELVIN"
    UNT_TDEWPOINT_KELVIN = "UNT_TDEWPOINT_KELVIN"
    UNT_TDEWPOINT_CELSIUS = "UNT_TDEWPOINT_CELSIUS"
    UNT_PMILLIBAR = "UNT_PMILLIBAR"
    UNT_PATM = "UNT_PATM"
    UNT_DPPMV = "UNT_DPPMV"
    UNT_DMOL_PER_CM3 = "UNT_DMOL_PER_CM3"
    UNT_DGRAM_PER_KG = "UNT_DGRAM_PER_KG"
    UNT_DGRAM_PER_M3 = "UNT_DGRAM_PER_M3"
    UNT_REL_HUMIDITY = "UNT_REL_HUMIDITY"


@enum.unique
class AerosolHaze(_StrEnum):
    """Options for `Aerosol.IHAZE`."""

    AER_NONE = "AER_NONE"
    AER_RURAL = "AER_RURAL"
    AER_RURAL_DENSE = "AER_RURAL_DENSE"
    AER_MARITIME_NAVY = "AER_MARITIME_NAVY"
    AER_MARITIME = "AER_MARITIME"
    AER_URBAN = "AER_URBAN"
    AER_TROPOSPHERIC = "AER_TROPOSPHERIC"
    AER_USER_DEFINED = "AER_USER_DEFINED"
    AER_FOG_ADVECTIVE = "AER_FOG_ADVECTIVE"
    AER_FOG_RADIATIVE = "AER_FOG_RADIATIVE"
    AER_DESERT = "AER_DESERT"


@enum.unique
class AerosolSeason(_StrEnum):
    """Options for `Aerosol.ISEASN`."""

    SEASN_AUTO = "SEASN_AUTO"
    SEASN_SPRING_SUMMER = "SEASN_SPRING_SUMMER"
    SEASN_FALL_WINTER = "SEASN_FALL_WINTER"


@enum.unique
class AerosolStratospheric(_StrEnum):
    """Options for `Aerosol.VULCN`."""

    STRATO_BACKGROUND = "STRATO_BACKGROUND"
    STRATO_MODERATE_VOLCANIC_AGED = "STRATO_MODERATE_VOLCANIC_AGED"
    STRATO_HIGH_VOLCANIC_FRESH = "STRATO_HIGH_VOLCANIC_FRESH"
    STRATO_HIGH_VOLCANIC_AGED = "STRATO_HIGH_VOLCANIC_AGED"
    STRATO_MODERATE_VOLCANIC_FRESH = "STRATO_MODERATE_VOLCANIC_FRESH"
    STRATO_MODERATE_VOLCANIC_BACKGROUND = "STRATO_MODERATE_VOLCANIC_BACKGROUND"
    STRATO_HIGH_VOLCANIC_BACKGROUND = "STRATO_HIGH_VOLCANIC_BACKGROUND"
    STRATO_EXTREME_VOLCANIC_FRESH = "STRATO_EXTREME_VOLCANIC_FRESH"


@enum.unique
class AerosolCloud(_StrEnum):
    """Options for `Aerosol.ICLD`."""

    CLOUD_NONE = "CLOUD_NONE"
    CLOUD_CUMULUS = "CLOUD_CUMULUS"
    CLOUD_ALTOSTRATUS = "CLOUD_ALTOSTRATUS"
    CLOUD_STRATUS = "CLOUD_STRATUS"
    CLOUD_STRATOCUMULUS = "CLOUD_STRATOCUMULUS"
    CLOUD_NIMBOSTRATUS = "CLOUD_NIMBOSTRATUS"
    CLOUD_RAIN_DRIZZLE = "CLOUD_RAIN_DRIZZLE"
    CLOUD_RAIN_LIGHT = "CLOUD_RAIN_LIGHT"
    CLOUD_RAIN_MODERATE = "CLOUD_RAIN_MODERATE"
    CLOUD_RAIN_HEAVY = "CLOUD_RAIN_HEAVY"
    CLOUD_RAIN_EXTREME = "CLOUD_RAIN_EXTREME"
    CLOUD_USER_DEFINED = "CLOUD_USER_DEFINED"
    CLOUD_CIRRUS = "CLOUD_CIRRUS"
    CLOUD_CIRRUS_THIN = "CLOUD_CIRRUS_THIN"


@enum.unique
class SurfaceType(_StrEnum):
    """Options for `Surface.SURFTYPE`."""

    REFL_CONSTANT = "REFL_CONSTANT"
    REFL_LAMBER_MODEL = "REFL_LAMBER_MODEL"
    REFL_BRDF = "REFL_BRDF"


@enum.unique
class SurfaceBRDFModel(_StrEnum):
    """Options for `SurfaceParam.CBRDF`."""

    BRDF_WALTHALL = "BRDF_WALTHALL"
    BRDF_WALTHALL_ANALYTIC = "BRDF_WALTHALL_ANALYTIC"
    BRDF_WALTHALL_SINE = "BRDF_WALTHALL_SINE"
    BRDF_WALTHALL_SINE_ANALYTIC = "BRDF_WALTHALL_SINE_ANALYTIC"
    BRDF_HAPKE = "BRDF_HAPKE"
    BRDF_RAHMAN = "BRDF_RAHMAN"
    BRDF_ROUJEAN = "BRDF_ROUJEAN"
    BRDF_PINTY_VERSTRAETE = "BRDF_PINTY_VERSTRAETE"
    BRDF_ROSS_LI = "BRDF_ROSS_LI"
    BRDF_ROSS_SEA = "BRDF_ROSS_SEA"


@enum.unique
class SurfaceLambertianModel(_StrEnum):
    """Options for `SurfaceParam.CSALB`."""

    LAMB_MODEL_USER_DEF = "LAMB_MODEL_USER_DEF"
    LAMB_SNOW_COVER = "LAMB_SNOW_COVER"
    LAMB_FOREST = "LAMB_FOREST"
    LAMB_FARM = "LAMB_FARM"
    LAMB_DESERT = "LAMB_DESERT"
    LAMB_OCEAN = "LAMB_OCEAN"
    LAMB_CLOUD_DECK = "LAMB_CLOUD_DECK"
    LAMB_OLD_GRASS = "LAMB_OLD_GRASS"
    LAMB_DECAYED_GRASS = "LAMB_DECAYED_GRASS"
    LAMB_MAPLE_LEAF = "LAMB_MAPLE_LEAF"
    LAMB_BURNT_GRASS = "LAMB_BURNT_GRASS"
    LAMB_CONST_0_PCT = "LAMB_CONST_0_PCT"
    LAMB_CONST_5_PCT = "LAMB_CONST_5_PCT"
    LAMB_CONST_50_PCT = "LAMB_CONST_50_PCT"
    LAMB_CONST_80_PCT = "LAMB_CONST_80_PCT"
    LAMB_CONST_30_PCT = "LAMB_CONST_30_PCT"
    LAMB_CONST_10_PCT = "LAMB_CONST_10_PCT"
    LAMB_CONST_100_PCT = "LAMB_CONST_100_PCT"
    LAMB_SEA_ICE_CCM3 = "LAMB_SEA_ICE_CCM3"
    LAMB_CONIFER = "LAMB_CONIFER"
    LAMB_OLIVE_GLOSS_PAINT = "LAMB_OLIVE_GLOSS_PAINT"
    LAMB_DECIDUOUS_TREE = "LAMB_DECIDUOUS_TREE"
    LAMB_SANDY_LOAM = "LAMB_SANDY_LOAM"
    LAMB_GRANITE = "LAMB_GRANITE"
    LAMB_GALVANIZED_STEEL = "LAMB_GALVANIZED_STEEL"
    LAMB_GRASS = "LAMB_GRASS"
    LAMB_BLACK_PLASTIC = "LAMB_BLACK_PLASTIC"

    LAMB_ALUMINUM = "LAMB_ALUMINUM"
    LAMB_ALUMINIUM = "LAMB_ALUMINIUM"

    LAMB_EVERGREEN_NEEDLE_FOREST = "LAMB_EVERGREEN_NEEDLE_FOREST"
    LAMB_EVERGREEN_BROADLEAF_FOREST = "LAMB_EVERGREEN_BROADLEAF_FOREST"
    LAMB_DECIDUOUS_NEEDLE_FOREST = "LAMB_DECIDUOUS_NEEDLE_FOREST"
    LAMB_DECIDUOUS_BROADLEAF_FOREST = "LAMB_DECIDUOUS_BROADLEAF_FOREST"
    LAMB_FOREST_MIXED = "LAMB_FOREST_MIXED"
    LAMB_SHRUBS_CLOSED = "LAMB_SHRUBS_CLOSED"
    LAMB_SHRUBS_OPEN = "LAMB_SHRUBS_OPEN"
    LAMB_SAVANNA_WOODY = "LAMB_SAVANNA_WOODY"
    LAMB_SAVANNA = "LAMB_SAVANNA"
    LAMB_GRASSLAND = "LAMB_GRASSLAND"
    LAMB_WETLAND = "LAMB_WETLAND"
    LAMB_CROPLAND = "LAMB_CROPLAND"
    LAMB_URBAN = "LAMB_URBAN"
    LAMB_CROP_MOSAIC = "LAMB_CROP_MOSAIC"
    LAMB_SNOW_ANTARCTIC = "LAMB_SNOW_ANTARCTIC"
    LAMB_DESERT_BARREN = "LAMB_DESERT_BARREN"
    LAMB_OCEAN_WATER = "LAMB_OCEAN_WATER"
    LAMB_TUNDRA = "LAMB_TUNDRA"
    LAMB_SNOW_FRESH = "LAMB_SNOW_FRESH"
    LAMB_SEA_ICE = "LAMB_SEA_ICE"
    LAMB_SPECTRALON = "LAMB_SPECTRALON"
    LAMB_SAND_DRY = "LAMB_SAND_DRY"


@enum.unique
class JSONPrintOpt(enum.IntFlag):
    """Options for `FileOptions.JSONPRNT`."""

    WRT_NONE = 0
    WRT_STATUS = 1
    WRT_INPUT = 2
    WRT_STAT_INPUT = 3
    WRT_OUTPUT = 4
    WRT_STAT_OUTPUT = 5
    WRT_INPUT_OUTPUT = 6
    WRT_ALL = 7


class RTOptions(TypedDict, total=False):
    """Settings for `CaseInput.RTOPTIONS`."""

    IEMSCT: RTExecutionMode
    MODTRN: RTAlgorithm
    LYMOLC: bool
    T_BEST: bool
    IMULT: RTMultipleScattering
    DISALB: bool
    NSTR: int
    NLBL: int
    SOLCON: float


class Atmosphere(TypedDict, total=False):
    """Settings for `CaseInput.ATMOSPHERE`."""

    MODEL: AtmosphereModel
    M1: AtmosphereModel
    M2: AtmosphereModel
    M3: AtmosphereModel
    M4: AtmosphereModel
    M5: AtmosphereModel
    M6: AtmosphereModel
    M2_RHC: bool
    MDEF: Literal[0, 1, 2]
    HMODEL: str
    NLAYERS: int
    NPROF: int
    PROFILES: list[AtmosphereProfile]
    CO2MX: float
    H2OSTR: float
    # uppercase variants appears in TEST/JSON examples.
    H2OUNIT: Literal[" ", "+", "g", "a", "G", "A"]
    H2OOPT: Literal[" "]  # not documented?
    O3STR: float
    # uppercase variants appears in TEST/JSON examples.
    O3UNIT: Literal[" ", "g", "a", "G", "A"]
    C_PROF: Literal[0, 1, 2, 3, 4, 5, 6, 7]
    S_UMIX: list[float]
    S_XSEC: list[float]
    S_TRAC: list[float]
    AERRH: float
    AYRANG: bool
    AYRANGFL: str
    E_MASS: float
    AIRMWT: float

    # Only for parsing keywords.json. Actually describes entries of PROFILES.
    ATMPROFILE: AtmosphereProfile


class AtmosphereProfile(TypedDict, total=False):
    """Entries `Atmosphere.PROFILES`."""

    TYPE: AtmosphereProfileType
    UNITS: AtmosphereProfileUnits
    UNAME: str
    PROFILE: list[float]
    PRO_MASK: list[Literal[-1, 0, 1, 2, 3, 4, 5, 6]]


class Aerosol(TypedDict, total=False):
    """Settings for `CaseInput.AEROSOL`."""

    IHAZE: AerosolHaze
    VIS: float
    WSS: float
    WHH: float
    # 0 undocumented, but appears in TEST/JSON examples.
    ICSTL: Literal[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    ISEASN: AerosolSeason
    IVULCN: AerosolStratospheric
    ICLD: AerosolCloud
    RAINRT: float
    IPH: Literal[0, 1, 2]
    HGPF: float

    H2OAER: bool
    CNOVAM: bool
    ARUSS: Literal[
        "USS", "SAP", "DEFAULT", "   ", "default"
    ]  # lowercase 'default' appears in keywords.json
    SAPFILE: str
    IVSA: bool
    ZCVSA: float
    ZTVSA: float
    ZINVSA: float

    ASTMX: float
    CDASTM: Literal[" ", "b", "B", "t", "T", "d", "D", "f"]  # TODO: "f" not documented?
    ASTMC: float
    ASTMO: float

    # TODO Flexible aerosol options
    SSALB: object
    APLUS: Literal["", "  ", "A+"]
    REGALT: AerosolRegAlt
    PHASEFN: AerosolPhaseFN
    IREGSPC: list[AerosolRegSPC]

    # Only for parsing keywords.json. Actually describes entries of IREGSPC.
    REGSPC: AerosolRegSPC

    CTHIK: float
    CALT: float
    CWAVLN: float
    CEXT: float
    CCOLWD: float
    CCOLIP: float
    CHUMID: float
    ASYMWD: float
    ASYMIP: float

    CLDALT: AerosolCloudAltitude
    CLDSPC: AerosolCloudSPC


class AerosolRegAlt(TypedDict, total=False):
    """Settings for `Aerosol.REGALT`."""

    ZAER1: tuple[float, float]
    SCALE1: float

    ZAER2: tuple[float, float]
    SCALE2: float

    ZAER3: tuple[float, float]
    SCALE3: float

    ZAER4: tuple[float, float]
    SCALE4: float


class AerosolPhaseFN(TypedDict, total=False):
    """Settings for `Aerosol.PHASEFN`."""

    NANGLS: int
    NWLF: int
    ANGF: list[float]
    WLF: list[float]
    AERPF: list[list[float]]


class AerosolRegSPC(TypedDict, total=False):
    """Settings for `Aerosol.IREGSPC`."""

    IREG: Literal[0, 1, 2, 3, 4]
    AWCCON: float
    AERNAM: str
    NARSPC: float
    VARSPC: list[float]
    EXTC: list[float]
    ABSC: list[float]
    ASYM: list[float]


class AerosolCloudAltitude(TypedDict, total=False):
    """Settings for `Aerosol.CLDALT`."""

    NCRALT: int
    ZPCLD: list[float]
    CLD: list[float]
    CLDICE: list[float]
    RR: list[float]


class AerosolCloudSPC(TypedDict, total=False):
    """Settings for `Aerosol.CLDSPC`."""

    NCRSPC: int
    WAVLEN: list[float]
    EXTC6: list[float]
    ABSC6: list[float]
    ASYM6: list[float]
    EXTC7: list[float]
    ABSC7: list[float]
    ASYM7: list[float]
    CFILE: str
    CLDTYP: str
    CIRTYP: str


class Geometry(TypedDict, total=False):
    """Settings for `CaseInput.GEOMETRY`."""

    # TEST/JSON/plumeMLOS uses undocumented -8
    # TEST/JSON/plumeMLOSthmCK.json use undocumented -11
    # TEST/JSON/lut01thm.json used undocumented -15
    # TEST/JSON/lut01BIN.json used undocumented -63
    ITYPE: Literal[1, 2, 3, 4, -8, -11, -15, -63]
    H1ALT: float
    H2ALT: float
    OBSZEN: float
    HRANGE: float
    BETA: float
    LENN: Literal[0, 1]
    BCKZEN: float
    NLOS: int  # not documented?
    MLOS: list[GeometryLOS]

    # Keywords BENDING through SEG_LEN appear to not be part of base Geometry structure,
    # despite what the docs suggest. Rather, these keywords appear to be found
    # inside MLOS and REFPATH.

    RAD_E: float
    CKRANG: float
    IDAY: int

    IPARM: Literal[0, 1, 2, 10, 11, 12]
    PARM1: float
    PARM2: float
    PARM3: float
    PARM4: float
    GMTIME: float
    TRUEAZ: float
    ANGLEM: float

    REFPATH: GeometryRefPath

    # Only for parsing keywords.json. Actually describes entries of MLOS.
    LOSGEOMETRY: GeometryLOS


class GeometryLOS(TypedDict, total=False):
    """Entries in `Geometry.MLOS`."""

    H1ALT: float
    H2ALT: float
    HRANGE: float
    CKRANG: float
    OBSZEN: float
    BCKZEN: float
    BETA: float
    AZ_INP: float
    LENN: int

    # Only for parsing keywords.json. Docs indicate only an output.
    BENDING: float


class GeometryRefPath(TypedDict, total=False):
    """Settings for `Geometry.REFPATH`."""

    NSEG: int
    SURF_DIST: list[float]
    SEG_ALT: list[float]
    SEG_ZEN: list[float]
    SEG_LEN: list[float]


class Surface(TypedDict, total=False):
    """Settings for `CaseInput.SURFACE`."""

    SURFTYPE: SurfaceType
    SURREF: float
    NSURF: Literal[1, 2]
    TPTEMP: float
    AATEMP: float
    WIDERP: bool
    GNDALT: float
    DH2O: float
    MLTRFL: bool
    SALBFL: str
    SURFP: object
    SURFA: object
    SURFNLOS: int
    SURFLOS: list[object]
    SURFACEPARAM: SurfaceParam


class SurfaceParam(TypedDict, total=False):
    """Settings for `Surface.SURFACEPARAM`."""

    CBRDF: SurfaceBRDFModel
    SALBSTR: str
    SURFZN: float  # can only be zero, but Literal[0.0] is not supported
    SURFAZ: float
    CSALB: SurfaceLambertianModel
    NWVSRF: float
    WVSURF: list[float]
    PBRDF1: list[float]
    PBRDF2: list[float]
    PBRDF3: list[float]
    PBRDF4: list[float]
    PBRDF5: list[float]
    PBRDF6: list[float]
    PBRDF7: list[float]
    UDSALB: list[float]


class Spectral(TypedDict, total=False):
    """Settings for `CaseInput.SPECTRAL`."""

    V1: float
    V2: float
    DV: float
    FWHM: float
    # lowercase and blank variants appear in TEST/JSON examples.
    YFLAG: Literal[" ", "T", "R", "t", "r"]
    # lowercase and blank variants appear in TEST/JSON examples.
    XFLAG: Literal[" ", "W", "M", "N", "w", "m", "n"]
    DLIMIT: str
    FLAGS: object
    MLFLX: int
    VRFRAC: float
    SFWHM: float
    LSUNFL: Literal[
        " ",
        "T",
        "t",
        "F",
        "f",
        "1",
        "2",
        "3",
        "4",
        "5",
        "6",
        "7",
        "8",
        "9",
        "A",
        "B",
        "C",
        "D",
    ]
    LBMNAM: Literal[" ", "f", "F", "t", "T", "4"]
    USRSUN: str
    BMNAME: str
    FILTNM: str
    CH2OCM: Literal[" ", "1"]


class FileOptions(TypedDict, total=False):
    """Settings for `CaseInput.FILEOPTIONS`."""

    NOFILE: Literal[0, 1, 2, "FC_ALLOWALL", "FC_TAPE6ONLY", "FC_NOFILES"]
    BINARY: bool
    CKPRNT: bool
    NOPRNT: Literal[0, 1, 2, 3, -1, -2]
    MSGPRNT: Literal[
        0, 1, 2, 3, 4, "MSG_NONE", "MSG_ERROR", "MSG_WARN", "MSG_INFO", "MSG_DEBUG"
    ]
    DATDIR: str
    FLROOT: str
    CSVPRNT: str
    SLIPRNT: str
    JSONPRNT: str
    JSONOPT: Union[
        JSONPrintOpt,
        Literal[
            "WRT_NONE",
            "WRT_STATUS",
            "WRT_INPUT",
            "WRT_STAT_INPUT",
            "WRT_OUTPUT",
            "WRT_STAT_OUTPUT",
            "WRT_INPUT_OUTPUT",
            "WRT_ALL",
        ],
    ]


CaseInput = TypedDict(
    "CaseInput",
    {
        "NAME": str,
        "DESCRIPTION": str,
        "CASE": int,
        "CASE TEMPLATE": int,
        "RTOPTIONS": RTOptions,
        "ATMOSPHERE": Atmosphere,
        "AEROSOLS": Aerosol,
        "GEOMETRY": Geometry,
        "SURFACE": Surface,
        "SPECTRAL": Spectral,
        "FILEOPTIONS": FileOptions,
        "TOOLBOX": dict[str, Any],
    },
    total=False,
)
CaseInput.__doc__ = """Settings for `Case.MODTRANINPUT`."""
CaseInput.__pydantic_config__ = ConfigDict(extra="forbid")  # type: ignore[attr-defined]


class CaseStatus(TypedDict, total=False):
    """Settings for `Case.MODTRANSTATUS`."""

    VERSION: str
    NAME: str
    CASE_STATUS: str
    WARNINGS: str


class Case(TypedDict, total=False):
    """Entries in `JSONInput.MODTRAN`."""

    MODTRANINPUT: CaseInput
    MODTRANSTATUS: CaseStatus
    MODTRANOUTPUT: dict[str, Any]


class JSONInput(TypedDict, total=True):
    """Complete MODTRAN JSON input file structure."""

    MODTRAN: list[Case]


JSONInput.__pydantic_config__ = ConfigDict(extra="forbid")  # type: ignore[attr-defined]
