"""
Input JSON file handling.
"""

from __future__ import annotations

import enum
import json
import re
from typing import Any, Final, Literal, overload

import pydantic
from pydantic import ConfigDict
from typing_extensions import TypedDict

_COMMENT_PATTERN: Final = re.compile(
    r'#(?:[^\n"]*(!<\\)"[^\n"]*(!<\\)")*[^\n"]*$', flags=re.MULTILINE
)


# Inherit from str so that the 'json' module can  serialize it.
# Can be swapped with enum.StrEnum if only Python 3.11+ is targeted.
# See also https://stackoverflow.com/q/24481852
class _StrEnum(str, enum.Enum):
    def __str__(self) -> str:
        return self.value  # type: ignore


@enum.unique
class RTExecutionMode(_StrEnum):
    RT_TRANSMITTANCE = "RT_TRANSMITTANCE"
    RT_THERMAL_ONLY = "RT_THERMAL_ONLY"
    RT_SOLAR_AND_THERMAL = "RT_SOLAR_AND_THERMAL"
    RT_LUNAR_AND_THERMAL = "RT_LUNAR_AND_THERMAL"
    RT_LUNAR_IRRADIANCE = "RT_LUNAR_IRRADIANCE"


@enum.unique
class RTAlgorithm(_StrEnum):
    RT_MODTRAN = "RT_MODTRAN"
    RT_CORRK_SLOW = "RT_CORRK_SLOW"
    RT_CORRK_FAST = "RT_CORRK_FAST"
    RT_MODTRAN_POLAR = "RT_MODTRAN_POLAR"
    RT_LINE_BY_LINE = "RT_LINE_BY_LINE"


@enum.unique
class RTMultipleScattering(_StrEnum):
    RT_NO_MULTIPLE_SCATTER = "RT_NO_MULTIPLE_SCATTER"
    RT_DISORT = "RT_DISORT"
    RT_DISORT_AT_OBS = "RT_DISORT_AT_OBS"
    RT_ISAACS_2STREAM = "RT_ISAACS_2STREAM"
    RT_ISAACS_2STREAM_AT_OBS = "RT_ISAACS_2STREAM_AT_OBS"
    RT_ISAACS_SCALED = "RT_ISAACS_SCALED"
    RT_ISAACS_SCALED_AT_OBS = "RT_ISAACS_SCALED_AT_OBS"


@enum.unique
class AtmosphereModel(_StrEnum):
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
    SEASN_AUTO = "SEASN_AUTO"
    SEASN_SPRING_SUMMER = "SEASN_SPRING_SUMMER"
    SEASN_FALL_WINTER = "SEASN_FALL_WINTER"


@enum.unique
class AerosolStratospheric(_StrEnum):
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


class RTOptions(TypedDict, total=False):
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
    PROFILES: object  # TODO
    CO2MX: float
    H2OSTR: float
    H2OUNIT: Literal[" ", "+", "g", "a"]
    H2OOPT: Literal[" "]  # not documented?
    O3STR: float
    O3UNIT: Literal[" ", "g", "a"]
    C_PROF: Literal[0, 1, 2, 3, 4, 5, 6, 7]
    S_UMIX: list[float]
    S_XSEC: list[float]
    S_TRACE: list[float]
    AERRH: float
    AYRANG: bool
    AYRANGFL: str
    E_MASS: float
    AIRMWT: float


class AtmosphereProfile(TypedDict, total=False):
    TYPE: AtmosphereProfileType
    UNITS: AtmosphereProfileUnits
    UNAME: str
    PROFILE: list[float]
    PRO_MASK: list[Literal[-1, 0, 1, 2, 3, 4, 5, 6]]


class Aerosol(TypedDict, total=False):
    IHAZE: AerosolHaze
    VIS: float
    WSS: float
    WHH: float
    ICSTL: Literal[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    ISEASN: AerosolSeason
    IVULCN: AerosolStratospheric
    ICLD: AerosolCloud
    RAINRT: float
    IPH: Literal[0, 1, 2]
    HGPF: float

    H2OAER: bool
    CNOVAM: bool
    ARUSS: Literal["USS", "SAP", "DEFAULT", "   "]
    SAPFILE: str
    IVSA: bool
    ZCVSA: float
    ZTVSA: float
    ZINVSA: float

    ASTMX: float
    CDASTM: Literal["b", "B", "t", "T", "d", "D", "f"]  # TODO: "f" not documented?
    ASTMC: float
    ASTMO: float

    # TODO Flexible aerosol options
    SSALB: object
    APLUS: Literal["  ", "A+"]
    REGALT: object
    PHASEFN: object
    IREGSPC: object
    CLDALT: object
    CLDSPC: object


class Geometry(TypedDict, total=False):
    ITYPE: Literal[1, 2, 3, 4]
    H1ALT: float
    H2ALT: float
    OBSZEN: float
    HRANGE: float
    BETA: float
    LENN: Literal[0, 1]
    BCKZEN: float
    NLOS: object  # not documented?
    MLOS: object
    BENDING: float
    NSEG: int
    SURF_DIST: float
    SEG_ALT: float
    SEG_ZEN: float
    SEG_LEN: float

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


class Surface(TypedDict, total=False):
    SURFTYPE: object
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


class Spectral(TypedDict, total=False):
    V1: float
    V2: float
    DV: float
    FWHM: float
    YFLAG: Literal["T", "R"]
    XFLAG: Literal["W", "M", "N"]
    DLIMIT: str
    FLAGS: object
    MLFLX: int
    VRFRAC: float
    SFWHM: float
    LSUNFL: object
    LBMNAM: Literal[" ", "f", "F", "t", "T", "4"]
    USRSUN: str
    BMNAME: str
    FILTNM: str
    CH2OCM: Literal[" ", "1"]


class FileOptions(TypedDict, total=False):
    NOFILE: Literal[0, 1, 2, "FC_ALLOWALL", "FC_TAPE6ONLY", "FC_NOFILES"]
    BINARY: bool
    CKPRNT: bool
    NOPRNT: Literal[0, 1, 2, 3, -1, -2]
    MSGPRNT: Literal[0, 1, 2, 3, 4]
    DATDIR: str
    FLROOT: str
    CSVPRNT: str
    SLIPRNT: str
    JSONPRNT: str
    JSONOPT: Literal[
        0,
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        "WRT_NONE",
        "WRT_STATUS",
        "WRT_INPUT",
        "WRT_STAT_INPUT",
        "WRT_OUTPUTPUT",
        "WRT_STAT_OUTPUT",
        "WRT_INPUT_OUTPUT",
        "WRT_ALL",
    ]  # todo enum


ModtranInput = TypedDict(
    "ModtranInput",
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


class ModtranStatus(TypedDict, total=False):
    VERSION: str
    NAME: str
    CASE_STATUS: str
    WARNINGS: str


class Case(TypedDict, total=False):
    MODTRANINPUT: ModtranInput
    MODTRANSTATUS: object
    MODTRANOUTPUT: object


class JSONInput(TypedDict, total=True):
    MODTRAN: list[Case]


JSONInput.__pydantic_config__ = ConfigDict(extra="forbid")  # type: ignore[attr-defined]


class _CommentedJSONDecoder(json.JSONDecoder):
    _comment_pattern: re.Pattern[str]

    def __init__(self, comment_pattern: str | re.Pattern[str], **kwargs: Any) -> None:
        self._comment_pattern = re.compile(comment_pattern)
        super().__init__(**kwargs)

    # noinspection PyMethodOverriding
    def decode(self, s: str) -> Any:  # type: ignore[override]
        return super().decode(self._comment_pattern.sub("", s))


def read_json_input(
    s: str, strip_comments: bool = True, validate: bool = True
) -> JSONInput:
    if strip_comments:
        input_dict = json.loads(
            s, cls=_CommentedJSONDecoder, comment_pattern=_COMMENT_PATTERN
        )
    else:
        input_dict = json.loads(s)

    if validate:
        return pydantic.TypeAdapter(JSONInput).validate_python(input_dict)

    return input_dict  # type: ignore
