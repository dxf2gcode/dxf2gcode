"""Toolkit-independent semantic values for a basic milling plan."""

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class ToolpathMove:
    """A linear cutting movement between two XY coordinates."""

    kind: str
    start_xy: Tuple[float, float]
    end_xy: Tuple[float, float]
    center_xy: Tuple[float, float] = None
    sweep: float = 0.0


@dataclass(frozen=True)
class ToolpathPass:
    """One ordered Z pass and the XY movements made at that depth."""

    number: int
    depth: float
    moves: Tuple[ToolpathMove, ...]


@dataclass(frozen=True)
class ToolpathPlan:
    """Immutable movement plan shared by preview and machine exporters."""

    shape_number: int
    approach_xy: Tuple[float, float]
    passes: Tuple[ToolpathPass, ...]
    workpiece_top: float
    safe_margin: float
    retract_depth: float
    feed_depth: float
    feed_xy: float
    commands: tuple = None


@dataclass(frozen=True)
class ToolpathCommand:
    """A postprocessor-neutral operation captured from a complete toolpath."""

    method: str
    args: tuple = ()
    kwargs: tuple = ()
