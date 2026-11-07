"""Application workflow for optimizing per-layer export routes."""

from copy import copy
from dxf2gcode.domain.toolpath.customgcode import CustomGCode


def apply_optimized_order(layer, shape_order, order_mode):
    """Apply the existing tree modes to enabled shapes and custom-code rows.

    ORDER_ONLY appends all routed shapes; PLACE_AFTER appends only released
    shapes. Other rows retain their relative order before the appended rows.
    """
    by_number = {shape.nr: index for index, shape in enumerate(layer.shapes)}
    moved = [by_number[nr] for nr in shape_order
             if order_mode == 'CONSTRAIN_ORDER_ONLY'
             or layer.shapes[by_number[nr]].send_to_TSP]
    moved_set = set(moved)
    layer.exp_order_complete = [index for index in layer.exp_order_complete
                                if index not in moved_set] + moved
    layer.exp_order = [layer.shapes[index].nr
                       for index in layer.exp_order_complete
                       if not isinstance(layer.shapes[index], CustomGCode)]


class OptimizeRoutes:
    """Optimize layer export orders through an injected route optimizer."""

    def __init__(self, optimizer_factory, max_iterations, start_point,
                 route_settings=None):
        self._optimizer_factory = optimizer_factory
        self._max_iterations = max_iterations
        self._start_point = start_point
        self._route_settings = route_settings

    def execute(self, layers, shapes, after_layer=None):
        """Update enabled layer routes and return the last optimizer result."""
        last_optimizer = None
        total_shapes = 0
        for layer in layers:
            if hasattr(layer, 'machining_step_id'):
                result = self._execute_step(layer, shapes)
                total_shapes += result.shape_count
                last_optimizer = result.optimizer
                if after_layer is not None:
                    after_layer(layer)
                continue
            if not layer.exp_order:
                layer.exp_order = []
                continue

            shape_order = list(layer.exp_order)
            fixed_order = [index for index, shape_nr in enumerate(shape_order)
                           if not shapes[shape_nr].send_to_TSP]
            endpoints = []
            for shape_nr in shape_order:
                shape = shapes[shape_nr]
                if shape.Pocket:
                    endpoints.append(shape.get_start_end_points(PPocket=True))
                else:
                    endpoints.append(shape.get_start_end_points())
            endpoints.append((self._start_point, self._start_point))

            optimizer = self._optimizer_factory(
                endpoints, fixed_order, self._route_settings)
            iterations = min(self._max_iterations, len(shape_order) * 50)
            for _ in range(iterations // 50):
                optimizer.calc_next_iteration()

            optimized_order = [shape_order[index]
                               for index in optimizer.opt_route[1:]]
            settings = self._route_settings or {}
            try:
                order_mode = settings['TSP_shape_order']
            except KeyError:
                order_mode = 'CONSTRAIN_ORDER_ONLY'
            apply_optimized_order(layer, optimized_order, order_mode)
            layer.optimize()
            total_shapes += len(shape_order)
            last_optimizer = optimizer
            if after_layer is not None:
                after_layer(layer)

        return RouteOptimizationResult(total_shapes, last_optimizer)

    def _execute_step(self, layer, shapes):
        """Retain literal-code barriers, including disabled literal rows."""
        ordered, segment = [], []
        count, optimizer = 0, None
        def flush():
            nonlocal count, optimizer
            if not segment:
                return
            chunk = copy(layer)
            del chunk.machining_step_id
            chunk.shapes = list(segment)
            chunk.exp_order_complete = [i for i, s in enumerate(segment) if not s.disabled]
            chunk.exp_order = [segment[i].nr for i in chunk.exp_order_complete]
            result = self.execute([chunk], shapes)
            count += result.shape_count
            optimizer = result.optimizer or optimizer
            enabled = iter(chunk.shapes[i] for i in chunk.exp_order_complete)
            ordered.extend(s if s.disabled else next(enabled) for s in segment)
            segment.clear()
        for shape in layer.shapes:
            if isinstance(shape, CustomGCode):
                flush()
                ordered.append(shape)
            else:
                segment.append(shape)
        flush()
        layer.shapes[:] = ordered
        layer.exp_order_complete = [i for i, s in enumerate(ordered) if not s.disabled]
        layer.exp_order = [s.nr for s in ordered if not s.disabled and not isinstance(s, CustomGCode)]
        return RouteOptimizationResult(count, optimizer)


class RouteOptimizationResult:
    """Summary of the optimizer state needed by existing GUI feedback."""

    def __init__(self, shape_count, optimizer):
        self.shape_count = shape_count
        self.optimizer = optimizer
