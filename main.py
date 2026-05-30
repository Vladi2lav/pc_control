import sys
import os
import signal

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
        primer_dir = r"c:\Новая папка\control_no_ai\primer"
        try:
            if os.path.exists(primer_dir):
                return [d for d in os.listdir(primer_dir) if os.path.isdir(os.path.join(primer_dir, d))]
        except Exception:
            pass
        return []

    @Slot(str)
    def runModule(self, name):
        import subprocess
        main_path = os.path.join(r"c:\Новая папка\control_no_ai\primer", name, "main.py")
        if os.path.exists(main_path):
            python_exe = sys.executable
            subprocess.Popen([python_exe, main_path], cwd=os.path.dirname(main_path))
            
    @Slot()
    def runConfigurator(self):
        import subprocess
        config_path = os.path.join(r"c:\Новая папка\control_no_ai", "configurator.py")
        if os.path.exists(config_path):
            python_exe = sys.executable
            subprocess.Popen([python_exe, config_path], cwd=r"c:\Новая папка\control_no_ai")

    @Slot(str)
    def editModule(self, name):
        import subprocess
        config_path = os.path.join(r"c:\Новая папка\control_no_ai", "configurator.py")
        if os.path.exists(config_path):
            python_exe = sys.executable
            subprocess.Popen([python_exe, config_path, name], cwd=r"c:\Новая папка\control_no_ai")

    @Slot(str, result=bool)
    def deleteModule(self, name):
        import shutil
        primer_dir = r"c:\Новая папка\control_no_ai\primer"
        mod_dir = os.path.join(primer_dir, name)
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