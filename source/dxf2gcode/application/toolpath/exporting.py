"""Application use case for exporting a planned shape."""


class ExportShape:
    """Plan a shape once and serialize that plan for the selected machine."""

    def __init__(self, plan_toolpath, plan_exporter):
        self._plan_toolpath = plan_toolpath
        self._plan_exporter = plan_exporter

    def execute(self, shape, postprocessor):
        plan = self._plan_toolpath.execute(shape, postprocessor)
        return self._plan_exporter.export(plan, postprocessor)

    def plan_shape(self, shape, postprocessor):
        """Build a plan for a view without serializing it."""
        return self._plan_toolpath.execute(shape, postprocessor)
