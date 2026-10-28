"""Build the editable DXF2GCODE project model from imported drawing data."""

from copy import copy, deepcopy

from dxf2gcode.domain.project.entitycontent import EntityContent
from dxf2gcode.domain.geometry.holegeo import HoleGeo
from dxf2gcode.domain.project.layercontent import LayerContent, Layers, Shapes
from dxf2gcode.domain.geometry.linegeo import LineGeo
from dxf2gcode.domain.geometry.point import Point


class DrawingModel:
    """Project model created from one imported drawing."""

    def __init__(self, entity_root, layers, shapes):
        self.entity_root = entity_root
        self.layers = layers
        self.shapes = shapes


class BuildDrawingModel:
    """Turn normalized imported entities into project layers and shapes."""

    def __init__(self, drawing, config, shape_factory, split_line_segments,
                 transform=None, shape_created=None):
        self.drawing = drawing
        self.config = config
        self.shape_factory = shape_factory
        self.split_line_segments = split_line_segments
        self.transform = transform or {}
        self.shape_created = shape_created
        self.layers = Layers([])
        self.shapes = Shapes([])

    def execute(self):
        root = EntityContent(
            nr=0, name="Entities", parent=None,
            p0=Point(self.transform.get("x", 0.0),
                     self.transform.get("y", 0.0)),
            pb=Point(), sca=[self.transform.get("scale", 1.0)] * 3,
            rot=self.transform.get("rotation", 0.0),
            mirrorx=self.transform.get("mirrorx", False),
            mirrory=self.transform.get("mirrory", False))
        self._add_entity_shapes(root)
        for layer in self.layers:
            layer.overrideDefaults()
        self.layers.sort(key=lambda layer: layer.nr)
        return DrawingModel(root, self.layers, self.shapes)

    def _add_entity_shapes(self, parent, layer_number=-1):
        if parent.name == "Entities":
            entities = self.drawing.entities
        else:
            block_number = self.drawing.Get_Block_Nr(parent.name)
            entities = self.drawing.blocks.Entities[block_number]

        for contour in entities.cont:
            first_geo = entities.geo[contour.order[0][0]]
            if first_geo.Typ == "Insert":
                block_number = self.drawing.Get_Block_Nr(first_geo.BlockName)
                block = self.drawing.blocks.Entities[block_number]
                child = EntityContent(
                    nr=0, name=first_geo.BlockName, parent=parent,
                    p0=first_geo.Point, pb=block.basep, sca=first_geo.Scale,
                    rot=first_geo.rot)
                parent.append(child)
                self._add_entity_shapes(child, first_geo.Layer_Nr)
                continue

            shape = self.shape_factory(len(self.shapes), contour.closed, parent)
            for geo_number, reverse in contour.order:
                for imported_geo in entities.geo[geo_number].geo:
                    geo = copy(imported_geo)
                    if reverse:
                        geo.reverse()
                    self._append_geo(shape, geo)
            if not len(shape.geos):
                continue

            shape.AnalyseAndOptimize()
            self.shapes.append(shape)
            layer_number_for_shape = (
                layer_number if self.config.vars.Import_Parameters[
                    "insert_at_block_layer"] and layer_number != -1
                else entities.geo[contour.order[0][0]].Layer_Nr)
            self._add_to_layer(shape, layer_number_for_shape)
            parent.append(shape)
            if self.shape_created is not None:
                self.shape_created(shape)

    def _append_geo(self, shape, geo):
        if -1e-5 <= geo.length < 1e-5:
            return
        if self.split_line_segments and isinstance(geo, LineGeo):
            diff = (geo.Pe - geo.Ps) / 2.0
            geo_b = deepcopy(geo)
            geo_a = deepcopy(geo)
            geo_b.Pe -= diff
            geo_a.Ps += diff
            shape.append(geo_b)
            shape.append(geo_a)
        else:
            shape.append(geo)

        if isinstance(geo, HoleGeo):
            shape.type = "Hole"
            shape.closed = True
            if self.config.machine_type == "drag_knife":
                shape.disabled = True
                shape.allowedToChange = False

    def _add_to_layer(self, shape, layer_number):
        for layer in self.layers:
            if layer.nr == layer_number:
                layer.shapes.append(shape)
                shape.parentLayer = layer
                shape.milling_offset = layer.milling_offset
                return

        layer_name = self.drawing.layers[layer_number].name
        layer = LayerContent(layer_number, layer_name, [shape])
        self.layers.append(layer)
        shape.parentLayer = layer
        shape.milling_offset = layer.milling_offset
