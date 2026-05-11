import QtQuick
import QtQuick.Window

Window {
    id: root
    visible: true; color: "transparent"
    flags: Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint

    property var sgStart
    property int snappedEdge: 0 // 0 = none, 1 = left, 2 = right
    property bool isInside: false
    
    // Сохраненные размеры в процентах от экрана
    property real floatWPct: 0.25
    property real floatHPct: 0.40
    property real snapWPct: 0.20
    property real snapHPct: 1.0
    
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
        
        // Размеры по сохраненным процентам
        var startW = Math.round(sg.width * floatWPct)
        var startH = Math.round(sg.height * floatHPct)
        
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
    
    Timer {
        id: hideTimer
        interval: 500
        repeat: false
        onTriggered: {
            if (appState === 2 && mouseArea.currentAction === 0) {
                appState = 3
                var sg = SysHelper.screenGeometry(curX + root.x + curW/2, curY + root.y + curH/2)
                var w1 = Math.round(sg.width * 0.01)
                if (w1 < 10) w1 = 10 // минимальная ширина
                
                if (snappedEdge === 2) {
                    tarX = curX + curW - w1
                }
                tarW = w1
            }
        }
    }
    
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
            var threshold = 0.5
            
            // X axis
            if (Math.abs(tarX - curX) < threshold && Math.abs(velX) < threshold) {
                if (curX !== tarX) curX = tarX; velX = 0
            } else {
                velX = (velX + (tarX - curX) * tension) * damping; curX += velX
            }
            
            // Y axis
            if (Math.abs(tarY - curY) < threshold && Math.abs(velY) < threshold) {
                if (curY !== tarY) curY = tarY; velY = 0
            } else {
                velY = (velY + (tarY - curY) * tension) * damping; curY += velY
            }
            
            // Width
            if (Math.abs(tarW - curW) < threshold && Math.abs(velW) < threshold) {
                if (curW !== tarW) curW = tarW; velW = 0
            } else {
                velW = (velW + (tarW - curW) * tension) * damping; curW += velW
            }
            
            // Height
            if (Math.abs(tarH - curH) < threshold && Math.abs(velH) < threshold) {
                if (curH !== tarH) curH = tarH; velH = 0
            } else {
                velH = (velH + (tarH - curH) * tension) * damping; curH += velH
            }
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

        Item {
            anchors.top: parent.top
            anchors.topMargin: 40 // отступ под верхнюю панель
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            opacity: appState === 3 ? 0 : 1
            Behavior on opacity { NumberAnimation { duration: 200 } }

            // Интерфейс для 1 состояния (Плавающее)
            Item {
                anchors.fill: parent
                visible: appState === 1
                Text {
                    anchors.centerIn: parent
                    text: "ПЛАВАЮЩИЙ ИНТЕРФЕЙС (1)"
                    color: "white"
                    font.pixelSize: 16
                }
            }

            // Интерфейс для 2 состояния (Прилепленное)
            Item {
                anchors.fill: parent
                visible: appState === 2
                Text {
                    anchors.centerIn: parent
                    text: "ПРИЛЕПЛЕННЫЙ ИНТЕРФЕЙС (2)"
                    color: "black"
                    font.pixelSize: 16
                }
            }
        }
    }


    MouseArea {
        id: mouseArea
        anchors.fill: parent
        hoverEnabled: true
        acceptedButtons: Qt.LeftButton | Qt.RightButton | Qt.MiddleButton

        property int currentAction: 0 
        property int anchorX; property int anchorY
        property int offX; property int offY

    function getEdge(lx, ly) {
        if (appState === 3) return 0
        var relX = lx - curX; var relY = ly - curY
        if (relX < -25 || relX > curW + 25 || relY < -25 || relY > curH + 25) return 0
        var l = relX <= resizeMargin; var r = relX >= curW - resizeMargin
        var t = relY <= resizeMargin; var b = relY >= curH - resizeMargin
        var e = 0
        
        // Запрет ресайза со стороны приклеенного края
        if (appState === 2) {
            if (snappedEdge === 1) l = false // Приклеены слева - нельзя тянуть левый край
            if (snappedEdge === 2) r = false // Приклеены справа - нельзя тянуть правый край
        }
        
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
                var resetW = Math.round(sg.width * floatWPct)
                var resetH = Math.round(sg.height * floatHPct)
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
                if (appState === 2 || appState === 3) {
                    appState = 1
                    hideTimer.stop()
                    var sg2 = SysHelper.screenGeometry(localX + root.x, localY + root.y)
                    tarW = Math.round(sg2.width * floatWPct)
                    tarH = Math.round(sg2.height * floatHPct)
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

            var inside = (localX >= curX && localX <= curX + curW && localY >= curY && localY <= curY + curH)
            if (inside !== isInside) {
                isInside = inside
                if (inside) {
                    hideTimer.stop()
                    if (appState === 3) {
                        appState = 2
                        var sg3 = SysHelper.screenGeometry(curX + root.x + curW/2, curY + root.y + curH/2)
                        var sw3 = Math.round(sg3.width * snapWPct)
                        if (snappedEdge === 2) {
                            tarX = curX + curW - sw3
                        }
                        tarW = sw3
                    }
                } else {
                    if (appState === 2 && currentAction === 0) {
                        hideTimer.restart()
                    }
                }
            }

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

        onReleased: (mouse) => {
            if (currentAction !== 0 && currentAction !== -1) {
                // Если мы только что меняли размер
                var sgSize = SysHelper.screenGeometry(curX + root.x + curW/2, curY + root.y + curH/2)
                if (appState === 1) {
                    floatWPct = curW / sgSize.width
                    floatHPct = curH / sgSize.height
                } else if (appState === 2) {
                    snapWPct = curW / sgSize.width
                    snapHPct = curH / sgSize.height
                }
            }

            if (currentAction === -1 && onEdge) {
                appState = 2
                tarW = phantom.width; tarH = phantom.height
                tarX = phantom.x
                tarY = phantom.y
                curX = tarX; curY = tarY; curW = tarW; curH = tarH
                velX = 0; velY = 0; velW = 0; velH = 0
                onEdge = false
                
                var insideSnap = (mouse.x >= curX && mouse.x <= curX + curW && mouse.y >= curY && mouse.y <= curY + curH)
                isInside = insideSnap
                if (!insideSnap) hideTimer.restart()
            }
            currentAction = 0
        }
        
        onExited: {
            isInside = false
            if (appState === 2 && currentAction === 0) {
                hideTimer.restart()
            }
        }
    }

    // --- ВЕРХНЯЯ ПАНЕЛЬ И КНОПКИ (ПОВЕРХ MOUSEAREA) ---
    Item {
        id: uiLayer
        x: curX; y: curY; width: curW; height: curH
        z: 4

        Item {
            id: titleBarArea
            width: parent.width
            height: 40
            visible: appState === 1 || appState === 2
            opacity: appState === 3 ? 0 : 1
            Behavior on opacity { NumberAnimation { duration: 200 } }

            Row {
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter
                anchors.rightMargin: 15
                spacing: 8
                Rectangle {
                    width: 14; height: 14; radius: 7; color: "#27c93f"
                    MouseArea { 
                        anchors.fill: parent
                        onClicked: {
                            if (appState === 2) {
                                hideTimer.stop()
                                appState = 3
                                var sg = SysHelper.screenGeometry(curX + root.x + curW/2, curY + root.y + curH/2)
                                var w1 = Math.round(sg.width * 0.01)
                                if (w1 < 10) w1 = 10
                                if (snappedEdge === 2) { tarX = curX + curW - w1 }
                                tarW = w1
                            } else if (appState === 1) {
                                root.showMinimized()
                            }
                        }
                    }
                }
                // Закрыть
                Rectangle {
                    width: 14; height: 14; radius: 7; color: "#ffbd2e"
                    MouseArea { anchors.fill: parent; onClicked: root.showMinimized() }
                }
                Rectangle {
                    width: 14; height: 14; radius: 7; color: "#ff5f56"
                    MouseArea { anchors.fill: parent; onClicked: Qt.quit() }
                }
                // Спрятать
                
            }

            // Выпадающее меню (3 точки)
            Rectangle {
                anchors.left: parent.left
                anchors.verticalCenter: parent.verticalCenter
                anchors.leftMargin: 15
                width: 30; height: 30; radius: 4
                color: dotsMouse.containsMouse ? (appState === 1 ? "#444" : "#eee") : "transparent"
                
                Text {
                    anchors.centerIn: parent
                    text: "⋮"
                    font.pixelSize: 32
                    color: appState === 1 ? "white" : "black"
                    font.bold: true
                }
                
                MouseArea {
                    id: dotsMouse
                    anchors.fill: parent
                    hoverEnabled: true
                    onClicked: {
                        console.log("Открыто выпадающее меню")
                    }
                }
            }
        }
    }

    function checkSnap(globalX, globalY) {
        var sg = SysHelper.screenGeometry(globalX, globalY)
        var local_x = sg.x - root.x
        var local_y = sg.y - root.y
        var sw = Math.round(sg.width * snapWPct) // ширина из сохраненного процента
        var sh = Math.round(sg.height * snapHPct) // высота из сохраненного процента
        
        // Позиция фантома по Y центрируется по курсору мыши, но не вылезает за экран
        var py = (globalY - root.y) - sh/2
        py = Math.max(local_y, Math.min(local_y + sg.height - sh, py))
        
        if (globalX <= sg.x + 50) {
            onEdge = true
            snappedEdge = 1 // левый край
            phantom.x = local_x
            phantom.y = py
            phantom.width = sw
            phantom.height = sh
        } else if (globalX >= sg.x + sg.width - 50) {
            onEdge = true
            snappedEdge = 2 // правый край
            phantom.x = local_x + sg.width - sw
            phantom.y = py
            phantom.width = sw
            phantom.height = sh
        } else {
            onEdge = false
            snappedEdge = 0
        }
    }


}