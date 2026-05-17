import sys
import os
import signal
import json
import platform

from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtCore import QObject, Slot, Property, Signal, QProcess

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


class ConfigHelper(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._app = QGuiApplication.instance()


if __name__ == "__main__":
    app = QGuiApplication(sys.argv)
    engine = QQmlApplicationEngine()
    
    settings_manager = SettingsManager(app)
    terminal_manager = TerminalManager(app)
    helper = ConfigHelper(app)
    
    engine.rootContext().setContextProperty("SettingsManager", settings_manager)
    engine.rootContext().setContextProperty("TerminalManager", terminal_manager)
    engine.rootContext().setContextProperty("SysHelper", helper)
    
    qml_file = os.path.join(os.path.dirname(__file__), "configurator.qml")
    engine.load(qml_file)
    
    if not engine.rootObjects():
        sys.exit(-1)
        
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    sys.exit(app.exec())