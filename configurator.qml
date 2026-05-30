import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

ApplicationWindow {
    id: mainWindow
    width: 1280
    height: 800
    visible: false
    title: "Конфигуратор"
    minimumWidth: 800
    minimumHeight: 600
    flags: Qt.Window

    property bool isDark: SettingsManager && SettingsManager.theme === "dark"
    property string defEncoding: SettingsManager ? SettingsManager.defaultEncoding : "utf-8"
    
    // Theme colors aligned with Antigravity IDE / VS Code Dark
    property color bgColor: isDark ? "#1e1e1e" : "#ffffff"
    property color panelColor: isDark ? "#252526" : "#f3f3f3"
    property color borderColor: isDark ? "#2b2b2b" : "#dddddd"
    property color textColor: isDark ? "#cccccc" : "#333333"
    property color headerColor: isDark ? "#2d2d2d" : "#e8e8e8"
    property color activeTabColor: isDark ? "#1e1e1e" : "#ffffff"
    property color inactiveTabColor: isDark ? "#2d2d2d" : "#ececec"
    property color accentColor: "#007fd4"
    
    // New VS Code Specific Palette elements
    property color activityBarBg: isDark ? "#181818" : "#2c2c2c"
    property color statusBarBg: isDark ? "#007acc" : "#005fb8"
    property color textMutedColor: isDark ? "#858585" : "#616161"
    property color floatingActiveBorder: isDark ? "#007fd4" : "#007acc"
    property color floatingInactiveBorder: isDark ? "#3c3c3c" : "#cccccc"
    property color listHoverBg: isDark ? "#2a2d2e" : "#e4e6f1"

    // Visibility States
    property bool showHierarchy: true
    property bool showProperties: true
    property bool showDebugger: false
    property bool showTerminal: true
    property string openedModule: ""
    
    ListModel { id: modulesModel }
    function refreshModules() {
        modulesModel.clear();
        if (typeof SysHelper !== "undefined") {
            var mods = SysHelper.getModules();
            for (var i = 0; i < mods.length; i++) {
                modulesModel.append({"name": mods[i]});
            }
        }
    }
    Connections { target: typeof SysHelper !== "undefined" ? SysHelper : null; function onModulesChanged() { refreshModules(); } }

    color: bgColor

    component VSSplitHandle: Rectangle {
        implicitWidth: 4
        implicitHeight: 4
        color: SplitHandle.hovered || SplitHandle.pressed ? accentColor : "transparent"
    }

    // --- Зоны изменения размера для нижней части окна (contentItem) ---
    Item {
        anchors.fill: parent
        enabled: mainWindow.visibility !== Window.Maximized
        z: 100

        // Левая сторона (ниже шапки)
        MouseArea {
            anchors.left: parent.left; anchors.top: parent.top; anchors.bottom: parent.bottom
            anchors.bottomMargin: 8; width: 6
            cursorShape: Qt.SizeHorCursor
            onPressed: mainWindow.startSystemResize(Qt.LeftEdge)
        }
        // Правая сторона (ниже шапки)
        MouseArea {
            anchors.right: parent.right; anchors.top: parent.top; anchors.bottom: parent.bottom
            anchors.bottomMargin: 8; width: 6
            cursorShape: Qt.SizeHorCursor
            onPressed: mainWindow.startSystemResize(Qt.RightEdge)
        }
        // Нижняя сторона
        MouseArea {
            anchors.left: parent.left; anchors.right: parent.right; anchors.bottom: parent.bottom
            anchors.leftMargin: 8; anchors.rightMargin: 8; height: 6
            cursorShape: Qt.SizeVerCursor
            onPressed: mainWindow.startSystemResize(Qt.BottomEdge)
        }
        // Нижний левый угол
        MouseArea {
            anchors.left: parent.left; anchors.bottom: parent.bottom; width: 8; height: 8
            cursorShape: Qt.SizeBDiagCursor
            onPressed: mainWindow.startSystemResize(Qt.BottomEdge | Qt.LeftEdge)
        }
        // Нижний правый угол
        MouseArea {
            anchors.right: parent.right; anchors.bottom: parent.bottom; width: 8; height: 8
            cursorShape: Qt.SizeFDiagCursor
            onPressed: mainWindow.startSystemResize(Qt.BottomEdge | Qt.RightEdge)
        }
    }

    header: Column {
        width: parent.width
        Rectangle {
            id: customTitleBar
            width: parent.width
            height: 35
            color: isDark ? "#333333" : "#e8e8e8"

        MouseArea {
            anchors.fill: parent
            onPressed: (mouse) => {
                mainWindow.startSystemMove()
            }
            onDoubleClicked: {
                if (mainWindow.visibility === Window.Maximized)
                    mainWindow.showNormal()
                else
                    mainWindow.showMaximized()
            }
        }

        // --- Зоны изменения размера для верхней части окна (внутри шапки) ---
        Item {
            anchors.fill: parent
            enabled: mainWindow.visibility !== Window.Maximized
            z: 100

            // Верхняя сторона
            MouseArea {
                anchors.left: parent.left; anchors.right: parent.right; anchors.top: parent.top
                anchors.leftMargin: 8; anchors.rightMargin: 8; height: 6
                cursorShape: Qt.SizeVerCursor
                onPressed: mainWindow.startSystemResize(Qt.TopEdge)
            }
            // Левая сторона (в шапке)
            MouseArea {
                anchors.left: parent.left; anchors.top: parent.top; anchors.bottom: parent.bottom
                anchors.topMargin: 8; width: 6
                cursorShape: Qt.SizeHorCursor
                onPressed: mainWindow.startSystemResize(Qt.LeftEdge)
            }
            // Правая сторона (в шапке)
            MouseArea {
                anchors.right: parent.right; anchors.top: parent.top; anchors.bottom: parent.bottom
                anchors.topMargin: 8; width: 6
                cursorShape: Qt.SizeHorCursor
                onPressed: mainWindow.startSystemResize(Qt.RightEdge)
            }
            // Верхний левый угол
            MouseArea {
                anchors.left: parent.left; anchors.top: parent.top; width: 8; height: 8
                cursorShape: Qt.SizeFDiagCursor
                onPressed: mainWindow.startSystemResize(Qt.TopEdge | Qt.LeftEdge)
            }
            // Верхний правый угол
            MouseArea {
                anchors.right: parent.right; anchors.top: parent.top; width: 8; height: 8
                cursorShape: Qt.SizeBDiagCursor
                onPressed: mainWindow.startSystemResize(Qt.TopEdge | Qt.RightEdge)
            }
        }

        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 10
            spacing: 5

            // MenuBar
            MenuBar {
                background: Rectangle { color: "transparent" }
                delegate: MenuBarItem {
                    contentItem: Text {
                        text: parent.text
                        font.pixelSize: 12
                        color: parent.highlighted ? (isDark ? "#ffffff" : "#000000") : (isDark ? "#cccccc" : "#333333")
                    }
                    background: Rectangle {
                        color: parent.highlighted ? (isDark ? "#505050" : "#d0d0d0") : "transparent"
                        radius: 4
                    }
                }

                Menu { 
                    title: qsTr("Файл") 
                    Menu {
                        title: qsTr("Создать")
                        MenuItem { 
                            text: qsTr("Новый модуль")
                            onTriggered: createModuleDialog.open()
                        }
                    }
                }
                Menu { title: qsTr("Правка") }
                Menu { 
                    title: qsTr("Вид")
                    MenuItem { 
                        text: showHierarchy ? qsTr("Скрыть Конфигурацию") : qsTr("Показать Конфигурацию")
                        onTriggered: { 
                            showHierarchy = !showHierarchy; 
                            if (showHierarchy) {
                                leftSidebar.SplitView.preferredWidth = 250;
                                hierarchyPanel.SplitView.preferredHeight = 200;
                            }
                        } 
                    }
                    MenuItem { 
                        text: showProperties ? qsTr("Скрыть Свойства") : qsTr("Показать Свойства")
                        onTriggered: { 
                            showProperties = !showProperties; 
                            if (showProperties) {
                                rightSidebar.SplitView.preferredWidth = 250;
                                propertiesPanel.SplitView.preferredHeight = 200;
                            }
                        } 
                    }
                    MenuItem { 
                        text: showDebugger ? qsTr("Скрыть Отладчик") : qsTr("Показать Отладчик")
                        onTriggered: { 
                            showDebugger = !showDebugger; 
                            if (showDebugger) {
                                rightSidebar.SplitView.preferredWidth = 250;
                                debuggerPanel.SplitView.preferredHeight = 200;
                            }
                        } 
                    }
                    MenuItem { 
                        text: showTerminal ? qsTr("Скрыть Терминал") : qsTr("Показать Терминал")
                        onTriggered: { 
                            showTerminal = !showTerminal; 
                            if (showTerminal) terminalContainer.SplitView.preferredHeight = 250;
                        } 
                    }
                }
                Menu { title: qsTr("Запуск") }
                Menu { 
                    title: qsTr("Настройки")
                    MenuItem {
                        text: qsTr("Открыть настройки")
                        onTriggered: settingsWindow.show()
                    }
                }
            }

            Item { Layout.fillWidth: true } 

            RowLayout {
                spacing: 0
                Rectangle {
                    width: 45; height: 35; color: "transparent"
                    Text { text: "—"; color: textColor; anchors.centerIn: parent }
                    MouseArea {
                        anchors.fill: parent
                        hoverEnabled: true
                        onEntered: parent.color = isDark ? "#505050" : "#d0d0d0"
                        onExited: parent.color = "transparent"
                        onClicked: mainWindow.showMinimized()
                    }
                }
                Rectangle {
                    width: 45; height: 35; color: "transparent"
                    Text { text: mainWindow.visibility === Window.Maximized ? "❐" : "□"; color: textColor; anchors.centerIn: parent }
                    MouseArea {
                        anchors.fill: parent
                        hoverEnabled: true
                        onEntered: parent.color = isDark ? "#505050" : "#d0d0d0"
                        onExited: parent.color = "transparent"
                        onClicked: {
                            if (mainWindow.visibility === Window.Maximized)
                                mainWindow.showNormal()
                            else
                                mainWindow.showMaximized()
                        }
                    }
                }
                Rectangle {
                    width: 45; height: 35; color: "transparent"
                    Text { text: "✕"; color: textColor; anchors.centerIn: parent }
                    MouseArea {
                        anchors.fill: parent
                        hoverEnabled: true
                        onEntered: parent.color = "#e81123"
                        onExited: parent.color = "transparent"
                        onClicked: mainWindow.close()
                    }
                }
            }
        }
    }
        
    Rectangle {
        id: mainToolBar
            width: parent.width
            height: 30
            color: panelColor
            Rectangle { width: parent.width; height: 1; color: borderColor; anchors.bottom: parent.bottom }
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 5
                spacing: 2
                Button { 
                    text: "▶"
                    background: Rectangle { color: parent.hovered ? (isDark ? "#505050" : "#d0d0d0") : "transparent"; radius: 4 }
                    contentItem: Text { text: parent.text; color: textColor; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                    implicitWidth: 30; implicitHeight: 25
                }
                Button { 
                    text: "💾"
                    background: Rectangle { color: parent.hovered ? (isDark ? "#505050" : "#d0d0d0") : "transparent"; radius: 4 }
                    contentItem: Text { text: parent.text; color: textColor; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                    implicitWidth: 30; implicitHeight: 25
                    onClicked: {
                        saveAllOpenedModules();
                    }
                }
            }
        }
    }

    Dialog {
        id: createModuleDialog
        title: "Создать модуль"
        x: Math.round((mainWindow.width - width) / 2)
        y: Math.round((mainWindow.height - height) / 2)
        width: 300
        modal: true
        standardButtons: Dialog.Ok | Dialog.Cancel
        
        ColumnLayout {
            anchors.fill: parent
            TextField {
                id: moduleNameInput
                Layout.fillWidth: true
                placeholderText: "Имя модуля (напр. nameModule)"
            }
        }
        onAccepted: {
            if (moduleNameInput.text.trim() !== "") {
                if (typeof SysHelper !== "undefined") SysHelper.createModule(moduleNameInput.text.trim());
                moduleNameInput.text = "";
            }
        }
    }

    // Settings Window
    Window {
        id: settingsWindow
        title: "Настройки"
        width: 600
        height: 400
        color: bgColor
        
        SplitView {
            anchors.fill: parent
            handle: VSSplitHandle {}
            
            ListView {
                id: settingsMenu
                SplitView.preferredWidth: 200
                model: ["Основное", "Конфигуратор"]
                currentIndex: 0
                delegate: Item {
                    width: ListView.view.width
                    height: 40
                    Rectangle {
                        anchors.fill: parent
                        color: settingsMenu.currentIndex === index ? activeTabColor : "transparent"
                    }
                    Text {
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.left: parent.left
                        anchors.leftMargin: 15
                        text: modelData
                        color: textColor
                        font.pixelSize: 14
                    }
                    MouseArea {
                        anchors.fill: parent
                        onClicked: settingsMenu.currentIndex = index
                    }
                }
            }
            
            StackLayout {
                currentIndex: settingsMenu.currentIndex
                SplitView.fillWidth: true
                
                // Основное
                Rectangle {
                    color: panelColor
                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 20
                        
                        Text {
                            text: "Кодировка по умолчанию"
                            color: textColor
                            font.bold: true
                            font.pixelSize: 14
                        }
                        
                        ComboBox {
                            Layout.fillWidth: true
                            model: ["utf-8", "cp866", "windows-1251"]
                            currentIndex: SettingsManager ? (model.indexOf(SettingsManager.defaultEncoding) !== -1 ? model.indexOf(SettingsManager.defaultEncoding) : 0) : 0
                            onActivated: function(index) {
                                if (SettingsManager) SettingsManager.defaultEncoding = model[index]
                            }
                        }
                        
                        Item { Layout.fillHeight: true }
                    }
                }
                
                // Конфигуратор
                Rectangle {
                    color: panelColor
                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 20
                        
                        Text {
                            text: "Цветовая гамма"
                            color: textColor
                            font.bold: true
                            font.pixelSize: 14
                        }
                        
                        ComboBox {
                            Layout.fillWidth: true
                            model: ["Тёмная", "Светлая"]
                            currentIndex: (SettingsManager && SettingsManager.theme === "dark") ? 0 : 1
                            onActivated: function(index) {
                                if (SettingsManager) SettingsManager.theme = index === 0 ? "dark" : "light"
                            }
                        }
                        
                        Item { Layout.fillHeight: true }
                    }
                }
            }
        }
    }

    // Export Loading Dialog (Modal, VS Code Style)
    Dialog {
        id: exportLoadingDialog
        property string moduleName: ""
        property string exportType: ""
        
        title: "Экспорт модуля"
        x: Math.round((mainWindow.width - width) / 2)
        y: Math.round((mainWindow.height - height) / 2)
        width: 300
        height: 150
        modal: true
        closePolicy: Popup.NoAutoClose
        
        background: Rectangle {
            color: panelColor
            border.color: borderColor
            border.width: 1
            radius: 6
        }

        header: Rectangle {
            color: headerColor
            height: 30
            width: parent.width
            Text {
                text: "Экспорт..."
                color: textColor
                font.bold: true
                anchors.centerIn: parent
            }
        }

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 15
            spacing: 12

            BusyIndicator {
                Layout.alignment: Qt.AlignHCenter
                running: exportLoadingDialog.visible
            }

            Text {
                text: "Экспортируем модуль " + exportLoadingDialog.moduleName + "..."
                color: textColor
                font.pixelSize: 12
                Layout.alignment: Qt.AlignHCenter
            }
        }
    }

    // Export Success Dialog
    Dialog {
        id: exportSuccessDialog
        property string messageText: ""
        
        title: "Успех"
        x: Math.round((mainWindow.width - width) / 2)
        y: Math.round((mainWindow.height - height) / 2)
        width: 320
        height: 140
        modal: true
        standardButtons: Dialog.Ok

        background: Rectangle {
            color: panelColor
            border.color: borderColor
            border.width: 1
            radius: 6
        }

        header: Rectangle {
            color: headerColor
            height: 30
            width: parent.width
            Text {
                text: "Успешно"
                color: textColor
                font.bold: true
                anchors.centerIn: parent
            }
        }

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 15
            spacing: 10

            Text {
                text: exportSuccessDialog.messageText
                color: textColor
                font.pixelSize: 12
                wrapMode: Text.Wrap
                Layout.fillWidth: true
                horizontalAlignment: Text.AlignHCenter
            }
        }
    }

    // Export Error Dialog
    Dialog {
        id: exportErrorDialog
        property string messageText: ""
        
        title: "Ошибка"
        x: Math.round((mainWindow.width - width) / 2)
        y: Math.round((mainWindow.height - height) / 2)
        width: 320
        height: 140
        modal: true
        standardButtons: Dialog.Ok

        background: Rectangle {
            color: panelColor
            border.color: borderColor
            border.width: 1
            radius: 6
        }

        header: Rectangle {
            color: headerColor
            height: 30
            width: parent.width
            Text {
                text: "Ошибка экспорта"
                color: "#ff5f56"
                font.bold: true
                anchors.centerIn: parent
            }
        }

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 15
            spacing: 10

            Text {
                text: exportErrorDialog.messageText
                color: textColor
                font.pixelSize: 12
                wrapMode: Text.Wrap
                Layout.fillWidth: true
                horizontalAlignment: Text.AlignHCenter
            }
        }
    }

    // Timer to simulate the export progress visually (1s duration)
    Timer {
        id: exportTimer
        interval: 1000
        repeat: false
        onTriggered: {
            var success = false
            var dest = "c:/Новая папка/control_no_ai/primer/" + exportLoadingDialog.moduleName
            if (typeof SysHelper !== "undefined") {
                if (exportLoadingDialog.exportType === "zip") {
                    success = SysHelper.exportModuleSource(exportLoadingDialog.moduleName, dest + "_export")
                } else if (exportLoadingDialog.exportType === "windows") {
                    success = SysHelper.exportModuleExe(exportLoadingDialog.moduleName, dest + "_win", "windows")
                } else if (exportLoadingDialog.exportType === "linux") {
                    success = SysHelper.exportModuleExe(exportLoadingDialog.moduleName, dest + "_linux", "linux")
                }
            }
            
            exportLoadingDialog.close()
            if (success) {
                exportSuccessDialog.messageText = "Модуль \"" + exportLoadingDialog.moduleName + "\" успешно экспортирован!"
                exportSuccessDialog.open()
            } else {
                exportErrorDialog.messageText = "Не удалось экспортировать модуль \"" + exportLoadingDialog.moduleName + "\""
                exportErrorDialog.open()
            }
        }
    }

    // Main Layout wrapping ActivityBar, SplitView and StatusBar
    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 0

            // 1. LEFTMOST ACTIVITY BAR (Permanent, 48px width)
            Rectangle {
                id: activityBar
                Layout.fillHeight: true
                width: 48
                color: activityBarBg

                Rectangle {
                    width: 1; anchors.right: parent.right; anchors.top: parent.top; anchors.bottom: parent.bottom
                    color: borderColor
                }

                ColumnLayout {
                    anchors.fill: parent
                    spacing: 0

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 8
                        Layout.topMargin: 10

                        // Explorer Toggle Button
                        Rectangle {
                            width: 48; height: 48; color: "transparent"
                            Rectangle {
                                width: 3; height: 24; anchors.left: parent.left; anchors.verticalCenter: parent.verticalCenter
                                color: accentColor; visible: showHierarchy
                            }
                            Item {
                                width: 20; height: 20
                                anchors.centerIn: parent
                                Rectangle {
                                    width: 15; height: 11
                                    x: 2.5; y: 5.5
                                    color: "transparent"
                                    border.color: showHierarchy ? textColor : textMutedColor
                                    border.width: 1.5
                                    radius: 1
                                }
                                Rectangle {
                                    width: 6; height: 3
                                    x: 3.5; y: 3.5
                                    color: activityBarBg
                                    border.color: showHierarchy ? textColor : textMutedColor
                                    border.width: 1.5
                                    Rectangle {
                                        anchors.bottom: parent.bottom
                                        anchors.left: parent.left
                                        anchors.right: parent.right
                                        anchors.leftMargin: 1.5
                                        anchors.rightMargin: 1.5
                                        height: 1.5
                                        color: activityBarBg
                                    }
                                }
                            }
                            MouseArea {
                                anchors.fill: parent
                                hoverEnabled: true
                                onEntered: parent.opacity = 0.8
                                onExited: parent.opacity = 1.0
                                onClicked: showHierarchy = !showHierarchy
                            }
                        }

                        // Search Placeholder
                        Rectangle {
                            width: 48; height: 48; color: "transparent"
                            Item {
                                width: 20; height: 20
                                anchors.centerIn: parent
                                Rectangle {
                                    width: 9; height: 9
                                    x: 3; y: 3
                                    color: "transparent"
                                    border.color: textMutedColor
                                    border.width: 1.5
                                    radius: 4.5
                                }
                                Rectangle {
                                    width: 6; height: 1.5
                                    x: 11; y: 11
                                    color: textMutedColor
                                    rotation: 45
                                    transformOrigin: Item.TopLeft
                                }
                            }
                            MouseArea { anchors.fill: parent; onClicked: console.log("Search panel placeholder") }
                        }

                        // Git / Version Control Placeholder
                        Rectangle {
                            width: 48; height: 48; color: "transparent"
                            Item {
                                width: 20; height: 20
                                anchors.centerIn: parent
                                Rectangle { width: 1.5; height: 11; x: 6; y: 4.5; color: textMutedColor }
                                Rectangle { width: 4; height: 4; radius: 2; x: 4.75; y: 2; color: textMutedColor }
                                Rectangle { width: 4; height: 4; radius: 2; x: 4.75; y: 14; color: textMutedColor }
                                Rectangle { width: 4; height: 4; radius: 2; x: 11.25; y: 5; color: textMutedColor }
                                Rectangle { width: 6; height: 1.5; x: 6.75; y: 9; color: textMutedColor }
                                Rectangle { width: 1.5; height: 3; x: 12.5; y: 7.25; color: textMutedColor }
                            }
                            MouseArea { anchors.fill: parent; onClicked: console.log("Git panel placeholder") }
                        }
                    }

                    Item { Layout.fillHeight: true } // Spacer

                    // Settings Button
                    Rectangle {
                        width: 48; height: 48; color: "transparent"
                        Text {
                            text: "⚙"
                            font.pixelSize: 22
                            color: textMutedColor
                            anchors.centerIn: parent
                            font.family: "Segoe UI Symbol"
                        }
                        MouseArea { anchors.fill: parent; onClicked: settingsWindow.show() }
                    }
                }
            }

            // 2. MAIN SPLITVIEW FOR CONTENT
            SplitView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                orientation: Qt.Horizontal
                handle: VSSplitHandle {}

                // Left Sidebar (Hierarchy / Configuration)
                SplitView {
                    id: leftSidebar
                    orientation: Qt.Vertical
                    SplitView.preferredWidth: 250
                    SplitView.minimumWidth: 150
                    visible: showHierarchy
                    handle: VSSplitHandle {}

                    Rectangle {
                        id: hierarchyPanel
                        color: panelColor
                        SplitView.fillHeight: true
                        SplitView.fillWidth: true
                        SplitView.minimumHeight: 100
                        visible: showHierarchy
                        
                        ColumnLayout {
                            anchors.fill: parent
                            spacing: 0
                            
                            Rectangle {
                                Layout.fillWidth: true
                                height: 35
                                color: headerColor
                                Text { 
                                    text: "КОНФИГУРАЦИЯ"
                                    color: textColor
                                    font.bold: true
                                    font.pixelSize: 11
                                    anchors.verticalCenter: parent.verticalCenter
                                    anchors.left: parent.left
                                    anchors.leftMargin: 20 
                                }
                                MouseArea {
                                    anchors.fill: parent
                                    acceptedButtons: Qt.RightButton
                                    onClicked: hierarchyMenu.popup()
                                }
                                Menu {
                                    id: hierarchyMenu
                                    MenuItem { text: qsTr("Создать модуль"); onTriggered: createModuleDialog.open() }
                                    MenuItem { text: qsTr("Скрыть панель"); onTriggered: showHierarchy = false }
                                    MenuItem { text: qsTr("Настройки"); onTriggered: settingsWindow.show() }
                                }
                                Menu {
                                    id: moduleContextMenu
                                    property string moduleName: ""
                                    MenuItem { 
                                        text: qsTr("Открыть модуль")
                                        onTriggered: {
                                            openModuleEditor(moduleContextMenu.moduleName);
                                        }
                                    }
                                    MenuItem {
                                        text: qsTr("Сменить иконку")
                                        onTriggered: {
                                            console.log("Сменить иконку для " + moduleContextMenu.moduleName);
                                        }
                                    }
                                    Menu {
                                        title: qsTr("Экспорт")
                                        MenuItem {
                                            text: qsTr("Как исходники (zip)")
                                            onTriggered: triggerExport("zip", moduleContextMenu.moduleName)
                                        }
                                        MenuItem {
                                            text: qsTr("В вид без редактирования (Windows)")
                                            onTriggered: triggerExport("windows", moduleContextMenu.moduleName)
                                        }
                                        MenuItem {
                                            text: qsTr("В вид без редактирования (Linux)")
                                            onTriggered: triggerExport("linux", moduleContextMenu.moduleName)
                                        }
                                    }
                                }
                            }
                            
                            Item { 
                                Layout.fillHeight: true; Layout.fillWidth: true 
                                ListView {
                                    anchors.fill: parent
                                    model: modulesModel
                                    delegate: Rectangle {
                                        width: ListView.view.width
                                        height: 28
                                        color: itemMouseArea.containsMouse ? listHoverBg : "transparent"
                                        
                                        Text {
                                            text: "📦  " + model.name
                                            color: textColor
                                            font.pixelSize: 12
                                            anchors.verticalCenter: parent.verticalCenter
                                            anchors.left: parent.left
                                            anchors.leftMargin: 15
                                        }
                                        
                                        MouseArea {
                                            id: itemMouseArea
                                            anchors.fill: parent
                                            hoverEnabled: true
                                            acceptedButtons: Qt.LeftButton | Qt.RightButton
                                            onDoubleClicked: {
                                                openModuleEditor(model.name);
                                            }
                                            onClicked: (mouse) => {
                                                if (mouse.button === Qt.RightButton) {
                                                    moduleContextMenu.moduleName = model.name;
                                                    moduleContextMenu.popup();
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }

                // Center Area (MDI Workspace + Terminal)
                SplitView {
                    SplitView.fillWidth: true
                    orientation: Qt.Vertical
                    handle: VSSplitHandle {}

                    // 3. MDI WORKSPACE AREA
                    Rectangle {
                        id: workspace
                        color: bgColor
                        SplitView.fillHeight: true
                        SplitView.fillWidth: true
                        SplitView.minimumHeight: 200
                        clip: true

                        // VS Code Tab Bar for Open Windows
                        Rectangle {
                            id: workspaceTabBar
                            width: parent.width
                            height: 35
                            color: panelColor
                            visible: openEditorsModel.count > 0
                            z: 999
                            
                            Rectangle { width: parent.width; height: 1; color: borderColor; anchors.bottom: parent.bottom }

                            ListView {
                                anchors.fill: parent
                                orientation: ListView.Horizontal
                                model: openEditorsModel
                                spacing: 1
                                delegate: Rectangle {
                                    width: 140
                                    height: 35
                                    color: (activeModuleName === model.moduleName) ? bgColor : inactiveTabColor
                                    
                                    // Accent color line on active tab top
                                    Rectangle {
                                        width: parent.width; height: 2; anchors.top: parent.top
                                        color: (activeModuleName === model.moduleName) ? accentColor : "transparent"
                                    }

                                    RowLayout {
                                        anchors.fill: parent
                                        anchors.leftMargin: 12
                                        anchors.rightMargin: 8
                                        spacing: 5
                                        
                                        Text {
                                            Layout.fillWidth: true
                                            text: "📦  " + model.moduleName
                                            color: (activeModuleName === model.moduleName) ? textColor : textMutedColor
                                            font.pixelSize: 11
                                            elide: Text.ElideRight
                                        }
                                        
                                        Text {
                                            text: "✕"
                                            color: textColor
                                            font.pixelSize: 12
                                            opacity: 0.6
                                            MouseArea {
                                                anchors.fill: parent
                                                hoverEnabled: true
                                                onEntered: parent.opacity = 1.0
                                                onExited: parent.opacity = 0.6
                                                onClicked: {
                                                    // Save on close
                                                    var editorItem = openEditorsRepeater.itemAt(index)
                                                    if (editorItem) {
                                                        SysHelper.saveModuleMain(model.moduleName, model.codeText)
                                                    }
                                                    openEditorsModel.remove(index)
                                                }
                                            }
                                        }
                                    }

                                    MouseArea {
                                        anchors.fill: parent
                                        z: -1
                                        onClicked: {
                                            model.isMinimized = false
                                            bringToFront(openEditorsRepeater.itemAt(index), index)
                                        }
                                    }
                                }
                            }
                        }

                        // Dashboard (visible if no files open)
                        ColumnLayout {
                            anchors.centerIn: parent
                            visible: openEditorsModel.count === 0
                            spacing: 12

                            Text {
                                text: "Antigravity Configurator"
                                color: textColor
                                font.pixelSize: 28
                                font.bold: true
                                font.family: "Outfit, Inter, sans-serif"
                                Layout.alignment: Qt.AlignHCenter
                            }
                            Text {
                                text: "Double-click on modules in the hierarchy to open them as floating windows"
                                color: textMutedColor
                                font.pixelSize: 13
                                Layout.alignment: Qt.AlignHCenter
                            }
                            Rectangle {
                                width: 250; height: 1; color: borderColor
                                Layout.alignment: Qt.AlignHCenter
                            }
                            ColumnLayout {
                                spacing: 6
                                Layout.alignment: Qt.AlignHCenter
                                Text { text: "Save File: Ctrl+S"; color: textMutedColor; font.pixelSize: 12; font.family: "monospace" }
                                Text { text: "Open Window: Double-click Hierarchy"; color: textMutedColor; font.pixelSize: 12; font.family: "monospace" }
                                Text { text: "Resize Windows: Drag borders/corners"; color: textMutedColor; font.pixelSize: 12; font.family: "monospace" }
                            }
                        }

                        // Floating Windows Repeater
                        Repeater {
                            id: openEditorsRepeater
                            model: openEditorsModel
                            delegate: Rectangle {
                                id: win
                                x: model.isMaximized ? 0 : model.editorX
                                y: model.isMaximized ? 35 : model.editorY
                                width: model.isMaximized ? workspace.width : model.editorWidth
                                height: model.isMaximized ? workspace.height - 35 : model.editorHeight
                                z: model.zIndex
                                visible: !model.isMinimized
                                
                                color: bgColor
                                border.color: win.activeFocus ? floatingActiveBorder : floatingInactiveBorder
                                border.width: 1
                                radius: model.isMaximized ? 0 : 5
                                clip: true

                                onActiveFocusChanged: {
                                    if (activeFocus) {
                                        bringToFront(win, index)
                                    }
                                }

                                // TitleBar of the Floating Window
                                Rectangle {
                                    id: winTitleBar
                                    width: parent.width
                                    height: 32
                                    color: win.activeFocus ? headerColor : (isDark ? "#282828" : "#f0f0f0")

                                    Text {
                                        text: "🐍  " + model.moduleName + "  -  main.py"
                                        color: win.activeFocus ? textColor : textMutedColor
                                        font.bold: true
                                        font.pixelSize: 11
                                        anchors.verticalCenter: parent.verticalCenter
                                        anchors.left: parent.left
                                        anchors.leftMargin: 12
                                    }

                                    RowLayout {
                                        anchors.right: parent.right
                                        anchors.verticalCenter: parent.verticalCenter
                                        anchors.rightMargin: 8
                                        spacing: 4

                                        // Save
                                        Rectangle {
                                            width: 22; height: 22; radius: 3; color: "transparent"
                                            Text { text: "💾"; anchors.centerIn: parent; color: textColor; font.pixelSize: 10 }
                                            MouseArea {
                                                anchors.fill: parent
                                                hoverEnabled: true
                                                onEntered: parent.color = isDark ? "#444" : "#ddd"
                                                onExited: parent.color = "transparent"
                                                onClicked: {
                                                    SysHelper.saveModuleMain(model.moduleName, codeTextArea.text)
                                                }
                                            }
                                        }

                                        // Minimize
                                        Rectangle {
                                            width: 22; height: 22; radius: 3; color: "transparent"
                                            Text { text: "—"; anchors.centerIn: parent; color: textColor; font.pixelSize: 10 }
                                            MouseArea {
                                                anchors.fill: parent
                                                hoverEnabled: true
                                                onEntered: parent.color = isDark ? "#444" : "#ddd"
                                                onExited: parent.color = "transparent"
                                                onClicked: {
                                                    model.isMinimized = true
                                                }
                                            }
                                        }

                                        // Maximize
                                        Rectangle {
                                            width: 22; height: 22; radius: 3; color: "transparent"
                                            Text { text: model.isMaximized ? "❐" : "□"; anchors.centerIn: parent; color: textColor; font.pixelSize: 10 }
                                            MouseArea {
                                                anchors.fill: parent
                                                hoverEnabled: true
                                                onEntered: parent.color = isDark ? "#444" : "#ddd"
                                                onExited: parent.color = "transparent"
                                                onClicked: {
                                                    model.isMaximized = !model.isMaximized
                                                }
                                            }
                                        }

                                        // Close
                                        Rectangle {
                                            width: 22; height: 22; radius: 3; color: "transparent"
                                            Text { text: "✕"; anchors.centerIn: parent; color: textColor; font.pixelSize: 10 }
                                            MouseArea {
                                                anchors.fill: parent
                                                hoverEnabled: true
                                                onEntered: parent.color = "#e81123"
                                                onExited: parent.color = "transparent"
                                                onClicked: {
                                                    SysHelper.saveModuleMain(model.moduleName, codeTextArea.text)
                                                    openEditorsModel.remove(index)
                                                }
                                            }
                                        }
                                    }

                                    MouseArea {
                                        anchors.fill: parent
                                        anchors.rightMargin: 100
                                        property int lastX
                                        property int lastY
                                        onPressed: (mouse) => {
                                            lastX = mouse.x
                                            lastY = mouse.y
                                            win.forceActiveFocus()
                                        }
                                        onPositionChanged: (mouse) => {
                                            if (pressed && !model.isMaximized) {
                                                var dx = mouse.x - lastX
                                                var dy = mouse.y - lastY
                                                model.editorX = Math.max(0, Math.min(workspace.width - win.width, win.x + dx))
                                                model.editorY = Math.max(35, Math.min(workspace.height - win.height, win.y + dy))
                                            }
                                        }
                                        onDoubleClicked: {
                                            model.isMaximized = !model.isMaximized
                                        }
                                    }
                                }

                                ScrollView {
                                    anchors.top: winTitleBar.bottom
                                    anchors.left: parent.left
                                    anchors.right: parent.right
                                    anchors.bottom: parent.bottom
                                    clip: true

                                    TextArea {
                                        id: codeTextArea
                                        text: model.codeText
                                        color: textColor
                                        font.family: "Consolas, Courier New, monospace"
                                        font.pixelSize: 13
                                        background: Rectangle { color: bgColor }
                                        selectByMouse: true
                                        padding: 10
                                        
                                        Component.onCompleted: {
                                            if (typeof SysHelper !== "undefined") {
                                                SysHelper.highlightDocument(codeTextArea.textDocument, isDark)
                                            }
                                        }
                                        
                                        onTextChanged: {
                                            model.codeText = text
                                        }

                                        onActiveFocusChanged: {
                                            if (activeFocus) {
                                                mainWindow.activeModuleName = model.moduleName
                                                mainWindow.cursorInfoText = getLineCol(text, cursorPosition)
                                            }
                                        }

                                        onCursorPositionChanged: {
                                            if (activeFocus) {
                                                mainWindow.cursorInfoText = getLineCol(text, cursorPosition)
                                            }
                                        }

                                        Shortcut {
                                            sequence: "Ctrl+S"
                                            onActivated: {
                                                SysHelper.saveModuleMain(model.moduleName, codeTextArea.text)
                                            }
                                        }
                                    }
                                }

                                // Resizing handles (Active when not maximized)
                                Item {
                                    anchors.fill: parent
                                    visible: !model.isMaximized

                                    // Left
                                    MouseArea {
                                        width: 5; anchors.left: parent.left; anchors.top: parent.top; anchors.bottom: parent.bottom; cursorShape: Qt.SizeHorCursor
                                        property int startX
                                        onPressed: (mouse) => { startX = mouse.x; win.forceActiveFocus() }
                                        onPositionChanged: (mouse) => {
                                            if (pressed) {
                                                var dx = mouse.x - startX
                                                if (win.width - dx >= 300) {
                                                    model.editorX = win.x + dx
                                                    model.editorWidth = win.width - dx
                                                }
                                            }
                                        }
                                    }
                                    // Right
                                    MouseArea {
                                        width: 5; anchors.right: parent.right; anchors.top: parent.top; anchors.bottom: parent.bottom; cursorShape: Qt.SizeHorCursor
                                        onPressed: { win.forceActiveFocus() }
                                        onPositionChanged: (mouse) => {
                                            if (pressed && mouse.x >= 300) {
                                                model.editorWidth = mouse.x
                                            }
                                        }
                                    }
                                    // Top
                                    MouseArea {
                                        height: 5; anchors.left: parent.left; anchors.right: parent.right; anchors.top: parent.top; cursorShape: Qt.SizeVerCursor
                                        property int startY
                                        onPressed: (mouse) => { startY = mouse.y; win.forceActiveFocus() }
                                        onPositionChanged: (mouse) => {
                                            if (pressed) {
                                                var dy = mouse.y - startY
                                                if (win.height - dy >= 200) {
                                                    model.editorY = win.y + dy
                                                    model.editorHeight = win.height - dy
                                                }
                                            }
                                        }
                                    }
                                    // Bottom
                                    MouseArea {
                                        height: 5; anchors.left: parent.left; anchors.right: parent.right; anchors.bottom: parent.bottom; cursorShape: Qt.SizeVerCursor
                                        onPressed: { win.forceActiveFocus() }
                                        onPositionChanged: (mouse) => {
                                            if (pressed && mouse.y >= 200) {
                                                model.editorHeight = mouse.y
                                            }
                                        }
                                    }
                                    // Corner TL
                                    MouseArea {
                                        width: 8; height: 8; anchors.left: parent.left; anchors.top: parent.top; cursorShape: Qt.SizeFDiagCursor
                                        property int startX; property int startY
                                        onPressed: (mouse) => { startX = mouse.x; startY = mouse.y; win.forceActiveFocus() }
                                        onPositionChanged: (mouse) => {
                                            if (pressed) {
                                                var dx = mouse.x - startX
                                                var dy = mouse.y - startY
                                                if (win.width - dx >= 300 && win.height - dy >= 200) {
                                                    model.editorX = win.x + dx
                                                    model.editorWidth = win.width - dx
                                                    model.editorY = win.y + dy
                                                    model.editorHeight = win.height - dy
                                                }
                                            }
                                        }
                                    }
                                    // Corner TR
                                    MouseArea {
                                        width: 8; height: 8; anchors.right: parent.right; anchors.top: parent.top; cursorShape: Qt.SizeBDiagCursor
                                        property int startY
                                        onPressed: (mouse) => { startY = mouse.y; win.forceActiveFocus() }
                                        onPositionChanged: (mouse) => {
                                            if (pressed) {
                                                var dy = mouse.y - startY
                                                var dx = mouse.x - win.width
                                                if (win.width + dx >= 300 && win.height - dy >= 200) {
                                                    model.editorWidth = win.width + dx
                                                    model.editorY = win.y + dy
                                                    model.editorHeight = win.height - dy
                                                }
                                            }
                                        }
                                    }
                                    // Corner BL
                                    MouseArea {
                                        width: 8; height: 8; anchors.left: parent.left; anchors.bottom: parent.bottom; cursorShape: Qt.SizeBDiagCursor
                                        property int startX
                                        onPressed: (mouse) => { startX = mouse.x; win.forceActiveFocus() }
                                        onPositionChanged: (mouse) => {
                                            if (pressed) {
                                                var dx = mouse.x - startX
                                                var dy = mouse.y - win.height
                                                if (win.width - dx >= 300 && win.height + dy >= 200) {
                                                    model.editorX = win.x + dx
                                                    model.editorWidth = win.width - dx
                                                    model.editorHeight = win.height + dy
                                                }
                                            }
                                        }
                                    }
                                    // Corner BR
                                    MouseArea {
                                        width: 8; height: 8; anchors.right: parent.right; anchors.bottom: parent.bottom; cursorShape: Qt.SizeFDiagCursor
                                        onPressed: { win.forceActiveFocus() }
                                        onPositionChanged: (mouse) => {
                                            if (pressed) {
                                                var dx = mouse.x - win.width
                                                var dy = mouse.y - win.height
                                                if (win.width + dx >= 300 && win.height + dy >= 200) {
                                                    model.editorWidth = win.width + dx
                                                    model.editorHeight = win.height + dy
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }

                    // 4. POLISHED VS CODE TERMINAL
                    Rectangle {
                        id: terminalContainer
                        color: bgColor
                        SplitView.preferredHeight: 250
                        SplitView.minimumHeight: 150
                        SplitView.fillWidth: true
                        visible: showTerminal

                        ColumnLayout {
                            anchors.fill: parent
                            spacing: 0

                            // Tab Headers (VS Code Style)
                            Rectangle {
                                Layout.fillWidth: true
                                height: 35
                                color: panelColor

                                Rectangle { width: parent.width; height: 1; color: borderColor; anchors.bottom: parent.bottom }

                                RowLayout {
                                    anchors.fill: parent
                                    anchors.margins: 0
                                    spacing: 0

                                    ListView {
                                        id: terminalTabs
                                        Layout.fillWidth: true
                                        Layout.fillHeight: true
                                        orientation: ListView.Horizontal
                                        model: terminalListModel
                                        spacing: 1
                                        delegate: Rectangle {
                                            width: 120
                                            height: 35
                                            color: (terminalTabs.currentIndex === index) ? bgColor : "transparent"
                                            
                                            // Accent border on bottom of active tab
                                            Rectangle {
                                                width: parent.width; height: 2; anchors.bottom: parent.bottom
                                                color: (terminalTabs.currentIndex === index) ? accentColor : "transparent"
                                            }

                                            RowLayout {
                                                anchors.fill: parent
                                                anchors.leftMargin: 12
                                                anchors.rightMargin: 8
                                                spacing: 5
                                                Text {
                                                    Layout.fillWidth: true
                                                    text: "🐚  " + model.name
                                                    color: (terminalTabs.currentIndex === index) ? textColor : textMutedColor
                                                    font.pixelSize: 11
                                                    font.bold: true
                                                    elide: Text.ElideRight
                                                }
                                                Text {
                                                    text: "✕"
                                                    color: textColor; font.pixelSize: 12; opacity: 0.6
                                                    MouseArea {
                                                        anchors.fill: parent
                                                        hoverEnabled: true
                                                        onEntered: parent.opacity = 1.0
                                                        onExited: parent.opacity = 0.6
                                                        onClicked: TerminalManager.removeSession(model.id)
                                                    }
                                                }
                                            }
                                            MouseArea {
                                                anchors.fill: parent; z: -1
                                                onClicked: terminalTabs.currentIndex = index
                                            }
                                        }
                                    }

                                    // Controls right side
                                    ComboBox {
                                        id: terminalEncodingSelector
                                        model: ["utf-8", "cp866", "windows-1251"]
                                        currentIndex: model.indexOf(defEncoding) !== -1 ? model.indexOf(defEncoding) : 0
                                        width: 90; height: 24
                                        Layout.alignment: Qt.AlignVCenter
                                        Layout.rightMargin: 6
                                    }

                                    ComboBox {
                                        id: shellSelector
                                        model: Qt.platform.os === "windows" ? ["powershell", "cmd"] : ["bash", "sh"]
                                        width: 110; height: 24
                                        Layout.alignment: Qt.AlignVCenter
                                        Layout.rightMargin: 6
                                    }

                                    Button {
                                        text: "+"
                                        width: 26; height: 24
                                        Layout.alignment: Qt.AlignVCenter
                                        Layout.rightMargin: 15
                                        onClicked: {
                                            TerminalManager.createSession(shellSelector.currentText, terminalEncodingSelector.currentText)
                                        }
                                    }
                                }
                            }

                            // Terminal Output Area
                            Rectangle {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                color: bgColor

                                Flickable {
                                    id: terminalFlickable
                                    anchors.fill: parent
                                    contentWidth: width
                                    contentHeight: terminalOutput.height + terminalInputRow.height + 20
                                    clip: true
                                    boundsBehavior: Flickable.StopAtBounds

                                    Column {
                                        width: parent.width

                                        TextEdit {
                                            id: terminalOutput
                                            width: parent.width
                                            color: textColor
                                            font.family: "Consolas, Courier New, monospace"
                                            font.pixelSize: 12
                                            readOnly: true
                                            selectByMouse: true
                                            textFormat: TextEdit.PlainText
                                            wrapMode: TextEdit.Wrap
                                            padding: 10
                                        }

                                        RowLayout {
                                            id: terminalInputRow
                                            width: parent.width
                                            spacing: 5
                                            Text {
                                                text: ">"
                                                color: accentColor
                                                font.family: "Consolas, Courier New, monospace"
                                                font.pixelSize: 12
                                                leftPadding: 10
                                            }
                                            TextInput {
                                                id: terminalInput
                                                Layout.fillWidth: true
                                                color: textColor
                                                font.family: "Consolas, Courier New, monospace"
                                                font.pixelSize: 12
                                                focus: true
                                                
                                                property var cmdHistory: []
                                                property int cmdHistoryIndex: -1

                                                onAccepted: {
                                                    var cmd = text
                                                    if (cmd.trim() !== "") {
                                                        var hist = cmdHistory
                                                        hist.push(cmd)
                                                        if (hist.length > 100) {
                                                            hist.shift()
                                                        }
                                                        cmdHistory = hist
                                                    }
                                                    cmdHistoryIndex = -1
                                                    
                                                    if (terminalTabs.currentIndex >= 0 && terminalListModel.count > 0) {
                                                        var sessionId = terminalListModel.get(terminalTabs.currentIndex).id;
                                                        TerminalManager.writeToSession(sessionId, cmd);
                                                        terminalOutput.text += "> " + cmd + "\n";
                                                        text = "";
                                                    }
                                                }

                                                Keys.onUpPressed: {
                                                    if (cmdHistory.length > 0) {
                                                        if (cmdHistoryIndex === -1) {
                                                            cmdHistoryIndex = cmdHistory.length - 1
                                                        } else if (cmdHistoryIndex > 0) {
                                                            cmdHistoryIndex--
                                                        }
                                                        text = cmdHistory[cmdHistoryIndex]
                                                        cursorPosition = text.length
                                                    }
                                                }

                                                Keys.onDownPressed: {
                                                    if (cmdHistoryIndex !== -1) {
                                                        if (cmdHistoryIndex < cmdHistory.length - 1) {
                                                            cmdHistoryIndex++
                                                            text = cmdHistory[cmdHistoryIndex]
                                                        } else {
                                                            cmdHistoryIndex = -1
                                                            text = ""
                                                        }
                                                        cursorPosition = text.length
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }

                // Right Sidebar (Properties + Debugger)
                SplitView {
                    id: rightSidebar
                    orientation: Qt.Vertical
                    SplitView.preferredWidth: 250
                    SplitView.minimumWidth: 150
                    visible: showProperties || showDebugger
                    handle: VSSplitHandle {}

                    Rectangle {
                        id: propertiesPanel
                        color: panelColor
                        SplitView.fillHeight: true
                        SplitView.fillWidth: true
                        visible: showProperties
                        
                        ColumnLayout {
                            anchors.fill: parent
                            spacing: 0
                            Rectangle {
                                Layout.fillWidth: true
                                height: 35
                                color: headerColor
                                Text { text: "СВОЙСТВА"; color: textColor; font.bold: true; font.pixelSize: 11; anchors.verticalCenter: parent.verticalCenter; anchors.left: parent.left; anchors.leftMargin: 20 }
                            }
                            Item { Layout.fillHeight: true; Layout.fillWidth: true }
                        }
                    }

                    Rectangle {
                        id: debuggerPanel
                        color: panelColor
                        SplitView.fillHeight: true
                        SplitView.fillWidth: true
                        visible: showDebugger
                        
                        ColumnLayout {
                            anchors.fill: parent
                            spacing: 0
                            Rectangle {
                                Layout.fillWidth: true
                                height: 35
                                color: headerColor
                                Text { text: "ОТЛАДЧИК"; color: textColor; font.bold: true; font.pixelSize: 11; anchors.verticalCenter: parent.verticalCenter; anchors.left: parent.left; anchors.leftMargin: 20 }
                            }
                            Item { Layout.fillHeight: true; Layout.fillWidth: true }
                        }
                    }
                }
            }
        }

        // 5. BLUE STATUS BAR AT THE BOTTOM (VS Code style)
        Rectangle {
            id: statusBar
            Layout.fillWidth: true
            height: 22
            color: statusBarBg

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 10
                anchors.rightMargin: 10
                spacing: 12

                // Left items
                RowLayout {
                    spacing: 8
                    Layout.alignment: Qt.AlignVCenter
                    Text { text: "⎇  no-ai"; color: "#ffffff"; font.pixelSize: 11; font.bold: true }
                    Text { text: "⟳"; color: "#ffffff"; font.pixelSize: 12 }
                    Text { text: "✕ 0  ⚠ 0"; color: "#ffffff"; font.pixelSize: 11 }
                }

                Item { Layout.fillWidth: true } // Spacer

                // Right items
                RowLayout {
                    spacing: 12
                    Layout.alignment: Qt.AlignVCenter
                    Text { text: cursorInfoText; color: "#ffffff"; font.pixelSize: 11 }
                    Text { text: "Spaces: 4"; color: "#ffffff"; font.pixelSize: 11 }
                    Text { text: defEncoding.toUpperCase(); color: "#ffffff"; font.pixelSize: 11 }
                    Text { text: "Python"; color: "#ffffff"; font.pixelSize: 11 }
                    Text { text: ".venv (Python 3.11)"; color: "#ffffff"; font.pixelSize: 11 }
                }
            }
        }
    }

    // Model for terminal tabs
    ListModel {
        id: terminalListModel
    }

    // Mapping from index to output text
    property var terminalOutputs: ({})

    Connections {
        target: typeof TerminalManager !== "undefined" ? TerminalManager : null
        function onSessionAdded(id, name) {
            terminalListModel.append({"id": id, "name": name});
            terminalOutputs[id] = "";
            terminalTabs.currentIndex = terminalListModel.count - 1;
        }
        function onSessionRemoved(id) {
            for (var i = 0; i < terminalListModel.count; ++i) {
                if (terminalListModel.get(i).id === id) {
                    terminalListModel.remove(i);
                    break;
                }
            }
            if (terminalTabs.currentIndex >= terminalListModel.count) {
                terminalTabs.currentIndex = terminalListModel.count - 1;
            }
            if (terminalListModel.count === 0) {
                terminalOutput.text = "";
            } else {
                updateTerminalOutput();
            }
        }
        function onOutputReceived(id, text) {
            if (terminalOutputs[id] === undefined) {
                terminalOutputs[id] = "";
            }
            terminalOutputs[id] += text;
            
            // Limit output size to prevent memory issues
            if (terminalOutputs[id].length > 10000) {
                terminalOutputs[id] = terminalOutputs[id].substring(terminalOutputs[id].length - 10000);
            }
            
            if (terminalTabs.currentIndex >= 0 && terminalListModel.count > 0) {
                if (terminalListModel.get(terminalTabs.currentIndex).id === id) {
                    terminalOutput.text = terminalOutputs[id];
                    // Scroll to bottom
                    terminalFlickable.contentY = Math.max(0, terminalFlickable.contentHeight - terminalFlickable.height);
                }
            }
        }
    }

    Connections {
        target: terminalTabs
        function onCurrentIndexChanged() {
            updateTerminalOutput();
        }
    }

    function updateTerminalOutput() {
        if (terminalTabs.currentIndex >= 0 && terminalListModel.count > 0) {
            var currentId = terminalListModel.get(terminalTabs.currentIndex).id;
            terminalOutput.text = terminalOutputs[currentId] || "";
            terminalFlickable.contentY = Math.max(0, terminalFlickable.contentHeight - terminalFlickable.height);
        } else {
            terminalOutput.text = "";
        }
    }

    // Model for open floating editors
    ListModel {
        id: openEditorsModel
    }

    property int maxZIndex: 10
    property string cursorInfoText: "Ln 1, Col 1"
    property string activeModuleName: ""

    function getLineCol(text, pos) {
        var lines = text.substring(0, pos).split("\n");
        var line = lines.length;
        var col = lines[lines.length - 1].length + 1;
        return "Ln " + line + ", Col " + col;
    }

    function openModuleEditor(name) {
        // Check if already open
        for (var i = 0; i < openEditorsModel.count; ++i) {
            if (openEditorsModel.get(i).moduleName === name) {
                var win = openEditorsRepeater.itemAt(i)
                if (win) {
                    openEditorsModel.setProperty(i, "isMinimized", false)
                    bringToFront(win, i)
                    win.forceActiveFocus()
                }
                return
            }
        }
        
        // Read content
        var code = ""
        if (typeof SysHelper !== "undefined") {
            code = SysHelper.readModuleMain(name)
        }
        
        // Calculate cascade position
        var offset = 30 * (openEditorsModel.count % 8)
        var startX = 50 + offset
        var startY = 40 + offset
        
        openEditorsModel.append({
            "moduleName": name,
            "codeText": code,
            "editorX": startX,
            "editorY": startY,
            "editorWidth": 700,
            "editorHeight": 450,
            "isMaximized": false,
            "isMinimized": false,
            "zIndex": ++maxZIndex
        })
        activeModuleName = name
    }

    function bringToFront(win, idx) {
        maxZIndex += 1
        openEditorsModel.setProperty(idx, "zIndex", maxZIndex)
        activeModuleName = openEditorsModel.get(idx).moduleName
    }

    function saveAllOpenedModules() {
        for (var i = 0; i < openEditorsModel.count; ++i) {
            var item = openEditorsModel.get(i)
            SysHelper.saveModuleMain(item.moduleName, item.codeText)
        }
    }

    function triggerExport(type, moduleName) {
        exportLoadingDialog.moduleName = moduleName
        exportLoadingDialog.exportType = type
        exportLoadingDialog.open()
        exportTimer.restart()
    }

    Component.onCompleted: {
        refreshModules();
        
        if (typeof initialModuleName !== "undefined" && initialModuleName !== "") {
            openModuleEditor(initialModuleName);
        }
        
        // Center the window on the monitor where the cursor is
        if (typeof SysHelper !== "undefined") {
            var g = SysHelper.cursorPos()
            var sg = SysHelper.screenGeometry(g.x, g.y)
            
            var newX = sg.x + (sg.width - mainWindow.width) / 2
            var newY = sg.y + (sg.height - mainWindow.height) / 2
            
            // Ensure the window is within screen bounds and header is reachable
            if (newY < sg.y + 10) {
                newY = sg.y + 10
            }
            if (newX < sg.x + 10) {
                newX = sg.x + 10
            }
            
            mainWindow.x = newX
            mainWindow.y = newY
        }
        
        mainWindow.visible = true

        // Initial terminal session
        if (typeof TerminalManager !== "undefined") {
            if (Qt.platform.os === "windows") {
                TerminalManager.createSession("powershell", defEncoding)
            } else {
                TerminalManager.createSession("bash", defEncoding)
            }
        }
    }
}
