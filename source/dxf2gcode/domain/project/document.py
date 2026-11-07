"""Versioned project document values, independent of codecs and UI."""
from dataclasses import dataclass

D2G_HEADER = "# +~+~+~ DXF2GCODE project file V%s ~+~+~+"
SUPPORTED_D2G_VERSIONS = (1.1, 1.2, 1.3, 1.4, 1.5)
CURRENT_D2G_VERSION = SUPPORTED_D2G_VERSIONS[-1]

@dataclass(frozen=True)
class LegacyProjectDocument:
    version: float
    values: dict


@dataclass(frozen=True)
class MachiningProjectDocument(LegacyProjectDocument):
    """Version 2 separates source restoration from machining assignments."""
    machining: object
