"""
Input file construction and handling.
"""

from . import basecases
from ._builder import CaseHandle, ModtranInputBuilder
from ._json import (
    Aerosol,
    AerosolCloud,
    AerosolHaze,
    AerosolSeason,
    AerosolStratospheric,
    Atmosphere,
    AtmosphereModel,
    AtmosphereProfile,
    AtmosphereProfileType,
    AtmosphereProfileUnits,
    Case,
    FileOptions,
    Geometry,
    JSONInput,
    JSONPrintOpt,
    ModtranInput,
    ModtranStatus,
    RTAlgorithm,
    RTExecutionMode,
    RTMultipleScattering,
    RTOptions,
    Spectral,
    Surface,
    SurfaceBRDFModel,
    SurfaceLambertianModel,
    SurfaceParam,
    SurfaceType,
)

__all__ = [
    "basecases",
    # Builder
    "ModtranInputBuilder",
    "CaseHandle",
    # JSON input
    "JSONInput",
    "Case",
    "ModtranInput",
    "ModtranStatus",
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
