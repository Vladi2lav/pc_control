import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

ApplicationWindow {
    id: mainWindow
    width: 1280
    height: 800
    visible: true
    title: "Конфигуратор"
    minimumWidth: 800
    minimumHeight: 600
    flags: Qt.Window | Qt.FramelessWindowHint

    property bool isDark: SettingsManager && SettingsManager.theme === "dark"
    property string defEncoding: SettingsManager ? SettingsManager.defaultEncoding : "utf-8"
    
    // Theme colors (VS Code style 1-in-1)
    property color bgColor: isDark ? "#1e1e1e" : "#ffffff"
    property color panelColor: isDark ? "#252526" : "#f3f3f3"
    property color borderColor: isDark ? "#3c3c3c" : "#cccccc"
    property color textColor: isDark ? "#cccccc" : "#333333"
    property color headerColor: isDark ? "#252526" : "#f3f3f3"
    property color activeTabColor: isDark ? "#1e1e1e" : "#ffffff"
    property color inactiveTabColor: isDark ? "#2d2d2d" : "#ececec"
    property color accentColor: "#007fd4"

    // Visibility States
    property bool showExplorer: true
    property bool showHierarchy: true
    property bool showProperties: true
    property bool showDebugger: false
    property bool showTerminal: true

    color: bgColor

    component VSSplitHandle: Rectangle {
        implicitWidth: 4
        implicitHeight: 4
        color: SplitHandle.hovered || SplitHandle.pressed ? accentColor : "transparent"
    }

    header: Rectangle {
        id: customTitleBar
        height: 35
        color: isDark ? "#333333" : "#e8e8e8"
        
        MouseArea {
            anchors.fill: parent
            property point clickPos: Qt.point(0,0)
            onPressed: (mouse) => { clickPos = Qt.point(mouse.x, mouse.y) }
            onPositionChanged: (mouse) => {
                mainWindow.x += mouse.x - clickPos.x
                mainWindow.y += mouse.y - clickPos.y
            }
        }

        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 10
            spacing: 5
            
            // App Icon Placeholder
            Rectangle {
                width: 16
                height: 16
                color: accentColor
                radius: 3
                Text { text: "C"; color: "white"; font.pixelSize: 10; font.bold: true; anchors.centerIn: parent }
            }

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

                Menu { title: qsTr("Файл") }
                Menu { title: qsTr("Правка") }
                Menu { title: qsTr("Выделение") }
                Menu { 
                    title: qsTr("Вид")
                    MenuItem { 
                        text: showExplorer ? qsTr("Скрыть Проводник") : qsTr("Показать Проводник")
                        onTriggered: { 
                            showExplorer = !showExplorer; 
                            if (showExplorer) {
                                leftSidebar.SplitView.preferredWidth = 250;
                                explorerPanel.SplitView.preferredHeight = 200;
                            }
                        } 
                    }
                    MenuItem { 
                        text: showHierarchy ? qsTr("Скрыть Иерархию") : qsTr("Показать Иерархию")
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
                }
                Menu { title: qsTr("Переход") }
                Menu { title: qsTr("Запуск") }
                Menu { 
                    title: qsTr("Терминал")
                    MenuItem { 
                        text: showTerminal ? qsTr("Скрыть Терминал") : qsTr("Показать Терминал")
                        onTriggered: { 
                            showTerminal = !showTerminal; 
                            if (showTerminal) terminalContainer.SplitView.preferredHeight = 250;
                        } 
                    }
                }
                Menu { 
                    title: qsTr("Настройки")
                    MenuItem {
                        text: qsTr("Открыть настройки")
                        onTriggered: settingsWindow.show()
                    }
                }
            }

            Item { Layout.fillWidth: true } // Spacer

            // Search Bar Area
            RowLayout {
                spacing: 10
                Text { text: "←"; color: textColor; font.pixelSize: 16 }
                Text { text: "→"; color: textColor; font.pixelSize: 16; opacity: 0.5 }
                
                Rectangle {
                    width: 400
                    height: 24
                    color: isDark ? "#2d2d2d" : "#ffffff"
                    border.color: isDark ? "#3c3c3c" : "#cccccc"
                    radius: 6
                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 10
                        Text { text: "🔍"; color: textColor; opacity: 0.6; font.pixelSize: 12 }
                        Text { text: "control_no_ai"; color: textColor; opacity: 0.8; font.pixelSize: 12; Layout.fillWidth: true; horizontalAlignment: Text.AlignHCenter }
                    }
                }
            }

            Item { Layout.fillWidth: true } // Spacer

            // Layout Toggles
            RowLayout {
                spacing: 8
                Text { text: "◧"; color: showExplorer||showHierarchy ? textColor : (isDark ? "#666" : "#aaa"); font.pixelSize: 14; MouseArea { anchors.fill: parent; onClicked: showExplorer = !showExplorer } }
                Text { text: "⬒"; color: showTerminal ? textColor : (isDark ? "#666" : "#aaa"); font.pixelSize: 14; MouseArea { anchors.fill: parent; onClicked: showTerminal = !showTerminal } }
                Text { text: "◨"; color: showProperties||showDebugger ? textColor : (isDark ? "#666" : "#aaa"); font.pixelSize: 14; MouseArea { anchors.fill: parent; onClicked: showProperties = !showProperties } }
            }

            Item { width: 10 } // Margin before window controls

            // Window Controls
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

    // Main Layout
    SplitView {
        anchors.fill: parent
        orientation: Qt.Horizontal
        handle: VSSplitHandle {}

        // Left Sidebar
        SplitView {
            id: leftSidebar
            orientation: Qt.Vertical
            SplitView.preferredWidth: 250
            SplitView.minimumWidth: 150
            visible: showExplorer || showHierarchy
            handle: VSSplitHandle {}

            Rectangle {
                id: explorerPanel
                color: panelColor
                SplitView.fillHeight: true
                SplitView.fillWidth: true
                SplitView.minimumHeight: 100
                visible: showExplorer
                
                ColumnLayout {
                    anchors.fill: parent
                    spacing: 0
                    Rectangle {
                        Layout.fillWidth: true
                        height: 35
                        color: headerColor
                        Text { text: "ПРОВОДНИК"; color: textColor; font.bold: true; font.pixelSize: 11; anchors.verticalCenter: parent.verticalCenter; anchors.left: parent.left; anchors.leftMargin: 20 }
                        MouseArea {
                            anchors.fill: parent
                            acceptedButtons: Qt.RightButton
                            onClicked: explorerMenu.popup()
                        }
                        Menu {
                            id: explorerMenu
                            MenuItem { text: qsTr("Скрыть панель"); onTriggered: showExplorer = false }
                            MenuItem { text: qsTr("Настройки"); onTriggered: settingsWindow.show() }
                        }
                    }
                    Item { Layout.fillHeight: true; Layout.fillWidth: true }
                }
            }

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
                        Text { text: "ИЕРАРХИЯ"; color: textColor; font.bold: true; font.pixelSize: 11; anchors.verticalCenter: parent.verticalCenter; anchors.left: parent.left; anchors.leftMargin: 20 }
                        MouseArea {
                            anchors.fill: parent
                            acceptedButtons: Qt.RightButton
                            onClicked: hierarchyMenu.popup()
                        }
                        Menu {
                            id: hierarchyMenu
                            MenuItem { text: qsTr("Скрыть панель"); onTriggered: showHierarchy = false }
                            MenuItem { text: qsTr("Настройки"); onTriggered: settingsWindow.show() }
                        }
                    }
                    Item { Layout.fillHeight: true; Layout.fillWidth: true }
                }
            }
        }

        // Center Area (Editor + Terminal)
        SplitView {
            SplitView.fillWidth: true
            orientation: Qt.Vertical
            handle: VSSplitHandle {}

            // Editor
            Rectangle {
                id: centralArea
                color: bgColor
                SplitView.fillHeight: true
                SplitView.fillWidth: true
                SplitView.minimumHeight: 200
                
                Text {
                    text: "Рабочая область"
                    anchors.centerIn: parent
                    color: textColor
                    opacity: 0.5
                    font.pixelSize: 24
                }
            }

            // Terminal
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
                    
                    // Terminal Header / Tabs
                    Rectangle {
                        Layout.fillWidth: true
                        height: 35
                        color: panelColor // Header in bottom panel
                        
                        RowLayout {
                            anchors.fill: parent
                            anchors.margins: 0
                            
                            ListView {
                                id: terminalTabs
                                Layout.fillHeight: true
                                Layout.fillWidth: true
                                orientation: ListView.Horizontal
                                model: terminalListModel
                                spacing: 1
                                
                                delegate: Rectangle {
                                    width: 120
                                    height: terminalTabs.height
                                    color: terminalTabs.currentIndex === index ? activeTabColor : inactiveTabColor
                                    
                                    // Top border for active tab (VS Code style)
                                    Rectangle {
                                        width: parent.width
                                        height: 2
                                        anchors.top: parent.top
                                        color: terminalTabs.currentIndex === index ? accentColor : "transparent"
                                    }
                                    
                                    RowLayout {
                                        anchors.fill: parent
                                        anchors.leftMargin: 10
                                        anchors.rightMargin: 10
                                        Text { 
                                            Layout.fillWidth: true
                                            text: model.name
                                            color: terminalTabs.currentIndex === index ? textColor : (isDark ? "#999999" : "#666666")
                                            elide: Text.ElideRight
                                        }
                                        Text {
                                            text: "×"
                                            color: textColor
                                            font.pixelSize: 16
                                            opacity: 0.6
                                            MouseArea {
                                                anchors.fill: parent
                                                hoverEnabled: true
                                                onEntered: parent.opacity = 1.0
                                                onExited: parent.opacity = 0.6
                                                onClicked: {
                                                    TerminalManager.removeSession(model.id);
                                                }
                                            }
                                        }
                                    }
                                    
                                    MouseArea {
                                        anchors.fill: parent
                                        z: -1
                                        onClicked: terminalTabs.currentIndex = index
                                    }
                                }
                            }
                            
                            ComboBox {
                                id: terminalEncodingSelector
                                model: ["utf-8", "cp866", "windows-1251"]
                                currentIndex: model.indexOf(defEncoding) !== -1 ? model.indexOf(defEncoding) : 0
                                width: 100
                                height: 25
                                Layout.alignment: Qt.AlignVCenter
                                Layout.rightMargin: 5
                            }
                            
                            ComboBox {
                                id: shellSelector
                                model: Qt.platform.os === "windows" ? ["powershell", "cmd"] : ["bash", "sh"]
                                width: 120
                                height: 25
                                Layout.alignment: Qt.AlignVCenter
                                Layout.rightMargin: 5
                            }
                            
                            Button {
                                text: "+"
                                width: 30
                                height: 25
                                Layout.alignment: Qt.AlignVCenter
                                Layout.rightMargin: 10
                                onClicked: {
                                    TerminalManager.createSession(shellSelector.currentText, terminalEncodingSelector.currentText)
                                }
                            }
                        }
                    }
                    
                    // Terminal Content (Output + Input)
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        color: bgColor
                        
                        Flickable {
                            id: terminalFlickable
                            anchors.fill: parent
                            contentWidth: width
                            contentHeight: terminalOutput.height + terminalInputRow.height
                            clip: true
                            
                            boundsBehavior: Flickable.StopAtBounds
                            
                            Column {
                                width: parent.width
                                
                                TextEdit {
                                    id: terminalOutput
                                    width: parent.width
                                    color: textColor
                                    font.family: "Consolas, Courier New, monospace"
                                    font.pixelSize: 13
                                    readOnly: true
                                    selectByMouse: true
                                    textFormat: TextEdit.PlainText
                                    wrapMode: TextEdit.Wrap
                                    padding: 8
                                }
                                
                                RowLayout {
                                    id: terminalInputRow
                                    width: parent.width
                                    spacing: 5
                                    Text {
                                        text: ">"
                                        color: accentColor
                                        font.family: "Consolas, Courier New, monospace"
                                        font.pixelSize: 13
                                        leftPadding: 8
                                    }
                                    TextInput {
                                        id: terminalInput
                                        Layout.fillWidth: true
                                        color: textColor
                                        font.family: "Consolas, Courier New, monospace"
                                        font.pixelSize: 13
                                        focus: true
                                        onAccepted: {
                                            if (terminalTabs.currentIndex >= 0 && terminalListModel.count > 0) {
                                                var sessionId = terminalListModel.get(terminalTabs.currentIndex).id;
                                                TerminalManager.writeToSession(sessionId, text);
                                                terminalOutput.text += "> " + text + "\n";
                                                text = "";
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

        // Right Sidebar
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

    Component.onCompleted: {
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
