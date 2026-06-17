import sys
import os
import signal
import paths

# Intercept command line for running dynamic modules within the compiled app context
if len(sys.argv) > 2 and sys.argv[1] == "--run-script":
    script_path = sys.argv[2]
    if os.path.exists(script_path):
        sys.path.insert(0, os.path.dirname(script_path))
        with open(script_path, "r", encoding="utf-8") as f:
            code = f.read()
        global_dict = {
            "__file__": script_path,
            "__name__": "__main__",
        }
        exec(code, global_dict)
    sys.exit(0)

# Configure Windows console to use system Active Code Page to prevent garbled text/mojibake
if sys.platform == "win32":
    try:
        import ctypes
        acp = ctypes.windll.kernel32.GetACP()
        ctypes.windll.kernel32.SetConsoleOutputCP(acp)
        ctypes.windll.kernel32.SetConsoleCP(acp)
    except Exception:
        pass

# Initialize folders and copy defaults if needed
paths.initialize_user_directories()

# DISABLE HIGH DPI SCALING to perfectly align multiple monitors 1:1
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "0"
os.environ["QT_QUICK_CONTROLS_STYLE"] = "Basic"

from PySide6.QtGui import QGuiApplication, QCursor, QRegion, QWindow
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtCore import QObject, Slot, QPoint, QRect

class SysHelper(QObject):
    def __init__(self, parent=None):
        
        super().__init__(parent)
        self._app = QGuiApplication.instance()

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

    @Slot(QObject, list, list)
    def updateMask(self, window, win_geom, ph_geom):
        if not isinstance(window, QWindow):
            return
            
        try:
            
            rect_main = QRect(int(win_geom[0] - 20), int(win_geom[1] - 20), 
                              int(win_geom[2] + 40), int(win_geom[3] + 40))
            combined_region = QRegion(rect_main)

            
            if ph_geom[4]: 
                rect_ph = QRect(int(ph_geom[0]), int(ph_geom[1]), 
                                int(ph_geom[2]), int(ph_geom[3]))
                combined_region = combined_region.united(QRegion(rect_ph))
            
            window.setMask(combined_region)
        except Exception as e:
            print(f"Mask Error: {e}")

    @Slot(result=list)
    def getModules(self):
        try:
            modules_dir = str(paths.MODULES_DIR)
            if os.path.exists(modules_dir):
                return [d for d in os.listdir(modules_dir) if os.path.isdir(os.path.join(modules_dir, d))]
        except Exception:
            pass
        return []

    @Slot(str)
    def runModule(self, name):
        import subprocess
        main_path = os.path.join(str(paths.MODULES_DIR), name, "main.py")
        if os.path.exists(main_path):
            if paths.IS_FROZEN:
                subprocess.Popen([sys.executable, "--run-script", main_path], cwd=os.path.dirname(main_path))
            else:
                subprocess.Popen([sys.executable, main_path], cwd=os.path.dirname(main_path))
            
    @Slot()
    def runConfigurator(self):
        import subprocess
        if paths.IS_FROZEN:
            exe_name = "Configurator.exe" if sys.platform == "win32" else "Configurator"
            config_path = os.path.join(str(paths.APP_DIR), exe_name)
            if os.path.exists(config_path):
                subprocess.Popen([config_path], cwd=str(paths.APP_DIR))
        else:
            config_path = os.path.join(str(paths.APP_DIR), "configurator.py")
            if os.path.exists(config_path):
                subprocess.Popen([sys.executable, config_path], cwd=str(paths.APP_DIR))

    @Slot(str)
    def editModule(self, name):
        import subprocess
        if paths.IS_FROZEN:
            exe_name = "Configurator.exe" if sys.platform == "win32" else "Configurator"
            config_path = os.path.join(str(paths.APP_DIR), exe_name)
            if os.path.exists(config_path):
                subprocess.Popen([config_path, name], cwd=str(paths.APP_DIR))
        else:
            config_path = os.path.join(str(paths.APP_DIR), "configurator.py")
            if os.path.exists(config_path):
                subprocess.Popen([sys.executable, config_path, name], cwd=str(paths.APP_DIR))

    @Slot(str, result=bool)
    def deleteModule(self, name):
        import shutil
        mod_dir = os.path.join(str(paths.MODULES_DIR), name)
        if os.path.exists(mod_dir) and os.path.isdir(mod_dir):
            try:
                shutil.rmtree(mod_dir)
                return True
            except Exception as e:
                print(f"Error deleting module: {e}")
                return False
        return False

if __name__ == "__main__":
    app = QGuiApplication(sys.argv)
    engine = QQmlApplicationEngine()
    helper = SysHelper()
    engine.rootContext().setContextProperty("SysHelper", helper)
    
    qml_file = os.path.join(os.path.dirname(__file__), "main.qml")
    engine.load(qml_file)
    
    if not engine.rootObjects():
        sys.exit(-1)
        
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    sys.exit(app.exec())