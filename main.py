import sys
import os
import signal

# DISABLE HIGH DPI SCALING to perfectly align multiple monitors 1:1
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "0"

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