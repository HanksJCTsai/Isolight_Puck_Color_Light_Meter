import qdarkstyle
import sys
import os

from qdarkstyle.dark.palette import DarkPalette
from PyQt5 import QtWidgets

from controller.frame_controller import frame_controller


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt5', palette=DarkPalette()))
    MainFrame = frame_controller()
    MainFrame.show()
    sys.exit(app.exec_())