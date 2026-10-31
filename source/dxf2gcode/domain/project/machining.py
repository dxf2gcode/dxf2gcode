"""Explicit transitions between compatible machining settings."""

from dataclasses import dataclass


def machining_conflict(drill, pocket, compensation):
    return drill and (pocket or compensation != 40)


@dataclass(frozen=True)
class MachiningState:
    drill: bool
    pocket: bool
    compensation: int

    def transition(self, action, value):
        if action == 'drill':
            return MachiningState(bool(value), False if value else self.pocket,
                                  40 if value else self.compensation)
        if action == 'pocket':
            return MachiningState(False if value else self.drill, bool(value),
                                  self.compensation)
        if action == 'compensation' and value in (40, 41, 42):
            return MachiningState(False, self.pocket, value)
        raise ValueError('unsupported machining action or value')
