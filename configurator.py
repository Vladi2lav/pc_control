"""
================================================================================
AI INSTRUCTIONS & SECTION ANCHORS (ATTENTION: ALWAYS KEEP ANCHOR NAMES ON EDITS)
================================================================================
Purpose: This file acts as the backend for the Lumen Configurator UI (QML-based).
Standard User Folder: Unified under %APPDATA%\Lumen\modules (Roaming AppData).

SECTION ANCHORS INDEX:
- # === [QSYNTAX_HIGHLIGHTER] ===   QSyntaxHighlighter (GenericHighlighter) code syntax formats.
- # === [NATIVE_FILTER] ===         Win32NativeEventFilter custom titlebar window moving/resizing.
- # === [SETTINGS_MANAGER] ===      Theme and default encoding manager (SettingsManager).
- # === [TERMINAL_MANAGER] ===      Native terminal processes runner & manager (TerminalSession/TerminalManager).
- # === [CONFIG_HELPER] ===          Core business logic helper slots (ConfigHelper class).
  - # === [MIGRATION] ===           migrate_all_modules(): relocates legacy form folders & writes defaults.
  - # === [TREE_STRUCTURE] ===      getTreeStructure(): returns a flat JSON node list for the QML Explorer tree.
  - # === [MODULES_CRUD] ===        createModule / saveModuleProperties / readModuleProperties / deleteModule.
  - # === [FORMS_CRUD] ===          createForm / saveFormProperties / readFormProperties / deleteForm.
  - # === [FORM_FILES_CRUD] ===     readFormFiles / saveFormFiles.
  - # === [VARIABLES_CRUD] ===      createVariable / saveVariableProperties / readVariableProperties / deleteVariable.
- # === [APP_ENTRY] ===             Application main loop entry point and NativeEventFilter install.
================================================================================
"""

import sys
import os

# Configure Windows console to use system Active Code Page to prevent garbled text/mojibake
if sys.platform == "win32":
    try:
        import ctypes
        acp = ctypes.windll.kernel32.GetACP()
        ctypes.windll.kernel32.SetConsoleOutputCP(acp)
        ctypes.windll.kernel32.SetConsoleCP(acp)
    except Exception:
        pass

import paths

# Initialize folders and copy defaults if needed
paths.initialize_user_directories()

os.environ["QT_QUICK_CONTROLS_STYLE"] = "Basic"
import signal
import json
import platform
import ctypes
from ctypes import wintypes

from PySide6.QtGui import QGuiApplication, QCursor, QSyntaxHighlighter, QTextCharFormat, QColor, QFont
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtCore import QObject, Slot, Property, Signal, QProcess, QAbstractNativeEventFilter, Qt, QPoint, QRect, QRegularExpression
from PySide6.QtQuick import QQuickTextDocument

# Win32 Constants
WM_NCCALCSIZE = 0x0083
WM_NCHITTEST = 0x0084

HTNOWHERE = 0
HTCLIENT = 1
HTCAPTION = 2
HTLEFT = 10
HTRIGHT = 11
HTTOP = 12
HTTOPLEFT = 13
HTTOPRIGHT = 14
HTBOTTOM = 15
HTBOTTOMLEFT = 16
HTBOTTOMRIGHT = 17

# === [NATIVE_FILTER] ===
class MSG(ctypes.Structure):
    _fields_ = [
        ("hwnd", wintypes.HWND),
        ("message", wintypes.UINT),
        ("wParam", wintypes.WPARAM),
        ("lParam", wintypes.LPARAM),
        ("time", wintypes.DWORD),
        ("pt", wintypes.POINT),
    ]

# === [QSYNTAX_HIGHLIGHTER] ===
class GenericHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None, is_dark=True, language="python"):
        super().__init__(parent)
        self.highlightingRules = []

        # Color configurations based on theme
        if is_dark:
            keyword_color = "#569cd6"     # Blue
            string_color = "#ce9178"      # Orange
            comment_color = "#6a9955"     # Green
            type_color = "#4ec9b0"        # Teal (types/components)
            number_color = "#b5cea8"      # Light Green
            property_color = "#9cdcfe"    # Light Blue (properties)
            function_color = "#dcdcaa"    # Yellow
            self_color = "#9cdcfe"        # Light Blue
        else:
            keyword_color = "#0000ff"     # Blue
            string_color = "#a31515"      # Dark Red
            comment_color = "#008000"     # Green
            type_color = "#267f99"        # Teal
            number_color = "#098658"      # Greenish
            property_color = "#0451a5"    # Dark Blue
            function_color = "#795e26"    # Brown
            self_color = "#000000"        # Black

        if language == "python":
            # Keyword format
            keywordFormat = QTextCharFormat()
            keywordFormat.setForeground(QColor(keyword_color))
            keywordFormat.setFontWeight(QFont.Bold)
            keywords = [
                "and", "as", "assert", "async", "await", "break", "class",
                "continue", "def", "del", "elif", "else", "except", "finally",
                "for", "from", "global", "if", "import", "in", "is", "lambda",
                "nonlocal", "not", "or", "pass", "raise", "return", "try",
                "while", "with", "yield", "True", "False", "None"
            ]
            for word in keywords:
                pattern = QRegularExpression(fr"\b{word}\b")
                self.highlightingRules.append((pattern, keywordFormat))

            # String format (Single and double quotes)
            stringFormat = QTextCharFormat()
            stringFormat.setForeground(QColor(string_color))
            self.highlightingRules.append((QRegularExpression(r'"[^"\\]*(\\.[^"\\]*)*"'), stringFormat))
            self.highlightingRules.append((QRegularExpression(r"'[^'\\]*(\\.[^'\\]*)*'"), stringFormat))

            # Comment format
            commentFormat = QTextCharFormat()
            commentFormat.setForeground(QColor(comment_color))
            self.highlightingRules.append((QRegularExpression(r"#[^\n]*"), commentFormat))

            # Function/Class format
            functionFormat = QTextCharFormat()
            functionFormat.setForeground(QColor(function_color))
            self.highlightingRules.append((QRegularExpression(r"\b[A-Za-z_][A-Za-z0-9_]*(?=\s*\()"), functionFormat))

            # Number format
            numberFormat = QTextCharFormat()
            numberFormat.setForeground(QColor(number_color))
            self.highlightingRules.append((QRegularExpression(r"\b\d+\b"), numberFormat))

            # Self format
            selfFormat = QTextCharFormat()
            selfFormat.setForeground(QColor(self_color))
            selfFormat.setFontItalic(True)
            self.highlightingRules.append((QRegularExpression(r"\bself\b"), selfFormat))

        elif language == "qml":
            # Keyword format
            keywordFormat = QTextCharFormat()
            keywordFormat.setForeground(QColor(keyword_color))
            keywordFormat.setFontWeight(QFont.Bold)
            keywords = [
                "import", "property", "alias", "signal", "function", "var",
                "let", "const", "return", "if", "else", "for", "while", "in",
                "typeof", "new", "true", "false", "null", "undefined", "as"
            ]
            for word in keywords:
                pattern = QRegularExpression(fr"\b{word}\b")
                self.highlightingRules.append((pattern, keywordFormat))

            # QML Type/Component format (capitalized words like Rectangle, Item, Button)
            typeFormat = QTextCharFormat()
            typeFormat.setForeground(QColor(type_color))
            typeFormat.setFontWeight(QFont.Bold)
            self.highlightingRules.append((QRegularExpression(r"\b[A-Z][A-Za-z0-9_]*\b"), typeFormat))

            # QML Property format (e.g. anchors.fill:, width:, height:)
            propertyFormat = QTextCharFormat()
            propertyFormat.setForeground(QColor(property_color))
            self.highlightingRules.append((QRegularExpression(r"\b[a-z_][A-Za-z0-9_\.]*(?=\s*:)"), propertyFormat))

            # String format
            stringFormat = QTextCharFormat()
            stringFormat.setForeground(QColor(string_color))
            self.highlightingRules.append((QRegularExpression(r'"[^"\\]*(\\.[^"\\]*)*"'), stringFormat))
            self.highlightingRules.append((QRegularExpression(r"'[^'\\]*(\\.[^'\\]*)*'"), stringFormat))

            # Comment format
            commentFormat = QTextCharFormat()
            commentFormat.setForeground(QColor(comment_color))
            self.highlightingRules.append((QRegularExpression(r"//[^\n]*"), commentFormat))
            self.highlightingRules.append((QRegularExpression(r"/\*.*?\*/"), commentFormat))

            # Number format
            numberFormat = QTextCharFormat()
            numberFormat.setForeground(QColor(number_color))
            self.highlightingRules.append((QRegularExpression(r"\b\d+\b"), numberFormat))

    def highlightBlock(self, text):
        for pattern, format in self.highlightingRules:
            expression = QRegularExpression(pattern)
            iterator = expression.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), format)


class Win32NativeEventFilter(QAbstractNativeEventFilter):
    def __init__(self, window):
        super().__init__()
        self.window = window
        self.hwnd = None
        self.is_closing = False

    def nativeEventFilter(self, eventType, message):
        if self.is_closing:
            return False, 0

        try:
            msg_ptr = int(message)
            msg = MSG.from_address(msg_ptr)

            # Перехват уничтожения окна
            if msg.message == 0x0002 or msg.message == 0x0082: # WM_DESTROY or WM_NCDESTROY
                if self.hwnd == msg.hwnd:
                    self.is_closing = True
                    return False, 0

            # Инициализация hwnd при первом сообщении
            if self.hwnd is None:
                if msg.message == WM_NCCALCSIZE:
                    self.hwnd = msg.hwnd
                else:
                    try:
                        self.hwnd = self.window.winId()
                    except:
                        pass

            if self.hwnd and msg.hwnd != self.hwnd:
                return False, 0

            if msg.message == WM_NCCALCSIZE:
                if msg.wParam:
                    # Убираем стандартный заголовок Windows при создании и ресайзе,
                    # сохраняя при этом системную рамку, тени и Aero Snap.
                    return True, 0

            # WM_NCHITTEST не перехватываем, позволяя Qt и QML MouseArea
            # свободно обрабатывать клики для startSystemMove() и startSystemResize()

        except Exception as e:
            pass

        return False, 0

# === [SETTINGS_MANAGER] ===
class SettingsManager(QObject):
    themeChanged = Signal()
    encodingChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings_file = str(paths.SETTINGS_FILE)
        self._theme = "dark"
        self._default_encoding = "utf-8"
        self.load_settings()

    def load_settings(self):
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._theme = data.get("theme", "dark")
                    self._default_encoding = data.get("default_encoding", "utf-8")
            except Exception as e:
                print(f"Error loading settings: {e}")

    def save_settings(self):
        try:
            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump({"theme": self._theme, "default_encoding": self._default_encoding}, f, indent=4)
        except Exception as e:
            print(f"Error saving settings: {e}")

    @Property(str, notify=themeChanged)
    def theme(self):
        return self._theme

    @theme.setter
    def theme(self, value):
        if self._theme != value:
            self._theme = value
            self.save_settings()
            self.themeChanged.emit()

    @Property(str, notify=encodingChanged)
    def defaultEncoding(self):
        return self._default_encoding

    @defaultEncoding.setter
    def defaultEncoding(self, value):
        if self._default_encoding != value:
            self._default_encoding = value
            self.save_settings()
            self.encodingChanged.emit()


# === [TERMINAL_MANAGER] ===
class TerminalSession(QObject):
    outputReceived = Signal(str)
    
    def __init__(self, executable, name, encoding="utf-8", parent=None):
        super().__init__(parent)
        self._name = name
        self._encoding = encoding
        self.process = QProcess()
        self.process.readyReadStandardOutput.connect(self.handle_stdout)
        self.process.readyReadStandardError.connect(self.handle_stderr)
        self.process.start(executable)

    @property
    def name(self):
        return self._name

    @Slot(str)
    def setEncoding(self, encoding):
        self._encoding = encoding

    @Slot(result=str)
    def getEncoding(self):
        return self._encoding

    def handle_stdout(self):
        data = self.process.readAllStandardOutput().data()
        try:
            decoded = data.decode(self._encoding, errors='replace')
        except:
            decoded = data.decode('utf-8', errors='replace')
        self.outputReceived.emit(decoded)

    def handle_stderr(self):
        data = self.process.readAllStandardError().data()
        try:
            decoded = data.decode(self._encoding, errors='replace')
        except:
            decoded = data.decode('utf-8', errors='replace')
        self.outputReceived.emit(decoded)

    @Slot(str)
    def writeInput(self, text):
        self.process.write(text.encode(self._encoding, errors='replace') + b'\r\n')

    def close(self):
        self.process.kill()


class TerminalManager(QObject):
    sessionAdded = Signal(int, str) # index, name
    sessionRemoved = Signal(int)
    outputReceived = Signal(int, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.sessions = []

    @Slot(str, str)
    def createSession(self, shell_type, encoding):
        executable = shell_type
        if platform.system() == "Windows":
            if shell_type == "powershell":
                executable = "powershell.exe"
            elif shell_type == "cmd":
                executable = "cmd.exe"
            else:
                executable = "cmd.exe"
        else:
            executable = "bash" if shell_type in ["bash", "powershell", "cmd"] else shell_type

        name = shell_type
        session = TerminalSession(executable, name, encoding, self)
        idx = len(self.sessions)
        self.sessions.append(session)
        
        # Connect signals
        session.outputReceived.connect(lambda text, i=idx: self.outputReceived.emit(i, text))
        self.sessionAdded.emit(idx, name)

    @Slot(int)
    def removeSession(self, index):
        if 0 <= index < len(self.sessions) and self.sessions[index] is not None:
            self.sessions[index].close()
            self.sessions[index] = None
            self.sessionRemoved.emit(index)

    @Slot(int, str)
    def writeToSession(self, index, text):
        if 0 <= index < len(self.sessions) and self.sessions[index] is not None:
            self.sessions[index].writeInput(text)

    @Slot()
    def close_all_sessions(self):
        for session in self.sessions:
            if session is not None:
                try:
                    session.close()
                    session.process.waitForFinished(500)
                except Exception:
                    pass


# === [CONFIG_HELPER] ===
class ConfigHelper(QObject):
    modulesChanged = Signal()

    @Property(str, constant=True)
    def modulesDir(self):
        return str(paths.MODULES_DIR)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._app = QGuiApplication.instance()
        self.modules_dir = str(paths.MODULES_DIR)
        if not os.path.exists(self.modules_dir):
            os.makedirs(self.modules_dir)
        self.migrate_all_modules()

    # === [MIGRATION] ===
    def migrate_all_modules(self):
        """
        Auto-migrates folders of forms from the root module folder to forms/ subdirectory
        and initializes manifest.json / variable.json.
        """
        if not os.path.exists(self.modules_dir):
            return
        for item in os.listdir(self.modules_dir):
            mod_path = os.path.join(self.modules_dir, item)
            if os.path.isdir(mod_path):
                # Ensure manifest.json
                manifest_path = os.path.join(mod_path, "manifest.json")
                if not os.path.exists(manifest_path) or os.path.getsize(manifest_path) == 0:
                    try:
                        with open(manifest_path, "w", encoding="utf-8") as f:
                            json.dump({
                                "name": item,
                                "version": "1.0.0",
                                "author": "",
                                "description": "Автоматически импортированный модуль",
                                "icon": "icon.jpg"
                            }, f, ensure_ascii=False, indent=4)
                    except Exception as e:
                        print(f"Error creating manifest for {item}: {e}")

                # Ensure variable.json
                var_path = os.path.join(mod_path, "variable.json")
                if not os.path.exists(var_path) or os.path.getsize(var_path) == 0:
                    try:
                        with open(var_path, "w", encoding="utf-8") as f:
                            f.write("[]")
                    except Exception as e:
                        print(f"Error creating variable.json for {item}: {e}")

                # Ensure forms/ folder and migrate legacy form folders
                forms_dir = os.path.join(mod_path, "forms")
                if not os.path.exists(forms_dir):
                    try:
                        os.makedirs(forms_dir)
                    except Exception as e:
                        print(f"Error creating forms dir for {item}: {e}")
                
                # Check for folders starting with "form_" that are NOT "forms" itself
                if os.path.exists(forms_dir):
                    for sub in os.listdir(mod_path):
                        sub_path = os.path.join(mod_path, sub)
                        if os.path.isdir(sub_path) and sub.startswith("form_") and sub != "forms":
                            target_path = os.path.join(forms_dir, sub)
                            try:
                                import shutil
                                if not os.path.exists(target_path):
                                    shutil.move(sub_path, target_path)
                                else:
                                    # Already exists, just remove legacy to avoid clutter
                                    shutil.rmtree(sub_path)
                            except Exception as e:
                                print(f"Error migrating form {sub} in module {item}: {e}")

                    # Ensure form.json exists for each form folder
                    for sub in os.listdir(forms_dir):
                        sub_path = os.path.join(forms_dir, sub)
                        if os.path.isdir(sub_path):
                            form_json_path = os.path.join(sub_path, "form.json")
                            if not os.path.exists(form_json_path) or os.path.getsize(form_json_path) == 0:
                                try:
                                    with open(form_json_path, "w", encoding="utf-8") as f:
                                        json.dump({
                                            "name": sub,
                                            "title": sub,
                                            "width": 800,
                                            "height": 600
                                        }, f, ensure_ascii=False, indent=4)
                                except Exception as e:
                                    print(f"Error creating form.json for {sub} in module {item}: {e}")

    @Slot(QObject, int, int, int, int)
    def clipCursor(self, window, x, y, width, height):
        if platform.system() == "Windows":
            ratio = window.devicePixelRatio() if window else 1.0
            px = int(round(x * ratio))
            py = int(round(y * ratio))
            pwidth = int(round(width * ratio))
            pheight = int(round(height * ratio))
            
            class RECT(ctypes.Structure):
                _fields_ = [
                    ("left", ctypes.c_long),
                    ("top", ctypes.c_long),
                    ("right", ctypes.c_long),
                    ("bottom", ctypes.c_long)
                ]
            rect = RECT(px, py, px + pwidth, py + pheight)
            ctypes.windll.user32.ClipCursor(ctypes.byref(rect))

    @Slot()
    def releaseCursor(self):
        if platform.system() == "Windows":
            ctypes.windll.user32.ClipCursor(None)

    @Slot(QObject, bool, str)
    def highlightDocument(self, quick_doc, is_dark, language):
        doc = quick_doc.textDocument()
        highlighter = GenericHighlighter(doc, is_dark, language)
        if not hasattr(self, "_highlighters"):
            self._highlighters = []
        self._highlighters.append(highlighter)

    @Slot(result=QRect)
    def virtualGeometry(self):
        return self._app.primaryScreen().virtualGeometry()

    @Slot(int, int, result=QRect)
    def screenGeometry(self, x, y):
        screen = self._app.screenAt(QPoint(x, y))
        if screen:
            return screen.geometry()
        return self._app.primaryScreen().geometry()

    @Slot(result=QPoint)
    def cursorPos(self):
        return QCursor.pos()

    # === [TREE_STRUCTURE] ===
    @Slot(result=str)
    def getTreeStructure(self):
        """
        Scans all modules and returns a serialized JSON list of nodes for building the tree.
        """
        self.migrate_all_modules() # Make sure structures are up to date
        nodes = []
        
        # Root node
        nodes.append({
            "id": "main",
            "parentId": "",
            "name": "main",
            "folderName": "main",
            "type": "root",
            "depth": 0,
            "hasChildren": True,
            "icon": "folder"
        })
        
        if not os.path.exists(self.modules_dir):
            return json.dumps(nodes)
            
        for item in sorted(os.listdir(self.modules_dir)):
            mod_path = os.path.join(self.modules_dir, item)
            if os.path.isdir(mod_path):
                # Read manifest
                manifest_name = item
                manifest_path = os.path.join(mod_path, "manifest.json")
                if os.path.exists(manifest_path):
                    try:
                        with open(manifest_path, "r", encoding="utf-8") as f:
                            m_data = json.load(f)
                            manifest_name = m_data.get("name", item)
                    except:
                        pass
                
                mod_node_id = f"module_{item}"
                nodes.append({
                    "id": mod_node_id,
                    "parentId": "main",
                    "name": manifest_name,
                    "folderName": item,
                    "type": "module",
                    "depth": 1,
                    "hasChildren": True,
                    "icon": "module"
                })
                
                # Category Forms
                forms_node_id = f"forms_{item}"
                nodes.append({
                    "id": forms_node_id,
                    "parentId": mod_node_id,
                    "name": "Формы",
                    "folderName": "forms",
                    "type": "category_forms",
                    "depth": 2,
                    "hasChildren": True,
                    "icon": "folder"
                })
                
                # Scan forms
                forms_dir = os.path.join(mod_path, "forms")
                if os.path.exists(forms_dir):
                    for sub in sorted(os.listdir(forms_dir)):
                        sub_path = os.path.join(forms_dir, sub)
                        if os.path.isdir(sub_path):
                            form_node_id = f"form_{item}_{sub}"
                            nodes.append({
                                "id": form_node_id,
                                "parentId": forms_node_id,
                                "name": sub,
                                "folderName": sub,
                                "type": "form",
                                "depth": 3,
                                "hasChildren": False,
                                "icon": "form"
                            })
                            
                # Category Variables
                vars_node_id = f"variables_{item}"
                nodes.append({
                    "id": vars_node_id,
                    "parentId": mod_node_id,
                    "name": "Переменные",
                    "folderName": "variables",
                    "type": "category_variables",
                    "depth": 2,
                    "hasChildren": True,
                    "icon": "folder"
                })
                
                # Read variables
                var_json_path = os.path.join(mod_path, "variable.json")
                if os.path.exists(var_json_path):
                    try:
                        with open(var_json_path, "r", encoding="utf-8") as f:
                            vars_list = json.load(f)
                            for idx, var_item in enumerate(vars_list):
                                var_name = var_item.get("name", f"var_{idx}")
                                var_node_id = f"var_{item}_{idx}"
                                nodes.append({
                                    "id": var_node_id,
                                    "parentId": vars_node_id,
                                    "name": var_name,
                                    "variableIndex": idx,
                                    "type": "variable",
                                    "depth": 3,
                                    "hasChildren": False,
                                    "icon": "variable"
                                })
                    except Exception as e:
                        print(f"Error reading variable.json for {item}: {e}")
                        
        return json.dumps(nodes, ensure_ascii=False)

    # === [MODULES_CRUD] ===
    @Slot(str, result=bool)
    def createModule(self, name):
        name = name.strip()
        if not name:
            return False
        mod_dir = os.path.join(self.modules_dir, name)
        if not os.path.exists(mod_dir):
            try:
                os.makedirs(mod_dir)
                
                # manifest.json
                with open(os.path.join(mod_dir, "manifest.json"), "w", encoding="utf-8") as f:
                    json.dump({
                        "name": name,
                        "version": "1.0.0",
                        "author": "",
                        "description": "Новый модуль",
                        "icon": "icon.jpg"
                    }, f, ensure_ascii=False, indent=4)
                
                # variable.json
                with open(os.path.join(mod_dir, "variable.json"), "w", encoding="utf-8") as f:
                    f.write("[]")
                
                # forms folder
                forms_dir = os.path.join(mod_dir, "forms")
                os.makedirs(forms_dir)
                
                # default form
                form_name = "form_" + name
                form_dir = os.path.join(forms_dir, form_name)
                os.makedirs(form_dir)
                
                # form.json
                with open(os.path.join(form_dir, "form.json"), "w", encoding="utf-8") as f:
                    json.dump({
                        "name": form_name,
                        "title": f"Форма {name}",
                        "width": 800,
                        "height": 600
                    }, f, ensure_ascii=False, indent=4)
                
                # form_name.py
                form_py_path = os.path.join(form_dir, form_name + ".py")
                with open(form_py_path, "w", encoding="utf-8") as f:
                    f.write(f"import sys\n"
                            f"from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton\n\n"
                            f"class MainForm:\n"
                            f"    def run(self):\n"
                            f"        app = QApplication.instance()\n"
                            f"        created_app = False\n"
                            f"        if not app:\n"
                            f"            app = QApplication(sys.argv)\n"
                            f"            created_app = True\n\n"
                            f"        window = QMainWindow()\n"
                            f"        window.setWindowTitle('Форма модуля {name}')\n"
                            f"        window.resize(400, 300)\n\n"
                            f"        central = QWidget()\n"
                            f"        layout = QVBoxLayout(central)\n\n"
                            f"        label = QLabel('Запущена главная форма модуля {name}')\n"
                            f"        label.setStyleSheet('font-size: 14px; font-weight: bold; margin: 20px;')\n"
                            f"        layout.addWidget(label)\n\n"
                            f"        btn = QPushButton('Закрыть')\n"
                            f"        btn.clicked.connect(window.close)\n"
                            f"        layout.addWidget(btn)\n\n"
                            f"        window.setCentralWidget(central)\n"
                            f"        window.show()\n\n"
                            f"        if created_app:\n"
                            f"            sys.exit(app.exec())\n")
                
                # form_name.qml
                form_qml_path = os.path.join(form_dir, form_name + ".qml")
                with open(form_qml_path, "w", encoding="utf-8") as f:
                    f.write("import QtQuick\nimport QtQuick.Controls\n\nWindow {\n    width: 640\n    height: 480\n    visible: true\n    title: \"QML Форма\"\n\n    Text {\n        anchors.centerIn: parent\n        text: \"Привет из QML!\"\n        font.pixelSize: 24\n    }\n}\n")
                
                # main.py
                main_path = os.path.join(mod_dir, "main.py")
                with open(main_path, "w", encoding="utf-8") as f:
                    f.write(f"import sys\nimport os\nsys.path.append(os.path.dirname(__file__))\nsys.path.append(os.path.join(os.path.dirname(__file__), 'forms'))\nfrom {form_name}.{form_name} import MainForm\n\nif __name__ == '__main__':\n    app = MainForm()\n    app.run()\n")
                
                # icon.py
                icon_path = os.path.join(mod_dir, "icon.py")
                with open(icon_path, "w", encoding="utf-8") as f:
                    f.write("from PIL import Image\ndef process_icon(input_path, output_path):\n    try:\n        img = Image.open(input_path)\n        img = img.resize((32, 32))\n        img.save(output_path)\n        return True\n    except:\n        return False\n")
                
                self.modulesChanged.emit()
                return True
            except Exception as e:
                print(f"Error creating module: {e}")
                return False
        return False

    @Slot(str, str, result=str)
    def saveModuleProperties(self, folder_name, properties_json_str):
        """
        Saves updated module properties (name, version, author, description, icon) in manifest.json.
        Renames folder if name property changes.
        """
        mod_dir = os.path.join(self.modules_dir, folder_name)
        if not os.path.exists(mod_dir):
            return folder_name
        try:
            properties = json.loads(properties_json_str)
            manifest_path = os.path.join(mod_dir, "manifest.json")
            
            # Read current manifest
            current = {}
            if os.path.exists(manifest_path):
                with open(manifest_path, "r", encoding="utf-8") as f:
                    current = json.load(f)
            
            # Update values
            current.update(properties)
            
            # Save manifest
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(current, f, ensure_ascii=False, indent=4)
                
            # If displayName/name changed, attempt to rename folder if it is safe
            new_folder_name = properties.get("name", folder_name).strip()
            # Clean folder name from bad characters
            new_folder_name = "".join(c for c in new_folder_name if c.isalnum() or c in ("_", "-"))
            if new_folder_name and new_folder_name != folder_name:
                new_mod_dir = os.path.join(self.modules_dir, new_folder_name)
                if not os.path.exists(new_mod_dir):
                    os.rename(mod_dir, new_mod_dir)
                    self.modulesChanged.emit()
                    return new_folder_name
            
            self.modulesChanged.emit()
            return folder_name
        except Exception as e:
            print(f"Error saving module properties: {e}")
            return folder_name

    @Slot(str, result=str)
    def readModuleProperties(self, folder_name):
        mod_dir = os.path.join(self.modules_dir, folder_name)
        manifest_path = os.path.join(mod_dir, "manifest.json")
        if os.path.exists(manifest_path):
            try:
                with open(manifest_path, "r", encoding="utf-8") as f:
                    return f.read()
            except:
                pass
        return "{}"

    # === [FORMS_CRUD] ===
    @Slot(str, str, result=bool)
    def createForm(self, module_folder, form_name):
        form_name = form_name.strip()
        if not form_name:
            return False
        form_name = "".join(c for c in form_name if c.isalnum() or c == "_")
        if not form_name:
            return False
            
        mod_dir = os.path.join(self.modules_dir, module_folder)
        forms_dir = os.path.join(mod_dir, "forms")
        os.makedirs(forms_dir, exist_ok=True)
        
        form_dir = os.path.join(forms_dir, form_name)
        if os.path.exists(form_dir):
            return False
            
        try:
            os.makedirs(form_dir)
            
            # form.json
            with open(os.path.join(form_dir, "form.json"), "w", encoding="utf-8") as f:
                json.dump({
                    "name": form_name,
                    "title": form_name,
                    "width": 800,
                    "height": 600
                }, f, ensure_ascii=False, indent=4)
                
            # Python script
            py_path = os.path.join(form_dir, f"{form_name}.py")
            with open(py_path, "w", encoding="utf-8") as f:
                f.write(f"import sys\n"
                        f"from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton\n\n"
                        f"class MainForm:\n"
                        f"    def run(self):\n"
                        f"        app = QApplication.instance()\n"
                        f"        created_app = False\n"
                        f"        if not app:\n"
                        f"            app = QApplication(sys.argv)\n"
                        f"            created_app = True\n\n"
                        f"        window = QMainWindow()\n"
                        f"        window.setWindowTitle('{form_name}')\n"
                        f"        window.resize(400, 300)\n\n"
                        f"        central = QWidget()\n"
                        f"        layout = QVBoxLayout(central)\n\n"
                        f"        label = QLabel('Запущена форма {form_name}')\n"
                        f"        label.setStyleSheet('font-size: 14px; margin: 20px;')\n"
                        f"        layout.addWidget(label)\n\n"
                        f"        window.setCentralWidget(central)\n"
                        f"        window.show()\n\n"
                        f"        if created_app:\n"
                        f"            sys.exit(app.exec())\n")
                        
            # QML file
            qml_path = os.path.join(form_dir, f"{form_name}.qml")
            with open(qml_path, "w", encoding="utf-8") as f:
                f.write("import QtQuick\nimport QtQuick.Controls\n\nWindow {\n    width: 640\n    height: 480\n    visible: true\n    title: \"QML Форма\"\n\n    Text {\n        anchors.centerIn: parent\n        text: \"Привет из QML!\"\n        font.pixelSize: 24\n    }\n}\n")
                
            self.modulesChanged.emit()
            return True
        except Exception as e:
            print(f"Error creating form: {e}")
            return False

    @Slot(str, str, result=str)
    def readFormProperties(self, module_folder, form_folder):
        form_json_path = os.path.join(self.modules_dir, module_folder, "forms", form_folder, "form.json")
        if os.path.exists(form_json_path):
            try:
                with open(form_json_path, "r", encoding="utf-8") as f:
                    return f.read()
            except:
                pass
        return "{}"

    @Slot(str, str, str, result=str)
    def saveFormProperties(self, module_folder, form_folder, properties_json_str):
        """
        Saves form.json changes. If renamed, handles folder and files renames inside forms/.
        """
        form_dir = os.path.join(self.modules_dir, module_folder, "forms", form_folder)
        if not os.path.exists(form_dir):
            return form_folder
        try:
            properties = json.loads(properties_json_str)
            form_json_path = os.path.join(form_dir, "form.json")
            
            current = {}
            if os.path.exists(form_json_path):
                with open(form_json_path, "r", encoding="utf-8") as f:
                    current = json.load(f)
            
            current.update(properties)
            
            with open(form_json_path, "w", encoding="utf-8") as f:
                json.dump(current, f, ensure_ascii=False, indent=4)
                
            # Handle renaming
            new_name = properties.get("name", form_folder).strip()
            new_name = "".join(c for c in new_name if c.isalnum() or c == "_")
            if new_name and new_name != form_folder:
                new_form_dir = os.path.join(self.modules_dir, module_folder, "forms", new_name)
                if not os.path.exists(new_form_dir):
                    # Rename files inside first
                    old_py_path = os.path.join(form_dir, f"{form_folder}.py")
                    new_py_path = os.path.join(form_dir, f"{new_name}.py")
                    if os.path.exists(old_py_path):
                        os.rename(old_py_path, new_py_path)
                        
                    old_qml_path = os.path.join(form_dir, f"{form_folder}.qml")
                    new_qml_path = os.path.join(form_dir, f"{new_name}.qml")
                    if os.path.exists(old_qml_path):
                        os.rename(old_qml_path, new_qml_path)
                        
                    # Now rename directory
                    os.rename(form_dir, new_form_dir)
                    
                    # Update main.py imports of the module
                    main_py_path = os.path.join(self.modules_dir, module_folder, "main.py")
                    if os.path.exists(main_py_path):
                        try:
                            with open(main_py_path, "r", encoding="utf-8") as f:
                                code = f.read()
                            # Replace old imports
                            code = code.replace(f"from {form_folder}.{form_folder} import", f"from {new_name}.{new_name} import")
                            code = code.replace(f"from {form_folder} import", f"from {new_name} import")
                            with open(main_py_path, "w", encoding="utf-8") as f:
                                f.write(code)
                        except Exception as ex:
                            print(f"Error updating main.py imports: {ex}")
                            
                    self.modulesChanged.emit()
                    return new_name
            self.modulesChanged.emit()
            return form_folder
        except Exception as e:
            print(f"Error saving form properties: {e}")
            return form_folder

    # === [FORM_FILES_CRUD] ===
    @Slot(str, str, result=str)
    def readFormFiles(self, module_folder, form_folder):
        """
        Reads python and qml files for form and returns JSON object with pyCode and qmlCode.
        """
        form_dir = os.path.join(self.modules_dir, module_folder, "forms", form_folder)
        py_path = os.path.join(form_dir, f"{form_folder}.py")
        qml_path = os.path.join(form_dir, f"{form_folder}.qml")
        
        py_code = ""
        qml_code = ""
        
        if os.path.exists(py_path):
            try:
                with open(py_path, "r", encoding="utf-8") as f:
                    py_code = f.read()
            except:
                pass
        if os.path.exists(qml_path):
            try:
                with open(qml_path, "r", encoding="utf-8") as f:
                    qml_code = f.read()
            except:
                pass
                
        return json.dumps({"pyCode": py_code, "qmlCode": qml_code}, ensure_ascii=False)

    @Slot(str, str, str, str, result=bool)
    def saveFormFiles(self, module_folder, form_folder, py_code, qml_code):
        form_dir = os.path.join(self.modules_dir, module_folder, "forms", form_folder)
        py_path = os.path.join(form_dir, f"{form_folder}.py")
        qml_path = os.path.join(form_dir, f"{form_folder}.qml")
        
        try:
            os.makedirs(form_dir, exist_ok=True)
            with open(py_path, "w", encoding="utf-8") as f:
                f.write(py_code)
            with open(qml_path, "w", encoding="utf-8") as f:
                f.write(qml_code)
            return True
        except Exception as e:
            print(f"Error saving form source code: {e}")
            return False

    @Slot(str, result=bool)
    def deleteModule(self, name):
        import shutil
        mod_dir = os.path.join(self.modules_dir, name)
        if os.path.exists(mod_dir) and os.path.isdir(mod_dir):
            try:
                shutil.rmtree(mod_dir)
                self.modulesChanged.emit()
                return True
            except Exception as e:
                print(f"Error deleting module: {e}")
                return False
        return False

    @Slot(str, str, result=bool)
    def deleteForm(self, module_folder, form_folder):
        import shutil
        form_dir = os.path.join(self.modules_dir, module_folder, "forms", form_folder)
        if os.path.exists(form_dir) and os.path.isdir(form_dir):
            try:
                shutil.rmtree(form_dir)
                self.modulesChanged.emit()
                return True
            except Exception as e:
                print(f"Error deleting form: {e}")
                return False
        return False

    # === [VARIABLES_CRUD] ===
    @Slot(str, result=int)
    def createVariable(self, module_folder):
        """
        Creates a default variable in variable.json.
        """
        var_path = os.path.join(self.modules_dir, module_folder, "variable.json")
        try:
            vars_list = []
            if os.path.exists(var_path):
                with open(var_path, "r", encoding="utf-8") as f:
                    try:
                        vars_list = json.load(f)
                    except:
                        vars_list = []
            
            # Find unique name
            names = {v.get("name") for v in vars_list}
            idx = 1
            while f"newVar{idx}" in names:
                idx += 1
            new_var = {
                "name": f"newVar{idx}",
                "type": "String",
                "value": "",
                "description": ""
            }
            vars_list.append(new_var)
            
            with open(var_path, "w", encoding="utf-8") as f:
                json.dump(vars_list, f, ensure_ascii=False, indent=4)
                
            self.modulesChanged.emit()
            return len(vars_list) - 1
        except Exception as e:
            print(f"Error creating variable: {e}")
            return -1

    @Slot(str, int, str, result=bool)
    def saveVariableProperties(self, module_folder, index, properties_json_str):
        var_path = os.path.join(self.modules_dir, module_folder, "variable.json")
        try:
            vars_list = []
            if os.path.exists(var_path):
                with open(var_path, "r", encoding="utf-8") as f:
                    vars_list = json.load(f)
            
            if 0 <= index < len(vars_list):
                properties = json.loads(properties_json_str)
                vars_list[index].update(properties)
                
                with open(var_path, "w", encoding="utf-8") as f:
                    json.dump(vars_list, f, ensure_ascii=False, indent=4)
                
                self.modulesChanged.emit()
                return True
        except Exception as e:
            print(f"Error saving variable: {e}")
        return False

    @Slot(str, int, result=str)
    def readVariableProperties(self, module_folder, index):
        var_path = os.path.join(self.modules_dir, module_folder, "variable.json")
        try:
            vars_list = []
            if os.path.exists(var_path):
                with open(var_path, "r", encoding="utf-8") as f:
                    vars_list = json.load(f)
            if 0 <= index < len(vars_list):
                return json.dumps(vars_list[index], ensure_ascii=False)
        except Exception as e:
            print(f"Error reading variable: {e}")
        return "{}"

    @Slot(str, int, result=bool)
    def deleteVariable(self, module_folder, index):
        var_path = os.path.join(self.modules_dir, module_folder, "variable.json")
        try:
            vars_list = []
            if os.path.exists(var_path):
                with open(var_path, "r", encoding="utf-8") as f:
                    vars_list = json.load(f)
            
            if 0 <= index < len(vars_list):
                vars_list.pop(index)
                with open(var_path, "w", encoding="utf-8") as f:
                    json.dump(vars_list, f, ensure_ascii=False, indent=4)
                
                self.modulesChanged.emit()
                return True
        except Exception as e:
            print(f"Error deleting variable: {e}")
        return False

    @Slot(str, str, result=bool)
    def saveModuleMain(self, name, content):
        main_path = os.path.join(self.modules_dir, name, "main.py")
        try:
            with open(main_path, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except:
            return False

    @Slot(str, str, result=bool)
    def exportModuleSource(self, name, dest_path):
        import shutil
        src_path = os.path.join(self.modules_dir, name)
        try:
            shutil.make_archive(dest_path, 'zip', src_path)
            return True
        except Exception as e:
            print(e)
            return False

    @Slot(str, str, str, result=bool)
    def exportModuleExe(self, name, dest_path, target_os):
        # Stub for executable export
        # In reality, you'd run pyinstaller here via QProcess or subprocess
        print(f"Экспорт {name} в вид без редактирования для {target_os} по пути {dest_path}")
        return True


    @Slot(result=list)
    def getModules(self):
        try:
            return [d for d in os.listdir(self.modules_dir) if os.path.isdir(os.path.join(self.modules_dir, d))]
        except:
            return []

    @Slot(str, result=str)
    def readModuleMain(self, name):
        main_path = os.path.join(self.modules_dir, name, "main.py")
        if os.path.exists(main_path):
            with open(main_path, "r", encoding="utf-8") as f:
                return f.read()
        return ""

# === [APP_ENTRY] ===
if __name__ == "__main__":
    app = QGuiApplication(sys.argv)
    engine = QQmlApplicationEngine()
    
    settings_manager = SettingsManager(app)
    terminal_manager = TerminalManager(app)
    app.aboutToQuit.connect(terminal_manager.close_all_sessions)
    helper = ConfigHelper(app)
    
    engine.rootContext().setContextProperty("SettingsManager", settings_manager)
    engine.rootContext().setContextProperty("TerminalManager", terminal_manager)
    engine.rootContext().setContextProperty("SysHelper", helper)
    
    initial_module = sys.argv[1] if len(sys.argv) > 1 else ""
    engine.rootContext().setContextProperty("initialModuleName", initial_module)
    
    qml_file = os.path.join(os.path.dirname(__file__), "configurator.qml")
    engine.load(qml_file)
    
    if not engine.rootObjects():
        sys.exit(-1)
        
    main_window = engine.rootObjects()[0]
    if platform.system() == "Windows":
        native_filter = Win32NativeEventFilter(main_window)
        app.installNativeEventFilter(native_filter)
        
        # Принудительно вызываем обновление рамки окна после установки фильтра,
        # чтобы Windows сразу отправил WM_NCCALCSIZE и убрал стандартный заголовок.
        hwnd = int(main_window.winId())
        SWP_NOMOVE = 0x0002
        SWP_NOSIZE = 0x0001
        SWP_NOZORDER = 0x0004
        SWP_FRAMECHANGED = 0x0020
        ctypes.windll.user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_FRAMECHANGED)
        
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    sys.exit(app.exec())