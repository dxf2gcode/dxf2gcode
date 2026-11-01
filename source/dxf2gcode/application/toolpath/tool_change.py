"""Explicit values supplied to a machine's tool-change macro."""

from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass(frozen=True)
class ToolChangeContext:
    tool_number: int
    previous_tool_number: Optional[int]
    speed: float
    next_start: Tuple[float, float]
    retract_z: float
    initial_retract_z: float
    metric: bool
