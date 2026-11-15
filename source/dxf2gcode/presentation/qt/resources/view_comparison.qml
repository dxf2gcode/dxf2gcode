import QtQuick
import QtQuick3D

Rectangle {
    color: "white"
    width: 800
    height: 600
    function projectPoint(point) { return viewport.mapFrom3DScene(point) }

    View3D {
        id: viewport
        objectName: "viewport"
        camera: viewCamera
        anchors.fill: parent
        environment: SceneEnvironment {
            backgroundMode: SceneEnvironment.Color
            clearColor: "white"
            antialiasingMode: SceneEnvironment.MSAA
            antialiasingQuality: SceneEnvironment.Medium
            tonemapMode: SceneEnvironment.TonemapModeNone
        }
        Node {
            position: viewBridge ? viewBridge.center : Qt.vector3d(0, 0, 0)
            rotation: viewBridge ? viewBridge.cameraRotation : Qt.quaternion(1, 0, 0, 0)
            OrthographicCamera {
                id: viewCamera
                objectName: "viewCamera"
                z: viewBridge ? viewBridge.distance : 1000
                clipNear: 0.01
                clipFar: viewBridge ? viewBridge.distance * 4 : 10000
                horizontalMagnification: viewBridge ? viewBridge.zoom : 1
                verticalMagnification: horizontalMagnification
            }
        }
        Model {
            objectName: "toolpathModel"
            geometry: viewBridge ? viewBridge.mesh : null
            materials: DefaultMaterial {
                lighting: DefaultMaterial.NoLighting
                vertexColorsEnabled: true
                cullMode: Material.NoCulling
            }
        }
        Node {
            objectName: "toolRoot"
            DirectionalLight {
                eulerRotation: Qt.vector3d(-45, -30, 0)
                ambientColor: Qt.rgba(0.3, 0.3, 0.3, 1)
            }
            Repeater3D {
                model: viewBridge ? viewBridge.toolBodies : []
                delegate: Model {
                    geometry: viewBridge.toolMesh
                    position: Qt.vector3d(modelData.x, modelData.z, -modelData.y)
                    scale: Qt.vector3d(modelData.radius, modelData.length, modelData.radius)
                    opacity: 0.25
                    pickable: false
                    castsShadows: false
                    receivesShadows: false
                    materials: DefaultMaterial {
                        diffuseColor: Qt.rgba(0.3, 0.55, 0.75, 1)
                        cullMode: Material.BackFaceCulling
                        depthDrawMode: Material.NeverDepthDraw
                    }
                }
            }
        }

    }
    Canvas {
        id: annotations
        anchors.fill: parent
        onPaint: {
            var ctx = getContext("2d")
            ctx.clearRect(0, 0, width, height)
            ctx.font = "12px sans-serif"
            var labels = viewBridge ? viewBridge.annotations : []
            for (var i = 0; i < labels.length; ++i) {
                var label = labels[i]
                var points = [[label.x, label.y, "S", label.startColor],
                              [label.endx, label.endy, "E", label.endColor]]
                for (var j = 0; j < points.length; ++j) {
                    var p = points[j]
                    ctx.strokeStyle = p[3]
                    ctx.fillStyle = p[3]
                    ctx.lineWidth = 2
                    ctx.beginPath()
                    ctx.arc(p[0], p[1], 4, 0, Math.PI * 2)
                    ctx.stroke()
                    ctx.fillText(p[2], p[0] + 6, p[1] - 4)
                }
                ctx.fillStyle = "black"
                ctx.fillText(label.title, label.x + 8, label.y + 16)
                if (label.diagnostic) {
                    ctx.fillStyle = "red"
                    ctx.fillText(label.diagnostic, label.x + 8, label.y + 32)
                }
            }
        }
        Connections {
            target: viewBridge
            function onAnnotationsChanged() { annotations.requestPaint() }
        }
    }
    MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.LeftButton | Qt.MiddleButton | Qt.RightButton
        onPressed: function(mouse) { viewBridge.mousePress(mouse.x, mouse.y, mouse.button, mouse.modifiers) }
        onPositionChanged: function(mouse) { viewBridge.mouseMove(mouse.x, mouse.y) }
        onReleased: function(mouse) { viewBridge.mouseRelease(mouse.x, mouse.y, mouse.modifiers) }
        onWheel: function(wheel) { viewBridge.mouseWheel(wheel.angleDelta.y, wheel.x, wheel.y); wheel.accepted = true }
    }
}
