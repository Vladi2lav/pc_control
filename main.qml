import QtQuick
import QtQuick.Window

Window {
    id: root
    visible: true; color: "transparent"
    flags: Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint

    property var sgStart
    
    Component.onCompleted: {
        var vg = SysHelper.virtualGeometry()
        root.x = vg.x
        root.y = vg.y
        root.width = vg.width
        root.height = vg.height

        // Позиция центра на текущем экране при старте
        var g = SysHelper.cursorPos()
        var sg = SysHelper.screenGeometry(g.x, g.y)
        sgStart = sg
        
        // Размеры по процентам от текущего экрана (например 25% на 40%)
        var startW = Math.round(sg.width * 0.25)
        var startH = Math.round(sg.height * 0.4)
        
        var startX = (sg.x - root.x) + (sg.width - startW) / 2
        var startY = (sg.y - root.y) + (sg.height - startH) / 2

        curX = startX
        curY = startY
        curW = startW
        curH = startH
        tarX = startX
        tarY = startY
        tarW = startW
        tarH = startH

        triggerMaskUpdate()
    }

    // --- ФИЗИКА (ТВОЙ ХАРАКТЕР) ---
    property real tension: 0.14
    property real damping: 0.76
    
    property real curX: 0; property real curY: 0
    property real curW: 0; property real curH: 0
    property real velX: 0; property real velY: 0
    property real velW: 0; property real velH: 0
    property real tarX: 0; property real tarY: 0
    property real tarW: 0; property real tarH: 0

    property int appState: 1
    property int resizeMargin: 15
    property bool onEdge: false
    
    // Принудительное обновление маски при любых изменениях
    onCurXChanged: triggerMaskUpdate()
    onCurYChanged: triggerMaskUpdate()
    onCurWChanged: triggerMaskUpdate()
    onCurHChanged: triggerMaskUpdate()
    onOnEdgeChanged: triggerMaskUpdate()

    function triggerMaskUpdate() {
        SysHelper.updateMask(root, 
            [curX, curY, curW, curH], 
            [phantom.x, phantom.y, phantom.width, phantom.height, onEdge]
        )
    }

    // --- ФИЗИЧЕСКИЙ ДВИЖОК ---
    Timer {
        interval: 16; running: true; repeat: true
        onTriggered: {
            velX = (velX + (tarX - curX) * tension) * damping
            velY = (velY + (tarY - curY) * tension) * damping
            velW = (velW + (tarW - curW) * tension) * damping
            velH = (velH + (tarH - curH) * tension) * damping
            
            curX += velX; curY += velY
            curW += velW; curH += velH
        }
    }


    Rectangle {
        id: phantom
        visible: onEdge
        x: 0; y: 0; width: 0; height: 0
        z: 1
        color: Qt.rgba(0, 120/255, 215/255, 80/255)
        border.color: Qt.rgba(0, 120/255, 215/255, 180/255)
        border.width: 2
        radius: 8
    }


    Rectangle {
        id: mainContainer
        x: curX; y: curY; width: curW; height: curH
        color: appState === 1 ? "#212121" : "#ffffff"
        radius: appState === 1 ? 8 : 0
        z: 2; clip: true

        Text {
            anchors.centerIn: parent
            text: "Fixed Ghost & Click-through\nWidth: 20% | Height: 100%"
            color: appState === 1 ? "white" : "black"
        }
    }


    MouseArea {
        anchors.fill: parent
        hoverEnabled: true
        acceptedButtons: Qt.LeftButton | Qt.RightButton | Qt.MiddleButton

        property int currentAction: 0 
        property int anchorX; property int anchorY
        property int offX; property int offY

        function getEdge(lx, ly) {
            var relX = lx - curX; var relY = ly - curY
            if (relX < -25 || relX > curW + 25 || relY < -25 || relY > curH + 25) return 0
            var l = relX <= resizeMargin; var r = relX >= curW - resizeMargin
            var t = relY <= resizeMargin; var b = relY >= curH - resizeMargin
            var e = 0
            if (t) e |= 1; if (b) e |= 2; if (l) e |= 4; if (r) e |= 8
            return e
        }

        onPressed: (mouse) => {
            // ИСПОЛЬЗУЕМ ВСТРОЕННЫЕ КООРДИНАТЫ MOUSEAREA
            var localX = mouse.x
            var localY = mouse.y
            
            if (mouse.button === Qt.MiddleButton) Qt.quit()
            
            if (mouse.button === Qt.RightButton) {
                appState = 1; 
                var sg = SysHelper.screenGeometry(localX + root.x, localY + root.y)
                var resetW = Math.round(sg.width * 0.25)
                var resetH = Math.round(sg.height * 0.4)
                tarW = resetW; tarH = resetH
                tarX = (sg.x - root.x) + (sg.width - resetW) / 2
                tarY = (sg.y - root.y) + (sg.height - resetH) / 2
                velX = 0; velY = 0; triggerMaskUpdate()
                return
            }

            var edge = getEdge(localX, localY)
            if (edge !== 0) {
                currentAction = edge
                anchorX = (edge & 4) ? (curX + curW) : curX
                anchorY = (edge & 1) ? (curY + curH) : curY
            } else if (localX >= curX - 25 && localX <= curX + curW + 25 && localY >= curY - 25 && localY <= curY + curH + 25) {
                if (appState === 2) {
                    appState = 1
                    var sg2 = SysHelper.screenGeometry(localX + root.x, localY + root.y)
                    tarW = Math.round(sg2.width * 0.25)
                    tarH = Math.round(sg2.height * 0.4)
                    tarX = localX - tarW/2
                    tarY = localY - tarH/2
                    curX = tarX; curY = tarY; curW = tarW; curH = tarH
                    currentAction = -1
                } else {
                    currentAction = -1
                }
            }
            offX = localX - curX; offY = localY - curY
        }

        onPositionChanged: (mouse) => {
            var localX = mouse.x
            var localY = mouse.y

            if (currentAction === 0) {
                var e = getEdge(localX, localY)
                if (e === 5 || e === 10) cursorShape = Qt.SizeFDiagCursor
                else if (e === 9 || e === 6) cursorShape = Qt.SizeBDiagCursor
                else if (e & 12) cursorShape = Qt.SizeHorCursor
                else if (e & 3) cursorShape = Qt.SizeVerCursor
                else cursorShape = Qt.ArrowCursor
                return
            }

            if (currentAction === -1) {
                tarX = localX - offX; tarY = localY - offY
                checkSnap(localX + root.x, localY + root.y)
            } else {
                if (currentAction & 4) { if (anchorX - localX > 150) { tarX = localX; tarW = anchorX - tarX } } 
                else if (currentAction & 8) { if (localX - anchorX > 150) { tarW = localX - anchorX } }
                if (currentAction & 1) { if (anchorY - localY > 100) { tarY = localY; tarH = anchorY - tarY } } 
                else if (currentAction & 2) { if (localY - anchorY > 100) { tarH = localY - anchorY } }
            }
        }

        onReleased: {
            if (currentAction === -1 && onEdge) {
                appState = 2
                tarW = phantom.width; tarH = phantom.height
                tarX = phantom.x
                tarY = phantom.y
                curX = tarX; curY = tarY; curW = tarW; curH = tarH
                velX = 0; velY = 0; velW = 0; velH = 0
                onEdge = false
            }
            currentAction = 0
        }
    }

    function checkSnap(globalX, globalY) {
        var sg = SysHelper.screenGeometry(globalX, globalY)
        var local_x = sg.x - root.x
        var local_y = sg.y - root.y
        var sw = Math.round(sg.width * 0.2) // 20% ширины
        
        if (globalX <= sg.x + 50) {
            onEdge = true
            phantom.x = local_x
            phantom.y = local_y
            phantom.width = sw
            phantom.height = sg.height // 100% высоты
        } else if (globalX >= sg.x + sg.width - 50) {
            onEdge = true
            phantom.x = local_x + sg.width - sw
            phantom.y = local_y
            phantom.width = sw
            phantom.height = sg.height
        } else {
            onEdge = false
        }
    }

    // --- АВТОМАТИЧЕСКИЙ ТЕСТ И ЛОГИРОВАНИЕ ---
    Timer {
        id: autoTestTimer
        interval: 1000
        running: true
        repeat: true
        property int tick: 0
        onTriggered: {
            tick++
            console.log("[LOG] Tick:", tick, "| Virtual root window geometry:", root.x, root.y, root.width, root.height, "| Container local pos:", curX, curY)
            
            if (tick === 2) {
                console.log("[LOG] Starting automated movement test. Moving container smoothly to Screen 2...")
                tarX = root.width - curW - 200 // Move to far right
            }
            if (tick === 6) {
                console.log("[LOG] Snap test. Simulating cursor hitting right edge...")
                checkSnap(root.x + root.width, root.y + 500)
                if (onEdge) {
                    console.log("[LOG] Snap detected successfully at: ", phantom.x, phantom.y)
                }
            }
            if (tick === 9) {
                console.log("[LOG] Automated test finished. Stopping test timer.")
                onEdge = false
                autoTestTimer.running = false
            }
        }
    }
}