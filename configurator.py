import sys
import os
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

class MSG(ctypes.Structure):
    _fields_ = [
        ("hwnd", wintypes.HWND),
        ("message", wintypes.UINT),
        ("wParam", wintypes.WPARAM),
        ("lParam", wintypes.LPARAM),
        ("time", wintypes.DWORD),
        ("pt", wintypes.POINT),
    ]

class PythonHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None, is_dark=True):
        super().__init__(parent)
        self.highlightingRules = []

        # Color configurations based on theme
        if is_dark:
            keyword_color = "#569cd6"  # Blue
            string_color = "#ce9178"   # Orange
            comment_color = "#6a9955"  # Green
            function_color = "#dcdcaa" # Yellow
            number_color = "#b5cea8"   # Light Green
            self_color = "#9cdcfe"     # Light Blue
        else:
            keyword_color = "#0000ff"  # Blue
            string_color = "#a31515"   # Dark Red
            comment_color = "#008000"  # Green
            function_color = "#795e26" # Brown
            number_color = "#098658"   # Greenish
            self_color = "#000000"     # Black

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

class SettingsManager(QObject):
    themeChanged = Signal()
    encodingChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings_file = os.path.join(os.path.dirname(__file__), "settings.json")
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


class ConfigHelper(QObject):
    modulesChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._app = QGuiApplication.instance()
        self.primer_dir = r"c:\Новая папка\control_no_ai\primer"
        if not os.path.exists(self.primer_dir):
            os.makedirs(self.primer_dir)

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

    @Slot(QObject, bool)
    def highlightDocument(self, quick_doc, is_dark):
        doc = quick_doc.textDocument()
        highlighter = PythonHighlighter(doc, is_dark)
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

    @Slot(str, result=bool)
    def createModule(self, name):
        mod_dir = os.path.join(self.primer_dir, name)
        if not os.path.exists(mod_dir):
            try:
                os.makedirs(mod_dir)
                
                # Создаем папку формы
                form_name = "form_" + name
                form_dir = os.path.join(mod_dir, form_name)
                os.makedirs(form_dir)
                
                # Создаем form_name.py
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
                
                # Создаем main.py
                main_path = os.path.join(mod_dir, "main.py")
                with open(main_path, "w", encoding="utf-8") as f:
                    f.write(f"import sys\nimport os\nsys.path.append(os.path.dirname(__file__))\nfrom {form_name}.{form_name} import MainForm\n\nif __name__ == '__main__':\n    app = MainForm()\n    app.run()\n")
                
                # Создаем icon.py
                icon_path = os.path.join(mod_dir, "icon.py")
                with open(icon_path, "w", encoding="utf-8") as f:
                    f.write("from PIL import Image\n# Простая обработка иконки под стандарт (напр. steam 32x32)\ndef process_icon(input_path, output_path):\n    try:\n        img = Image.open(input_path)\n        img = img.resize((32, 32))\n        img.save(output_path)\n        return True\n    except:\n        return False\n")
                self.modulesChanged.emit()
                return True
            except Exception as e:
                print(e)
                return False
        return False

    @Slot(str, str, result=bool)
    def saveModuleMain(self, name, content):
        main_path = os.path.join(self.primer_dir, name, "main.py")
        try:
            with open(main_path, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except:
            return False

    @Slot(str, str, result=bool)
    def exportModuleSource(self, name, dest_path):
        import shutil
        src_path = os.path.join(self.primer_dir, name)
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
            return [d for d in os.listdir(self.primer_dir) if os.path.isdir(os.path.join(self.primer_dir, d))]
        except:
            return []

    @Slot(str, result=str)
    def readModuleMain(self, name):
        main_path = os.path.join(self.primer_dir, name, "main.py")
        if os.path.exists(main_path):
            with open(main_path, "r", encoding="utf-8") as f:
                return f.read()
        return ""

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