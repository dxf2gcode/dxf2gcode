"""Serialize immutable toolpath plans through the selected machine profile."""


class ToolpathGCodeExporter:
    """Render either semantic moves or recorded toolpath operations."""

    def export(self, plan, postprocessor):
        if plan.commands is not None:
            output = ""
            for command in plan.commands:
                if command.method == "literal":
                    output += command.args[0]
                    continue
                method = getattr(postprocessor, command.method)
                output += method(*command.args, **dict(command.kwargs))
            return output

        from dxf2gcode.domain.geometry.point import Point

        output = postprocessor.rap_pos_xy(Point(*plan.approach_xy))
        output += postprocessor.write_pre_shape_cut()
        safe_depth = plan.workpiece_top + abs(plan.safe_margin)
        output += postprocessor.rap_pos_z(safe_depth)

        for toolpath_pass in plan.passes:
            output += postprocessor.chg_feed_rate(plan.feed_depth)
            output += postprocessor.lin_pol_z(toolpath_pass.depth)
            output += postprocessor.chg_feed_rate(plan.feed_xy)
            for move in toolpath_pass.moves:
                start = Point(*move.start_xy)
                end = Point(*move.end_xy)
                output += postprocessor.lin_pol_xy(start, end)

        output += postprocessor.chg_feed_rate(plan.feed_depth)
        output += postprocessor.lin_pol_z(safe_depth)
        output += postprocessor.rap_pos_z(plan.retract_depth)
        output += postprocessor.write_post_shape_cut()
        return output
