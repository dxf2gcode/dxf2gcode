"""Application entry point for requesting a semantic toolpath plan."""


class PlanToolpath:
    """Plan a shape through an injected planner implementation."""

    def __init__(self, planner):
        self._planner = planner

    def execute(self, shape, postprocessor):
        """Return a complete toolpath plan for the requested shape."""
        return self._planner.plan(shape, postprocessor)
