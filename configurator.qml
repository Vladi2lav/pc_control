/*
================================================================================
AI INSTRUCTIONS & FILE LAYOUT (ATTENTION: ALWAYS UPDATE THIS BLOCK AFTER EDITS)
================================================================================
Purpose: Main user interface for the Lumen Configurator, written in QML.

FILE LAYOUT & SECTION INDEX:
- L6-L50: Palette properties, visibility flags, theme/colors.
- L51-L155: Flat list tree model flattening logic, expand/collapse and CRUD helpers.
- L157-L245: Selected tree node property readers/savers.
- L247-L347: Workspace floating window loaders for py and qml editors.
- L349-L509: Vector Canvas Icons (ChevronIcon, FolderIcon, CubeIcon, FormIcon, VariableIcon).
- L512-L739: Top application header (Titlebar, MenuBar, window maximize/minimize/close).
- L741-L768: Configuration toolbar (Save modules button).
- L770-L832: Dialog configurations (Create module dialog, create form dialog).
- L834-L1340: Dialog confirmation boxes (deletions and warning modals).
- L1342-L1532: SplitView Left Sidebar (Configuration hierarchy panel ListView & Explorer tree view).
- L1535-L2400: SplitView Center Workspace (MDI floating windows area, text area codes editing tabs).
- L2401-L2618: SplitView Right Sidebar (Properties Panel sheet with Modules, Forms, and Variables sheets).
- L2620-L2656: StatusBar at the bottom (branch, encoding, space indices).
- L2657-L2802: Native Terminal emulator container and session scripts.
================================================================================
*/

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

    onActiveChanged: {
        if (!active && typeof SysHelper !== "undefined") {
            SysHelper.releaseCursor()
        }
    }

    property bool isDark: SettingsManager && SettingsManager.theme === "dark"
    property string defEncoding: SettingsManager ? SettingsManager.defaultEncoding : "utf-8"
    
    // Theme colors aligned with Antigravity IDE / VS Code Dark
    property color bgColor: isDark ? "#1e1e1e" : "#ffffff"
    property color windowBgColor: isDark ? "#212121" : "#fafafa"
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
    
    ListModel { id: visibleTreeModel }
    property var expandedTreeNodes: ({"main": true})
    property var selectedTreeNode: null

    function refreshTree() {
        if (typeof SysHelper === "undefined") return;
        var rawJson = SysHelper.getTreeStructure();
        var allNodes = JSON.parse(rawJson);
        var visibleList = [];
        
        function isNodeVisible(node) {
            var parentId = node.parentId;
            while (parentId !== "") {
                if (!expandedTreeNodes[parentId]) {
                    return false;
                }
                var pNode = null;
                for (var i = 0; i < allNodes.length; i++) {
                    if (allNodes[i].id === parentId) {
                        pNode = allNodes[i];
                        break;
                    }
                }
                if (!pNode) break;
                parentId = pNode.parentId;
            }
            return true;
        }
        
        for (var i = 0; i < allNodes.length; i++) {
            var node = allNodes[i];
            if (node.parentId === "" || isNodeVisible(node)) {
                node.isExpanded = !!expandedTreeNodes[node.id];
                visibleList.push(node);
            }
        }
        
        visibleTreeModel.clear();
        for (var j = 0; j < visibleList.length; j++) {
            visibleTreeModel.append(visibleList[j]);
        }
    }

    Connections {
        target: typeof SysHelper !== "undefined" ? SysHelper : null
        function onModulesChanged() { refreshTree(); }
    }

    function toggleNodeExpanded(id) {
        if (expandedTreeNodes[id]) {
            delete expandedTreeNodes[id];
        } else {
            expandedTreeNodes[id] = true;
        }
        expandedTreeNodes = Object.assign({}, expandedTreeNodes);
        refreshTree();
    }

    function createVariableForModule(modFolder) {
        var newIndex = SysHelper.createVariable(modFolder);
        if (newIndex >= 0) {
            var varsNodeId = "variables_" + modFolder;
            expandedTreeNodes[varsNodeId] = true;
            expandedTreeNodes = Object.assign({}, expandedTreeNodes);
            refreshTree();
            
            selectedTreeNode = {
                "id": "var_" + modFolder + "_" + newIndex,
                "parentId": varsNodeId,
                "name": "newVar",
                "folderName": "",
                "type": "variable",
                "depth": 3,
                "hasChildren": false,
                "icon": "variable",
                "variableIndex": newIndex
            };
            loadSelectedNodeProperties();
        }
    }

    function showTreeContextMenu(model, x, y) {
        if (model.type === "root") {
            contextMenuRoot.popup();
        } else if (model.type === "module") {
            contextMenuModule.folderName = model.folderName;
            contextMenuModule.popup();
        } else if (model.type === "category_forms") {
            contextMenuCategoryForms.folderName = model.parentId.substring(7);
            contextMenuCategoryForms.popup();
        } else if (model.type === "category_variables") {
            contextMenuCategoryVariables.folderName = model.parentId.substring(7);
            contextMenuCategoryVariables.popup();
        } else if (model.type === "form") {
            var modFolder = model.parentId.substring(6);
            contextMenuForm.moduleFolder = modFolder;
            contextMenuForm.formFolder = model.folderName;
            contextMenuForm.popup();
        } else if (model.type === "variable") {
            var modFolder = model.parentId.substring(10);
            contextMenuVariable.moduleFolder = modFolder;
            contextMenuVariable.varIndex = model.variableIndex;
            contextMenuVariable.popup();
        }
    }

    function loadSelectedNodeProperties() {
        if (!selectedTreeNode) return;
        
        if (selectedTreeNode.type === "module") {
            var raw = SysHelper.readModuleProperties(selectedTreeNode.folderName);
            var props = JSON.parse(raw);
            propModuleNameField.text = props.name || selectedTreeNode.folderName;
            propModuleVersionField.text = props.version || "1.0.0";
            propModuleAuthorField.text = props.author || "";
            propModuleDescField.text = props.description || "";
        } else if (selectedTreeNode.type === "form") {
            var modFolder = selectedTreeNode.parentId.substring(6);
            var raw = SysHelper.readFormProperties(modFolder, selectedTreeNode.folderName);
            var props = JSON.parse(raw);
            propFormNameField.text = props.name || selectedTreeNode.folderName;
            propFormTitleField.text = props.title || selectedTreeNode.folderName;
            propFormWidthField.text = props.width !== undefined ? props.width.toString() : "800";
            propFormHeightField.text = props.height !== undefined ? props.height.toString() : "600";
        } else if (selectedTreeNode.type === "variable") {
            var modFolder = selectedTreeNode.parentId.substring(10);
            var raw = SysHelper.readVariableProperties(modFolder, selectedTreeNode.variableIndex);
            var props = JSON.parse(raw);
            propVarNameField.text = props.name || "";
            var tIdx = propVarTypeCombo.indexOfValue(props.type || "String");
            propVarTypeCombo.currentIndex = tIdx !== -1 ? tIdx : 0;
            propVarValueField.text = props.value !== undefined ? props.value.toString() : "";
            propVarDescField.text = props.description || "";
        }
    }

    function saveSelectedNodeProperties() {
        if (!selectedTreeNode) return;
        
        if (selectedTreeNode.type === "module") {
            var modProps = {
                "name": propModuleNameField.text,
                "version": propModuleVersionField.text,
                "author": propModuleAuthorField.text,
                "description": propModuleDescField.text
            };
            var res = SysHelper.saveModuleProperties(selectedTreeNode.folderName, JSON.stringify(modProps));
            if (res !== selectedTreeNode.folderName) {
                var oldId = selectedTreeNode.id;
                var newId = "module_" + res;
                if (expandedTreeNodes[oldId]) {
                    expandedTreeNodes[newId] = true;
                    delete expandedTreeNodes[oldId];
                }
                for (var i = 0; i < openEditorsModel.count; i++) {
                    if (openEditorsModel.get(i).moduleName === selectedTreeNode.folderName) {
                        openEditorsModel.setProperty(i, "moduleName", res);
                    }
                }
                selectedTreeNode.folderName = res;
                selectedTreeNode.id = newId;
            }
            selectedTreeNode.name = propModuleNameField.text;
            refreshTree();
        } else if (selectedTreeNode.type === "form") {
            var formProps = {
                "name": propFormNameField.text,
                "title": propFormTitleField.text,
                "width": parseInt(propFormWidthField.text) || 800,
                "height": parseInt(propFormHeightField.text) || 600
            };
            var modFolder = selectedTreeNode.parentId.substring(6);
            var res = SysHelper.saveFormProperties(modFolder, selectedTreeNode.folderName, JSON.stringify(formProps));
            if (res !== selectedTreeNode.folderName) {
                var oldId = "form_" + modFolder + "_" + selectedTreeNode.folderName;
                var newId = "form_" + modFolder + "_" + res;
                for (var i = 0; i < openEditorsModel.count; i++) {
                    if (openEditorsModel.get(i).editorId === oldId) {
                        openEditorsModel.setProperty(i, "editorId", newId);
                        openEditorsModel.setProperty(i, "formName", res);
                    }
                }
                selectedTreeNode.folderName = res;
                selectedTreeNode.id = newId;
            }
            selectedTreeNode.name = propFormNameField.text;
            refreshTree();
        } else if (selectedTreeNode.type === "variable") {
            var varProps = {
                "name": propVarNameField.text,
                "type": propVarTypeCombo.currentText,
                "value": propVarValueField.text,
                "description": propVarDescField.text
            };
            var modFolder = selectedTreeNode.parentId.substring(10);
            SysHelper.saveVariableProperties(modFolder, selectedTreeNode.variableIndex, JSON.stringify(varProps));
            selectedTreeNode.name = propVarNameField.text;
            refreshTree();
        }
    }

    function openFormEditor(moduleFolder, formFolder) {
        var editorId = "form_" + moduleFolder + "_" + formFolder;
        for (var i = 0; i < openEditorsModel.count; ++i) {
            var item = openEditorsModel.get(i);
            if (item.editorId === editorId) {
                var win = openEditorsRepeater.itemAt(i);
                if (win) {
                    openEditorsModel.setProperty(i, "isMinimized", false);
                    var newX = Math.max(0, Math.round((workspace.width - win.width) / 2));
                    var newY = Math.max(workspaceTabBar.visible ? 35 : 0, Math.round((workspace.height - win.height) / 2));
                    openEditorsModel.setProperty(i, "editorX", newX);
                    openEditorsModel.setProperty(i, "editorY", newY);
                    bringToFront(win, i);
                    win.forceActiveFocus();
                }
                return;
            }
        }
        
        var raw = SysHelper.readFormFiles(moduleFolder, formFolder);
        var codes = JSON.parse(raw);
        var defaultWidth = 800;
        var defaultHeight = 550;
        var startX = Math.max(0, Math.round((workspace.width - defaultWidth) / 2));
        var startY = Math.max(workspaceTabBar.visible ? 35 : 0, Math.round((workspace.height - defaultHeight) / 2));
        
        openEditorsModel.append({
            "editorId": editorId,
            "editorType": "form",
            "moduleName": moduleFolder,
            "formName": formFolder,
            "pyCode": codes.pyCode,
            "qmlCode": codes.qmlCode,
            "currentTab": 0,
            "editorX": startX,
            "editorY": startY,
            "editorWidth": defaultWidth,
            "editorHeight": defaultHeight,
            "isMaximized": false,
            "isMinimized": false,
            "zIndex": ++maxZIndex
        });
        activeModuleName = moduleFolder;
    }

    function openModuleEditor(name) {
        var editorId = "module_" + name;
        for (var i = 0; i < openEditorsModel.count; ++i) {
            var item = openEditorsModel.get(i);
            if (item.editorId === editorId) {
                var win = openEditorsRepeater.itemAt(i);
                if (win) {
                    openEditorsModel.setProperty(i, "isMinimized", false);
                    var newX = Math.max(0, Math.round((workspace.width - win.width) / 2));
                    var newY = Math.max(workspaceTabBar.visible ? 35 : 0, Math.round((workspace.height - win.height) / 2));
                    openEditorsModel.setProperty(i, "editorX", newX);
                    openEditorsModel.setProperty(i, "editorY", newY);
                    bringToFront(win, i);
                    win.forceActiveFocus();
                }
                return;
            }
        }
        
        var code = SysHelper.readModuleMain(name);
        var defaultWidth = 750;
        var defaultHeight = 480;
        var startX = Math.max(0, Math.round((workspace.width - defaultWidth) / 2));
        var startY = Math.max(workspaceTabBar.visible ? 35 : 0, Math.round((workspace.height - defaultHeight) / 2));
        
        openEditorsModel.append({
            "editorId": editorId,
            "editorType": "module",
            "moduleName": name,
            "codeText": code,
            "editorX": startX,
            "editorY": startY,
            "editorWidth": defaultWidth,
            "editorHeight": defaultHeight,
            "isMaximized": false,
            "isMinimized": false,
            "zIndex": ++maxZIndex
        });
        activeModuleName = name;
    }

    function saveEditor(idx) {
        var item = openEditorsModel.get(idx);
        if (!item) return;
        if (item.editorType === "form") {
            SysHelper.saveFormFiles(item.moduleName, item.formName, item.pyCode, item.qmlCode);
        } else {
            SysHelper.saveModuleMain(item.moduleName, item.codeText);
        }
    }

    function saveAllOpenedModules() {
        for (var i = 0; i < openEditorsModel.count; ++i) {
            saveEditor(i);
        }
    }

    color: bgColor

    component ChevronIcon: Item {
        width: 16
        height: 16
        property bool expanded: false
        Canvas {
            anchors.fill: parent
            rotation: expanded ? 90 : 0
            Behavior on rotation { NumberAnimation { duration: 150 } }
            onPaint: {
                var ctx = getContext("2d");
                ctx.reset();
                ctx.strokeStyle = textColor;
                ctx.lineWidth = 1.5;
                ctx.lineCap = "round";
                ctx.lineJoin = "round";
                ctx.beginPath();
                ctx.moveTo(6, 4);
                ctx.lineTo(10, 8);
                ctx.lineTo(6, 12);
                ctx.stroke();
            }
        }
    }

    component FolderIcon: Item {
        width: 16
        height: 16
        property bool open: false
        Canvas {
            anchors.fill: parent
            onPaint: {
                var ctx = getContext("2d");
                ctx.reset();
                ctx.fillStyle = isDark ? "#c59b27" : "#a17e1b";
                ctx.beginPath();
                ctx.rect(2, 4, 12, 9);
                ctx.fill();
                ctx.fillStyle = isDark ? "#e5b83b" : "#c69b27";
                ctx.beginPath();
                ctx.moveTo(2, 6);
                ctx.lineTo(6, 6);
                ctx.lineTo(8, 4);
                ctx.lineTo(13, 4);
                ctx.lineTo(13, 6);
                ctx.lineTo(2, 6);
                ctx.fill();
            }
        }
    }

    component CubeIcon: Item {
        width: 18
        height: 18
        Canvas {
            anchors.fill: parent
            onPaint: {
                var ctx = getContext("2d");
                ctx.reset();
                var cx = 9, cy = 9;
                ctx.fillStyle = "#2d7dd2";
                ctx.beginPath();
                ctx.moveTo(cx, cy - 8);
                ctx.lineTo(cx + 7, cy - 4);
                ctx.lineTo(cx, cy);
                ctx.lineTo(cx - 7, cy - 4);
                ctx.closePath();
                ctx.fill();
                ctx.fillStyle = "#1b4d8a";
                ctx.beginPath();
                ctx.moveTo(cx - 7, cy - 4);
                ctx.lineTo(cx, cy);
                ctx.lineTo(cx, cy + 8);
                ctx.lineTo(cx - 7, cy + 4);
                ctx.closePath();
                ctx.fill();
                ctx.fillStyle = "#113057";
                ctx.beginPath();
                ctx.moveTo(cx, cy);
                ctx.lineTo(cx + 7, cy - 4);
                ctx.lineTo(cx + 7, cy + 4);
                ctx.lineTo(cx, cy + 8);
                ctx.closePath();
                ctx.fill();
                ctx.fillStyle = "#55b1f9";
                ctx.beginPath();
                ctx.moveTo(cx, cy - 3);
                ctx.lineTo(cx + 4, cy - 1);
                ctx.lineTo(cx, cy + 1);
                ctx.lineTo(cx - 4, cy - 1);
                ctx.closePath();
                ctx.fill();
                ctx.fillStyle = "#439be3";
                ctx.beginPath();
                ctx.moveTo(cx - 4, cy - 1);
                ctx.lineTo(cx, cy + 1);
                ctx.lineTo(cx, cy + 5);
                ctx.lineTo(cx - 4, cy + 3);
                ctx.closePath();
                ctx.fill();
                ctx.fillStyle = "#3382c2";
                ctx.beginPath();
                ctx.moveTo(cx, cy + 1);
                ctx.lineTo(cx + 4, cy - 1);
                ctx.lineTo(cx + 4, cy + 3);
                ctx.lineTo(cx, cy + 5);
                ctx.closePath();
                ctx.fill();
            }
        }
    }

    component FormIcon: Item {
        width: 16
        height: 16
        Canvas {
            anchors.fill: parent
            onPaint: {
                var ctx = getContext("2d");
                ctx.reset();
                ctx.strokeStyle = isDark ? "#4ec9b0" : "#267f99";
                ctx.lineWidth = 1.2;
                ctx.strokeRect(2, 3, 12, 10);
                ctx.fillStyle = isDark ? "#4ec9b0" : "#267f99";
                ctx.fillRect(2, 3, 12, 2.5);
                ctx.fillStyle = "#ff5f56"; ctx.fillRect(3.5, 4, 1, 1);
                ctx.strokeStyle = textMutedColor;
                ctx.beginPath();
                ctx.moveTo(4, 8); ctx.lineTo(12, 8);
                ctx.moveTo(4, 10); ctx.lineTo(8, 10);
                ctx.stroke();
            }
        }
    }

    component VariableIcon: Item {
        width: 16
        height: 16
        Canvas {
            anchors.fill: parent
            onPaint: {
                var ctx = getContext("2d");
                ctx.reset();
                ctx.strokeStyle = isDark ? "#b5cea8" : "#098658";
                ctx.lineWidth = 1.2;
                ctx.beginPath();
                ctx.moveTo(5, 4); ctx.lineTo(3, 4); ctx.lineTo(3, 12); ctx.lineTo(5, 12);
                ctx.moveTo(11, 4); ctx.lineTo(13, 4); ctx.lineTo(13, 12); ctx.lineTo(11, 12);
                ctx.moveTo(6, 6); ctx.lineTo(10, 10);
                ctx.moveTo(10, 6); ctx.lineTo(6, 10);
                ctx.stroke();
            }
        }
    }

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

    Dialog {
        id: createFormDialog
        property string moduleFolder: ""
        title: "Создать форму"
        x: Math.round((mainWindow.width - width) / 2)
        y: Math.round((mainWindow.height - height) / 2)
        width: 300
        modal: true
        standardButtons: Dialog.Ok | Dialog.Cancel
        
        ColumnLayout {
            anchors.fill: parent
            TextField {
                id: formNameInput
                Layout.fillWidth: true
                placeholderText: "Имя формы (напр. FormMain)"
            }
        }
        onAccepted: {
            if (formNameInput.text.trim() !== "") {
                SysHelper.createForm(moduleFolder, formNameInput.text.trim());
                var formsNodeId = "forms_" + moduleFolder;
                expandedTreeNodes[formsNodeId] = true;
                expandedTreeNodes = Object.assign({}, expandedTreeNodes);
                refreshTree();
                formNameInput.text = "";
            }
        }
    }

    Dialog {
        id: deleteModuleConfirmDialog
        property string folderName: ""
        title: "Удалить модуль"
        x: Math.round((mainWindow.width - width) / 2)
        y: Math.round((mainWindow.height - height) / 2)
        width: 350
        modal: true
        standardButtons: Dialog.Yes | Dialog.No
        Text {
            text: "Вы действительно хотите удалить модуль \"" + deleteModuleConfirmDialog.folderName + "\" и все его файлы?"
            color: textColor
            wrapMode: Text.Wrap
            width: parent.width
        }
        onAccepted: {
            for (var i = openEditorsModel.count - 1; i >= 0; i--) {
                if (openEditorsModel.get(i).moduleName === folderName) {
                    openEditorsModel.remove(i);
                }
            }
            if (selectedTreeNode && selectedTreeNode.folderName === folderName) {
                selectedTreeNode = null;
            }
            SysHelper.deleteModule(folderName);
            refreshTree();
        }
    }

    Dialog {
        id: deleteFormConfirmDialog
        property string moduleFolder: ""
        property string formFolder: ""
        title: "Удалить форму"
        x: Math.round((mainWindow.width - width) / 2)
        y: Math.round((mainWindow.height - height) / 2)
        width: 350
        modal: true
        standardButtons: Dialog.Yes | Dialog.No
        Text {
            text: "Вы действительно хотите удалить форму \"" + deleteFormConfirmDialog.formFolder + "\"?"
            color: textColor
            wrapMode: Text.Wrap
            width: parent.width
        }
        onAccepted: {
            var editorId = "form_" + moduleFolder + "_" + formFolder;
            for (var i = openEditorsModel.count - 1; i >= 0; i--) {
                if (openEditorsModel.get(i).editorId === editorId) {
                    openEditorsModel.remove(i);
                }
            }
            if (selectedTreeNode && selectedTreeNode.folderName === formFolder && selectedTreeNode.type === "form") {
                selectedTreeNode = null;
            }
            SysHelper.deleteForm(moduleFolder, formFolder);
            refreshTree();
        }
    }

    Dialog {
        id: deleteVariableConfirmDialog
        property string moduleFolder: ""
        property int varIndex: -1
        title: "Удалить переменную"
        x: Math.round((mainWindow.width - width) / 2)
        y: Math.round((mainWindow.height - height) / 2)
        width: 320
        modal: true
        standardButtons: Dialog.Yes | Dialog.No
        Text {
            text: "Вы действительно хотите удалить эту переменную?"
            color: textColor
            wrapMode: Text.Wrap
            width: parent.width
        }
        onAccepted: {
            if (selectedTreeNode && selectedTreeNode.type === "variable" && selectedTreeNode.variableIndex === varIndex) {
                selectedTreeNode = null;
            }
            SysHelper.deleteVariable(moduleFolder, varIndex);
            refreshTree();
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
            var modules_dir = (typeof SysHelper !== "undefined") ? SysHelper.modulesDir : ""
            var dest = modules_dir + "/" + exportLoadingDialog.moduleName
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
                                    onClicked: contextMenuRoot.popup()
                                }
                                
                                Menu {
                                    id: contextMenuRoot
                                    MenuItem { text: qsTr("Создать модуль"); onTriggered: createModuleDialog.open() }
                                }

                                Menu {
                                    id: contextMenuModule
                                    property string folderName: ""
                                    MenuItem { text: qsTr("Создать форму"); onTriggered: { createFormDialog.moduleFolder = contextMenuModule.folderName; createFormDialog.open() } }
                                    MenuItem { text: qsTr("Создать переменную"); onTriggered: { createVariableForModule(contextMenuModule.folderName) } }
                                    MenuItem { text: qsTr("Открыть main.py"); onTriggered: openModuleEditor(contextMenuModule.folderName) }
                                    Menu {
                                        title: qsTr("Экспорт")
                                        MenuItem { text: qsTr("Как исходники (zip)"); onTriggered: triggerExport("zip", contextMenuModule.folderName) }
                                        MenuItem { text: qsTr("В вид без редактирования (Windows)"); onTriggered: triggerExport("windows", contextMenuModule.folderName) }
                                        MenuItem { text: qsTr("В вид без редактирования (Linux)"); onTriggered: triggerExport("linux", contextMenuModule.folderName) }
                                    }
                                    MenuItem { text: qsTr("Удалить модуль"); onTriggered: { deleteModuleConfirmDialog.folderName = contextMenuModule.folderName; deleteModuleConfirmDialog.open() } }
                                }

                                Menu {
                                    id: contextMenuCategoryForms
                                    property string folderName: ""
                                    MenuItem { text: qsTr("Создать форму"); onTriggered: { createFormDialog.moduleFolder = contextMenuCategoryForms.folderName; createFormDialog.open() } }
                                }

                                Menu {
                                    id: contextMenuForm
                                    property string moduleFolder: ""
                                    property string formFolder: ""
                                    MenuItem { text: qsTr("Открыть форму"); onTriggered: openFormEditor(contextMenuForm.moduleFolder, contextMenuForm.formFolder) }
                                    MenuItem { text: qsTr("Удалить форму"); onTriggered: { deleteFormConfirmDialog.moduleFolder = contextMenuForm.moduleFolder; deleteFormConfirmDialog.formFolder = contextMenuForm.formFolder; deleteFormConfirmDialog.open() } }
                                }

                                Menu {
                                    id: contextMenuCategoryVariables
                                    property string folderName: ""
                                    MenuItem { text: qsTr("Создать переменную"); onTriggered: { createVariableForModule(contextMenuCategoryVariables.folderName) } }
                                }

                                Menu {
                                    id: contextMenuVariable
                                    property string moduleFolder: ""
                                    property int varIndex: -1
                                    MenuItem { text: qsTr("Удалить переменную"); onTriggered: { deleteVariableConfirmDialog.moduleFolder = contextMenuVariable.moduleFolder; deleteVariableConfirmDialog.varIndex = contextMenuVariable.varIndex; deleteVariableConfirmDialog.open() } }
                                }
                            }
                            
                            Item { 
                                Layout.fillHeight: true; Layout.fillWidth: true 
                                ListView {
                                    id: treeListView
                                    anchors.fill: parent
                                    model: visibleTreeModel
                                    clip: true
                                    delegate: Rectangle {
                                        width: treeListView.width
                                        height: 26
                                        color: {
                                            if (selectedTreeNode && selectedTreeNode.id === model.id) {
                                                return isDark ? "#37373d" : "#e4e6f1"
                                            }
                                            return itemMouseArea.containsMouse ? listHoverBg : "transparent"
                                        }
                                        
                                        RowLayout {
                                            anchors.fill: parent
                                            anchors.leftMargin: 8 + model.depth * 14
                                            spacing: 5
                                            
                                            Item {
                                                width: 14; height: 14
                                                visible: model.hasChildren
                                                ChevronIcon {
                                                    anchors.fill: parent
                                                    expanded: model.isExpanded
                                                }
                                            }
                                            
                                            Item {
                                                width: 14; height: 14
                                                visible: !model.hasChildren
                                            }
                                            
                                            Item {
                                                width: 16; height: 16
                                                Layout.alignment: Qt.AlignVCenter
                                                
                                                FolderIcon {
                                                    anchors.fill: parent
                                                    visible: model.icon === "folder"
                                                    open: model.isExpanded
                                                }
                                                
                                                CubeIcon {
                                                    anchors.fill: parent
                                                    visible: model.icon === "module"
                                                }
                                                
                                                FormIcon {
                                                    anchors.fill: parent
                                                    visible: model.icon === "form"
                                                }
                                                
                                                VariableIcon {
                                                    anchors.fill: parent
                                                    visible: model.icon === "variable"
                                                }
                                            }
                                            
                                            Text {
                                                Layout.fillWidth: true
                                                text: model.name
                                                color: (selectedTreeNode && selectedTreeNode.id === model.id) ? (isDark ? "#ffffff" : "#000000") : textColor
                                                font.pixelSize: 12
                                                font.bold: model.type === "root" || model.type === "module"
                                                elide: Text.ElideRight
                                            }
                                        }
                                        
                                        MouseArea {
                                            id: itemMouseArea
                                            anchors.fill: parent
                                            hoverEnabled: true
                                            acceptedButtons: Qt.LeftButton | Qt.RightButton
                                            onDoubleClicked: {
                                                if (model.hasChildren) {
                                                    toggleNodeExpanded(model.id);
                                                } else if (model.type === "module") {
                                                    openModuleEditor(model.folderName);
                                                } else if (model.type === "form") {
                                                    var modFolder = model.parentId.substring(6); // parentId: "forms_<modFolder>"
                                                    openFormEditor(modFolder, model.folderName);
                                                }
                                            }
                                            onClicked: (mouse) => {
                                                selectedTreeNode = {
                                                    "id": model.id,
                                                    "parentId": model.parentId,
                                                    "name": model.name,
                                                    "folderName": model.folderName,
                                                    "type": model.type,
                                                    "depth": model.depth,
                                                    "hasChildren": model.hasChildren,
                                                    "icon": model.icon,
                                                    "variableIndex": model.type === "variable" ? model.variableIndex : -1
                                                };
                                                loadSelectedNodeProperties();
                                                
                                                if (mouse.button === Qt.RightButton) {
                                                    showTreeContextMenu(model, mouse.x, mouse.y);
                                                } else {
                                                    // Check if clicked in the chevron or indentation area on the left
                                                    var chevronEndX = 8 + model.depth * 14 + 18;
                                                    if (model.hasChildren && mouse.x >= 0 && mouse.x <= chevronEndX) {
                                                        toggleNodeExpanded(model.id);
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
                                            text: model.editorType === "form" ? "🖼️  " + model.formName : "🐍  " + model.moduleName
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
                                
                                color: windowBgColor
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
                                        text: model.editorType === "form" ? "🖼️  " + model.moduleName + "  -  " + model.formName : "🐍  " + model.moduleName + "  -  main.py"
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
                                                    saveEditor(index)
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
                                                    saveEditor(index)
                                                    openEditorsModel.remove(index)
                                                }
                                            }
                                        }
                                    }

                                    MouseArea {
                                        anchors.fill: parent
                                        anchors.rightMargin: 100
                                        property int startMouseX
                                        property int startMouseY
                                        property int startWinX
                                        property int startWinY
                                        
                                        onPressed: (mouse) => {
                                            win.forceActiveFocus()
                                            if (!model.isMaximized) {
                                                var globalPos = mapToItem(workspace, mouse.x, mouse.y)
                                                startMouseX = globalPos.x
                                                startMouseY = globalPos.y
                                                startWinX = win.x
                                                startWinY = win.y
                                                
                                                if (typeof SysHelper !== "undefined") {
                                                    var topOffset = workspaceTabBar.visible ? 35 : 0
                                                    var globalPos = workspace.mapToGlobal(0, topOffset)
                                                    SysHelper.clipCursor(mainWindow, globalPos.x, globalPos.y, workspace.width, workspace.height - topOffset)
                                                }
                                            }
                                        }
                                        
                                        onPositionChanged: (mouse) => {
                                            if (pressed && !model.isMaximized) {
                                                var globalPos = mapToItem(workspace, mouse.x, mouse.y)
                                                var topLimit = workspaceTabBar.visible ? 35 : 0
                                                var clampedMouseX = Math.max(0, Math.min(workspace.width, globalPos.x))
                                                var clampedMouseY = Math.max(topLimit, Math.min(workspace.height, globalPos.y))
                                                var clickOffsetX = startMouseX - startWinX
                                                var clickOffsetY = startMouseY - startWinY
                                                model.editorX = clampedMouseX - clickOffsetX
                                                model.editorY = clampedMouseY - clickOffsetY
                                            }
                                        }
                                        
                                        onReleased: {
                                            if (typeof SysHelper !== "undefined") {
                                                SysHelper.releaseCursor()
                                            }
                                        }
                                        
                                        onCanceled: {
                                            if (typeof SysHelper !== "undefined") {
                                                SysHelper.releaseCursor()
                                            }
                                        }
                                        
                                        onDoubleClicked: {
                                            model.isMaximized = !model.isMaximized
                                        }
                                    }
                                }

                                ColumnLayout {
                                    anchors.top: winTitleBar.bottom
                                    anchors.left: parent.left
                                    anchors.right: parent.right
                                    anchors.bottom: parent.bottom
                                    spacing: 0

                                    // Tab buttons for Form editor
                                    Rectangle {
                                        Layout.fillWidth: true
                                        height: 28
                                        color: panelColor
                                        visible: model.editorType === "form"
                                        
                                        Rectangle { width: parent.width; height: 1; color: borderColor; anchors.bottom: parent.bottom }
                                        
                                        RowLayout {
                                            anchors.fill: parent
                                            spacing: 1
                                            
                                            Rectangle {
                                                width: 80; height: 28
                                                color: (model.currentTab === 0) ? windowBgColor : "transparent"
                                                Text { text: "QML"; color: (model.currentTab === 0) ? textColor : textMutedColor; font.pixelSize: 11; font.bold: true; anchors.centerIn: parent }
                                                MouseArea { anchors.fill: parent; onClicked: model.currentTab = 0 }
                                            }
                                            
                                            Rectangle {
                                                width: 80; height: 28
                                                color: (model.currentTab === 1) ? windowBgColor : "transparent"
                                                Text { text: "Python"; color: (model.currentTab === 1) ? textColor : textMutedColor; font.pixelSize: 11; font.bold: true; anchors.centerIn: parent }
                                                MouseArea { anchors.fill: parent; onClicked: model.currentTab = 1 }
                                            }
                                        }
                                    }

                                    StackLayout {
                                        Layout.fillWidth: true
                                        Layout.fillHeight: true
                                        currentIndex: (model.editorType === "form" && model.currentTab !== undefined) ? model.currentTab : 0
                                        
                                        // Tab 0 / Single Editor: QML or main.py
                                        ScrollView {
                                            clip: true
                                            TextArea {
                                                id: editorArea1
                                                text: model.editorType === "form" ? (model.qmlCode || "") : (model.codeText || "")
                                                color: textColor
                                                font.family: "Consolas, Courier New, monospace"
                                                font.pixelSize: 13
                                                background: Rectangle { color: windowBgColor }
                                                selectByMouse: true
                                                padding: 10
                                                
                                                Component.onCompleted: {
                                                    if (typeof SysHelper !== "undefined") {
                                                        var lang = model.editorType === "form" ? "qml" : "python"
                                                        SysHelper.highlightDocument(editorArea1.textDocument, isDark, lang)
                                                    }
                                                }
                                                
                                                onTextChanged: {
                                                    if (model.editorType === "form") {
                                                        model.qmlCode = text
                                                    } else {
                                                        model.codeText = text
                                                    }
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
                                                        saveEditor(index)
                                                    }
                                                }
                                            }
                                        }

                                        // Tab 1: Python editor for Form
                                        ScrollView {
                                            clip: true
                                            TextArea {
                                                id: editorArea2
                                                text: model.pyCode || ""
                                                color: textColor
                                                font.family: "Consolas, Courier New, monospace"
                                                font.pixelSize: 13
                                                background: Rectangle { color: windowBgColor }
                                                selectByMouse: true
                                                padding: 10
                                                
                                                Component.onCompleted: {
                                                    if (typeof SysHelper !== "undefined") {
                                                        SysHelper.highlightDocument(editorArea2.textDocument, isDark, "python")
                                                    }
                                                }
                                                
                                                onTextChanged: {
                                                    if (model.editorType === "form") {
                                                        model.pyCode = text
                                                    }
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
                                                        saveEditor(index)
                                                    }
                                                }
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
                                        property int startMouseX; property int startWinX; property int startWidth
                                        onPressed: (mouse) => {
                                            win.forceActiveFocus()
                                            var gp = mapToItem(workspace, mouse.x, mouse.y)
                                            startMouseX = gp.x
                                            startWinX = win.x
                                            startWidth = win.width
                                        }
                                        onPositionChanged: (mouse) => {
                                            if (pressed) {
                                                var gp = mapToItem(workspace, mouse.x, mouse.y)
                                                var dx = gp.x - startMouseX
                                                var newWidth = startWidth - dx
                                                if (newWidth >= 300) {
                                                    model.editorX = startWinX + dx
                                                    model.editorWidth = newWidth
                                                }
                                            }
                                        }
                                    }
                                    // Right
                                    MouseArea {
                                        width: 5; anchors.right: parent.right; anchors.top: parent.top; anchors.bottom: parent.bottom; cursorShape: Qt.SizeHorCursor
                                        property int startMouseX; property int startWidth
                                        onPressed: (mouse) => {
                                            win.forceActiveFocus()
                                            var gp = mapToItem(workspace, mouse.x, mouse.y)
                                            startMouseX = gp.x
                                            startWidth = win.width
                                        }
                                        onPositionChanged: (mouse) => {
                                            if (pressed) {
                                                var gp = mapToItem(workspace, mouse.x, mouse.y)
                                                var dx = gp.x - startMouseX
                                                var newWidth = startWidth + dx
                                                if (newWidth >= 300) {
                                                    model.editorWidth = newWidth
                                                }
                                            }
                                        }
                                    }
                                    // Top
                                    MouseArea {
                                        height: 5; anchors.left: parent.left; anchors.right: parent.right; anchors.top: parent.top; cursorShape: Qt.SizeVerCursor
                                        property int startMouseY; property int startWinY; property int startHeight
                                        onPressed: (mouse) => {
                                            win.forceActiveFocus()
                                            var gp = mapToItem(workspace, mouse.x, mouse.y)
                                            startMouseY = gp.y
                                            startWinY = win.y
                                            startHeight = win.height
                                        }
                                        onPositionChanged: (mouse) => {
                                            if (pressed) {
                                                var gp = mapToItem(workspace, mouse.x, mouse.y)
                                                var dy = gp.y - startMouseY
                                                var newHeight = startHeight - dy
                                                if (newHeight >= 200) {
                                                    model.editorY = startWinY + dy
                                                    model.editorHeight = newHeight
                                                }
                                            }
                                        }
                                    }
                                    // Bottom
                                    MouseArea {
                                        height: 5; anchors.left: parent.left; anchors.right: parent.right; anchors.bottom: parent.bottom; cursorShape: Qt.SizeVerCursor
                                        property int startMouseY; property int startHeight
                                        onPressed: (mouse) => {
                                            win.forceActiveFocus()
                                            var gp = mapToItem(workspace, mouse.x, mouse.y)
                                            startMouseY = gp.y
                                            startHeight = win.height
                                        }
                                        onPositionChanged: (mouse) => {
                                            if (pressed) {
                                                var gp = mapToItem(workspace, mouse.x, mouse.y)
                                                var dy = gp.y - startMouseY
                                                var newHeight = startHeight + dy
                                                if (newHeight >= 200) {
                                                    model.editorHeight = newHeight
                                                }
                                            }
                                        }
                                    }
                                    // Corner TL
                                    MouseArea {
                                        width: 8; height: 8; anchors.left: parent.left; anchors.top: parent.top; cursorShape: Qt.SizeFDiagCursor
                                        property int startMouseX; property int startMouseY
                                        property int startWinX; property int startWinY
                                        property int startWidth; property int startHeight
                                        onPressed: (mouse) => {
                                            win.forceActiveFocus()
                                            var gp = mapToItem(workspace, mouse.x, mouse.y)
                                            startMouseX = gp.x
                                            startMouseY = gp.y
                                            startWinX = win.x
                                            startWinY = win.y
                                            startWidth = win.width
                                            startHeight = win.height
                                        }
                                        onPositionChanged: (mouse) => {
                                            if (pressed) {
                                                var gp = mapToItem(workspace, mouse.x, mouse.y)
                                                var dx = gp.x - startMouseX
                                                var dy = gp.y - startMouseY
                                                var newWidth = startWidth - dx
                                                var newHeight = startHeight - dy
                                                if (newWidth >= 300) {
                                                    model.editorX = startWinX + dx
                                                    model.editorWidth = newWidth
                                                }
                                                if (newHeight >= 200) {
                                                    model.editorY = startWinY + dy
                                                    model.editorHeight = newHeight
                                                }
                                            }
                                        }
                                    }
                                    // Corner TR
                                    MouseArea {
                                        width: 8; height: 8; anchors.right: parent.right; anchors.top: parent.top; cursorShape: Qt.SizeBDiagCursor
                                        property int startMouseX; property int startMouseY
                                        property int startWinY
                                        property int startWidth; property int startHeight
                                        onPressed: (mouse) => {
                                            win.forceActiveFocus()
                                            var gp = mapToItem(workspace, mouse.x, mouse.y)
                                            startMouseX = gp.x
                                            startMouseY = gp.y
                                            startWinY = win.y
                                            startWidth = win.width
                                            startHeight = win.height
                                        }
                                        onPositionChanged: (mouse) => {
                                            if (pressed) {
                                                var gp = mapToItem(workspace, mouse.x, mouse.y)
                                                var dx = gp.x - startMouseX
                                                var dy = gp.y - startMouseY
                                                var newWidth = startWidth + dx
                                                var newHeight = startHeight - dy
                                                if (newWidth >= 300) {
                                                    model.editorWidth = newWidth
                                                }
                                                if (newHeight >= 200) {
                                                    model.editorY = startWinY + dy
                                                    model.editorHeight = newHeight
                                                }
                                            }
                                        }
                                    }
                                    // Corner BL
                                    MouseArea {
                                        width: 8; height: 8; anchors.left: parent.left; anchors.bottom: parent.bottom; cursorShape: Qt.SizeBDiagCursor
                                        property int startMouseX; property int startMouseY
                                        property int startWinX
                                        property int startWidth; property int startHeight
                                        onPressed: (mouse) => {
                                            win.forceActiveFocus()
                                            var gp = mapToItem(workspace, mouse.x, mouse.y)
                                            startMouseX = gp.x
                                            startMouseY = gp.y
                                            startWinX = win.x
                                            startWidth = win.width
                                            startHeight = win.height
                                        }
                                        onPositionChanged: (mouse) => {
                                            if (pressed) {
                                                var gp = mapToItem(workspace, mouse.x, mouse.y)
                                                var dx = gp.x - startMouseX
                                                var dy = gp.y - startMouseY
                                                var newWidth = startWidth - dx
                                                var newHeight = startHeight + dy
                                                if (newWidth >= 300) {
                                                    model.editorX = startWinX + dx
                                                    model.editorWidth = newWidth
                                                }
                                                if (newHeight >= 200) {
                                                    model.editorHeight = newHeight
                                                }
                                            }
                                        }
                                    }
                                    // Corner BR
                                    MouseArea {
                                        width: 8; height: 8; anchors.right: parent.right; anchors.bottom: parent.bottom; cursorShape: Qt.SizeFDiagCursor
                                        property int startMouseX; property int startMouseY
                                        property int startWidth; property int startHeight
                                        onPressed: (mouse) => {
                                            win.forceActiveFocus()
                                            var gp = mapToItem(workspace, mouse.x, mouse.y)
                                            startMouseX = gp.x
                                            startMouseY = gp.y
                                            startWidth = win.width
                                            startHeight = win.height
                                        }
                                        onPositionChanged: (mouse) => {
                                            if (pressed) {
                                                var gp = mapToItem(workspace, mouse.x, mouse.y)
                                                var dx = gp.x - startMouseX
                                                var dy = gp.y - startMouseY
                                                var newWidth = startWidth + dx
                                                var newHeight = startHeight + dy
                                                if (newWidth >= 300) {
                                                    model.editorWidth = newWidth
                                                }
                                                if (newHeight >= 200) {
                                                    model.editorHeight = newHeight
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
                            
                            ScrollView {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                clip: true
                                
                                ColumnLayout {
                                    id: propScrollCol
                                    width: parent.width - 20
                                    Layout.margins: 10
                                    spacing: 12
                                    visible: selectedTreeNode !== null
                                    
                                    // --- Module Properties ---
                                    ColumnLayout {
                                        Layout.fillWidth: true
                                        visible: selectedTreeNode && selectedTreeNode.type === "module"
                                        spacing: 6
                                        
                                        Text { text: "Имя папки:"; color: textMutedColor; font.pixelSize: 11 }
                                        TextField {
                                            id: propModuleNameField
                                            Layout.fillWidth: true
                                            color: textColor
                                            background: Rectangle { color: bgColor; border.color: borderColor; radius: 3 }
                                            onEditingFinished: saveSelectedNodeProperties()
                                        }
                                        
                                        Text { text: "Версия:"; color: textMutedColor; font.pixelSize: 11 }
                                        TextField {
                                            id: propModuleVersionField
                                            Layout.fillWidth: true
                                            color: textColor
                                            background: Rectangle { color: bgColor; border.color: borderColor; radius: 3 }
                                            onEditingFinished: saveSelectedNodeProperties()
                                        }
                                        
                                        Text { text: "Автор:"; color: textMutedColor; font.pixelSize: 11 }
                                        TextField {
                                            id: propModuleAuthorField
                                            Layout.fillWidth: true
                                            color: textColor
                                            background: Rectangle { color: bgColor; border.color: borderColor; radius: 3 }
                                            onEditingFinished: saveSelectedNodeProperties()
                                        }
                                        
                                        Text { text: "Описание:"; color: textMutedColor; font.pixelSize: 11 }
                                        TextArea {
                                            id: propModuleDescField
                                            Layout.fillWidth: true
                                            implicitHeight: 80
                                            color: textColor
                                            background: Rectangle { color: bgColor; border.color: borderColor; radius: 3 }
                                            onEditingFinished: saveSelectedNodeProperties()
                                        }
                                    }
                                    
                                    // --- Form Properties ---
                                    ColumnLayout {
                                        Layout.fillWidth: true
                                        visible: selectedTreeNode && selectedTreeNode.type === "form"
                                        spacing: 6
                                        
                                        Text { text: "Имя формы:"; color: textMutedColor; font.pixelSize: 11 }
                                        TextField {
                                            id: propFormNameField
                                            Layout.fillWidth: true
                                            color: textColor
                                            background: Rectangle { color: bgColor; border.color: borderColor; radius: 3 }
                                            onEditingFinished: saveSelectedNodeProperties()
                                        }
                                        
                                        Text { text: "Заголовок:"; color: textMutedColor; font.pixelSize: 11 }
                                        TextField {
                                            id: propFormTitleField
                                            Layout.fillWidth: true
                                            color: textColor
                                            background: Rectangle { color: bgColor; border.color: borderColor; radius: 3 }
                                            onEditingFinished: saveSelectedNodeProperties()
                                        }
                                        
                                        RowLayout {
                                            Layout.fillWidth: true
                                            spacing: 10
                                            
                                            ColumnLayout {
                                                Layout.fillWidth: true
                                                Text { text: "Ширина:"; color: textMutedColor; font.pixelSize: 11 }
                                                TextField {
                                                    id: propFormWidthField
                                                    Layout.fillWidth: true
                                                    color: textColor
                                                    background: Rectangle { color: bgColor; border.color: borderColor; radius: 3 }
                                                    validator: IntValidator { bottom: 100; top: 5000 }
                                                    onEditingFinished: saveSelectedNodeProperties()
                                                }
                                            }
                                            
                                            ColumnLayout {
                                                Layout.fillWidth: true
                                                Text { text: "Высота:"; color: textMutedColor; font.pixelSize: 11 }
                                                TextField {
                                                    id: propFormHeightField
                                                    Layout.fillWidth: true
                                                    color: textColor
                                                    background: Rectangle { color: bgColor; border.color: borderColor; radius: 3 }
                                                    validator: IntValidator { bottom: 100; top: 5000 }
                                                    onEditingFinished: saveSelectedNodeProperties()
                                                }
                                            }
                                        }
                                    }
                                    
                                    // --- Variable Properties ---
                                    ColumnLayout {
                                        Layout.fillWidth: true
                                        visible: selectedTreeNode && selectedTreeNode.type === "variable"
                                        spacing: 6
                                        
                                        Text { text: "Имя:"; color: textMutedColor; font.pixelSize: 11 }
                                        TextField {
                                            id: propVarNameField
                                            Layout.fillWidth: true
                                            color: textColor
                                            background: Rectangle { color: bgColor; border.color: borderColor; radius: 3 }
                                            onEditingFinished: saveSelectedNodeProperties()
                                        }
                                        
                                        Text { text: "Тип:"; color: textMutedColor; font.pixelSize: 11 }
                                        ComboBox {
                                            id: propVarTypeCombo
                                            Layout.fillWidth: true
                                            model: ["String", "Integer", "Float", "Boolean", "List", "Dict"]
                                            onActivated: saveSelectedNodeProperties()
                                        }
                                        
                                        Text { text: "Значение:"; color: textMutedColor; font.pixelSize: 11 }
                                        TextField {
                                            id: propVarValueField
                                            Layout.fillWidth: true
                                            color: textColor
                                            background: Rectangle { color: bgColor; border.color: borderColor; radius: 3 }
                                            onEditingFinished: saveSelectedNodeProperties()
                                        }
                                        
                                        Text { text: "Описание:"; color: textMutedColor; font.pixelSize: 11 }
                                        TextField {
                                            id: propVarDescField
                                            Layout.fillWidth: true
                                            color: textColor
                                            background: Rectangle { color: bgColor; border.color: borderColor; radius: 3 }
                                            onEditingFinished: saveSelectedNodeProperties()
                                        }
                                    }
                                }
                            }
                            
                            Text {
                                Layout.alignment: Qt.AlignHCenter
                                visible: selectedTreeNode === null
                                text: "Выберите элемент для просмотра свойств"
                                color: textMutedColor
                                font.pixelSize: 11
                                horizontalAlignment: Text.AlignHCenter
                                wrapMode: Text.Wrap
                                Layout.fillWidth: true
                                Layout.margins: 15
                            }
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


    function bringToFront(win, idx) {
        maxZIndex += 1
        openEditorsModel.setProperty(idx, "zIndex", maxZIndex)
        activeModuleName = openEditorsModel.get(idx).moduleName
    }

    function triggerExport(type, moduleName) {
        exportLoadingDialog.moduleName = moduleName
        exportLoadingDialog.exportType = type
        exportLoadingDialog.open()
        exportTimer.restart()
    }

    Component.onCompleted: {
        refreshTree();
        
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
